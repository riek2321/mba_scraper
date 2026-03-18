import asyncio
from playwright.async_api import async_playwright
import datetime
import dateutil.parser as dparser
import re
import random

class MBAScraper:
    def __init__(self, base_url="https://web.sol.du.ac.in/home"):
        self.base_url = base_url
        self.keywords = ['MBA', 'Master of Business Administration']
        self.visited = set()
        self.notices = []
        self.days_back = 15 # Default
        # Golden Fingerprint from successful subagent session
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"

    async def run(self, days_back=None, targets=None):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # V5 STEALTH: Advanced Human Fingerprinting
            headers = {
                "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Cache-Control": "max-age=0",
                "DNT": "1",
                "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand)";v="24", "Google Chrome";v="122"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            }
            context = await browser.new_context(
                user_agent=self.user_agent,
                extra_http_headers=headers,
                viewport={'width': 1366, 'height': 768},
                locale="en-IN",
                timezone_id="Asia/Kolkata"
            )
            page = await context.new_page()
            # Advanced Evasive markers (V2)
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en-GB', 'en-US', 'en'] });
            """)
            
            self.visited = set()
            self.notices = []
            self.days_back = days_back if days_back is not None else self.days_back
            
            # Key targets for deep scan - STRICTLY AS REQUESTED
            all_targets = [
                "https://sol.du.ac.in/home.php",
                "https://web.sol.du.ac.in/info/online-class-schedule",
                "https://sol.du.ac.in/all-notices.php"
            ]
            
            start_urls = targets if targets else all_targets
            
            print(f"[CRAWLER]: Starting scan of {len(start_urls)} target areas")
            for url in start_urls:
                # Patient waiting to seem more human and allow server response
                await asyncio.sleep(random.uniform(3.0, 6.0))
                # Strict 0 depth - do not follow any links deep
                await self.crawl(page, url, depth=0, max_depth=0) 
            
            await browser.close()
            return self.notices

    async def crawl(self, page, url, depth, max_depth):
        if url in self.visited or depth > max_depth:
            return
        self.visited.add(url)
        
        # Log console messages from browser to Python stdout
        page.on("console", lambda msg: print(f"[BROWSER]: {msg.text}"))
        
        await asyncio.sleep(random.uniform(2.0, 4.0)) # Patient delay

        print(f"[CRAWLER][Depth {depth}]: Visiting {url}")
        try:
            # V4 STEALTH: Human-First Flow for Class Schedule
            force_human_navigation = "online-class-schedule" in url
            
            if not force_human_navigation:
                # Normal flow for other pages: Attempt primary visit
                response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                is_blocked = response and response.status == 403
            else:
                is_blocked = True # Force fallback for these URLs
                print(f"[CRAWLER]: Enforcing Mandatory Human Flow for {url}")
            
            if is_blocked:
                print(f"[CRAWLER][WARNING]: 403 Forbidden for {url}. Attempting Human-like navigation from Legacy...")
                
                # V6.8: ULTRA-HUMAN LINK-CLICK TRANSITION (Broadened)
                # Establish session/cookies from legacy home page first
                legacy_home = "https://sol.du.ac.in/home.php"
                print(f"[CRAWLER]: Visiting Legacy Home {legacy_home} (Patient Mode)...")
                try:
                    await page.goto(legacy_home, wait_until="domcontentloaded", timeout=120000)
                    await asyncio.sleep(random.uniform(5, 10))
                except Exception as e:
                    print(f"[CRAWLER][WARNING]: Legacy home failed to load ({e}). Proceeding to direct visit...")
                
                found = False
                if "online-class-schedule" in url:
                    try:
                        print("[CRAWLER]: Clicking transition button for Online Classes...")
                        # Target ANY link containing 'online-class-schedule'
                        transition_btn = page.locator("a[href*='online-class-schedule']").first
                        if await transition_btn.count() > 0:
                            print(f"[CRAWLER]: Found transition button, clicking naturally...")
                            await transition_btn.click()
                            await page.wait_for_load_state("load", timeout=90000)
                            await asyncio.sleep(random.uniform(10, 15))
                            found = True
                        else:
                            print("[CRAWLER][WARNING]: Transition button 'online-class-schedule' not found.")
                    except Exception as e:
                        print(f"[CRAWLER][ERROR]: Transition click failed: {e}")

                if not found:
                    # General Fallback for any 403: Try to find a matching link on the page
                    try:
                        short_url = url.split('/')[-1] if '/' in url else url
                        link = page.locator(f"a[href*='{short_url}']").first
                        if await link.count() > 0:
                            print(f"[CRAWLER]: Found matching link for {short_url}, clicking...")
                            await link.click()
                            await page.wait_for_load_state("load", timeout=60000)
                            await asyncio.sleep(8)
                            found = True
                    except: pass

                if not found:
                    # Last resort: direct visit with session cookies established
                    print(f"[CRAWLER]: Falling back to direct transition to {url}...")
                    await page.goto(url, wait_until="load", timeout=60000)
                    await asyncio.sleep(random.uniform(5, 10))
                    found = True
                
                if found:
                    await page.wait_for_load_state("networkidle", timeout=60000)
                else:
                    print(f"[CRAWLER][FAIL]: Could not resolve navigation path for {url}")
                    return

                if not found:
                    # Generic Fallback: Try by href fragment
                    filename = url.split("/")[-1]
                    link = page.locator(f'a[href*="{filename}"]').first
                    if await link.count() > 0:
                        print(f"[CRAWLER]: Found link via href: {filename}")
                        await link.click(force=True)
                        found = True
                
                if found:
                    await page.wait_for_load_state("networkidle", timeout=45000)
                else:
                    # Extra Debug: Log what we see
                    print(f"[CRAWLER][FAIL]: Could not resolve navigation path for {url}")
                    print(f"               Page Title: {await page.title()}")
                    return
            else:
                await page.wait_for_load_state("networkidle", timeout=45000)
            
            # 1. Handle specialized pages (like tables in Online Classes)
            if "online-class-schedule" in url:
                await self.extract_online_classes(page)
            
            # 2. Handle generic legacy blocks (Important Notices / All Notices)
            if "sol.du.ac.in" in url and ("all-notices" in url or "home" in url):
                await self.extract_legacy_notices(page)

            # 3. Expand interactive content
            await self.expand_content(page)
            
            # 4. Handle jstree (Study Materials / SLM)
            if await page.query_selector(".jstree"):
                await self.handle_jstree(page)
            
            # 5. Extract MBA content from general links (Modern & General)
            await self.extract_mba_content(page)
            
            # 6. Find menu links for deeper crawling
            if depth < max_depth:
                menu_links = await page.locator("nav a, .menu a, .dropdown-menu a").all()
                link_urls = []
                for link in menu_links:
                    href = await link.get_attribute("href")
                    if href and (href.startswith("/") or "sol.du.ac.in" in href):
                        full_url = "https://web.sol.du.ac.in" + href if href.startswith("/") else href
                        if "#" not in full_url and full_url not in self.visited:
                            link_urls.append(full_url)
                
                sub_pages = list(set(link_urls))
                for sub_url in sub_pages[:10]: # Limit branching
                    await self.crawl(page, sub_url, depth + 1, max_depth)
                    
        except Exception as e:
            print(f"[CRAWLER][ERROR]: Failed to visit {url}: {e}")

    async def extract_online_classes(self, page):
        """Specifically parse the online class schedule table"""
        # V6.8: TRUSTED IFRAME CONTENT
        # We no longer goto() the iframe directly as it triggers 403. 
        # Instead we wait for the parent page to load it and then parse all frames.
        print(f"[CRAWLER]: Waiting for schedule iframe content to stabilize...")
        await asyncio.sleep(15) 
        await self.auto_scroll(page)
        await asyncio.sleep(5) 

        print("[CRAWLER]: Parsing Online Class Schedule tables (Hyper-Robust)...")
        try:
            # Capture ALL tables from ALL frames to be safe
            all_raw_tables = []
            for frame in page.frames:
                try:
                    tables_data = await frame.evaluate("""() => {
                        return Array.from(document.querySelectorAll('table')).map(table => {
                            return Array.from(table.querySelectorAll('tr')).map(tr => 
                                Array.from(tr.querySelectorAll('td')).map(td => {
                                    const a = td.querySelector('a');
                                    return { text: td.innerText.trim(), href: a ? a.href : null };
                                })
                            );
                        });
                    }""")
                    if tables_data: all_raw_tables.extend(tables_data)
                except: continue

            print(f"[CRAWLER][DEBUG]: Found {len(all_raw_tables)} raw tables in parent page frames.")
            
            # V7.0: If still no tables, Try DIRECT IFRAME URL (Bypassing parent completely)
            if not all_raw_tables:
                print("[CRAWLER]: Parent page failed to reveal tables. Attempting DIRECT IFRAME ACCESS...")
                vcs_url = "https://web.sol.du.ac.in/my/team_schedules/vcs.php"
                try:
                    # We use a new page/context or just navigate the current one to the iframe source
                    # But often the iframe source needs to be visited directly to bypass frame restrictions
                    await page.goto(vcs_url, wait_until="networkidle", timeout=60000)
                    await asyncio.sleep(5)
                    direct_tables = await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('table')).map(table => {
                            return Array.from(table.querySelectorAll('tr')).map(tr => 
                                Array.from(tr.querySelectorAll('td')).map(td => {
                                    const a = td.querySelector('a');
                                    return { text: td.innerText.trim(), href: a ? a.href : null };
                                })
                            );
                        });
                    }""")
                    if direct_tables:
                        print(f"[CRAWLER]: Success! Found {len(direct_tables)} tables via DIRECT ACCESS.")
                        all_raw_tables.extend(direct_tables)
                except Exception as direct_e:
                    print(f"[CRAWLER][ERROR]: Direct iframe access failed: {direct_e}")

            print(f"[CRAWLER][DEBUG]: Total raw tables collected: {len(all_raw_tables)}.")
            
            for rows in all_raw_tables:
                # Find date within this specific table
                date_str = None
                for row in rows:
                    combined_text = " ".join([c['text'] for c in row])
                    if 'date:' in combined_text.lower():
                        date_str = combined_text.split(':')[1].strip()
                        break
                
                if not date_str: continue
                
                for cells in rows:
                    if len(cells) < 4: continue
                    
                    # Combine all text for fuzzy course matching
                    row_text = " ".join([c['text'] for c in cells])
                    if not any(kw.lower() in row_text.lower() for kw in self.keywords):
                        continue
                        
                    # Extract fields with fallback indexing
                    course_text = cells[0]['text']
                    sem_text = cells[1]['text']
                    subject_text = cells[2]['text']
                    
                    # Find Time (looking for AM/PM or HH:MM)
                    time_text = ""
                    for c in cells:
                        if re.search(r'\d{1,2}:\d{2}', c['text']):
                            time_text = c['text']
                            break
                    
                    # Find Link
                    href = None
                    link_data = None # Initialize link_data
                    for c in reversed(cells):
                        if c['href'] and ('teams.microsoft.com' in c['href'] or 'join' in c['text'].lower()):
                            href = c['href']
                            link_data = c # Store the cell data for link_text
                            break
                        
                    # Apply strict Course filter
                    is_mba_course = any(kw.lower() in course_text.lower() for kw in self.keywords)
                    if is_mba_course:
                        semester = self.extract_semester_logic(sem_text if sem_text else course_text)
                        if semester == "0": semester = self.extract_semester_logic(course_text)
                        
                        title = f"[{date_str}] {course_text} Sem {semester}: {subject_text} ({time_text})"
                        
                        # Robust Pending Detection
                        link_text = link_data.get('text', '').strip() if link_data else ""
                        final_link = href
                        
                        # V6.7: If it's a real Teams URL, it's NOT pending, regardless of 'Login' text
                        is_teams_link = href and "teams.microsoft.com" in href
                        
                        is_pending = (
                            not href or 
                            ("online-class-schedule" in href and not is_teams_link) or 
                            "..." in href or 
                            "..." in link_text or 
                            ("login" in link_text.lower() and not is_teams_link) or 
                            "available soon" in link_text.lower() or
                            len(link_text) < 4
                        )
                        
                        if is_pending:
                            print(f"[SCRAPE]: Found pending link for: {subject_text}")
                            final_link = "#pending"
                        
                        # Get current date in IST
                        now_utc = datetime.datetime.utcnow()
                        ist_offset = datetime.timedelta(hours=5, minutes=30)
                        current_date_ist = (now_utc + ist_offset).date()
                        
                        # Parse item date robustly
                        item_date_obj = self._normalize_date(date_str)
                        
                        # HARD FILTER: Strict lifecycle management (Only Today and Future)
                        if item_date_obj and item_date_obj < current_date_ist:
                            print(f"[SCRAPE][SKIP OLD]: {subject_text} is from {date_str} (Past class)")
                            continue

                        # Dynamic Description: Today, Tomorrow, or Specific Date
                        if item_date_obj == current_date_ist:
                            desc_prefix = "[TODAY]"
                        elif item_date_obj == current_date_ist + datetime.timedelta(days=1):
                            desc_prefix = "[TOMORROW]"
                        else:
                            # e.g., "[20 Mar]"
                            desc_prefix = f"[{item_date_obj.strftime('%d %b')}]"
                        # Add IST time for extra clarity in description if needed
                        description = f"{desc_prefix} MBA Live Class: {subject_text}. Time: {time_text}."

                        self.notices.append({
                            "title": title.strip(),
                            "link": final_link,
                            "semester": semester,
                            "date": self.parse_date(date_str),
                            "class_time": time_text.strip(),
                            "description": description
                        })
                        print(f"[CRAWLER][CLASS FOUND]: {title} (Link: {final_link})")
        except Exception as e:
            print(f"[CRAWLER][ERROR]: Online classes parsing failed: {e}")

    async def extract_legacy_notices(self, page):
        """Parse notices from sol.du.ac.in (legacy) pages using targeted selectors"""
        print(f"[CRAWLER]: Extracting legacy notices from {page.url}...")
        try:
            # We target .scroll-block for notices and #important-links for links
            links = await page.evaluate("""() => {
                const results = [];
                const selectors = ['.scroll-block a', '#important-links a', '.notice-list a', '.important-links a'];
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

            import re
            date_pattern = re.compile(r'\[(\d{1,2}-\d{2}-\d{4})\]|(\d{1,2}\s+[A-Za-z]+\s+\d{4})')

            for item in links:
                text = item['text']
                href = item['href']
                if not text or not href: continue

                # Broad keyword check (MBA or Important Notice keywords)
                is_relevant = any(kw.lower() in text.lower() for kw in self.keywords)
                # If it's in important-links or is an MBA notice, we take it
                if is_relevant or item['source'] == '#important-links a':
                    # Date Extraction
                    notice_date = datetime.datetime.now()
                    date_match = date_pattern.search(text)
                    if date_match:
                        date_str = date_match.group(1) or date_match.group(2)
                        try:
                            # Try different formats
                            for fmt in ("%d-%m-%Y", "%d %B %Y", "%d %b %Y"):
                                try:
                                    notice_date = datetime.datetime.strptime(date_str, fmt)
                                    break
                                except: pass
                        except: pass
                    
                    # Deduplicate
                    if any(n['link'] == href for n in self.notices): continue

                    # Semester Identify
                    semester = self.extract_semester_logic(text)
                    
                    print(f"[CRAWLER][LEGACY FOUND]: {text.strip()} (Sem {semester})")
                    self.notices.append({
                        "title": text.strip(),
                        "link": href,
                        "semester": semester,
                        "date": notice_date.strftime("%Y-%m-%d"),
                        "description": f"MBA Notification for Semester {semester}" if semester != "0" else "Generic MBA notification or information."
                    })
        except Exception as e:
            print(f"[CRAWLER][ERROR]: Legacy notices parsing failed: {e}")

    async def handle_jstree(self, page):
        """Recursively expands jstree and extracts MBA links."""
        print("[CRAWLER]: Expanding jstree folders...")
        try:
            # Click all closed folder icons to expand
            icons = await page.locator(".jstree-icon.jstree-ocl").all()
            for icon in icons:
                # We target icons that are not already open (jstree-open class on the li parent)
                await icon.click()
                await asyncio.sleep(0.5)
                
            # Extract anchors from the jstree
            anchors = await page.locator(".jstree-anchor").all()
            for a in anchors:
                text = await a.inner_text()
                href = await a.get_attribute("href")
                if not href or href == "#": continue
                
                if "MBA" in text.upper():
                    semester = self.extract_semester_logic(text)
                    if semester != "0":
                        self.notices.append({
                            "title": text.strip(),
                            "link": href,
                            "semester": semester,
                            "date": datetime.datetime.now().strftime("%Y-%m-%d")
                        })
                        print(f"[CRAWLER][JSTREE FOUND]: {text.strip()}")
        except Exception as e:
            print(f"[CRAWLER][ERROR]: jstree handling failed: {e}")

    def extract_semester_logic(self, text):
        if not text: return "0"
        
        # 1. Standard "Sem 1", "Semester - II", "Sem IV", "Sem: 3"
        sem_match = re.search(r'\bSem(?:ester)?\s*[-: ]*\s*([1-4]|I{1,3}|IV)\b', text, re.I)
        if sem_match: 
            val = sem_match.group(1).upper()
            if val == 'I': return '1'
            if val == 'II': return '2'
            if val == 'III': return '3'
            if val == 'IV': return '4'
            return val
        
        # 2. Ordinal format explicitly attached to SEM: "1st SEM", "2nd SEM", "3rd SEM", "4th SEM"
        ordinal_match = re.search(r'\b([1-4])(?:st|nd|rd|th)?\s*SEM\b', text, re.I)
        if ordinal_match: return ordinal_match.group(1)
        
        # 3. Simple Digit hyphen fallbacks (strictly bound to "Sem")
        for num in ["1", "2", "3", "4"]:
            if f"sem-{num}" in text.lower() or f"sem{num}" in text.lower(): return num

        # 4. "MBA" + specific number / word / roman numeral combinations
        # E.g. "MBA I", "MBA First", "MBA 1"
        if "mba" in text.lower() or "master of business" in text.lower():
            # Check 4 first (IV)
            if re.search(r'\b(4|IV|Fourth)\b', text, re.I): return "4"
            # Check 3 (III)
            if re.search(r'\b(3|III|Third)\b', text, re.I): return "3"
            # Check 2 (II)  
            if re.search(r'\b(2|II|Second)\b', text, re.I): return "2"
            # Check 1 (I) - "I" as a standalone word
            if re.search(r'\b(1|I|First)\b', text, re.I): return "1"

        # If it doesn't clearly say "Sem X" or "MBA X", it is General info
        return "0"

    def _normalize_date(self, date_str):
        if not date_str: return None
        
        # 1. Try common formats first manually for speed
        for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"]:
            try:
                return datetime.datetime.strptime(date_str.strip(), fmt).date()
            except: continue
            
        # 2. Try Fuzzy Parsing with dateutil
        try:
            return dparser.parse(date_str, fuzzy=True).date()
        except: pass

        # 3. Fallback to Regex for DD-MM-YYYY or DD Month YYYY
        try:
            match = re.search(r'(\d{1,2})[-/\s](\d{1,2}|[a-zA-Z]+)[-/\s](\d{4})', date_str)
            if match:
                clean_date = match.group(0)
                return dparser.parse(clean_date).date()
        except: pass
        return None

    def parse_date(self, date_str):
        # Return YYYY-MM-DD string
        obj = self._normalize_date(date_str)
        if obj:
            return obj.strftime("%Y-%m-%d")
        # If all else fails, default to today but log it as a warning
        print(f"[WARNING]: Could not parse date '{date_str}', defaulting to today.")
        return datetime.datetime.now().strftime("%Y-%m-%d")

    async def expand_content(self, page):
        """Click buttons like 'View All', 'Show More', 'View More', and toggle Dropdowns"""
        expand_selectors = [
            "text='Show More'", "text='View All'", "text='View More'",
            "button:has-text('Read More')", ".btn-show-more", ".load-more"
        ]
        
        for selector in expand_selectors:
            try:
                btns = await page.locator(selector).all()
                for btn in btns:
                    if await btn.is_visible():
                        print(f"[CRAWLER]: Clicking expansion element: {selector}")
                        await btn.click()
                        await asyncio.sleep(1) # Wait for animation/load
            except:
                continue

    async def auto_scroll(self, page):
        """Smoothly scroll to the bottom of the page to load all content."""
        await page.evaluate("""async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                let distance = 100;
                let timer = setInterval(() => {
                    let scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if(totalHeight >= scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        }""")
        await asyncio.sleep(2) # Give a moment for content to settle

    async def extract_mba_content(self, page):
        """Find links and content matching MBA keywords"""
        import re
        date_pattern = re.compile(r'\[(\d{2}-\d{2}-\d{4})\]')
        
        links = await page.locator("a").all()
        for link in links:
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                
                if not href or not text: continue
                
                # Broad keyword check
                is_relevant = any(kw.lower() in text.lower() for kw in self.keywords)
                if not is_relevant: continue
                
                # Normalize URL
                if not href.startswith("http"):
                    href = "https://web.sol.du.ac.in" + href if href.startswith("/") else self.base_url + href
                
                # Date Extraction
                notice_date = datetime.datetime.now()
                date_match = date_pattern.search(text)
                if date_match:
                    try:
                        notice_date = datetime.datetime.strptime(date_match.group(1), "%d-%m-%Y")
                    except: pass
                
                # Recency Filter: Rely on notice_date and days_back
                # Only absolute cutoff is 2024 or older to avoid archival noise
                if notice_date.year < 2025:
                    print(f"[CRAWLER][SKIP OLD]: {text.strip()} ({notice_date.year})")
                    continue
                
                # Days Back Filter
                if self.days_back is not None and self.days_back > 0:
                    delta = datetime.datetime.now() - notice_date
                    if delta.days > self.days_back: continue
                
                # Deduplicate within current run
                if any(n['link'] == href for n in self.notices): continue

                # Semester Identify
                semester = "0"
                sem_match = re.search(r'(Sem(?:ester)?\s*([1-4]))', text, re.I)
                if sem_match: semester = sem_match.group(2)
                
                print(f"[CRAWLER][FOUND]: {text.strip()} (Sem {semester})")
                self.notices.append({
                    "title": text.strip(),
                    "link": href,
                    "semester": semester,
                    "date": notice_date.strftime("%Y-%m-%d"),
                    "description": f"MBA Notification for Semester {semester}" if semester != "0" else "Generic MBA notification or information."
                })
            except:
                continue
