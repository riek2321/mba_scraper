import asyncio
import time
import os
import sqlite3
import datetime
try:
    import requests # type: ignore
except ImportError:
    pass
import sys
import re
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
try:
    from scraper import MBAScraper # type: ignore
    from database import ScraperDatabase # type: ignore
    from notifier import Notifier # type: ignore
except ImportError:
    pass

# Tiny Health Check Server for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Scraper is Alive")
    def log_message(self, format, *args): return # Silence logs

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"[HEALTH]: Started on port {port}")
    server.serve_forever()

async def job(targets=None):
    # V18.6: Even in targeted scans, ensure legacy fallback is included if seeking classes
    if targets is not None:
        if any("online-class-schedule" in t for t in targets):
            legacy_url = "https://sol.du.ac.in/all-notices.php"
            if legacy_url not in targets:
                targets.append(legacy_url)

    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Scraper Job (Targeted: {targets is not None})...")
    
    # v17.0: PRODUCTION UNIFIED CONFIGURATION
    API_URL = os.environ.get("BACKEND_URL", "https://solmates-backend.onrender.com")
    API_KEY = os.environ.get("SCRAPER_KEY", "0c464de4beef5fc8c8bf52256d9b662a835247ae6e880c71a15d62bb02062601")
    
    scraper = MBAScraper()
    db = ScraperDatabase()
    notifier = Notifier(api_url=API_URL, scraper_key=API_KEY)
    
    # Check if this is the first run (seeding)
    is_empty = False
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM notices")
        is_empty = cursor.fetchone()[0] == 0

    try:
        # Pre-Check for Subdomain Health (Watchdog) - V17.0 Stealth
        HEALTH_URL = "https://web.sol.du.ac.in/home"
        
        # Only probe if we are doing a full scan or if home is targeted
        if targets is None or HEALTH_URL in targets:
            print(f"[WATCHDOG]: Probing Subdomain Health...")
            try:
                # Use very stealthy headers for the probe (Matching v17.0 Scraper)
                probe_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "max-age=0",
                    "Sec-Ch-Ua": '"Microsoft Edge";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1"
                }
                resp = requests.get(HEALTH_URL, headers=probe_headers, timeout=20)
                
                if resp.status_code != 200:
                    print(f"[WATCHDOG][WARNING]: Subdomain Health returned {resp.status_code}.")
                else:
                    print(f"[WATCHDOG][ONLINE]: Subdomain is reachable!")
            except Exception as e:
                print(f"[WATCHDOG][FAIL]: Connection failed: {e}.")

        # 1. RUN TARGETED OR EXHAUSTIVE SCRAPE
        found_notices = await scraper.run(days_back=15, targets=targets)
        # v16.0: None guard for return value
        found_notices = found_notices if found_notices is not None else []
        print(f"[JOB]: Scan found {len(found_notices)} possible MBA items.") # type: ignore
        
        # 2. TRACK CURRENT ITEMS (For presence check)
        current_item_titles = set()
        current_item_links = set()
        current_items_on_site = set() # (title, link) tuples
        strict_mba_notices = []

        for n in found_notices: # type: ignore
            # Strict Filter (Double Check)
            if "MBA" in n['title'].upper() or "MBA" in n.get('description', '').upper(): # type: ignore
                current_item_titles.add(n['title']) # type: ignore
                current_item_links.add(n['link']) # type: ignore
                current_items_on_site.add((n['title'], n['link'])) # type: ignore
                strict_mba_notices.append(n)
        
        print(f"[JOB]: Filtered to {len(strict_mba_notices)} strict MBA items.")

        # 3. SEMESTER-WISE SYNC & CLEANUP
        for sem in ["1", "2", "3", "4", "0"]:
            print(f"[JOB]: Processing Semester {sem}...")
            backend_url = f"{API_URL}/api/sol/notifications/{sem}"
            try:
                backend_items = notifier.get_from_website(sem)
                if backend_items is None: # Critical failure even after retries
                    print(f"[JOB][ERROR]: Could not fetch backend for sem {sem} after retries")
                    continue
                    
                backend_items_map = {item.get('title'): item for item in backend_items}

                # --- STEP A: SYNC / UPDATE ---
                for notice in strict_mba_notices:
                    if str(notice['semester']) != sem: continue
                    
                    link = notice['link']
                    title = notice['title']
                    backend_item = backend_items_map.get(title)
                    
                    if not backend_item:
                        # NEW or DELETED: If it's in our DB but not backend, it was likely processed once and then deleted.
                        # We only sync if it's NOT in our DB.
                        if db.save_link(link, title, sem):
                            print(f"[JOB]: New item found, syncing to backend: {title}")
                            notice['semester'] = sem # type: ignore
                            notifier.sync_to_website(notice) # type: ignore
                        else:
                            # Already in DB but missing from backend = Already processed + Deleted by admin.
                            # We respect the deletion and DON'T re-sync.
                            pass
                    else:
                        # EXISTING: Update if link or description changed
                        curr_link = backend_item.get('link', '')
                        curr_desc = backend_item.get('description', '')
                        
                        if curr_link != link:
                            # LINK REFRESH: Scraper found a different URL
                            print(f"[JOB]: Link mismatch for {title}:")
                            print(f"       Backend: {curr_link}")
                            print(f"       Scraper: {link}")
                            notifier.update_on_website(sem, backend_item['id'], notice) # type: ignore
                        elif curr_desc != notice.get('description'): # type: ignore
                            # DESCRIPTION REFRESH: Corrected label or today/tomorrow
                            print(f"[JOB]: Description mismatch for Sem {sem} - {title}:")
                            print(f"       Backend: {curr_desc}")
                            print(f"       Scraper: {notice.get('description')}") # type: ignore
                            notifier.update_on_website(sem, backend_item['id'], notice) # type: ignore

                    # --- STEP B: CLEANUP ---
                    for item in backend_items:
                        title = item.get('title', '')
                        desc = item.get('description', '')
                        item_id = item.get('id', '')
                        item_date_str = item.get('date', '') # YYYY-MM-DD
                        
                        is_live_class = "MBA Live Class" in desc or ("[" in title and "] MBA Sem" in title)
                        
                        if is_live_class and title not in current_item_titles:
                            # The live class is no longer on the DU class schedule (or has passed).
                            print(f"[JOB][CLEANUP]: Live Class finished/removed. Deleting: {title}")
                            notifier.delete_from_website(sem, item_id)
            except Exception as e:
                print(f"[JOB][ERROR]: Failed processing sem {sem}: {e}")
        
        # Cleanup expired existing notifications
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [CLEANUP]: Checking for expired notices...")
        
        # Get current IST date and time
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        ist_offset = datetime.timedelta(hours=5, minutes=30)
        now_ist = now_utc + ist_offset
        current_date_obj = now_ist.date()

        for sem in [1, 2, 3, 4, 0]:
            try:
                notices = notifier.get_from_website(sem)
                if not notices: continue
                
                for notice in notices:
                    if not isinstance(notice, dict): continue # v17.0 Guard
                    notice_id = notice.get('id')
                    notice_title = notice.get('title', '')
                    notice_desc = notice.get('description', '')
                    notice_date_str = str(notice.get('date', ''))
                    
                    # V18.5: Properly define is_live_class in this scope
                    is_live_class = "MBA Live Class" in notice_desc or ("[" in notice_title and "] MBA Sem" in notice_title)
                    
                    try:
                        item_date = None
                        # Standard YYYY-MM-DD (from scraper)
                        if notice_date_str and "-" in notice_date_str and len(notice_date_str) == 10:
                            try:
                                item_date = datetime.datetime.strptime(notice_date_str, "%Y-%m-%d").date()
                            except: pass
                        
                        # Fallback for DD-MM-YYYY or DD Month YYYY
                        if not item_date and notice_date_str:
                            if "-" in notice_date_str:
                                parts = notice_date_str.split("-")
                                if len(parts) == 3:
                                    # Try DD-MM-YYYY
                                    try: 
                                        if len(parts[0]) == 4: # YYYY-MM-DD
                                            item_date = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                                        else: # DD-MM-YYYY
                                            item_date = datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
                                    except: pass
                            elif " " in notice_date_str:
                                parts = notice_date_str.split()
                                if len(parts) >= 3:
                                    try:
                                        day = int(parts[0])
                                        months = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6, 
                                                 "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
                                        month_str = parts[1]
                                        month = months.get(month_str, 3) 
                                        year = int(parts[2])
                                        item_date = datetime.date(year, month, day)
                                    except: pass

                        if item_date:
                            # STRICT CLEANUP for Live Classes: Delete if date is past
                            if is_live_class and item_date < current_date_obj:
                                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [CLEANUP]: Removing past live class: {notice_title} ({notice_date_str})")
                                notifier.delete_from_website(sem, notice_id)
                                continue

                            # RELAXED CLEANUP for other notices: Only remove if older than 15 days
                            cleanup_threshold = current_date_obj - datetime.timedelta(days=15)
                            if not is_live_class and item_date < cleanup_threshold:
                                print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [CLEANUP]: Removing very old notice: {notice_title} ({notice_date_str})")
                                notifier.delete_from_website(sem, notice_id)
                                continue

                            # If it's today, check if the specific time has passed (Expiring classes for TODAY)
                            if item_date == current_date_obj:
                                class_time_raw = notice.get('class_time', '')
                                # Example time format: "2:00 PM - 3:00 PM" or "10:00 AM"
                                if class_time_raw:
                                    time_parts = re.split(r'[-–]', class_time_raw)
                                    end_time_str = time_parts[-1].strip()
                                    
                                    try:
                                        # Convert to 24h for comparison
                                        end_time_obj = datetime.datetime.strptime(end_time_str, "%I:%M %p").time()
                                        # Use IST time for comparison
                                        if now_ist.time() > end_time_obj:
                                            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [CLEANUP]: Removing expired today's notice: {notice_title} ({class_time_raw})")
                                            notifier.delete_from_website(sem, notice_id)
                                    except: pass
                    except Exception as e:
                        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [CLEANUP][ERROR]: Failed to parse date '{notice_date_str}': {e}")
            except Exception as e:
                print(f"[CLEANUP][ERROR]: Failed sem {sem} cleanup: {e}")


        # 5. LOCAL DB CLEANUP
        # PERPETUAL MEMORY: Keep records for 365 days to remember admin deletions
        one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            try:
                # Keep items for a full year to prevent re-syncing items deleted by admin
                cursor.execute("DELETE FROM notices WHERE date < ?", (one_year_ago.strftime("%Y-%m-%d"),))
            except: pass

        print(f"[JOB]: Finished Scraper Job.")
        
    except Exception as e:
        # v19.2: Handle Unicode in Errors (box characters etc)
        error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        print(f"[ERROR]: Job failed: {error_msg}")

def keep_alive():
    """Self-ping to prevent Render sleep (Free Tier)"""
    url = os.environ.get("SELF_URL", "https://mba-scraper.onrender.com")
    while True:
        try:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [KEEP-ALIVE]: Pinging {url}...")
            requests.get(url, timeout=10)
        except Exception as e:
            print(f"[KEEP-ALIVE][ERROR]: {e}")
        time.sleep(600) # Ping every 10 minutes

async def main():
    # Start Health Check Server in a separate thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Start Keep-Alive Pinger in a separate thread
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()

    run_once = "--once" in sys.argv

    if run_once:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MBA Scraper - Running One-Shot Job...")
        await job()
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] One-Shot Job Complete.")
        return

    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MBA Scraper Service Initializing...")
    print(f"Mode: PATIENT Watchdog | Pulse: 300s | Full Scan: 900s")
    
    pulse_index = 0
    CLASS_URL = "https://web.sol.du.ac.in/info/online-class-schedule"
    
    while True:
        try:
            # Every 3rd pulse (0, 3, 6...) run a FULL SCAN (900 seconds)
            if pulse_index % 3 == 0: # type: ignore
                print(f"\n[PULSE {pulse_index}]: Triggering FULL SCAN...")
                await job(targets=None) 
            else:
                # Other pulses run TARGETED CLASS SCAN (every 300 seconds)
                print(f"\n[PULSE {pulse_index}]: Triggering TARGETED CLASS SCAN...")
                # targeted class scan now uses the internal target name in scraper.py
                await job(targets=["https://web.sol.du.ac.in/info/online-class-schedule"])
            
            pulse_index += 1 # type: ignore
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SLEEP]: Pulse complete. Next pulse in 300 seconds...")
            await asyncio.sleep(300)
            
        except Exception as e:
            print(f"[MAIN][ERROR]: Loop error: {e}")
            await asyncio.sleep(60) # Recover delay

if __name__ == "__main__":
    asyncio.run(main())
