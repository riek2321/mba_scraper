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
        self.days_back = None

    async def run(self, days_back=None, targets=None):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # V2 STEALTH: Minimalist headers, let Playwright handle dynamic flow
            headers = {
                "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Cache-Control": "max-age=0",
                "DNT": "1"
            }
            # EXTREME STEALTH: Match regional profile
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                extra_http_headers=headers,
                viewport={'width': 1280 + random.randint(-20, 20), 'height': 800 + random.randint(-20, 20)},
                device_scale_factor=random.choice([1, 2]),
                locale="en-IN",
                timezone_id="Asia/Kolkata",
                ignore_https_errors=True
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
            self.days_back = days_back
            
            # Key targets for deep scan - PRIORITIZED Online Class Schedule
            all_targets = [
                "https://web.sol.du.ac.in/info/online-class-schedule",
                self.base_url,
                "https://web.sol.du.ac.in/info/archive-notices-information",
                "https://web.sol.du.ac.in/student-academic-information",
                "https://sol.du.ac.in/all-notices.php",
                "https://sol.du.ac.in/home.php"
            ]
            
            start_urls = targets if targets else all_targets
            
            print(f"[CRAWLER]: Starting scan of {len(start_urls)} target areas")
            for url in start_urls:
                # Patient waiting to seem more human and allow server response
                await asyncio.sleep(random.uniform(3.0, 6.0))
                await self.crawl(page, url, depth=0, max_depth=1) 
            
            await browser.close()
            return self.notices

    async def crawl(self, page, url, depth, max_depth):
        if url in self.visited or depth > max_depth:
            return
        self.visited.add(url)
        
        await asyncio.sleep(random.uniform(2.0, 4.0)) # Patient delay

        print(f"[CRAWLER][Depth {depth}]: Visiting {url}")
        try:
            # Set a more realistic timeout and handle 403 gracefully
            response = await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            
            if response and response.status == 403:
                print(f"[CRAWLER][WARNING]: 403 Forbidden for {url}. Site might be blocking or offline.")
                return

            await page.wait_for_load_state("networkidle", timeout=15000)
            
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
        # Try direct visit first, if 403, try navigating from Home
        if "403" in page.url or "Forbidden" in await page.title():
            print("[CRAWLER]: Direct visit blocked (403). Attempting human-like navigation from Home...")
            await page.goto(self.base_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(random.uniform(2, 5))
            try:
                # Target the schedule link - using flexible text matching
                link = page.get_by_role("link", name=re.compile("Online Class Schedule", re.I))
                if await link.count() > 0:
                    await link.first.click()
                    await page.wait_for_load_state("networkidle")
                else:
                    # Fallback for dropdowns or hidden menus
                    await page.locator("text='Students'").hover()
                    await asyncio.sleep(1)
                    await page.locator("text='Online Class Schedule'").click()
                    await page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"[CRAWLER][ERROR]: Human navigation failed: {e}")
                return

        print("[CRAWLER]: Scrolling deeply to load all class entries (Patient Mode)...")
        await self.auto_scroll(page)
        await asyncio.sleep(5) # Extra wait for lazy content
        
        # Capture Top Timetable Buttons (MBA focus)
        print("[CRAWLER]: Checking for MBA Timetable buttons at the top...")
        top_links = await page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('a.btn, .btn, a')).filter(a => 
                a.innerText.toUpperCase().includes('MBA') && 
                (a.innerText.toUpperCase().includes('TIMETABLE') || a.innerText.toUpperCase().includes('SCHEDULE'))
            );
            return btns.map(a => ({ title: a.innerText.trim(), href: a.href }));
        }""")
        for link in top_links:
            if link['href'] and link['href'] not in [n['link'] for n in self.notices]:
                print(f"[CRAWLER][HEADER FOUND]: {link['title']}")
                self.notices.append({
                    "title": f"[OFFICIAL] {link['title']}",
                    "link": link['href'],
                    "semester": self.extract_semester_logic(link['title']),
                    "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "description": "Official MBA Time Table / Schedule from DU SOL"
                })

        print("[CRAWLER]: Parsing Online Class Schedule table...")
        try:
            # Each date has its own section/header and table
            sections = await page.evaluate("""() => {
                const results = [];
                // Look for elements containing 'Date:'
                const elements = Array.from(document.querySelectorAll('h4, h5, p, b, strong'));
                elements.forEach(el => {
                    const text = el.innerText.trim();
                    if (text.toLowerCase().includes('date:')) {
                        // Attempt to find the next table
                        let next = el.nextElementSibling;
                        let foundTable = null;
                        
                        // Search for table in next siblings or their children
                        let sibling = next;
                        let limit = 5; // Search up to 5 siblings
                        while (sibling && limit > 0) {
                            if (sibling.tagName === 'TABLE') {
                                foundTable = sibling;
                                break;
                            }
                            const tableInSibling = sibling.querySelector('table');
                            if (tableInSibling) {
                                foundTable = tableInSibling;
                                break;
                            }
                            sibling = sibling.nextElementSibling;
                            if (sibling && (sibling.tagName === 'H4' || sibling.tagName === 'H5') && sibling.innerText.toLowerCase().includes('date:')) break;
                            limit--;
                        }
                        
                        if (foundTable) {
                            results.push({
                                date_str: text.split(':')[1].trim(),
                                rows: Array.from(foundTable.querySelectorAll('tr')).map(tr => 
                                    Array.from(tr.querySelectorAll('td')).map(td => {
                                        const a = td.querySelector('a');
                                        return {
                                            text: td.innerText.trim(),
                                            href: a ? a.href : null
                                        };
                                    })
                                )
                            });
                        }
                    }
                });
                return results;
            }""")

            for block in sections:
                date_str = block.get('date_str', '')
                rows = block.get('rows', [])
                
                for cells in rows:
                    if len(cells) >= 6: # New structure: Course | Year/Sem | Subject | Medium | Time | Teacher | Link
                        course_text = cells[0]['text']
                        sem_text = cells[1]['text']
                        subject_text = cells[2]['text']
                        time_text = cells[4]['text']
                        link_data = cells[6] if len(cells) > 6 else (cells[-1] if len(cells) > 0 else None)
                        href = link_data['href'] if link_data else None
                        
                        # Apply strict Course filter
                        is_mba_course = any(kw.lower() in course_text.lower() for kw in self.keywords)
                        if is_mba_course:
                            semester = self.extract_semester_logic(sem_text if sem_text else course_text)
                            if semester == "0": semester = self.extract_semester_logic(course_text)
                            
                            title = f"[{date_str}] {course_text} Sem {semester}: {subject_text} ({time_text})"
                            
                            # Handle placeholder links (like '...', 'Login', 'Available Soon')
                            link_text = link_data.get('text', '').strip() if link_data else ""
                            final_link = href
                            
                            # Aggressive pending detection
                            is_pending = (
                                not href or 
                                "online-class-schedule" in href or 
                                "..." in href or 
                                "..." in link_text or 
                                "login" in link_text.lower() or 
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
                            
                            # HARD FILTER: Don't scrape anything older than today
                            if item_date_obj and item_date_obj < current_date_ist:
                                print(f"[SCRAPE][SKIP OLD]: {subject_text} is from {date_str} (Yesterday/Old)")
                                continue

                            # Dynamic Description: Today vs Tomorrow
                            desc_prefix = "[TODAY]" if item_date_obj == current_date_ist else "[TOMORROW]"
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
        
        # 1. Roman Numerals: IV, III, II, I (Strict word boundary)
        # We check IV first so it doesn't match I partially
        roman_map = {"IV": "4", "III": "3", "II": "2", "I": "1"}
        for rom, num in roman_map.items():
            if re.search(rf'\b{rom}\b', text, re.I):
                return num

        # 2. Standard Sem 1, Semester 1
        sem_match = re.search(r'(Sem(?:ester)?\s*([1-4]))', text, re.I)
        if sem_match: return sem_match.group(2)
        
        # 3. Ordinal format: 1st SEM, 2nd SEM, 3rd SEM, 4th SEM
        ordinal_match = re.search(r'([1-4])(?:st|nd|rd|th)?\s*SEM', text, re.I)
        if ordinal_match: return ordinal_match.group(1)
        
        # 4. Word format (expanded)
        word_map = {"First": "1", "Second": "2", "Third": "3", "Fourth": "4"}
        for word, num in word_map.items():
            if word.lower() in text.lower(): return num
        
        # 5. Simple Digit fallbacks
        if "sem-4" in text.lower() or "sem4" in text.lower(): return "4"
        if "sem-3" in text.lower() or "sem3" in text.lower(): return "3"
        if "sem-2" in text.lower() or "sem2" in text.lower(): return "2"
        if "sem-1" in text.lower() or "sem1" in text.lower(): return "1"

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
                
                # STRICT YEAR FILTER: Ignore anything from 2025 or older
                if "2025" in text or notice_date.year < 2026:
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
