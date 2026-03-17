import asyncio
import time
import os
import sqlite3
import datetime
import requests
import sys
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from scraper import MBAScraper
from database import ScraperDatabase
from notifier import Notifier

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

async def job():
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting Scraper Job...")
    
    # Configuration via environment variables
    API_URL = os.environ.get("BACKEND_API_URL", "https://solmates-backend.onrender.com")
    API_KEY = os.environ.get("SCRAPER_API_KEY", "0c464de4beef5fc8c8bf52256d9b662a835247ae6e880c71a15d62bb02062601")
    
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
        # 1. RUN EXHAUSTIVE SCRAPE
        found_notices = await scraper.run(days_back=7)
        print(f"[JOB]: Deep Scan found {len(found_notices)} possible MBA items.")
        
        # 2. TRACK CURRENT ITEMS (For presence check)
        current_item_titles = set()
        current_item_links = set()
        current_items_on_site = set() # (title, link) tuples
        strict_mba_notices = []

        for n in found_notices:
            # Strict Filter (Double Check)
            if "MBA" in n['title'].upper() or "MBA" in n.get('description', '').upper():
                current_item_titles.add(n['title'])
                current_item_links.add(n['link'])
                current_items_on_site.add((n['title'], n['link']))
                strict_mba_notices.append(n)
        
        print(f"[JOB]: Filtered to {len(strict_mba_notices)} strict MBA items.")

        # 3. SEMESTER-WISE SYNC & CLEANUP
        for sem in ["1", "2", "3", "4", "0"]:
            print(f"[JOB]: Processing Semester {sem}...")
            backend_url = f"{API_URL}/api/sol/notifications/{sem}"
            try:
                resp = requests.get(backend_url)
                if resp.status_code != 200:
                    print(f"[JOB][ERROR]: Could not fetch backend for sem {sem}")
                    continue
                    
                backend_items = resp.json().get('data', [])
                backend_items_map = {item.get('title'): item for item in backend_items}

                # --- STEP A: SYNC / UPDATE ---
                for notice in strict_mba_notices:
                    if str(notice['semester']) != sem: continue
                    
                    link = notice['link']
                    title = notice['title']
                    backend_item = backend_items_map.get(title)
                    
                    if not backend_item:
                        if db.save_link(link, title, sem):
                            notice['semester'] = sem
                            notifier.sync_to_website(notice)
                    else:
                        # EXISTING: Update if link or description changed
                        curr_link = backend_item.get('link', '')
                        curr_desc = backend_item.get('description', '')
                        
                        if curr_link != link:
                            # LINK REFRESH: Scraper found a different URL
                            print(f"[JOB]: Link mismatch for {title}:")
                            print(f"       Backend: {curr_link}")
                            print(f"       Scraper: {link}")
                            notifier.update_on_website(sem, backend_item['id'], notice)
                        elif curr_desc != notice.get('description'):
                            # DESCRIPTION REFRESH: Corrected label or today/tomorrow
                            print(f"[JOB]: Description mismatch for Sem {sem} - {title}:")
                            print(f"       Backend: {curr_desc}")
                            print(f"       Scraper: {notice.get('description')}")
                            notifier.update_on_website(sem, backend_item['id'], notice)

                    # --- STEP B: CLEANUP ---
                    for item in backend_items:
                        title = item.get('title', '')
                        link = item.get('link', '')
                        item_id = item.get('id', '')
                        item_date_str = item.get('date', '') # YYYY-MM-DD
                        
                        pass
                        
            except Exception as e:
                print(f"[JOB][ERROR]: Failed processing sem {sem}: {e}")
        
        # Cleanup expired existing notifications
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [CLEANUP]: Checking for expired notices...")
        
        # Get current IST date and time
        now_utc = datetime.datetime.utcnow()
        ist_offset = datetime.timedelta(hours=5, minutes=30)
        now_ist = now_utc + ist_offset
        current_date_obj = now_ist.date()

        for sem in [1, 2, 3, 4, 0]:
            try:
                notices = notifier.get_from_website(sem)
                if not notices: continue
                
                for notice in notices:
                    notice_id = notice.get('id')
                    notice_title = notice.get('title', '')
                    notice_date_str = notice.get('date', '') # Expects YYYY-MM-DD
                    
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
                            # RELAXED CLEANUP: Only remove if older than 7 days (preserve some history)
                            cleanup_threshold = current_date_obj - datetime.timedelta(days=7)
                            if item_date < cleanup_threshold:
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
        fifteen_days_ago = datetime.datetime.now() - datetime.timedelta(days=15)
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM notices WHERE processed_at < ?", (fifteen_days_ago.isoformat(),))
            except: pass

        print(f"[JOB]: Finished Scraper Job.")
        
    except Exception as e:
        print(f"[ERROR]: Job failed: {e}")

async def main():
    # Start Health Check Server in a separate thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    run_once = "--once" in sys.argv

    if run_once:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MBA Scraper - Running One-Shot Job...")
        await job()
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] One-Shot Job Complete.")
        return

    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MBA Scraper Service Initializing...")
    print(f"Interval: 2 minutes | IST-Aware Cleanup: ENABLED")
    while True:
        await job()
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SLEEP]: Scan complete. Next check in 120 seconds...")
        await asyncio.sleep(120)

if __name__ == "__main__":
    asyncio.run(main())
