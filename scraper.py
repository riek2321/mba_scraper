import asyncio
import datetime
import re
import random
import os
import json
from typing import List, Dict, Any, Optional

# Attempted imports for IDE support
try:
    from playwright.async_api import async_playwright, Page, BrowserContext # type: ignore
except ImportError:
    pass

try:
    import dateutil.parser as dparser # type: ignore
except ImportError:
    pass

try:
    from playwright_stealth import stealth_async # type: ignore
except ImportError:
    pass

# Internal project import
try:
    from notifier import Notifier # type: ignore
except ImportError:
    pass

try:
    import requests # type: ignore
    from curl_cffi import requests as cffi_requests # type: ignore
    from bs4 import BeautifulSoup # type: ignore
except ImportError:
    pass

class MBAScraper:
    def __init__(self, base_url: str = "https://web.sol.du.ac.in/home"):
        self.base_url = base_url
        self.keywords = ['MBA', 'Master of Business Administration']
        self.visited = set()
        self.notices = []
        self.days_back = 15 # Default
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.94 Safari/537.36"
        self.scraper_api_key = os.environ.get("SCRAPER_API_KEY", "652ee4df232c710d89ef5c6a7b5df80d")
        print(f"[JOB]: Scraper API Key configured: {'YES' if self.scraper_api_key else 'NO'}")
        print(f"[JOB]: Scraper Backend Key configured: {'YES' if os.environ.get('SCRAPER_KEY') else 'NO'}")
        self.targets = [
            "https://sol.du.ac.in/home.php",
            "https://web.sol.du.ac.in/my/team_schedules/vcs.php", # Direct Target (v19.1)
            "https://sol.du.ac.in/all-notices.php"
        ]

    async def fetch_via_api(self, url: str) -> Optional[str]:
        """V50.0: Level 3 Bypass via Scraping API (Residential Proxies)"""
        if not self.scraper_api_key:
            return None
            
        print(f"[CRAWLER][API]: Attempting residential proxy fetch for {url}...")
        try:
            # ScraperAPI format
            api_url = f"http://api.scraperapi.com?api_key={self.scraper_api_key}&url={url}"
            # Add render_js=true if hitting the main page, but direct vcs.php might not need it
            if "vcs.php" not in url:
                api_url += "&render_js=true"
                
            loop = asyncio.get_event_loop()
            # Fix: provide a clear function for run_in_executor
            def sync_get(u):
                return requests.get(u, timeout=60)
                
            response = await loop.run_in_executor(None, sync_get, api_url)
            
            if response.status_code == 200:
                print(f"[CRAWLER][API]: Success! Fetched {len(response.text)} chars.")
                return response.text
            else:
                print(f"[CRAWLER][API]: Failed with status {response.status_code}")
                return None
        except Exception as e:
            print(f"[CRAWLER][API][ERROR]: {e}")
            return None

    async def fetch_schedule_cffi(self) -> list:
        """V35.0: TLS Fingerprint Impersonation via curl_cffi"""
        print("[CRAWLER][CFFI]: Attempting Chrome TLS impersonation...")
        try:
            session = cffi_requests.Session(impersonate="chrome120")
            
            # Step 1: Prime session on main portal
            session.get("https://sol.du.ac.in/home.php", timeout=30)
            
            # Step 2: Hit subdomain home
            session.get("https://web.sol.du.ac.in/home", timeout=30)
            
            # Step 3: Fetch the actual schedule page
            r = session.get(
                "https://web.sol.du.ac.in/info/online-class-schedule",
                headers={
                    "Referer": "https://web.sol.du.ac.in/home",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
                },
                timeout=30
            )
            
            print(f"[CRAWLER][CFFI]: Response status: {r.status_code}")
            
            if r.status_code == 403:
                print("[CRAWLER][CFFI]: Still 403. WAF is very aggressive.")
                return []
            
            # Parse the HTML
            soup = BeautifulSoup(r.text, "html.parser")
            tables = soup.find_all("table")
            print(f"[CRAWLER][CFFI]: Found {len(tables)} tables.")
            
            results = []
            for table in tables:
                rows = table.find_all("tr")
                # Find date row
                date_str = None
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    text = " ".join(c.get_text(strip=True) for c in cells)
                    if "date:" in text.lower():
                        # Extract 10-character date like 19-03-2026
                        m = re.search(r'(\d{1,2}[-/]\d{2}[-/]\d{4})', text)
                        if m:
                            date_str = m.group(1)
                            break
                
                if not date_str:
                    continue
                
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) < 4:
                        continue
                    row_text = " ".join(c.get_text(strip=True) for c in cells)
                    if not any(kw.lower() in row_text.lower() for kw in self.keywords):
                        continue
                    
                    course = cells[0].get_text(strip=True)
                    sem = cells[1].get_text(strip=True)
                    subject = cells[2].get_text(strip=True)
                    time_text = ""
                    for c in cells:
                        t = c.get_text(strip=True)
                        if re.search(r'\d{1,2}:\d{2}', t):
                            time_text = t
                            break
                    
                    href = None
                    link_tag = None
                    for c in reversed(cells):
                        a = c.find("a")
                        if a and a.get("href"):
                            href = a["href"]
                            link_tag = a
                            break
                    
                    semester = self.extract_semester_logic(sem or course)
                    title = f"[{str(date_str)}] {course} Sem {semester}: {subject} ({time_text})"
                    print(f"[CRAWLER][CFFI CLASS FOUND]: {title}")
                    results.append({
                        "title": str(title),
                        "link": str(href) if href else "#pending",
                        "semester": str(semester),
                        "date": self.parse_date(str(date_str)),
                        "class_time": str(time_text),
                        "description": f"MBA Live Class: {subject}. Time: {time_text}."
                    })
            
            return results
        except Exception as e:
            print(f"[CRAWLER][CFFI][ERROR]: {e}")
            return []

    async def run(self, days_back: int = 15, targets: Optional[List[str]] = None):
        """v19.2: DUAL-ENGINE (Firefox) + LEGACY PROMOTION"""
        self.days_back = days_back
        async with async_playwright() as p:
            # V19.6: Pure Chromium + Natural Navigation (Final Production)
            print("[CRAWLER]: Launching Chromium Engine (v17.6 Stable Target)...")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--window-position=0,0',
                    '--ignore-certifcate-errors',
                    '--ignore-certifcate-errors-spki-list'
                ]
            )
            
            headers = {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "User-Agent": self.user_agent,
                "Upgrade-Insecure-Requests": "1"
            }
            
            viewports = [
                {'width': 1366, 'height': 768},
                {'width': 1536, 'height': 864},
                {'width': 1920, 'height': 1080}
            ]
            
            context = await browser.new_context(
                user_agent=self.user_agent,
                extra_http_headers=headers,
                viewport=random.choice(viewports)
            )
            page = await context.new_page()
            
            try:
                await stealth_async(page)
                print("[CRAWLER]: Stealth signatures applied.")
            except Exception: pass

            print("[CRAWLER]: Priming NATURAL NAVIGATION Session...")
            try:
                # Step 0: Main portal
                print("[CRAWLER][PRIMER]: Visiting Main Portal...")
                await page.goto("https://sol.du.ac.in/home.php", wait_until="domcontentloaded", timeout=120000)
                await asyncio.sleep(2)

                # Step 1: Subdomain Home
                print("[CRAWLER][PRIMER]: Visiting Subdomain Home...")
                await page.goto("https://web.sol.du.ac.in/home", wait_until="domcontentloaded", timeout=120000)
                await asyncio.sleep(3)
                
                # V17.5 Natural Navigation: Click via UI instead of direct jump
                print("[CRAWLER][PRIMER]: Clicking 'Student Support' (Natural Flow)...")
                try:
                    # Look for links that might lead to support/classes
                    await page.locator("text='Student Support'").first.click(timeout=10000)
                    await asyncio.sleep(2)
                except Exception:
                    # Fallback to direct jump if click fails, but prefer click
                    await page.goto("https://web.sol.du.ac.in/info/student-support", wait_until="domcontentloaded", timeout=60000)
            except Exception as e: 
                print(f"[CRAWLER][PRIMER][WARNING]: Natural flow warning: {e}")

            # v15.0: REQUEST INTERCEPTION (Bypass 403)
            async def intercept_vcs(route):
                h = {**route.request.headers}
                h["Referer"] = "https://web.sol.du.ac.in/info/online-class-schedule"
                await route.continue_(headers=h)
            
            await context.route("**/vcs.php", intercept_vcs)

            actual_targets = targets if targets else self.targets
            print(f"[CRAWLER]: Starting scan of {len(actual_targets)} target areas sequentially")

            for url in actual_targets:
                try:
                    print(f"[CRAWLER][DIRECT]: Visiting target {url}")
                    
                    if "vcs.php" in url or "online-class-schedule" in url:
                        # V50.0: Level 3 Bypass (Scraping API) - Try FIRST on server
                        if self.scraper_api_key:
                            api_html = await self.fetch_via_api(url)
                            if api_html:
                                try:
                                    # Create a temporary page to reuse extraction logic
                                    api_page = await context.new_page()
                                    await api_page.set_content(api_html)
                                    await self.extract_online_classes(api_page)
                                    await api_page.close()
                                    print("[CRAWLER][API]: SUCCESS! Data extracted via residential proxy.")
                                    return
                                except Exception as e:
                                    print(f"[CRAWLER][API][ERROR]: Extraction failed: {e}")

                        # V35.0: Try TLS impersonation (Fallback)
                        cffi_results = await self.fetch_schedule_cffi()
                        if cffi_results:
                            self.notices.extend(cffi_results)
                            print(f"[CRAWLER][CFFI]: SUCCESS! Got {len(cffi_results)} classes.")
                            return
                        
                        print("[CRAWLER][CFFI]: Failed, falling back to Playwright flows...")

                        # V38.0: IFRAME-HEADER GHOST FETCH
                        # Key insight: server checks sec-fetch-dest: iframe + AWSALB sticky session
                        print("[CRAWLER]: Initiating IFRAME-HEADER GHOST FETCH for Schedule...")
                        
                        try:
                            # 1. Visit parent page first to acquire AWSALB + PHPSESSID cookies
                            print("[CRAWLER][GHOST]: Acquiring session cookies via parent page...")
                            await page.goto("https://web.sol.du.ac.in/info/online-class-schedule", wait_until="networkidle", timeout=60000)
                            await asyncio.sleep(5)
                            
                            # 2. Use context.request with EXACT iframe headers from real browser
                            print("[CRAWLER][GHOST]: Executing iframe-spoofed request to vcs.php...")
                            response = await context.request.get(
                                "https://web.sol.du.ac.in/my/team_schedules/vcs.php",
                                headers={
                                    "referer": "https://web.sol.du.ac.in/info/online-class-schedule",
                                    "sec-fetch-dest": "iframe",
                                    "sec-fetch-mode": "navigate",
                                    "sec-fetch-site": "same-origin",
                                    "upgrade-insecure-requests": "1",
                                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                                    "accept-language": "en-IN,en;q=0.9,hi;q=0.8",
                                }
                            )
                            
                            print(f"[CRAWLER][GHOST]: Response status: {response.status}")
                            if response.ok:
                                print("[CRAWLER][GHOST]: Fetch SUCCESS. Parsing content.")
                                html_content = await response.text()
                                ghost_page = await context.new_page()
                                await ghost_page.set_content(html_content)
                                await self.extract_online_classes(ghost_page)
                                await ghost_page.close()
                                return
                            else:
                                print(f"[CRAWLER][GHOST][WARNING]: Ghost fetch failed with status {response.status}. Falling back to click flow.")
                        except Exception as e:
                            print(f"[CRAWLER][GHOST][ERROR]: Ghost protocol failed: {e}. Falling back to click flow.")

                        # V27.0: ULTIMATE CLICK-THROUGH BYPASS (Restored as Fallback)
                        print("[CRAWLER]: Executing Click-Through Bypass for Schedule...")
                        try:
                            # 1. Start at Subdomain Home (to drop session cookies)
                            print("[CRAWLER][BYPASS]: Visiting Subdomain Home (home.php)...")
                            await page.goto("https://sol.du.ac.in/home.php", wait_until="networkidle", timeout=60000)
                            await asyncio.sleep(3)
                            
                            # 2. Click 'Online Class Schedule' link and CAPTURE NEW PAGE
                            link_selector = "a:has-text('Online Class Schedule')"
                            await page.wait_for_selector(link_selector, timeout=20000)
                            
                            async with context.expect_page(timeout=30000) as new_page_info:
                                await page.click(link_selector)
                            target_page = await new_page_info.value
                            
                            print("[CRAWLER][BYPASS]: Captured NEW TAB. Parsing...")
                            await target_page.wait_for_load_state("load", timeout=60000)
                            await asyncio.sleep(5)
                            await self.extract_online_classes(target_page)
                            return
                        except Exception as e:
                            print(f"[CRAWLER][BYPASS][ERROR]: Click Flow failed: {e}.")
                    else:
                        await page.goto(url, wait_until="domcontentloaded", timeout=90000)
                        await asyncio.sleep(random.uniform(2, 5))
                        await self.expand_content(page)
                        await self.auto_scroll(page)
                        
                        if "sol.du.ac.in" in url and ("all-notices" in url or "home.php" in url):
                            await self.extract_legacy_notices(page)
                        
                        await self.extract_mba_content(page)
                except Exception as e:
                    print(f"[CRAWLER][ERROR]: Failed to visit {url}: {e}")

            await browser.close()
            print(f"[JOB]: Scan found {len(self.notices)} possible MBA items.")
            return self.notices # v16.0: Fix NoneType error in main.py

    async def extract_online_classes(self, page):
        """V36.0: IFRAME-AWARE EXTRACTION (Targeting dynamic vcs.php)"""
        print(f"[CRAWLER]: Analyzing Class Schedule on {page.url}")
        
        try:
            # 1. IFRAME DETECTION: Get all iframe srcs from the page
            raw_srcs = await page.evaluate("""() => 
                Array.from(document.querySelectorAll('iframe')).map(f => {
                    try { return f.src; } catch(e) { return null; }
                }).filter(src => src !== null)
            """)
            iframe_srcs = list(raw_srcs) if isinstance(raw_srcs, list) else []
            print(f"[CRAWLER][IFRAME]: Found {len(iframe_srcs)} iframes.")
            
            # 2. TARGET SELECTION: Find vcs.php iframe specifically
            vcs_url = next((s for s in iframe_srcs if 'vcs' in s.lower() or 'team_schedules' in s.lower()), None)
            
            target_ctx = page
            vcs_page = None
            
            if vcs_url:
                print(f"[CRAWLER][IFRAME]: Direct Hit! Navigating to: {vcs_url}")
                try:
                    # Open vcs_url as a new page WITH the parent page's referer to bypass WAF
                    vcs_page = await page.context.new_page()
                    await vcs_page.goto(vcs_url, 
                        wait_until="networkidle", 
                        timeout=60000,
                        referer="https://web.sol.du.ac.in/info/online-class-schedule"
                    )
                    await asyncio.sleep(5)
                    target_ctx = vcs_page
                except Exception as e:
                    print(f"[CRAWLER][IFRAME][ERROR]: Failed to navigate into iframe: {e}. Falling back to page scan.")
                    target_ctx = page
            else:
                print("[CRAWLER][IFRAME]: No vcs iframe found, scanning all available frames...")
                target_ctx = page

            # 3. EXTRACTION: Now extract tables from target_ctx
            all_raw_tables = []
            
            # Start with the targeted context
            contexts_to_scan = [target_ctx]
            
            # Add frames if target_ctx is a Page-like object
            try:
                # Type safe way to get frames
                if hasattr(target_ctx, "frames"):
                    # Use a temporary variable to help the type checker
                    frames_list = getattr(target_ctx, "frames")
                    if isinstance(frames_list, list):
                        for f in frames_list:
                            contexts_to_scan.append(f)
            except Exception: pass
            
            print(f"[CRAWLER]: Accessing {len(contexts_to_scan)} contexts for table extraction.")
            
            for ctx in contexts_to_scan:
                try:
                    # Optimized JS for row-level cell extraction
                    tables_data = await ctx.evaluate("""() => {
                        try {
                            const found_tables = document.querySelectorAll('table');
                            return Array.from(found_tables).map(table => {
                                return Array.from(table.querySelectorAll('tr')).map(tr => 
                                    Array.from(tr.querySelectorAll('td, th')).map(cell => {
                                        const a = cell.querySelector('a');
                                        return { text: cell.innerText.trim(), href: a ? a.href : null };
                                    })
                                );
                            });
                        } catch (e) { return null; }
                    }""")
                    if isinstance(tables_data, list):
                        for t in tables_data: all_raw_tables.append(t)
                except Exception: continue

            print(f"[CRAWLER]: Final raw table count: {len(all_raw_tables)}")
            
            # Close the temporary iframe page if created
            if vcs_page is not None:
                try:
                    await getattr(vcs_page, "close")()
                except Exception: pass
            
            # V26.4: CRITICAL CONTENT LOGGING
            if len(all_raw_tables) == 0:
                print(f"[CRAWLER][DIAGNOSTIC]: Page URL: {page.url}")
                page_content = await page.content()
                clean_content = page_content[:2000].replace("\n", " ")
                print(f"[CRAWLER][DIAGNOSTIC]: FULL PAGE CONTENT SNIPPET: {clean_content}")
                if "403 Forbidden" in page_content or "Access Denied" in page_content:
                    print("[CRAWLER][DIAGNOSTIC]: WAF BLOCK DETECTED (403/Access Denied)")
            
            for rows in all_raw_tables:
                # 1. FIND DATE FOR THIS TABLE
                date_str = None
                for row in rows:
                    combined = " ".join([c['text'] for c in row]) # type: ignore
                    # Case insensitive date search
                    if 'date:' in combined.lower():
                        # Extract 10-character date like 19-03-2026
                        match = re.search(r'(\d{1,2}[-/]\d{2}[-/]\d{4})', combined)
                        if match:
                            date_str = match.group(1)
                            break
                        else:
                            # Fallback to colon split
                            parts = combined.split(':')
                            if len(parts) > 1:
                                date_str = parts[1].strip()[:10] # type: ignore
                                break
                
                if not date_str:
                    print("[CRAWLER][DEBUG]: Table skipped, no date found.")
                    continue
                    
                # 2. EXTRACT CLASSES
                for cells in rows: 
                    if len(cells) < 4: continue
                    row_text = " ".join([c['text'] for c in cells]) # type: ignore
                    if not any(kw.lower() in row_text.lower() for kw in self.keywords):
                        continue
                        
                    course_text = cells[0]['text'] # type: ignore
                    sem_text = cells[1]['text'] # type: ignore
                    subject_text = cells[2]['text'] # type: ignore
                    
                    time_text = ""
                    for c in cells: # type: ignore
                        if re.search(r'\d{1,2}:\d{2}', c['text']):
                            time_text = c['text']
                            break
                    
                    href = None
                    link_data = None
                    for c in reversed(cells): # type: ignore
                        if c['href'] and ('teams.microsoft.com' in c['href'] or 'join' in c['text'].lower()): # type: ignore
                            href = c['href']
                            link_data = c
                            break
                        
                    is_mba_course = any(kw.lower() in course_text.lower() for kw in self.keywords)
                    if is_mba_course:
                        semester = self.extract_semester_logic(sem_text if sem_text else course_text)
                        if semester == "0": semester = self.extract_semester_logic(course_text)
                        
                        title = f"[{date_str}] {course_text} Sem {semester}: {subject_text} ({time_text})"
                        link_text = link_data.get('text', '').strip() if link_data else "" # type: ignore
                        final_link = href
                        is_teams_link = href and "teams.microsoft.com" in href # type: ignore
                        
                        is_pending = (
                            not href or 
                            ("online-class-schedule" in href and not is_teams_link) or # type: ignore
                            "..." in href or # type: ignore
                            ("available soon" in link_text.lower() and not is_teams_link)
                        )
                        
                        if is_pending:
                            final_link = "#pending"
                        elif is_teams_link:
                            final_link = href
                        
                        now_utc = datetime.datetime.utcnow()
                        ist_offset = datetime.timedelta(hours=5, minutes=30)
                        current_date_ist = (now_utc + ist_offset).date()
                        item_date_obj = self._normalize_date(str(date_str))
                        
                        if item_date_obj and item_date_obj < current_date_ist: continue

                        description = f"MBA Live Class: {subject_text}. Time: {time_text}."

                        self.notices.append({
                            "title": title.strip(),
                            "link": final_link,
                            "semester": semester,
                            "date": self.parse_date(str(date_str)),
                            "class_time": time_text.strip(),
                            "description": description
                        })
                        print(f"[CRAWLER][CLASS FOUND]: {title}")
        except Exception as e:
            print(f"[CRAWLER][ERROR]: Online classes parsing failed: {e}")

    async def extract_legacy_notices(self, page):
        """Parse notices from sol.du.ac.in (legacy) pages"""
        print(f"[CRAWLER]: Extracting legacy notices from {page.url}")
        try:
            links = await page.evaluate("""() => {
                const results = [];
                const selectors = ['.scroll-block a', '#important-links a', '.notice-list a'];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(a => {
                        results.push({
                            text: a.innerText.trim(),
                            href: a.href,
                            source: sel
                        });
                    });
                });
                return results;
            }""")

            date_pattern = re.compile(r'\[(\d{1,2}-\d{2}-\d{4})\]')

            for item in links:
                text = item['text']
                href = item['href']
                if not text or not href: continue

                is_relevant = any(kw.lower() in text.lower() for kw in self.keywords)
                if is_relevant or item['source'] == '#important-links a':
                    notice_date = datetime.datetime.now()
                    date_match = date_pattern.search(text)
                    if date_match:
                        try:
                            notice_date = datetime.datetime.strptime(date_match.group(1), "%d-%m-%Y")
                        except Exception: pass
                    
                    if any(n['link'] == href for n in self.notices): continue
                    semester = self.extract_semester_logic(text)
                    
                    print(f"[CRAWLER][LEGACY FOUND]: {text.strip()} (Sem {semester})")
                    description = f"MBA Notification for Semester {semester}" if semester != "0" else "Generic MBA information."
                    is_class_related = any(kw.lower() in text.lower() for kw in ["online class", "live class", "vcs", "schedule", "date sheet", "datesheet"])
                    if is_class_related:
                        description = f"MBA Live Class: {text.strip()}"

                    self.notices.append({
                        "title": text.strip(),
                        "link": href,
                        "semester": semester,
                        "date": notice_date.strftime("%Y-%m-%d"),
                        "description": description
                    })
        except Exception as e:
            print(f"[CRAWLER][ERROR]: Legacy notices parsing failed: {e}")

    async def extract_mba_content(self, page):
        """v19.3: Turbo Link Extraction (Single Page Evaluate)"""
        try:
            # Get all links and texts in one single JS call to avoid 100s of 'awaits'
            link_data = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a')).map(a => ({
                    text: a.innerText,
                    href: a.href
                }))
            """)
            
            for item in link_data:
                text = item.get('text', '').strip()
                href = item.get('href', '')
                if not href or not text: continue
                
                if any(kw.lower() in text.lower() for kw in self.keywords):
                    # Ensure absolute URL
                    if not href.startswith("http"):
                        href = "https://web.sol.du.ac.in" + href if href.startswith("/") else self.base_url + href
                        
                    if any(n['link'] == href for n in self.notices): continue
                    semester = self.extract_semester_logic(text)
                    
                    description = "General MBA information."
                    is_class_related = any(kw.lower() in text.lower() for kw in ["online class", "live class", "vcs", "schedule", "date sheet", "datesheet"])
                    if is_class_related:
                        description = f"MBA Live Class: {text}"

                    self.notices.append({
                        "title": text,
                        "link": href,
                        "semester": semester,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "description": description
                    })
                    print(f"[CRAWLER][FOUND]: {text}")
        except Exception as e:
            print(f"[CRAWLER][ERROR]: Turbo extraction failed: {e}")

    def extract_semester_logic(self, text: str) -> str:
        if not text: return "0"
        
        # V18.8: Multi-semester detection (e.g. I-IV, I to IV, I,II,III,IV)
        multi_patterns = [
            r'\bI\b.*?\bIV\b',     # I...IV range
            r'\b1\b.*?\b4\b',     # 1...4 range
            r'I, II, III, IV',    # Standard list
            r'All\s+Sem', r'Entire\s+Programme'
        ]
        if any(re.search(p, text, re.I) for p in multi_patterns):
            return "0"

        # v20.0: More robust semester extraction
        # Try finding standard 1-4 with sem suffix
        ordinal_match = re.search(r'\b([1-4])(?:st|nd|rd|th)?\s*(?:SEM|Semester)?\b', text, re.I)
        if ordinal_match: return str(ordinal_match.group(1)) # Changed to str to match return type
        
        # Try finding bare number if the text is short (likely a sem column)
        bare_match = re.search(r'\b([1-4])\b', text)
        if bare_match: return str(bare_match.group(1)) # Changed to str to match return type
        if "mba" in text.lower():
            if re.search(r'\b(4|IV|Fourth)\b', text, re.I): return "4"
            if re.search(r'\b(3|III|Third)\b', text, re.I): return "3"
            if re.search(r'\b(2|II|Second)\b', text, re.I): return "2"
            if re.search(r'\b(1|I|First)\b', text, re.I): return "1"
        return "0"

    def _normalize_date(self, date_str: str) -> Optional[datetime.date]:
        if not date_str: return None
        for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"]:
            try: return datetime.datetime.strptime(date_str.strip(), fmt).date()
            except Exception: continue
        try: return dparser.parse(date_str, fuzzy=True).date()
        except Exception: return None

    def parse_date(self, date_str: str) -> str:
        obj = self._normalize_date(date_str)
        return obj.strftime("%Y-%m-%d") if obj else datetime.datetime.now().strftime("%Y-%m-%d")

    async def expand_content(self, page):
        expand_selectors = ["text='Show More'", "text='View All'", "text='View More'", ".btn-show-more"]
        for selector in expand_selectors:
            try:
                btns = await page.locator(selector).all()
                for btn in btns:
                    if await btn.is_visible():
                        await btn.click()
                        await asyncio.sleep(1)
            except Exception: continue

    async def auto_scroll(self, page):
        try:
            await page.evaluate("""async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    let distance = 100;
                    let timer = setInterval(() => {
                        let scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if(totalHeight >= scrollHeight){ clearInterval(timer); resolve(); }
                    }, 100);
                });
            }""")
            await asyncio.sleep(2)
        except Exception: pass


if __name__ == "__main__":
    # V30.0: Configuration from Environment (for GitHub Actions)
    backend_url = os.environ.get("BACKEND_URL", "https://mba-scraper.onrender.com")
    scraper_key = os.environ.get("SCRAPER_KEY", "your-secret-key-123")
    
    print(f"[JOB]: Starting Scraper with Backend: {backend_url}")
    scraper = MBAScraper()
    # Initialize Notifier (if needed inside MBAScraper, usually it's initialized during run or passed in)
    # For now, we ensure the scraper logic uses these config values.
    
    asyncio.run(scraper.run())
