from __future__ import annotations
import asyncio
import datetime
import re
import random
import os
import json
import base64
import sys
import argparse
import time
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor

# ─────────────────────────────────────────────
# IMPORTS — Graceful fallback if not installed
# ─────────────────────────────────────────────
try:
    from playwright.async_api import async_playwright, Page, BrowserContext # type: ignore
    from playwright_stealth import stealth_async # type: ignore
except ImportError:
    pass

try:
    from patchright.async_api import async_playwright as patchright_playwright # type: ignore
except ImportError:
    pass

try:
    from notifier import Notifier # type: ignore
except ImportError:
    pass

try:
    import requests # type: ignore
    from curl_cffi import requests as cffi_requests # type: ignore
    from bs4 import BeautifulSoup # type: ignore
    import dateutil.parser as dparser # type: ignore
except ImportError:
    pass

try:
    import httpx # type: ignore
except ImportError:
    pass

try:
    import nodriver as uc_nodriver # type: ignore
except ImportError:
    pass

try:
    from camoufox.async_api import AsyncCamoufox # type: ignore
except ImportError:
    pass

try:
    from seleniumbase import Driver as SBDriver # type: ignore
except ImportError:
    pass

try:
    import undetected_chromedriver as uc_chrome # type: ignore
    from selenium.webdriver.common.by import By as SBy # type: ignore
    from selenium.webdriver.support.ui import WebDriverWait # type: ignore
    from selenium.webdriver.support import expected_conditions as EC # type: ignore
except ImportError:
    pass

try:
    from DrissionPage import ChromiumPage, ChromiumOptions # type: ignore
except ImportError:
    pass

try:
    import cloudscraper as cloudscraper_lib # type: ignore
except ImportError:
    pass

try:
    import tls_client as tls_client_lib # type: ignore
except ImportError:
    pass

try:
    from botasaurus.browser import browser as botasaurus_browser, Driver as BotDriver # type: ignore
    from botasaurus.request import request as botasaurus_request, AntiDetectRequests # type: ignore
except ImportError:
    pass

try:
    from pydoll.browser.chrome import Chrome as PydollChrome # type: ignore
    from pydoll.constants import By as PydollBy # type: ignore
except ImportError:
    pass

try:
    from scrapling import StealthyFetcher, PlayWrightFetcher # type: ignore
except ImportError:
    pass

try:
    import seleniumwire.undetected_chromedriver as swire_uc # type: ignore
except ImportError:
    pass

try:
    import pychrome as pychrome_lib # type: ignore
except ImportError:
    pass

try:
    import proxybroker as pb_lib # type: ignore
except ImportError:
    pass

try:
    from fp.fp import FreeProxy # type: ignore
except ImportError:
    pass

# ─────────────────────────────────────────────
# BEZIER HUMAN BOT
# ─────────────────────────────────────────────
class HumanBot:
    def __init__(self, page: Page):
        self.page: Page = page

    async def bezier_move(self, tx: int, ty: int):
        try:
            vp: Optional[Dict[str, int]] = self.page.viewport_size or {"width": 1366, "height": 768}
            sx, sy = random.randint(0, vp["width"]), random.randint(0, vp["height"])
            cp1x, cp1y = sx + random.randint(-200, 200), sy + random.randint(-200, 200)
            cp2x, cp2y = tx + random.randint(-100, 100), ty + random.randint(-100, 100)
            steps: int = random.randint(20, 40)
            for i in range(steps + 1):
                t: float = i / steps
                x: float = (1-t)**3*sx + 3*(1-t)**2*t*cp1x + 3*(1-t)*t**2*cp2x + t**3*tx
                y: float = (1-t)**3*sy + 3*(1-t)**2*t*cp1y + 3*(1-t)*t**2*cp2y + t**3*ty
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.005, 0.015))
        except Exception: pass

    async def click(self, selector: str):
        try:
            el = self.page.locator(selector).first
            box = await el.bounding_box()
            if box:
                tx, ty = box["x"] + box["width"]*random.random(), box["y"] + box["height"]*random.random()
                await self.bezier_move(int(tx), int(ty))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await self.page.mouse.click(tx, ty)
        except Exception: await self.page.locator(selector).first.click()

    async def scroll(self, amount: int = 500):
        for _ in range(random.randint(3, 6)):
            await self.page.mouse.wheel(0, amount // 5 + random.randint(-50, 50))
            await asyncio.sleep(random.uniform(0.1, 0.4))

    async def read(self, duration: float = 5.0):
        end: float = time.time() + duration
        while time.time() < end:
            await self.scroll(random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.5, 2.0))

# ─────────────────────────────────────────────
# MAIN SCRAPER CLASS (v100: OMNI-CRAWLER)
# ─────────────────────────────────────────────
class MBAScraper:
    def __init__(self, target_mode: str = "all", force_sync: bool = False):
        self.target_mode: str = target_mode
        self.force_sync: bool = force_sync
        self.base_url: str = "https://sol.du.ac.in"
        self.keywords: List[str] = ['MBA', 'Master of Business Administration']
        self.visited: Set[str] = set()
        self.notices: List[Dict[str, Any]] = []
        self.discovery_queue: List[str] = [
            "https://sol.du.ac.in/home.php",
            "https://web.sol.du.ac.in/home",
            "https://sol.du.ac.in/all-notices.php",
            "https://web.sol.du.ac.in/info/online-class-schedule"
        ]
        self.class_schedule_url: str = "https://web.sol.du.ac.in/my/team_schedules/vcs.php"
        self.parent_url: str = "https://web.sol.du.ac.in/info/online-class-schedule"
        self.user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/124.0.0.0 Safari/537.36"
        self.current_url: str = ""
        self.keys: Dict[str, str] = {
            "SCRAPER_API": os.environ.get("SCRAPER_API_KEY", ""),
            "WSAI": os.environ.get("WEBSCRAPING_AI_KEY", ""),
            "ANT": os.environ.get("SCRAPER_ANT_KEY", ""),
        }

    def _iframe_headers(self) -> dict:
        return {
            "User-Agent": self.user_agent, "Referer": self.parent_url,
            "sec-fetch-dest": "iframe", "sec-fetch-mode": "navigate", "sec-fetch-site": "same-origin",
        }

    # ═══════════════════════════════════════════
    # FETCHING METHODS
    # ═══════════════════════════════════════════
    async def fetch_cffi(self, url: str) -> Optional[str]:
        self.current_url = url
        try:
            session = cffi_requests.Session(impersonate="chrome124")
            r = session.get(url, headers=self._iframe_headers() if "vcs.php" in url else {"User-Agent": self.user_agent}, timeout=30)
            return r.text if r.status_code == 200 else None
        except Exception: return None

    async def fetch_wayback(self, url: str) -> Optional[str]:
        self.current_url = url
        try:
            r = requests.get(f"http://archive.org/wayback/available?url={url}", timeout=10).json()
            snap: Optional[str] = r.get("archived_snapshots", {}).get("closest", {}).get("url")
            return requests.get(snap, timeout=20).text if snap else None
        except Exception: return None

    async def fetch_paid(self, url: str, provider: str) -> Optional[str]:
        self.current_url = url
        key: Optional[str] = self.keys.get(provider)
        if not key: return None
        try:
            api: str
            if provider == "SCRAPER_API":
                api = f"http://api.scraperapi.com?api_key={key}&url={url}&render_js=true"
            elif provider == "ANT":
                api = f"https://api.scraperant.com/v2/general?url={url}&x-api-key={key}&browser=true"
            else: # WSAI
                api = f"https://api.webscraping.ai/html?url={url}&api_key={key}&proxy=residential&render=true"
            return requests.get(api, timeout=60).text
        except Exception: return None

    # ═══════════════════════════════════════════
    # CRAWLER & DISCOVERY
    # ═══════════════════════════════════════════
    async def discover_and_crawl(self, max_pages: int = 50):
        print(f"[CRAWLER]: Discovering MBA content on {self.base_url}...")
        count: int = 0
        while self.discovery_queue and count < max_pages: # type: ignore
            url: str = self.discovery_queue.pop(0)
            if url in self.visited: continue
            self.visited.add(url)
            count = int(count) + 1 # type: ignore
            print(f"[CRAWLER][{count}/{max_pages}]: Visiting {url}")
            html: Optional[str] = await self.fetch_cffi(url)
            if not html: continue
            
            soup: BeautifulSoup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                href: str = a['href']
                if href.startswith('/'): href = self.base_url + href
                elif not href.startswith('http'): href = self.base_url + '/' + href
                if 'sol.du.ac.in' in href and href not in self.visited and href not in self.discovery_queue:
                    if any(ext in href.lower() for ext in ['.pdf', '.php', '.html']) or '/' in href:
                        self.discovery_queue.append(href)
            
            # Special parsing with current URL set
            self.current_url = url
            parsed = self._parse_html(html)
            for item in parsed:
                if not any(n['link'] == item['link'] for n in self.notices):
                    self.notices.append(item)

    # ═══════════════════════════════════════════
    # CLASS CHAIN (PAID APIs LAST)
    # ═══════════════════════════════════════════
    async def run_class_chain(self) -> List[Dict[str, Any]]:
        print("[OMNI]: Running Class Schedule Chain...")
        for method in [self.fetch_cffi, self.fetch_wayback]:
            html: Optional[str] = await method(self.class_schedule_url)
            if html and self._is_valid(html):
                res: List[Dict[str, Any]] = self._parse_html(html)
                if res: return res
        
        # Playwright Human Fallback
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
                page: Page = await browser.new_page()
                bot: HumanBot = HumanBot(page)
                await page.goto(self.parent_url, wait_until="networkidle")
                await bot.read(5)
                self.current_url = self.class_schedule_url
                res_frames: List[Dict[str, Any]] = await self._extract_frames(page)
                await browser.close()
                if res_frames: return res_frames
        except Exception: pass

        # PAID APIs (ULTIMATE LAST RESORT)
        print("[OMNI]: Free methods failed. Using paid fallbacks...")
        for provider in ["SCRAPER_API", "ANT", "WSAI"]:
            html = await self.fetch_paid(self.class_schedule_url, provider)
            if html and self._is_valid(html):
                res_paid: List[Dict[str, Any]] = self._parse_html(html)
                if res_paid: return res_paid
        return []

    # ═══════════════════════════════════════════
    # PARSING LOGIC
    # ═══════════════════════════════════════════
    def _parse_html(self, html: str) -> List[Dict[str, Any]]:
        soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
        results: List[Dict[str, Any]] = []
        
        # SPECIAL: Target "Important Links" and "Important Notices" on home.php (Full capture)
        is_home = "home.php" in self.current_url.lower()
        if is_home:
            # 1. Marquee / Important Links
            imp_links_div = soup.find(id="important-links")
            if imp_links_div:
                for a in imp_links_div.find_all('a', href=True): # type: ignore
                    txt = a.get_text().strip()
                    if txt:
                        results.append({
                            "title": f"[Important Link] {txt}", "link": a['href'],
                            "semester": "0", "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                            "description": "Found in Important Links section."
                        })
            
            # 2. Important Notices / Information (Blue box to the right)
            for alert in soup.find_all(class_="alert"):
                header = alert.find(["h4", "h5", "b", "strong"])
                if (header and "important notices" in header.get_text().lower()) or alert.get("id") != "important-links":
                    # If it has many links and isn't the pink marquee, it's likely the right box
                    links = alert.find_all('a', href=True)
                    if len(links) > 3:
                        for a in links:
                            txt = a.get_text().strip()
                            # APPLY MBA FILTER HERE
                            if txt and any(kw.lower() in txt.lower() for kw in self.keywords):
                                results.append({
                                    "title": f"[Notice] {txt}", "link": a['href'],
                                    "semester": "0", "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                                    "description": "Found in Important Notices section (MBA filtered)."
                                })

        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            date_str: Optional[str] = None
            for r in rows:
                if "date:" in r.get_text().lower():
                    m = re.search(r'(\d{1,2}[-/]\d{2}[-/]\d{4})', r.get_text())
                    if m:
                        date_str = m.group(1)
                        break
            if not date_str: continue
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) < 4: continue
                course = cells[0].get_text(strip=True)
                if not any(kw.lower() in course.lower() for kw in self.keywords): continue
                sem, subj = cells[1].get_text(strip=True), cells[2].get_text(strip=True)
                time_txt = next((c.get_text(strip=True) for c in cells if re.search(r'\d{1,2}:\d{2}', c.get_text())), "")
                href = next((a["href"] for c in reversed(cells) for a in [c.find("a")] if a and a.get("href")), "#pending")
                semester = self.extract_semester_logic(sem or course)
                link = href if href else "#pending"
                results.append({
                    "title": f"[{date_str}] MBA Sem {semester}: {subj} ({time_txt})",
                    "link": link, "semester": semester, "date": self.parse_date(str(date_str)), # type: ignore
                    "class_time": time_txt, "description": f"MBA Live Class: {subj} at {time_txt}"
                })
        
        # General MBA filter for all other links
        for a in soup.find_all('a', href=True):
            txt = a.get_text().strip()
            if any(kw.lower() in txt.lower() for kw in self.keywords):
                if not any(r['link'] == a['href'] for r in results):
                    results.append({
                        "title": f"MBA Content: {txt}", "link": a['href'],
                        "semester": self.extract_semester_logic(txt),
                        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "description": f"MBA update found on {self.current_url}"
                    })

        return results

    async def _extract_frames(self, page: Page) -> List[Dict[str, Any]]:
        all_raw = []
        for ctx in [page] + list(page.frames):
            try:
                data = await ctx.evaluate("""() => Array.from(document.querySelectorAll('table')).map(t => 
                    Array.from(t.querySelectorAll('tr')).map(tr => 
                        Array.from(tr.querySelectorAll('td,th')).map(c => ({
                            text: c.innerText.trim(), href: (c.querySelector('a') || {}).href
                        }))
                    )
                )""")
                if data: all_raw.extend(data)
            except Exception: continue
        return self._parse_raw_tables(all_raw)

    def _parse_raw_tables(self, tables: List[Any]) -> List[Dict[str, Any]]:
        results = []
        for rows in tables:
            d_str = None
            for r in rows:
                combined_text = " ".join(c.get("text", "") for c in r)
                if "date:" in combined_text.lower():
                    m = re.search(r'(\d{1,2}[-/]\d{2}[-/]\d{4})', combined_text)
                    if m:
                        d_str = m.group(1)
                        break
            if not d_str: continue
            for cells_raw in rows:
                cells = list(cells_raw) # type: ignore
                if len(cells) < 4: continue
                course = str(cells[0].get("text", "")) # type: ignore
                if not any(kw.lower() in course.lower() for kw in self.keywords): continue
                sem, subj = str(cells[1].get("text", "")), str(cells[2].get("text", "")) # type: ignore
                time_txt = next((str(c.get("text", "")) for c in cells if re.search(r'\d{1,2}:\d{2}', str(c.get("text", "")))), "") # type: ignore
                href = next((str(c["href"]) for c in list(reversed(cells)) if c.get("href") and "teams.microsoft" in str(c["href"])), "#pending") # type: ignore
                semester = self.extract_semester_logic(sem or course)
                results.append({
                    "title": f"[{d_str}] MBA Sem {semester}: {subj} ({time_txt})",
                    "link": href, "semester": semester, "date": self.parse_date(str(d_str)), # type: ignore
                    "class_time": time_txt, "description": f"MBA Live Class: {subj} at {time_txt}"
                })
        return results

    def extract_semester_logic(self, text: str) -> str:
        m = re.search(r'\b([1-4])(?:st|nd|rd|th)?\b', text, re.I)
        return m.group(1) if m else "0"

    def _is_valid(self, html):
        return html and "sol" in html.lower() and len(html) > 500

    def parse_date(self, ds: str) -> str:
        for fmt in ["%d-%m-%Y", "%d/%m/%Y"]:
            try: return datetime.datetime.strptime(ds.strip(), fmt).strftime("%Y-%m-%d")
            except Exception: continue
        return datetime.datetime.now().strftime("%Y-%m-%d")

    async def run(self, days_back: int = 15, mode: str = "all", targets: Optional[List[str]] = None) -> list:
        # Full Comprehensive Scan (Manual or All)
        if mode == "all":
            print("[OMNI]: Running COMPREHENSIVE scan (Website + Notices + Classes)")
            self.notices.extend(await self.run_class_chain()) # type: ignore
            await self.discover_and_crawl(max_pages=100)
            return self.notices

        # Standard Website & Notices (10 min)
        if mode == "website":
            print("[OMNI]: Running DEEP WEBSITE & NOTICES scan (10 min cycle)")
            # Targeted check of known critical notice pages
            for url in ["https://sol.du.ac.in/all-notices.php", "https://sol.du.ac.in/home.php"]:
                html = await self.fetch_cffi(url)
                if html:
                    self.current_url = url
                    parsed = self._parse_html(html)
                    for item in parsed:
                        if not any(n['link'] == item['link'] for n in self.notices):
                            self.notices.append(item)
            # Also run a discovery crawl
            await self.discover_and_crawl(max_pages=50)
            return self.notices

        # Class Schedule Only (60 min)
        if mode == "classes":
            print("[OMNI]: Running CLASS SCHEDULE ONLY scan (60 min cycle)")
            self.notices.extend(await self.run_class_chain()) # type: ignore
            return self.notices

        return self.notices

    def sync_results(self, results: list, notifier, memory_file: str):
        synced = set()
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r') as f:
                    content = f.read().strip()
                    if content: synced = set(json.loads(content))
            except Exception: pass
        stats = {"new": 0, "skipped": 0}
        for item in results:
            h = base64.b64encode(f"{item['semester']}:{item['title']}:{item['date']}:{item['class_time']}".encode()).decode()
            if h in synced and not getattr(self, "force_sync", False): # type: ignore
                stats["skipped"] = int(stats["skipped"]) + 1; continue
            if notifier.sync_to_website(item):
                synced.add(h); stats["new"] = int(stats["new"]) + 1 # type: ignore
            else: stats["skipped"] = int(stats["skipped"]) + 1 # type: ignore
        print(f"[SYNC]: New={stats['new']} Skipped={stats['skipped']}")
        with open(memory_file, "w") as f:
            json.dump(list(synced), f)

if __name__ == "__main__":
    asyncio.run(MBAScraper().run())
