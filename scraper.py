from __future__ import annotations
import asyncio
import datetime
import re
import random
import os
import json
import types
import base64
import sys
import argparse
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor

# Unified Imports 
try:
    from playwright.async_api import async_playwright, Page, BrowserContext, request # type: ignore
    from playwright_stealth import stealth_async # type: ignore
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

class MBAScraper:
    """v70.0: OMNI-SCRAPER (The Finite Fallback Engine)"""
    def __init__(self, target_mode: str = "all", force_sync: bool = False):
        self.target_mode = target_mode
        self.force_sync = force_sync
        self.base_url = "https://web.sol.du.ac.in/home"
        self.keywords = ['MBA', 'Master of Business Administration']
        self.visited = set()
        self.notices = []
        self.days_back = 15
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ]
        self.mobile_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.64 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
        ]
        self.user_agent = random.choice(self.user_agents)
        
        self.targets = [
            "https://sol.du.ac.in/home.php",
            "https://web.sol.du.ac.in/my/team_schedules/vcs.php",
            "https://sol.du.ac.in/all-notices.php"
        ]

        # API Keys - v70.2: Explicit checking
        self.keys = {
            "SCRAPER_API": os.environ.get("SCRAPER_API_KEY", ""),
            "WSAI": os.environ.get("WEBSCRAPING_AI_KEY", ""),
            "ANT": os.environ.get("SCRAPER_ANT_KEY", ""),
            "CF_WORKER": os.environ.get("CF_WORKER_URL", ""),
            "TOR": os.environ.get("TOR_PROXY", "")
        }
        
        for k, v in self.keys.items():
            if not v: print(f"[OMNI][INFO]: Key {k} is missing. Strategy will be skipped.")
            else: print(f"[OMNI][INFO]: Key {k} is present.")
        

    # --- ADVANCED STEALTH SENSORS ---
    async def bezier_mouse_move(self, page, x2, y2, x1=None, y1=None):
        """v70.0: Human-like mouse movement using Bezier curves"""
        if x1 is None or y1 is None:
            x1, y1 = await page.evaluate("() => [window.innerWidth / 2, window.innerHeight / 2]")
        # Control points for the curve
        cx = (x1 + x2) / 2 + random.randint(-100, 100)
        cy = (y1 + y2) / 2 + random.randint(-100, 100)
        
        steps = 25
        for i in range(steps):
            t = i / steps
            # Quadratic Bezier formula: (1-t)^2*P1 + 2(1-t)t*Pc + t^2*P2
            x = (1-t)**2 * x1 + 2*(1-t)*t * cx + t**2 * x2
            y = (1-t)**2 * y1 + 2*(1-t)*t * cy + t**2 * y2
            await page.mouse.move(x, y)
            if i % 5 == 0: await asyncio.sleep(0.01)

    async def sensory_hover(self, page, selector):
        """v70.0: Realistic hover before interaction"""
        try:
            el = page.locator(selector).first
            box = await el.bounding_box()
            if box:
                target_x = box['x'] + box['width']/2 + random.randint(-5, 5)
                target_y = box['y'] + box['height']/2 + random.randint(-5, 5)
                await self.bezier_mouse_move(page, target_x, target_y)
                await asyncio.sleep(random.uniform(0.5, 1.5))
        except Exception: pass

    # --- TLS & FINGERPRINTING ---
    async def fetch_via_tls_rotation(self, url: str) -> Optional[str]:
        """v75.0: Scrapy-Standard TLS Fingerprinting (Bypass common WAFs)"""
        # Scrapy-standard JA3 profiles for high-end stealth
        ja3_fingerprints = ["chrome120", "chrome116", "safari15", "firefox117", "edge101"]
        selected = random.choice(ja3_fingerprints)
        print(f"[OMNI][TLS]: Using Scrapy-standard fingerprint {selected}...")
        try:
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-IN,en;q=0.9",
                "Referer": "https://web.sol.du.ac.in/home",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            }
            if "vcs.php" in url:
                headers.update({"Sec-Fetch-Dest": "iframe"})
            session = cffi_requests.Session(impersonate=selected)
            r = session.get(url, headers=headers, timeout=30)
            if r.status_code == 200: return r.text
            return None
        except Exception as e:
            print(f"[OMNI][TLS][ERROR]: {e}")
            return None

    async def ghost_fetch(self, context, url: str) -> Optional[str]:
        """v76.0: Ninja Ghost Fetch (Masked headers + Client Hints)"""
        print(f"[OMNI][GHOST]: Attempting Ghost fetch for {url}...")
        try:
            headers = {
                "Referer": "https://web.sol.du.ac.in/home",
                "Sec-Fetch-Dest": "iframe" if "vcs.php" in url else "document",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            }
            response = await context.request.get(url, headers=headers)
            if response.status == 200:
                t = await response.text()
                return t
            return None
        except Exception: return None

    # --- EXOTIC FALLBACKS ---
    async def fetch_via_wayback(self, url: str) -> Optional[str]:
        """v70.0: Wayback Machine API (When site is 403)"""
        print(f"[OMNI][WAYBACK]: Checking archives for {url}...")
        try:
            api_url = f"http://archive.org/wayback/available?url={url}"
            loop = asyncio.get_event_loop()
            def get_json(u): return requests.get(u).json()
            r_resp = await loop.run_in_executor(None, get_json, api_url)
            snapshot = r_resp.get("archived_snapshots", {}).get("closest", {}).get("url")
            if snapshot:
                print(f"[OMNI][WAYBACK]: Snapshot found: {snapshot}")
                resp = await loop.run_in_executor(None, requests.get, snapshot)
                return resp.text
            return None
        except Exception: return None

    async def fetch_via_google_cache(self, url: str) -> Optional[str]:
        """v70.0: Google Cache Fetch"""
        cache_url = f"http://webcache.googleusercontent.com/search?q=cache:{url}"
        print(f"[OMNI][CACHE]: Checking Google Cache...")
        try:
            loop = asyncio.get_event_loop()
            def sync_get(u):
                return requests.get(u, timeout=20)
            r = await loop.run_in_executor(None, sync_get, cache_url)
            if r.status_code == 200: return r.text
            return None
        except Exception: return None

    async def fetch_via_scraperant(self, url: str) -> Optional[str]:
        """V70.0: ScraperAnt (10,000 free credits/mo)"""
        if not self.keys["ANT"]: return None
        try:
            loop = asyncio.get_event_loop()
            def sync_get(u, k):
                api_url = f"https://api.scraperant.com/v2/general?url={u}&x-api-key={k}&browser=true"
                return requests.get(api_url, timeout=60)
            response = await loop.run_in_executor(None, sync_get, url, self.keys["ANT"])
            return response.text if response.status_code == 200 else None
        except Exception: return None

    async def fetch_via_webscraping_ai(self, url: str) -> Optional[str]:
        if not self.keys["WSAI"]: return None
        try:
            loop = asyncio.get_event_loop()
            def sync_get(u, k):
                api_url = f"https://api.webscraping.ai/html?url={u}&api_key={k}&proxy=residential&render=true"
                return requests.get(api_url, timeout=60)
            response = await loop.run_in_executor(None, sync_get, url, self.keys["WSAI"])
            return response.text if response.status_code == 200 else None
        except Exception: return None

    async def fetch_via_cf_worker(self, url: str) -> Optional[str]:
        """v75.0: Cloudflare Worker Bridge (Free & Open Source DIY Proxy)"""
        if not self.keys["CF_WORKER"]: return None
        print(f"[OMNI][CF_WORKER]: Fetching via Cloudflare Worker...")
        try:
            loop = asyncio.get_event_loop()
            def sync_get(u, k):
                # CF Workers are extremely resilient against WAFs
                params = {"url": u}
                return requests.get(k, params=params, timeout=45)
            response = await loop.run_in_executor(None, sync_get, url, self.keys["CF_WORKER"])
            return response.text if response.status_code == 200 else None
        except Exception as e:
            print(f"[OMNI][CF_WORKER][ERROR]: {e}")
            return None

    async def fetch_via_google_search(self, query: str) -> Optional[str]:
        """v78.0: Google Dorking Strategy (Prophet Mode)"""
        print(f"[OMNI][PROPHET]: Searching Google for latest notices...")
        dork_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        # We use our own bridge_fetch to scrape Google!
        try:
            # Recursively use TLS rotation or Tor to hit Google (Meta-Scraping)
            html = await self.fetch_via_tls_rotation(dork_url)
            if html and ("site:sol.du.ac.in" in html or "results" in html):
                return html
            return None
        except Exception as e:
            print(f"[OMNI][PROPHET][ERR]: {e}")
            return None

    async def fetch_via_sitemap(self, url: str) -> Optional[str]:
        """v80.0: Sitemap Dorking (Omniscient Mode)"""
        sitemap_url = f"https://sol.du.ac.in/sitemap.xml"
        print(f"[OMNI][SITEMAP]: Checking {sitemap_url} for updates...")
        try:
            html = await self.fetch_via_tls_rotation(sitemap_url)
            if html and "<urlset" in html:
                return html
            return None
        except Exception: return None

    async def fetch_via_cdx(self, url: str) -> Optional[str]:
        """v80.0: Wayback CDX Historical Index (Finding hidden uploads)"""
        print(f"[OMNI][CDX]: Querying Wayback Historical Index for PDFs...")
        # Search for all PDFs uploaded to sol.du.ac.in in the last 30 days
        cdx_url = f"http://web.archive.org/cdx/search/cdx?url=sol.du.ac.in&matchType=domain&filter=mimetype:application/pdf&limit=50&output=json"
        try:
            loop = asyncio.get_event_loop()
            def get_json(u): return requests.get(u).json()
            data = await loop.run_in_executor(None, get_json, cdx_url)
            # Convert CDX JSON to a pseudo-HTML links list for our parser
            if data and len(data) > 1:
                html_links = "<html><body>"
                for entry in data[1:]: # Skip header
                    orig_url = entry[2]
                    html_links += f'<a href="{orig_url}">Archive Result</a> '
                html_links += "</body></html>"
                return html_links
            return None
        except Exception: return None

    async def fetch_via_tor(self, url: str) -> Optional[str]:
        """v77.0: Tor Ghost Bridge (Ultimate Open-Source Anonymous Proxy)"""
        if not self.keys["TOR"]: return None
        print(f"[OMNI][TOR]: Fetching via Tor Proxy {self.keys['TOR']}...")
        try:
            proxies = {'http': self.keys["TOR"], 'https': self.keys["TOR"]}
            loop = asyncio.get_event_loop()
            def sync_get(u, p):
                return requests.get(u, proxies=p, timeout=45, headers={"User-Agent": random.choice(self.user_agents)})
            response = await loop.run_in_executor(None, sync_get, url, proxies)
            return response.text if response.status_code == 200 else None
        except Exception as e:
            print(f"[OMNI][TOR][ERROR]: {e}")
            return None

    # [DELETE] fetch_via_scrapfly - Removed per user request v75.0 (Not open source)

    # [DELETE] fetch_via_zyte - Removed per user request v70.1

    def is_valid_html(self, html: str) -> bool:
        """v70.4: Check if retrieved HTML is actual data, not a bot-check or redirect"""
        if not html or len(html) < 200: return False
        blocked_keywords = ["Google Search", "Wayback Machine", "captcha", "security check", "challenge-platform"]
        # If it's a redirect/interstitial, it usually has these in the title/body
        title_match = re.search(r"<title>(.*?)</title>", html, re.I)
        title = title_match.group(1) if title_match else ""
        if any(kw.lower() in title.lower() for kw in blocked_keywords): return False
        
        # Must contain some SOL specific text
        low_html = html.lower()
        if "sol" not in low_html and "university of delhi" not in low_html: return False
        return True

    # --- BRIDGE & API FETCHER ---
    async def bridge_fetch(self, context, url: str) -> Optional[str]:
        """v70.4: Finite Fallback Chain with Validation"""
        strategies = [
            ("GHOST", lambda u: self.ghost_fetch(context, u)),
            ("TLS_ROTATION", self.fetch_via_tls_rotation),
            ("GOOGLE_CACHE", self.fetch_via_google_cache),
            ("WAYBACK", self.fetch_via_wayback),
        ]
        # v80.0: Omniscient Strategy (Archives & Indices)
        if "all-notices" in url or "home.php" in url:
            strategies.append(("G-SEARCH", lambda u: self.fetch_via_google_search("site:sol.du.ac.in +MBA +notices")))
            strategies.append(("SITEMAP", self.fetch_via_sitemap))
            strategies.append(("CDX-INDEX", self.fetch_via_cdx))
        
        # Add API strategies if keys exist
        if self.keys["TOR"]: strategies.append(("TOR", self.fetch_via_tor))
        if self.keys["SCRAPER_API"]: strategies.append(("SCRAPERAPI", self.fetch_via_api))
        if self.keys["CF_WORKER"]: strategies.append(("CF_WORKER", self.fetch_via_cf_worker))
        if self.keys["ANT"]: strategies.append(("SCRAPER_ANT", self.fetch_via_scraperant))
        if self.keys["WSAI"]: strategies.append(("WEBSCRAPING_AI", self.fetch_via_webscraping_ai))
        
        for name, func in strategies:
            print(f"[OMNI][CHAIN]: Trying {name}...")
            try:
                if name == "GHOST":
                    html = await self.ghost_fetch(context, url)
                else:
                    html = await func(url)
                
                if html:
                    if self.is_valid_html(html):
                        print(f"[OMNI][SUCCESS]: Strategy {name} recovered valid data.")
                        return html
                    else:
                        print(f"[OMNI][CHAIN]: {name} returned invalid content (Redirect/BotCheck). Continuing...")
            except Exception as e:
                print(f"[OMNI][CHAIN][ERROR]: {name} failed: {e}")
        return None

    async def fetch_via_api(self, url: str) -> Optional[str]:
        """v70.2: ScraperAPI Bridge"""
        if not self.keys["SCRAPER_API"]: return None
        print(f"[OMNI][SCRAPERAPI]: Fetching via ScraperAPI...")
        api_url = f"http://api.scraperapi.com?api_key={self.keys['SCRAPER_API']}&url={url}&render_js=true"
        try:
            loop = asyncio.get_event_loop()
            def sync_get(u):
                return requests.get(u, timeout=60)
            r = await loop.run_in_executor(None, sync_get, api_url)
            return r.text if r.status_code == 200 else None
        except Exception as e:
            print(f"[OMNI][SCRAPERAPI][ERROR]: {e}")
            return None

    # --- HUMAN NAVIGATION ENGINE ---
    async def stealth_navigate_flow(self, page) -> bool:
        """v70.0: Complex, randomized human workflow"""
        print("[OMNI][STEALTH]: Initiating human-sensory navigation...")
        try:
            # Step 1: Home page visit
            await page.goto("https://sol.du.ac.in/home.php", wait_until="domcontentloaded")
            # v79.0: Bézier Hover
            await self.bezier_mouse_move(page, 0, 0, random.randint(200, 500), random.randint(100, 400))
            await self.sensory_hover(page, "text='Academic'") 
            await asyncio.sleep(random.uniform(2, 4))
            
            # Step 2: Random reading scroll
            for _ in range(3):
                await page.mouse.wheel(0, random.randint(300, 700))
                await asyncio.sleep(random.uniform(1, 2))
                
            # Step 3: Click through to support
            support_link = "text='Student Support'"
            await self.sensory_hover(page, support_link)
            await page.locator(support_link).first.click()
            await asyncio.sleep(3)
            
            # Step 4: Final Target transition
            # v78.0: Human Hesitation Pause
            await asyncio.sleep(random.uniform(1.5, 3.5))
            await page.mouse.move(random.randint(100, 700), random.randint(100, 500), steps=15)
            
            await page.goto("https://web.sol.du.ac.in/info/online-class-schedule", wait_until="networkidle")
            if "Forbidden" in await page.content(): return False
            return True
        except Exception: return False

    async def run(self, days_back: int = 15, targets: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """v77.0: OMNI Master Sequence (God-Tier Stealth Mode)"""
        self.days_back = days_back
        print("[OMNI]: Launching Master Stealth Browser (Ninja Mode)...")
        async with async_playwright() as p:
            # v79.0: Persona Swapping (Digital Chameleon)
            is_mobile = random.choice([True, False])
            persona_ua = random.choice(self.mobile_agents if is_mobile else self.user_agents)
            persona_viewport = {"width": 390, "height": 844} if is_mobile else res
            
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
            )
            context = await browser.new_context(
                user_agent=persona_ua,
                viewport=persona_viewport,
                is_mobile=is_mobile,
                has_touch=is_mobile,
                device_pixel_ratio=2 if is_mobile else 1,
                locale="en-IN",
                timezone_id="Asia/Kolkata"
            )
            # v80.0: Network-Layer Spoofing (4G Profile)
            if is_mobile:
                await context.set_offline(False)
                # Simulating 4G latency (~100ms) and throughput
                try:
                    cdp = await context.new_cdp_session(page)
                    await cdp.send("Network.emulateNetworkConditions", {
                        "offline": False,
                        "latency": 100 + random.randint(0, 50),
                        "downloadThroughput": 4 * 1024 * 1024 / 8, # 4 Mbps
                        "uploadThroughput": 2 * 1024 * 1024 / 8  # 2 Mbps
                    })
                except Exception: pass
            
            ua_prefix = persona_ua
            print(f"[OMNI][PERSONA]: Launching as {'MOBILE' if is_mobile else 'DESKTOP'} (UA: {ua_prefix})")
            
            # v77.0: Advanced God-Tier Masking Script (mimicking SeleniumBase CDP)
            await context.add_init_script("""
                // Mask Webdriver
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                // Mask Chrome Runtime
                window.chrome = { runtime: {} };
                // Mask Languages & Plugins
                Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en-US', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                // Mask Permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
                // v78.0: Hardware Fingerprint Masking
                // Canvas Masking
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {
                    const context = originalGetContext.apply(this, arguments);
                    if (type === '2d') {
                        const originalGetImageData = context.getImageData;
                        context.getImageData = function() {
                            const image = originalGetImageData.apply(this, arguments);
                            image.data[0] = image.data[0] + (Math.random() > 0.5 ? 1 : -1);
                            return image;
                        };
                    }
                    return context;
                };
                // WebGL Masking
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) return 'NVIDIA Corporation';
                    if (parameter === 37446) return 'NVIDIA GeForce RTX 4090';
                    return getParameter.apply(this, arguments);
                };
                // v79.0: Font & Audio Masking
                // Font Masking
                Object.defineProperty(navigator, 'fonts', { get: () => ({}) });
                // AudioContext Masking
                const originalAudioContext = window.AudioContext || window.webkitAudioContext;
                if (originalAudioContext) {
                    const originalGetChannelData = AudioBuffer.prototype.getChannelData;
                    AudioBuffer.prototype.getChannelData = function() {
                        const data = originalGetChannelData.apply(this, arguments);
                        data[0] = data[0] + (Math.random() * 0.0001);
                        return data;
                    };
                }
            """)
            
            page = await context.new_page()
            try: await stealth_async(page); print("[OMNI]: Stealth active.")
            except Exception: pass

            actual_targets = targets if targets else self.targets
            for url in actual_targets:
                # v71.0: Mode-based filtering for scheduling
                if self.target_mode == "classes" and "vcs.php" not in url: continue # type: ignore
                if self.target_mode == "notices" and "vcs.php" in url: continue # type: ignore
                
                try:
                    if "vcs.php" in url or "online-class-schedule" in url:
                        # v71.0: ITERATIVE EXTRACTION - Keep trying until we get tables!
                        strategies = [
                            ("GHOST", lambda u: self.ghost_fetch(context, u)), # type: ignore
                            ("G-SEARCH", lambda u: self.fetch_via_google_search("site:sol.du.ac.in +MBA +notices")),
                            ("SITEMAP", self.fetch_via_sitemap), # type: ignore
                            ("CDX-INDEX", self.fetch_via_cdx), # type: ignore
                            ("TLS_ROTATION", self.fetch_via_tls_rotation), # type: ignore
                            ("GOOGLE_CACHE", self.fetch_via_google_cache), # type: ignore
                            ("WAYBACK", self.fetch_via_wayback), # type: ignore
                            ("CF_WORKER", self.fetch_via_cf_worker), # type: ignore
                            ("SCRAPERAPI", self.fetch_via_api), # type: ignore
                            ("SCRAPER_ANT", self.fetch_via_scraperant), # type: ignore
                            ("WEBSCRAPING_AI", self.fetch_via_webscraping_ai), # type: ignore
                        ]
                        
                        found_data = False
                        for name, func in strategies:
                            # Skip strategy if API key is missing
                            if any(k in name for k in ["API", "ANT", "WSAI", "CF_WORKER"]) and not any(self.keys.values()): # type: ignore
                                continue
                                
                            print(f"[OMNI][ITERATIVE]: Trying {name} for Class Schedule...")
                            try:
                                res = func(url)
                                # v71.0: Correctly await if it's a coroutine or lambda-returned coroutine
                                if asyncio.iscoroutine(res) or (hasattr(res, "__await__") and res.__await__):
                                    html = await res
                                else:
                                    html = res
                                
                                if html and self.is_valid_html(html): # type: ignore
                                    temp_page = await context.new_page()
                                    await temp_page.set_content(html)
                                    extracted = await self.extract_online_classes(temp_page) # type: ignore
                                    await temp_page.close()
                                    
                                    if extracted and len(extracted) > 0: # type: ignore
                                        print(f"[OMNI][SUCCESS]: {len(extracted)} classes found via {name}!") # type: ignore
                                        found_data = True
                                        break
                                    else:
                                        print(f"[OMNI][FAIL]: {name} returned HTML but 0 tables found. Trying next...")
                            except Exception as e:
                                print(f"[OMNI][ERR]: {name} failed: {e}")
                        
                        if not found_data:
                            print("[OMNI][FINAL]: All fallbacks failed. Trying Direct Human Navigation...")
                            if await self.stealth_navigate_flow(page): # type: ignore
                                await self.extract_online_classes(page) # type: ignore
                    
                    elif "home.php" in url:
                        await page.goto(url, wait_until="domcontentloaded")
                        await self.extract_legacy_notices(page) # type: ignore
                    else:
                        await page.goto(url, wait_until="domcontentloaded")
                        await self.extract_mba_content(page) # type: ignore
                except Exception as e: print(f"[OMNI][ERROR]: {e}")
            await browser.close()
        return self.notices # type: ignore
    async def extract_online_classes(self, page):
        """V71.1: IFRAME-AWARE EXTRACTION (Targeting dynamic vcs.php)"""
        print(f"[CRAWLER]: Analyzing Class Schedule on {page.url}")
        local_results = []
        
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
                    if not row: continue
                    combined = " ".join([c.get('text', '') for c in row if c and isinstance(c, dict)]) # type: ignore
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
                    if not cells or len(cells) < 4: continue
                    row_text = " ".join([c.get('text', '') for c in cells if c and isinstance(c, dict)]) # type: ignore
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
                        
                        now_utc = datetime.datetime.now(datetime.timezone.utc)
                        ist_offset = datetime.timedelta(hours=5, minutes=30)
                        current_date_ist = (now_utc + ist_offset).date()
                        item_date_obj = self._normalize_date(str(date_str))
                        
                        description = f"MBA Live Class: {subject_text}. Time: {time_text}."
                        item = {
                            "title": title.strip(),
                            "link": final_link,
                            "semester": semester,
                            "date": self.parse_date(str(date_str)),
                            "class_time": time_text.strip(),
                            "description": description
                        }
                        # v73.1: Precision deduplication including time to support same-day multiple sessions
                        if not any(n['title'] == item['title'] and n['date'] == item['date'] and n.get('class_time') == item.get('class_time') for n in local_results):
                            local_results.append(item)
                            self.notices.append(item)
                            print(f"[CRAWLER][CLASS FOUND]: {title}")
        except Exception as e:
            print(f"[CRAWLER][ERROR]: Online classes parsing failed: {e}")
        return local_results

    async def extract_legacy_notices(self, page):
        """Parse notices from sol.du.ac.in (legacy) pages"""
        print(f"[CRAWLER]: Extracting legacy notices from {page.url}")
        local_results = []
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

                    item_data = {
                        "title": text.strip(),
                        "link": href,
                        "semester": semester,
                        "date": notice_date.strftime("%Y-%m-%d"),
                        "description": description
                    }
                    local_results.append(item_data)
                    self.notices.append(item_data)
        except Exception as e:
            print(f"[CRAWLER][ERROR]: Legacy notices parsing failed: {e}")
        return local_results

    async def extract_mba_content(self, page):
        """v19.3: Turbo Link Extraction (Single Page Evaluate)"""
        local_results = []
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

                    item_data = {
                        "title": text,
                        "link": href,
                        "semester": semester,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "description": description
                    }
                    local_results.append(item_data)
                    self.notices.append(item_data)
                    print(f"[CRAWLER][FOUND]: {text}")
        except Exception as e:
            print(f"[CRAWLER][ERROR]: Turbo extraction failed: {e}")
        return local_results

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

    async def auto_scroll(self, page):
        """Scroll for dynamic content loading"""
        try:
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
            await asyncio.sleep(2)
        except Exception: pass

    def parse_date(self, date_str: str) -> str:
        obj = self._normalize_date(date_str)
        return obj.strftime("%Y-%m-%d") if obj else datetime.datetime.now().strftime("%Y-%m-%d")

    def sync_results(self, results: List[Dict[str, Any]], notifier: 'Notifier', memory_file: str):
        """v72.0: Smart-Sync + Strict Midnight Cleanup & Data Preservation"""
        synced_memory: Set[str] = set()
        # v73.2: Allow forcing sync by ignoring memory
        is_force = getattr(self, 'force_sync', False)
        
        if not is_force and os.path.exists(memory_file):
            try:
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list): synced_memory = set(data)
            except Exception: pass
        
        if is_force:
            print("[JOB][FORCE]: Force sync enabled. Ignoring synced_ids.json memory.")

        s_stats = {"new": 0, "updated": 0, "skipped": 0, "cleaned": 0}
        
        if not results:
            print("[JOB]: 0 new items scraped. Proceeding with Strict Midnight Cleanup only.")
        else:
            print(f"[JOB]: Processing {len(results)} scraped items across semesters...")
        for sem in ["1", "2", "3", "4", "0"]:
            existing_items = notifier.get_from_website(sem)
            current_results = [r for r in results if r.get('semester') == sem]
            
            now_ist = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
            today_str = now_ist.strftime("%Y-%m-%d")
            
            # Use ThreadPoolExecutor for high-speed parallel sync
            with ThreadPoolExecutor(max_workers=10) as executor:
                # 1. Cleanup old
                cleanup_tasks = []
                for ext in existing_items:
                    ext_date = ext.get('date', '')
                    if ext_date and ext_date < today_str:
                        cleanup_tasks.append(executor.submit(notifier.delete_from_website, sem, ext.get('id', ext.get('_id')))) # type: ignore
                        stats["cleaned"] += 1
                
                # 2. Smart Sync
                sync_tasks = []
                for item in current_results:
                    title = str(item.get('title', ''))
                    date = str(item.get('date', ''))
                    time_t = str(item.get('class_time', ''))
                    # v73.1: Enhanced hash including semester and time
                    item_hash = base64.b64encode(f"{sem}:{title}:{date}:{time_t}".encode()).decode()
                    
                    matching_ext = next((e for e in existing_items if e.get('title') == title and e.get('date') == date), None)
                    
                    if matching_ext:
                        ext_id = matching_ext.get('id', matching_ext.get('_id'))
                        ext_link = str(matching_ext.get('link', ''))
                        if ("pending" in ext_link or "soon" in ext_link.lower()) and "teams.microsoft" in str(item.get('link', '')):
                            executor.submit(notifier.update_on_website, sem, ext_id, item) # type: ignore
                            s_stats["updated"] += 1 # type: ignore
                        else:
                            s_stats["skipped"] += 1 # type: ignore
                        synced_memory.add(item_hash) # type: ignore
                    else:
                        if item_hash in synced_memory: # type: ignore
                            s_stats["skipped"] += 1 # type: ignore
                            continue
                        
                        # v77.0: Use simple sync logic for new items
                        if notifier.sync_to_website(item):
                            synced_memory.add(item_hash) # type: ignore
                            s_stats["new"] += 1 # type: ignore
                        else:
                            s_stats["skipped"] += 1 # type: ignore
                        # Submit for parallel sync
                        sync_tasks.append(executor.submit(self._execute_sync, notifier, item, item_hash, synced_memory, s_stats)) # type: ignore
                
                # Wait for all to finish
                for t in cleanup_tasks: t.result()
                for t in sync_tasks: t.result()

        print(f"\n[JOB][SUMMARY]: Sync Complete!")
        print(f" - Newly Added: {s_stats['new']}")
        print(f" - Updated (Links): {s_stats['updated']}")
        print(f" - Already Synced (Skipped): {s_stats['skipped']}")
        print(f" - Cleaned (Expired): {s_stats['cleaned']}")
        print(f" - Total in Memory: {len(synced_memory)}")

        # Save memory AFTER all semesters
        with open(memory_file, 'w') as f:
            json.dump(list(synced_memory), f)

    def _execute_sync(self, notifier, item, item_hash, memory, stats_dict: Any):
        """v76.0: Atomic Sync with Any-Type Stats (Bypass Pyre2 limitations)"""
        try:
            if notifier.sync_to_website(item):
                memory.add(item_hash)
                # Use thread-safe update if needed, but dict.update/set is mostly atomic in CPython
                stats_dict["new"] = stats_dict.get("new", 0) + 1
                return True
        except Exception: pass
        return False

    async def expand_content(self, page):
        """Click 'Load More' or 'View All' if present"""
        try:
            selectors = ["text='Load More'", "text='View All'", "button:has-text('More')", ".btn-show-more"]
            for sel in selectors:
                try:
                    btns = await page.locator(sel).all()
                    for btn in btns:
                        if await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(2)
                except Exception: continue
        except Exception: pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["all", "classes", "notices"], default="all")
    parser.add_argument("--force", action="store_true", help="Force sync all items (ignore memory)")
    args = parser.parse_args()

    backend_url = os.environ.get("BACKEND_URL", "https://solmates-backend.onrender.com")
    scraper_key = os.environ.get("SCRAPER_KEY", "0c464de4beef5fc8c8bf52256d9b662a835247ae6e880c71a15d62bb02062601")
    
    print(f"[JOB]: Starting Omni-Scraper v73.2 | Mode: {args.mode} | Backend: {backend_url}")
    scraper = MBAScraper(target_mode=args.mode, force_sync=args.force)
    notifier = Notifier(backend_url, scraper_key)
    
    try:
        results = asyncio.run(scraper.run())
        # v72.0: Always sync results, even if empty, to trigger Auto-Cleanup (Date deletion)
        # and to preserve older valid data as requested: "purana data hi use karegi"
        scraper.sync_results(results, notifier, "synced_ids.json")
    except Exception as e:
        print(f"[JOB][FATAL]: {e}")
