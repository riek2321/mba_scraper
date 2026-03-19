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

class MBAScraper:
    def __init__(self, base_url: str = "https://web.sol.du.ac.in/home"):
        self.base_url = base_url
        self.keywords = ['MBA', 'Master of Business Administration']
        self.visited = set()
        self.notices = []
        self.days_back = 15 # Default
        # V19.0: Modern Professional Headers (Microsoft Edge on Windows)
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.3060.0"
        self.targets = [
            "https://sol.du.ac.in/home.php",
            "https://web.sol.du.ac.in/my/team_schedules/vcs.php", # Direct Target (v19.1)
            "https://sol.du.ac.in/all-notices.php"
        ]

    async def run(self, days_back: int = 15, targets: Optional[List[str]] = None):
        """v19.2: DUAL-ENGINE (Firefox) + LEGACY PROMOTION"""
        self.days_back = days_back
        async with async_playwright() as p:
            # V19.2: Browser fallback - Prioritize Firefox for Render stealth, revert to Chromium for local
            try:
                print("[CRAWLER]: Launching Firefox Engine...")
                browser = await p.firefox.launch(headless=True)
            except Exception:
                print(f"[CRAWLER][WARNING]: Firefox missing or unsupported. Reverting to Chromium...")
                browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
            
            headers = {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
                "Sec-Fetch-User": "?1",
                "Accept-Encoding": "gzip, deflate, br",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }
            
            # v17.0: Randomized Viewport
            viewports = [
                {'width': 1366, 'height': 768},
                {'width': 1536, 'height': 864},
                {'width': 1920, 'height': 1080},
                {'width': 1440, 'height': 900}
            ]
            
            context = await browser.new_context(
                user_agent=self.user_agent,
                extra_http_headers=headers,
                viewport=random.choice(viewports)
            )
            page = await context.new_page()
            
            # v17.0: STEALTH LAYER
            try:
                await stealth_async(page)
                print("[CRAWLER]: Stealth signatures applied.")
            except Exception: pass

            # v17.0: ADVANCED SESSION PRIMER (Warming up the entire domain)
            print("[CRAWLER]: Priming Multi-Step Session (sol.du.ac.in + web.sol.du.ac.in)")
            try:
                # Step 0: Main portal
                print("[CRAWLER][PRIMER]: Visiting Main Portal...")
                await page.goto("https://sol.du.ac.in/home.php", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)

                # Step 1: Subdomain Root
                print("[CRAWLER][PRIMER]: Visiting Subdomain Root...")
                await page.goto("https://web.sol.du.ac.in/home", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)
                
                # Step 2: Intermediate page (Student Support)
                print("[CRAWLER][PRIMER]: Visiting Student Support...")
                await page.goto("https://web.sol.du.ac.in/info/student-support", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(2, 4))
            except Exception as e: 
                print(f"[CRAWLER][PRIMER][WARNING]: Primer interrupted: {e}")

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
                        # V19.1: FAST-PATH DIRECT VCS (Anti-Timeout)
                        # Instead of the heavy wrapper, we visit vcs.php directly but with 
                        # intense session priming and Referer spoofing.
                        home_url = "https://web.sol.du.ac.in/home"
                        support_url = "https://web.sol.du.ac.in/info/student-support"
                        wrapper_url = "https://web.sol.du.ac.in/info/online-class-schedule"
                        target_url = "https://web.sol.du.ac.in/my/team_schedules/vcs.php"
                        
                        print(f"[CRAWLER][STEALTH]: Priming Session (Home): {home_url}")
                        await page.goto(home_url, wait_until="networkidle", timeout=60000)
                        await asyncio.sleep(2)
                        
                        print(f"[CRAWLER][STEALTH]: Priming Session (Support): {support_url}")
                        await page.goto(support_url, wait_until="domcontentloaded", timeout=60000)
                        await asyncio.sleep(2)

                        print(f"[CRAWLER][STEALTH]: Navigating to Direct Data with Referer: {target_url}")
                        try:
                            # We use the wrapper URL as the Referer to make it look legitimate
                            await page.goto(target_url, wait_until="load", timeout=90000, referer=wrapper_url)
                        except Exception as e:
                            print(f"[CRAWLER][STEALTH][WARNING]: Direct attempt failed: {e}. Trying via Wrapper jump...")
                            await page.goto(wrapper_url, wait_until="domcontentloaded", timeout=90000, referer=support_url)
                            await asyncio.sleep(5)
                            await page.goto(target_url, wait_until="load", timeout=90000, referer=wrapper_url)
                        
                        print("[CRAWLER][STEALTH]: Final Stealth Interaction...")
                        await page.mouse.wheel(0, 500)
                        await asyncio.sleep(3)
                        
                        await self.extract_online_classes(page)
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
        """Specifically parse the online class schedule table (Direct/V15.0)"""
        print(f"[CRAWLER]: Analyzing Class Schedule on {page.url}")
        try:
            # 1. Wait for Table with timeout
            try:
                await page.wait_for_selector("table", timeout=20000)
            except Exception:
                print("[CRAWLER][WARNING]: Table not found immediately. Triggering interaction...")

            # 2. Human-Like Keyboard Scrolling to trigger lazy load
            await page.mouse.move(random.randint(200, 400), random.randint(200, 400))
            for _ in range(3):
                await page.keyboard.press("PageDown")
                await asyncio.sleep(1)
            await asyncio.sleep(5) 
        except Exception as e:
            print(f"[CRAWLER][WARNING]: Interaction trigger failed: {e}")

        all_raw_tables = []
        try:
            # V15.0: Extract from current page AND any frames
            contexts_to_scan = [page] + page.frames
            print(f"[CRAWLER]: Scanning {len(contexts_to_scan)} contexts (Page + Frames)")
            
            for ctx in contexts_to_scan:
                try:
                    # v16.0: Frame-level wait
                    try: await ctx.wait_for_selector("table", timeout=5000)
                    except: pass
                    
                    tables_data = await ctx.evaluate("""() => {
                        const tables = Array.from(document.querySelectorAll('table'));
                        if (tables.length === 0) return null;
                        return tables.map(table => {
                            return Array.from(table.querySelectorAll('tr')).map(tr => 
                                Array.from(tr.querySelectorAll('td')).map(td => {
                                    const a = td.querySelector('a');
                                    return { text: td.innerText.trim(), href: a ? a.href : null };
                                })
                            );
                        });
                    }""")
                    if isinstance(tables_data, list):
                        for t in tables_data: # type: ignore
                            all_raw_tables.append(t)
                except Exception: continue

            print(f"[CRAWLER]: Final raw table count: {len(all_raw_tables)}")
            
            # v16.0: HTML Diagnostics if 0 tables
            if not all_raw_tables:
                print("[CRAWLER][DIAGNOSTIC]: No tables found. Source snippet:")
                try:
                    html = await page.content()
                    print(html[:500].replace('\n', ' '))
                except: pass

            if isinstance(all_raw_tables, list):
                for rows in all_raw_tables: # type: ignore
                    date_str = None
                    for row in rows: # type: ignore
                        combined_text = " ".join([c['text'] for c in row]) # type: ignore
                        if 'date:' in combined_text.lower():
                            date_str = combined_text.split(':')[1].strip()
                            break
                    
                    if not date_str: continue
                    
                    for cells in rows: # type: ignore
                        if len(cells) < 4: continue # type: ignore
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

        sem_match = re.search(r'\bSem(?:ester)?\s*[-: ]*\s*([1-4]|I{1,3}|IV)\b', text, re.I)
        if sem_match: 
            val = sem_match.group(1).upper()
            mapping = {'I': '1', 'II': '2', 'III': '3', 'IV': '4'}
            return mapping.get(val, val)
        ordinal_match = re.search(r'\b([1-4])(?:st|nd|rd|th)?\s*SEM\b', text, re.I)
        if ordinal_match: return ordinal_match.group(1)
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
    scraper = MBAScraper()
    asyncio.run(scraper.run())
