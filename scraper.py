from __future__ import annotations
import asyncio
import datetime
import re
import random
import os
import json
import base64
import sys
import time
import argparse
import subprocess as _subprocess
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    pass

# ─────────────────────────────────────────────
# IMPORTS — All graceful fallbacks
# ─────────────────────────────────────────────
try:
    from playwright.async_api import async_playwright, Page, BrowserContext  # type: ignore
    from playwright_stealth import stealth_async  # type: ignore
except ImportError:
    pass

try:
    from patchright.async_api import async_playwright as patchright_playwright  # type: ignore
except ImportError:
    pass

try:
    from notifier import Notifier  # type: ignore
except ImportError:
    pass

try:
    import requests
except ImportError:
    pass

try:
    from curl_cffi import requests as cffi_requests  # type: ignore
except ImportError:
    pass

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:
    pass

try:
    import dateutil.parser as dparser  # type: ignore
except ImportError:
    pass

try:
    import httpx  # type: ignore
except ImportError:
    pass

try:
    import cloudscraper as cloudscraper_lib  # type: ignore
except ImportError:
    pass

try:
    import tls_client as tls_client_lib  # type: ignore
except ImportError:
    pass

try:
    import nodriver as uc_nodriver  # type: ignore
except ImportError:
    pass

try:
    from camoufox.async_api import AsyncCamoufox  # type: ignore
except ImportError:
    pass

try:
    from seleniumbase import Driver as SBDriver  # type: ignore
except ImportError:
    pass

try:
    import undetected_chromedriver as uc_chrome  # type: ignore
except ImportError:
    pass

try:
    from DrissionPage import ChromiumPage, ChromiumOptions  # type: ignore
except ImportError:
    pass

try:
    from botasaurus.request import request as botasaurus_request, AntiDetectRequests  # type: ignore
except ImportError:
    pass

try:
    from pydoll.browser.chrome import Chrome as PydollChrome  # type: ignore
except ImportError:
    pass

try:
    from scrapling import StealthyFetcher, PlayWrightFetcher  # type: ignore
except ImportError:
    pass

try:
    import seleniumwire.undetected_chromedriver as swire_uc  # type: ignore
except ImportError:
    pass

try:
    import pychrome as pychrome_lib  # type: ignore
except ImportError:
    pass

try:
    from fp.fp import FreeProxy  # type: ignore
except ImportError:
    pass

try:
    import proxybroker as pb_lib  # type: ignore
except ImportError:
    pass


# ─────────────────────────────────────────────
# HUMAN BOT — Full behavior simulation
# ─────────────────────────────────────────────
class HumanBot:
    def __init__(self, page: Any):
        self.page = page

    async def bezier_move(self, tx: int, ty: int):
        try:
            vp = self.page.viewport_size or {"width": 1366, "height": 768}
            sx, sy = random.randint(0, vp["width"]), random.randint(0, vp["height"])
            cp1x = sx + random.randint(-200, 200)
            cp1y = sy + random.randint(-200, 200)
            cp2x = tx + random.randint(-100, 100)
            cp2y = ty + random.randint(-100, 100)
            steps = random.randint(20, 40)
            for i in range(steps + 1):
                t = i / steps
                x = (1-t)**3*sx + 3*(1-t)**2*t*cp1x + 3*(1-t)*t**2*cp2x + t**3*tx
                y = (1-t)**3*sy + 3*(1-t)**2*t*cp1y + 3*(1-t)*t**2*cp2y + t**3*ty
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.005, 0.015))
        except Exception:
            pass

    async def click(self, selector: str):
        try:
            el = self.page.locator(selector).first
            box = await el.bounding_box()
            if box:
                tx = box["x"] + box["width"] * random.uniform(0.3, 0.7)
                ty = box["y"] + box["height"] * random.uniform(0.3, 0.7)
                await self.bezier_move(int(tx), int(ty))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await self.page.mouse.down()
                await asyncio.sleep(random.uniform(0.05, 0.12))
                await self.page.mouse.up()
                await asyncio.sleep(random.uniform(0.3, 0.8))
        except Exception:
            try:
                await self.page.locator(selector).first.click()
            except Exception:
                pass

    async def scroll(self, amount: int = 500):
        steps = random.randint(3, 8)
        for _ in range(steps):
            await self.page.mouse.wheel(0, amount // steps + random.randint(-30, 30))
            await asyncio.sleep(random.uniform(0.08, 0.25))
            if random.random() < 0.1:
                await asyncio.sleep(random.uniform(0.5, 1.5))

    async def read(self, duration: float = 5.0):
        end = time.time() + duration
        while time.time() < end:
            action = random.choices(["scroll", "move", "pause"], weights=[0.4, 0.3, 0.3])[0]
            if action == "scroll":
                await self.scroll(random.randint(100, 400))
            elif action == "move":
                vp = self.page.viewport_size or {"width": 1366, "height": 768}
                await self.bezier_move(
                    random.randint(50, vp["width"] - 50),
                    random.randint(50, vp["height"] - 50)
                )
            else:
                await asyncio.sleep(random.uniform(0.5, 2.0))

    async def random_type(self, text: str):
        """Human-like typing with variable speed and occasional typos"""
        for char in text:
            if random.random() < 0.04:
                wrong = random.choice("abcdefghijklmnopqrstuvwxyz")
                await self.page.keyboard.type(wrong)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.05, 0.15))
            await self.page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.04, 0.22))
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.3, 1.2))

    async def tab_switch_simulation(self):
        """Simulate tab switching (visibilitychange event)"""
        try:
            await self.page.evaluate("""() => {
                Object.defineProperty(document, 'hidden', { get: () => true, configurable: true });
                document.dispatchEvent(new Event('visibilitychange'));
            }""")
            await asyncio.sleep(random.uniform(1.5, 4.0))
            await self.page.evaluate("""() => {
                Object.defineProperty(document, 'hidden', { get: () => false, configurable: true });
                document.dispatchEvent(new Event('visibilitychange'));
                window.dispatchEvent(new Event('focus'));
            }""")
            await asyncio.sleep(random.uniform(0.5, 1.5))
        except Exception:
            pass

    async def back_button_behavior(self):
        """Simulate browser back + forward"""
        try:
            await self.page.go_back(wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(random.uniform(1.0, 2.5))
            await self.page.go_forward(wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(random.uniform(1.0, 2.0))
        except Exception:
            pass

    async def copy_paste_simulation(self):
        """Simulate Ctrl+A, Ctrl+C"""
        try:
            vp = self.page.viewport_size or {"width": 1366, "height": 768}
            await self.page.mouse.click(
                random.randint(100, vp["width"] - 100),
                random.randint(200, vp["height"] - 100)
            )
            await asyncio.sleep(random.uniform(0.2, 0.5))
            if random.random() < 0.5:
                await self.page.keyboard.down("Control")
                await self.page.keyboard.press("a")
                await self.page.keyboard.up("Control")
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await self.page.keyboard.down("Control")
                await self.page.keyboard.press("c")
                await self.page.keyboard.up("Control")
            await asyncio.sleep(random.uniform(0.3, 0.8))
        except Exception:
            pass

    async def right_click_simulation(self):
        """Simulate right-click + Escape"""
        try:
            vp = self.page.viewport_size or {"width": 1366, "height": 768}
            tx = random.randint(200, vp["width"] - 200)
            ty = random.randint(200, vp["height"] - 200)
            await self.bezier_move(tx, ty)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await self.page.mouse.click(tx, ty, button="right")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(random.uniform(0.2, 0.5))
        except Exception:
            pass

    async def full_human_session(self, duration: float = 10.0):
        """Mix all behaviors for realistic session"""
        end = time.time() + duration
        behaviors = [
            (self.scroll, 0.35),
            (self.read, 0.25),
            (self.tab_switch_simulation, 0.1),
            (self.right_click_simulation, 0.1),
            (self.copy_paste_simulation, 0.1),
        ]
        fns = [b[0] for b in behaviors]
        wts = [b[1] for b in behaviors]
        while time.time() < end:
            fn = random.choices(fns, weights=wts)[0]
            try:
                if fn == self.scroll:
                    await self.scroll(random.randint(100, 500))
                elif fn == self.read:
                    await self.read(random.uniform(1, 3))
                else:
                    await fn()
            except Exception:
                pass
            await asyncio.sleep(random.uniform(0.3, 1.5))

    @staticmethod
    def js_mask_script() -> str:
        return """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.chrome = { runtime: {}, loadTimes: () => {}, csi: () => {}, app: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en-US', 'en', 'hi'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
        Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
        Object.defineProperty(navigator, 'connection', {
            get: () => ({ effectiveType: '4g', rtt: 50, downlink: 10, saveData: false })
        });
        const getParam = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(p) {
            if (p === 37445) return 'NVIDIA Corporation';
            if (p === 37446) return 'NVIDIA GeForce RTX 3080';
            return getParam.apply(this, arguments);
        };
        const origCtx = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type) {
            const ctx = origCtx.apply(this, arguments);
            if (type === '2d' && ctx) {
                const orig = ctx.getImageData;
                ctx.getImageData = function() {
                    const img = orig.apply(this, arguments);
                    img.data[0] = img.data[0] ^ 1;
                    return img;
                };
            }
            return ctx;
        };
        if (navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true, chargingTime: 0, dischargingTime: Infinity, level: 0.89,
                addEventListener: () => {}, removeEventListener: () => {}
            });
        }
        Object.defineProperty(screen, 'width', { get: () => 1366 });
        Object.defineProperty(screen, 'height', { get: () => 768 });
        Object.defineProperty(document, 'hidden', { get: () => false });
        Object.defineProperty(document, 'visibilityState', { get: () => 'visible' });
        const origPerms = window.navigator.permissions.query;
        window.navigator.permissions.query = (p) => p.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : origPerms(p);
        """


# ─────────────────────────────────────────────
# MAIN SCRAPER CLASS — v100.0 OMNI-CRAWLER
# ─────────────────────────────────────────────
class MBAScraper:
    def __init__(self, target_mode: str = "all", force_sync: bool = False):
        self.target_mode = target_mode
        self.force_sync = force_sync
        self.base_url = "https://sol.du.ac.in"
        self.keywords: List[str] = ['MBA', 'Master of Business Administration']
        self.visited: Set[str] = set()
        self.notices: List[Dict[str, Any]] = []
        self.discovery_queue: List[str] = [
            "https://sol.du.ac.in/home.php",
            "https://web.sol.du.ac.in/home",
            "https://sol.du.ac.in/all-notices.php",
            "https://web.sol.du.ac.in/info/online-class-schedule"
        ]
        self.class_schedule_url = "https://web.sol.du.ac.in/my/team_schedules/vcs.php"
        self.parent_url = "https://web.sol.du.ac.in/info/online-class-schedule"
        self.current_url = ""
        self.current_year = datetime.datetime.now().year

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        ]
        self.mobile_agents = [
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        ]
        self.user_agent = random.choice(self.user_agents)

        self.keys: Dict[str, str] = {
            "SCRAPER_API": os.environ.get("SCRAPER_API_KEY") or os.environ.get("SCRAPERAPI_KEY", ""),
            "WSAI": os.environ.get("WEBSCRAPING_AI_KEY", ""),
            "ANT": os.environ.get("SCRAPER_ANT_KEY", ""),
            "CF_WORKER": os.environ.get("CF_WORKER_URL", ""),
            "TOR": os.environ.get("TOR_PROXY", ""),
            "SOL_COOKIES": os.environ.get("SOL_COOKIES", ""),
            "NETLIFY": os.environ.get("NETLIFY_PROXY_URL", ""),
            "VERCEL": os.environ.get("VERCEL_PROXY_URL", ""),
            "I2P": os.environ.get("I2P_PROXY", ""),
        }
        for k, v in self.keys.items():
            if v:
                print(f"[OMNI][KEY]: {k} ✅ present")

    def _iframe_headers(self, ua: str = None) -> dict:
        return {
            "User-Agent": ua or self.user_agent,
            "Referer": self.parent_url,
            "sec-fetch-dest": "iframe",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
            "upgrade-insecure-requests": "1",
        }

    # ═══════════════════════════════════════════
    # M01: curl_cffi — TLS fingerprint rotation
    # ═══════════════════════════════════════════
    async def m01_cffi(self, url: str) -> Optional[str]:
        print("[M01][CFFI]: TLS fingerprint rotation...")
        for fp in ["chrome124", "chrome120", "chrome116", "firefox122", "edge101"]:
            try:
                session = cffi_requests.Session(impersonate=fp)
                session.get("https://sol.du.ac.in/home.php", timeout=12)
                time.sleep(1)
                session.get("https://web.sol.du.ac.in/home", timeout=12)
                time.sleep(1)
                h = self._iframe_headers() if "vcs.php" in url else {"User-Agent": self.user_agent}
                r = session.get(url, headers=h, timeout=30)
                print(f"[M01][CFFI][{fp}]: {r.status_code}")
                if r.status_code == 200:
                    return r.text
            except Exception as e:
                print(f"[M01][CFFI][{fp}]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M02: tls-client — JA3/JA4 rotation
    # ═══════════════════════════════════════════
    async def m02_tls_client(self, url: str) -> Optional[str]:
        print("[M02][TLS-CLIENT]: JA3/JA4 fingerprint...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                for profile in ["chrome_120", "chrome_117", "firefox_120", "safari_16_0"]:
                    try:
                        session = tls_client_lib.Session(
                            client_identifier=profile,
                            random_tls_extension_order=True
                        )
                        session.get("https://sol.du.ac.in/home.php", timeout_seconds=12)
                        time.sleep(1)
                        r = session.get(url, headers=self._iframe_headers(), timeout_seconds=30)
                        print(f"[M02][TLS-CLIENT][{profile}]: {r.status_code}")
                        if r.status_code == 200:
                            return r.text
                    except Exception as e:
                        print(f"[M02][TLS-CLIENT][{profile}]: {e}")
                return None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M02][TLS-CLIENT]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M03: httpx HTTP/2
    # ═══════════════════════════════════════════
    async def m03_httpx(self, url: str) -> Optional[str]:
        print("[M03][HTTPX-H2]: HTTP/2 fingerprint...")
        try:
            async with httpx.AsyncClient(http2=True, follow_redirects=True, timeout=30) as client:
                await client.get("https://sol.du.ac.in/home.php",
                                 headers={"User-Agent": self.user_agent})
                await asyncio.sleep(1)
                r = await client.get(url, headers=self._iframe_headers())
                print(f"[M03][HTTPX-H2]: {r.status_code}")
                if r.status_code == 200:
                    return r.text
        except Exception as e:
            print(f"[M03][HTTPX-H2]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M04: cloudscraper
    # ═══════════════════════════════════════════
    async def m04_cloudscraper(self, url: str) -> Optional[str]:
        print("[M04][CLOUDSCRAPER]: JS challenge bypass...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                scraper = cloudscraper_lib.create_scraper(
                    browser={"browser": "chrome", "platform": "windows", "mobile": False}
                )
                scraper.get("https://sol.du.ac.in/home.php", timeout=12)
                time.sleep(1)
                r = scraper.get(url, headers=self._iframe_headers(), timeout=30)
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M04][CLOUDSCRAPER]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M05: Manual cookies (SOL_COOKIES env)
    # ═══════════════════════════════════════════
    async def m05_manual_cookies(self, url: str) -> Optional[str]:
        cookie_str = self.keys["SOL_COOKIES"]
        if not cookie_str:
            return None
        print("[M05][COOKIES]: Injected session cookies...")
        try:
            session = cffi_requests.Session(impersonate="chrome124")
            h = self._iframe_headers()
            h["Cookie"] = cookie_str
            r = session.get(url, headers=h, timeout=30)
            print(f"[M05][COOKIES]: {r.status_code}")
            return r.text if r.status_code == 200 else None
        except Exception as e:
            print(f"[M05][COOKIES]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M06: Wayback Machine
    # ═══════════════════════════════════════════
    async def m06_wayback(self, url: str) -> Optional[str]:
        print("[M06][WAYBACK]: archive.org snapshot...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                r = requests.get(
                    f"http://archive.org/wayback/available?url={url}", timeout=10
                ).json()
                snap = r.get("archived_snapshots", {}).get("closest", {}).get("url")
                if snap:
                    return requests.get(snap, timeout=20).text
                return None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M06][WAYBACK]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M07: Wayback CDX Index
    # ═══════════════════════════════════════════
    async def m07_cdx(self, url: str) -> Optional[str]:
        print("[M07][CDX]: Wayback CDX historical index...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                api = "http://web.archive.org/cdx/search/cdx?url=sol.du.ac.in&matchType=domain&filter=mimetype:application/pdf&limit=30&output=json"
                data = requests.get(api, timeout=12).json()
                if data and len(data) > 1:
                    html = "<html><body>"
                    for e in data[1:]:
                        html += f'<a href="{e[2]}">{e[2]}</a> '
                    return html + "</body></html>"
                return None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M07][CDX]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M08: Google Cache
    # ═══════════════════════════════════════════
    async def m08_google_cache(self, url: str) -> Optional[str]:
        print("[M08][GCACHE]: Google Cache...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                r = requests.get(
                    f"http://webcache.googleusercontent.com/search?q=cache:{url}",
                    headers={"User-Agent": self.user_agent}, timeout=12
                )
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M08][GCACHE]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M09: Bing Cache
    # ═══════════════════════════════════════════
    async def m09_bing_cache(self, url: str) -> Optional[str]:
        print("[M09][BING-CACHE]: Bing Cache...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                r = requests.get(
                    f"https://cc.bingj.com/cache.aspx?q={url}&url={url}",
                    headers={"User-Agent": self.user_agent}, timeout=12
                )
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M09][BING-CACHE]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M10: Yandex Cache
    # ═══════════════════════════════════════════
    async def m10_yandex_cache(self, url: str) -> Optional[str]:
        print("[M10][YANDEX-CACHE]: Yandex Cache...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                r = requests.get(
                    f"https://yandex.com/search/?text=cache:{url}",
                    headers={"User-Agent": self.user_agent}, timeout=12
                )
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M10][YANDEX-CACHE]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M11: CommonCrawl
    # ═══════════════════════════════════════════
    async def m11_commoncrawl(self, url: str) -> Optional[str]:
        print("[M11][COMMONCRAWL]: CommonCrawl index...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                import gzip
                api = f"http://index.commoncrawl.org/CC-MAIN-2024-10-index?url={url}&output=json"
                r = requests.get(api, timeout=12)
                if r.status_code == 200:
                    lines = r.text.strip().split("\n")
                    if lines:
                        entry = json.loads(lines[0])
                        filename = entry.get("filename")
                        offset = int(entry.get("offset", 0))
                        length = int(entry.get("length", 0))
                        if filename:
                            s3url = f"https://data.commoncrawl.org/{filename}"
                            resp = requests.get(
                                s3url,
                                headers={"Range": f"bytes={offset}-{offset+length-1}"},
                                timeout=20
                            )
                            try:
                                content = gzip.decompress(resp.content).decode("utf-8", errors="ignore")
                                idx = content.lower().find("<html")
                                return content[idx:] if idx >= 0 else None
                            except Exception:
                                pass
                return None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M11][COMMONCRAWL]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M12: CachedView.nl
    # ═══════════════════════════════════════════
    async def m12_cachedview(self, url: str) -> Optional[str]:
        print("[M12][CACHEDVIEW]: CachedView.nl...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                r = requests.get(
                    f"https://cachedview.nl/cachedPage.php?url={url}",
                    headers={"User-Agent": self.user_agent}, timeout=12
                )
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M12][CACHEDVIEW]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M13: Cloudflare Worker proxy
    # ═══════════════════════════════════════════
    async def m13_cf_worker(self, url: str) -> Optional[str]:
        if not self.keys["CF_WORKER"]:
            return None
        print("[M13][CF-WORKER]: Cloudflare Worker proxy...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                r = requests.get(self.keys["CF_WORKER"], params={"url": url}, timeout=40)
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M13][CF-WORKER]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M14: Vercel Edge proxy
    # ═══════════════════════════════════════════
    async def m14_vercel(self, url: str) -> Optional[str]:
        if not self.keys["VERCEL"]:
            return None
        print("[M14][VERCEL]: Vercel Edge proxy...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                r = requests.get(self.keys["VERCEL"], params={"url": url}, timeout=40)
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M14][VERCEL]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M15: Netlify Functions proxy
    # ═══════════════════════════════════════════
    async def m15_netlify(self, url: str) -> Optional[str]:
        if not self.keys["NETLIFY"]:
            return None
        print("[M15][NETLIFY]: Netlify proxy...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                r = requests.get(self.keys["NETLIFY"], params={"url": url}, timeout=40)
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M15][NETLIFY]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M16: Tor proxy
    # ═══════════════════════════════════════════
    async def m16_tor(self, url: str) -> Optional[str]:
        if not self.keys["TOR"]:
            return None
        print(f"[M16][TOR]: Tor proxy {self.keys['TOR']}...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                proxies = {"http": self.keys["TOR"], "https": self.keys["TOR"]}
                s = requests.Session()
                s.get("https://sol.du.ac.in/home.php", proxies=proxies, timeout=25)
                r = s.get(url, headers=self._iframe_headers(), proxies=proxies, timeout=40)
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M16][TOR]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M17: I2P outproxy
    # ═══════════════════════════════════════════
    async def m17_i2p(self, url: str) -> Optional[str]:
        i2p = self.keys.get("I2P", "http://127.0.0.1:4444")
        print(f"[M17][I2P]: I2P outproxy...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                proxies = {"http": i2p, "https": i2p}
                r = requests.get(url, headers=self._iframe_headers(), proxies=proxies, timeout=50)
                return r.text if r.status_code == 200 else None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M17][I2P]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M18: FreeProxy rotation
    # ═══════════════════════════════════════════
    async def m18_freeproxy(self, url: str) -> Optional[str]:
        print("[M18][FREEPROXY]: Free proxy rotation...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                for _ in range(5):
                    try:
                        proxy_addr = FreeProxy(rand=True, timeout=3).get()
                        if not proxy_addr:
                            continue
                        proxies = {"http": proxy_addr, "https": proxy_addr}
                        s = requests.Session()
                        s.get("https://sol.du.ac.in/home.php",
                              proxies=proxies, timeout=12,
                              headers={"User-Agent": self.user_agent})
                        r = s.get(url, headers=self._iframe_headers(),
                                  proxies=proxies, timeout=20)
                        if r.status_code == 200:
                            return r.text
                    except Exception:
                        continue
                return None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M18][FREEPROXY]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M19: IPv6 rotation
    # ═══════════════════════════════════════════
    async def m19_ipv6(self, url: str) -> Optional[str]:
        print("[M19][IPv6]: IPv6 address rotation...")
        try:
            import socket
            loop = asyncio.get_event_loop()
            def _run():
                orig = socket.getaddrinfo
                def ipv6_only(host, port, family=0, type=0, proto=0, flags=0):
                    return orig(host, port, socket.AF_INET6, type, proto, flags)
                socket.getaddrinfo = ipv6_only
                try:
                    session = cffi_requests.Session(impersonate="chrome124")
                    session.get("https://sol.du.ac.in/home.php", timeout=12)
                    r = session.get(url, headers=self._iframe_headers(), timeout=25)
                    return r.text if r.status_code == 200 else None
                finally:
                    socket.getaddrinfo = orig
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M19][IPv6]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M20: DNS-over-HTTPS
    # ═══════════════════════════════════════════
    async def m20_doh(self, url: str) -> Optional[str]:
        print("[M20][DoH]: DNS-over-HTTPS resolution...")
        try:
            loop = asyncio.get_event_loop()
            def _resolve():
                r = requests.get(
                    "https://cloudflare-dns.com/dns-query?name=web.sol.du.ac.in&type=A",
                    headers={"Accept": "application/dns-json"}, timeout=8
                )
                if r.status_code == 200:
                    ans = r.json().get("Answer", [])
                    return ans[0].get("data") if ans else None
                return None
            ip = await loop.run_in_executor(None, _resolve)
            if ip:
                def _run(resolved_ip):
                    import warnings
                    warnings.filterwarnings("ignore")
                    session = cffi_requests.Session(impersonate="chrome124")
                    h = {**self._iframe_headers(), "Host": "web.sol.du.ac.in"}
                    target = url.replace("web.sol.du.ac.in", resolved_ip)
                    r = session.get(target, headers=h, verify=False, timeout=25)
                    return r.text if r.status_code == 200 else None
                return await loop.run_in_executor(None, _run, ip)
        except Exception as e:
            print(f"[M20][DoH]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M21: Request timing jitter
    # ═══════════════════════════════════════════
    async def m21_timing_jitter(self, url: str) -> Optional[str]:
        print("[M21][TIMING-JITTER]: Human-paced timing with jitter...")
        try:
            session = cffi_requests.Session(impersonate="chrome124")
            loop = asyncio.get_event_loop()
            sequence = [
                ("https://sol.du.ac.in/home.php", random.uniform(2.5, 5.0)),
                ("https://web.sol.du.ac.in/home", random.uniform(3.0, 6.0)),
                ("https://web.sol.du.ac.in/info/student-support", random.uniform(2.0, 4.0)),
                (self.parent_url, random.uniform(4.0, 8.0)),
            ]
            for seq_url, wait in sequence:
                def _get(u):
                    return session.get(u, headers={"User-Agent": self.user_agent}, timeout=15)
                await loop.run_in_executor(None, _get, seq_url)
                if random.random() < 0.2:
                    await asyncio.sleep(random.uniform(8, 15))
                else:
                    await asyncio.sleep(wait)
            def _final():
                return session.get(url, headers=self._iframe_headers(), timeout=30)
            r = await loop.run_in_executor(None, _final)
            print(f"[M21][TIMING-JITTER]: {r.status_code}")
            return r.text if r.status_code == 200 else None
        except Exception as e:
            print(f"[M21][TIMING-JITTER]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M22: curl-impersonate subprocess
    # ═══════════════════════════════════════════
    async def m22_curl_impersonate(self, url: str) -> Optional[str]:
        print("[M22][CURL-IMPERSONATE]: Rust TLS via curl-impersonate binary...")
        try:
            for binary in ["curl-impersonate-chrome", "curl_chrome116", "curl"]:
                try:
                    cmd = [
                        binary, "--silent", "--location",
                        "-H", f"Referer: {self.parent_url}",
                        "-H", "sec-fetch-dest: iframe",
                        "-H", "sec-fetch-mode: navigate",
                        "-H", f"User-Agent: {self.user_agent}",
                        "--max-time", "30", url
                    ]
                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=40)
                    html = stdout.decode("utf-8", errors="ignore")
                    if html and self._is_valid(html):
                        return html
                except FileNotFoundError:
                    continue
        except Exception as e:
            print(f"[M22][CURL-IMPERSONATE]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M23: ScraperAPI
    # ═══════════════════════════════════════════
    async def m23_scraperapi(self, url: str) -> Optional[str]:
        if not self.keys["SCRAPER_API"]:
            return None
        print("[M23][SCRAPERAPI]: ScraperAPI residential proxy...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                api = f"http://api.scraperapi.com?api_key={self.keys['SCRAPER_API']}&url={url}&render_js=true"
                return requests.get(api, timeout=60).text
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M23][SCRAPERAPI]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M24: ScraperAnt (10k free/mo)
    # ═══════════════════════════════════════════
    async def m24_scraperант(self, url: str) -> Optional[str]:
        if not self.keys["ANT"]:
            return None
        print("[M24][SCRAPERАNT]: ScraperAnt API...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                api = f"https://api.scraperant.com/v2/general?url={url}&x-api-key={self.keys['ANT']}&browser=true"
                return requests.get(api, timeout=60).text
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M24][SCRAPERАNT]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M25: WebScraping.ai (1k free/mo)
    # ═══════════════════════════════════════════
    async def m25_wsai(self, url: str) -> Optional[str]:
        if not self.keys["WSAI"]:
            return None
        print("[M25][WSAI]: WebScraping.ai...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                api = f"https://api.webscraping.ai/html?url={url}&api_key={self.keys['WSAI']}&proxy=residential&render=true"
                return requests.get(api, timeout=60).text
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M25][WSAI]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M26: Playwright Ghost Fetch
    # ═══════════════════════════════════════════
    async def m26_pw_ghost(self, url: str, context: Any) -> Optional[str]:
        print("[M26][PW-GHOST]: Playwright context iframe ghost fetch...")
        try:
            page = await context.new_page()
            await context.add_init_script(HumanBot.js_mask_script())
            bot = HumanBot(page)
            await page.goto(self.parent_url, wait_until="networkidle", timeout=60000)
            await bot.read(random.uniform(4, 7))
            response = await context.request.get(url, headers={
                "referer": self.parent_url,
                "sec-fetch-dest": "iframe",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
            })
            await page.close()
            print(f"[M26][PW-GHOST]: {response.status}")
            if response.ok:
                return await response.text()
        except Exception as e:
            print(f"[M26][PW-GHOST]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M27: Playwright Full Human Bot
    # ═══════════════════════════════════════════
    async def m27_pw_human(self, url: str, context: Any) -> Optional[str]:
        print("[M27][PW-HUMAN]: Full Playwright human bot...")
        try:
            page = await context.new_page()
            bot = HumanBot(page)
            await page.goto("https://sol.du.ac.in/home.php",
                            wait_until="domcontentloaded", timeout=60000)
            await bot.read(random.uniform(3, 5))
            await page.goto("https://web.sol.du.ac.in/home",
                            wait_until="domcontentloaded", timeout=60000)
            await bot.read(random.uniform(3, 5))
            try:
                await bot.click("text='Student Support'")
                await asyncio.sleep(random.uniform(2, 4))
            except Exception:
                await page.goto("https://web.sol.du.ac.in/info/student-support",
                                wait_until="domcontentloaded", timeout=60000)
            await bot.read(random.uniform(2, 4))
            link_sel = "a:has-text('Online Class Schedule')"
            try:
                await page.wait_for_selector(link_sel, timeout=12000)
                async with context.expect_page(timeout=25000) as new_pg:
                    await bot.click(link_sel)
                target_page = await new_pg.value
            except Exception:
                await page.goto(self.parent_url, wait_until="networkidle", timeout=60000)
                target_page = page
            await target_page.wait_for_load_state("networkidle", timeout=60000)
            target_bot = HumanBot(target_page)
            await target_bot.full_human_session(duration=random.uniform(10, 15))
            # Try ghost fetch from new page's context
            try:
                response = await context.request.get(url, headers={
                    "referer": self.parent_url,
                    "sec-fetch-dest": "iframe",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "same-origin",
                })
                print(f"[M27][PW-HUMAN][GHOST]: {response.status}")
                if response.ok:
                    html = await response.text()
                    await page.close()
                    try:
                        await target_page.close()
                    except Exception:
                        pass
                    return html
            except Exception:
                pass
            # Fallback: extract from frames
            html = await self._extract_frames_html(target_page)
            await page.close()
            try:
                await target_page.close()
            except Exception:
                pass
            return html
        except Exception as e:
            print(f"[M27][PW-HUMAN]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M28: Patchright
    # ═══════════════════════════════════════════
    async def m28_patchright(self, url: str) -> Optional[str]:
        print("[M28][PATCHRIGHT]: Source-level CDP patch...")
        try:
            async with patchright_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1366, "height": 768},
                    locale="en-IN", timezone_id="Asia/Kolkata"
                )
                await context.add_init_script(HumanBot.js_mask_script())
                page = await context.new_page()
                bot = HumanBot(page)
                await page.goto("https://sol.du.ac.in/home.php",
                                wait_until="domcontentloaded", timeout=60000)
                await bot.read(3)
                await page.goto(self.parent_url, wait_until="networkidle", timeout=60000)
                await bot.full_human_session(random.uniform(5, 8))
                response = await context.request.get(url, headers={
                    "referer": self.parent_url,
                    "sec-fetch-dest": "iframe",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "same-origin",
                })
                await browser.close()
                print(f"[M28][PATCHRIGHT]: {response.status}")
                if response.ok:
                    return await response.text()
        except Exception as e:
            print(f"[M28][PATCHRIGHT]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M29: Nodriver
    # ═══════════════════════════════════════════
    async def m29_nodriver(self, url: str) -> Optional[str]:
        print("[M29][NODRIVER]: Direct CDP, no WebDriver...")
        try:
            browser = await uc_nodriver.start(
                headless=True,
                browser_args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = await browser.get("https://sol.du.ac.in/home.php")
            await asyncio.sleep(random.uniform(3, 5))
            page = await browser.get(self.parent_url)
            await asyncio.sleep(random.uniform(8, 12))
            html = await page.get_content()
            print(f"[M29][NODRIVER]: Got {len(html)} bytes")
            await browser.stop()
            return html if html and self._is_valid(html) else None
        except Exception as e:
            print(f"[M29][NODRIVER]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M30: Camoufox (Firefox C++)
    # ═══════════════════════════════════════════
    async def m30_camoufox(self, url: str) -> Optional[str]:
        print("[M30][CAMOUFOX]: Firefox C++ fingerprint...")
        try:
            async with AsyncCamoufox(headless=True, geoip=True) as browser:
                page = await browser.new_page()
                await page.goto("https://sol.du.ac.in/home.php",
                                wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(3, 5))
                await page.goto(self.parent_url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(random.uniform(5, 8))
                try:
                    response = await page.context.request.get(url, headers={
                        "referer": self.parent_url,
                        "sec-fetch-dest": "iframe",
                        "sec-fetch-mode": "navigate",
                        "sec-fetch-site": "same-origin",
                    })
                    print(f"[M30][CAMOUFOX]: {response.status}")
                    if response.ok:
                        return await response.text()
                except Exception:
                    pass
                return await self._extract_frames_html(page)
        except Exception as e:
            print(f"[M30][CAMOUFOX]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M31: SeleniumBase UC Mode
    # ═══════════════════════════════════════════
    async def m31_seleniumbase(self, url: str) -> Optional[str]:
        print("[M31][SELENIUMBASE-UC]: 89% AWS WAF bypass rate...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                driver = SBDriver(uc=True, headless=True, no_sandbox=True)
                try:
                    driver.uc_open_with_reconnect("https://sol.du.ac.in/home.php", reconnect_time=3)
                    time.sleep(random.uniform(2, 4))
                    driver.uc_open_with_reconnect(self.parent_url, reconnect_time=4)
                    time.sleep(random.uniform(6, 10))
                    return driver.get_page_source()
                finally:
                    driver.quit()
            html = await loop.run_in_executor(None, _run)
            print(f"[M31][SELENIUMBASE-UC]: {len(html) if html else 0} bytes")
            return html if html and self._is_valid(html) else None
        except Exception as e:
            print(f"[M31][SELENIUMBASE-UC]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M32: undetected-chromedriver
    # ═══════════════════════════════════════════
    async def m32_ucd(self, url: str) -> Optional[str]:
        print("[M32][UCD]: undetected-chromedriver...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                opts = uc_chrome.ChromeOptions()
                opts.add_argument("--no-sandbox")
                opts.add_argument("--disable-dev-shm-usage")
                driver = uc_chrome.Chrome(options=opts, headless=True)
                try:
                    driver.get("https://sol.du.ac.in/home.php")
                    time.sleep(random.uniform(2, 4))
                    driver.get(self.parent_url)
                    time.sleep(random.uniform(6, 10))
                    return driver.page_source
                finally:
                    driver.quit()
            html = await loop.run_in_executor(None, _run)
            return html if html and self._is_valid(html) else None
        except Exception as e:
            print(f"[M32][UCD]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M33: DrissionPage
    # ═══════════════════════════════════════════
    async def m33_drissionpage(self, url: str) -> Optional[str]:
        print("[M33][DRISSIONPAGE]: Hybrid requests+browser...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                opts = ChromiumOptions()
                opts.headless(True)
                opts.set_argument("--no-sandbox")
                opts.set_argument("--disable-dev-shm-usage")
                page = ChromiumPage(opts)
                try:
                    page.get("https://sol.du.ac.in/home.php")
                    time.sleep(random.uniform(2, 4))
                    page.get(self.parent_url)
                    time.sleep(random.uniform(6, 10))
                    return page.html
                finally:
                    page.quit()
            html = await loop.run_in_executor(None, _run)
            return html if html and self._is_valid(html) else None
        except Exception as e:
            print(f"[M33][DRISSIONPAGE]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M34: Pydoll (CDP direct)
    # ═══════════════════════════════════════════
    async def m34_pydoll(self, url: str) -> Optional[str]:
        print("[M34][PYDOLL]: CDP direct, no WebDriver artifacts...")
        try:
            async with PydollChrome(options={
                "args": ["--no-sandbox", "--disable-dev-shm-usage"],
                "headless": True
            }) as browser:
                tab = await browser.start()
                await tab.go_to("https://sol.du.ac.in/home.php")
                await asyncio.sleep(random.uniform(2, 4))
                await tab.go_to(self.parent_url)
                await asyncio.sleep(random.uniform(6, 10))
                el = await tab.get_element("html")
                html = str(el) if el else ""
                return html if html and self._is_valid(html) else None
        except Exception as e:
            print(f"[M34][PYDOLL]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M35: Scrapling
    # ═══════════════════════════════════════════
    async def m35_scrapling(self, url: str) -> Optional[str]:
        print("[M35][SCRAPLING]: Adaptive stealth fetcher...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                for FetcherClass in [StealthyFetcher, PlayWrightFetcher]:
                    try:
                        fetcher = FetcherClass()
                        resp = fetcher.fetch(self.parent_url)
                        if resp and resp.status == 200:
                            return resp.content
                    except Exception:
                        continue
                return None
            html = await loop.run_in_executor(None, _run)
            return html if html and self._is_valid(html) else None
        except Exception as e:
            print(f"[M35][SCRAPLING]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M36: Botasaurus
    # ═══════════════════════════════════════════
    async def m36_botasaurus(self, url: str) -> Optional[str]:
        print("[M36][BOTASAURUS]: Human mouse + Google referer trick...")
        try:
            loop = asyncio.get_event_loop()
            parent = self.parent_url
            def _run():
                @botasaurus_request
                def fetch(request: AntiDetectRequests, data):
                    return request.get(parent, timeout=30).text
                results = fetch()
                return results[0] if results else None
            html = await loop.run_in_executor(None, _run)
            return html if html and self._is_valid(html) else None
        except Exception as e:
            print(f"[M36][BOTASAURUS]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M37: Selenium Wire
    # ═══════════════════════════════════════════
    async def m37_selenium_wire(self, url: str) -> Optional[str]:
        print("[M37][SELENIUM-WIRE]: Request interception + replay...")
        try:
            loop = asyncio.get_event_loop()
            parent = self.parent_url
            def _run():
                opts = swire_uc.ChromeOptions()
                opts.add_argument("--no-sandbox")
                opts.add_argument("--disable-dev-shm-usage")
                driver = swire_uc.Chrome(options=opts, headless=True)
                try:
                    driver.get("https://sol.du.ac.in/home.php")
                    time.sleep(random.uniform(2, 4))
                    driver.get(parent)
                    time.sleep(random.uniform(6, 10))
                    # Try to capture vcs.php response from intercepted requests
                    for req in driver.requests:
                        if "vcs.php" in req.url and req.response:
                            return req.response.body.decode("utf-8", errors="ignore")
                    return driver.page_source
                finally:
                    driver.quit()
            html = await loop.run_in_executor(None, _run)
            return html if html and self._is_valid(html) else None
        except Exception as e:
            print(f"[M37][SELENIUM-WIRE]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M38: Puppeteer (Node.js subprocess)
    # ═══════════════════════════════════════════
    async def m38_puppeteer(self, url: str) -> Optional[str]:
        print("[M38][PUPPETEER]: Node.js Puppeteer subprocess...")
        try:
            parent = self.parent_url
            script = f"""
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());
(async () => {{
    const browser = await puppeteer.launch({{
        headless: 'new',
        args: ['--no-sandbox', '--disable-dev-shm-usage']
    }});
    const page = await browser.newPage();
    await page.setUserAgent('{self.user_agent}');
    await page.goto('https://sol.du.ac.in/home.php', {{waitUntil:'domcontentloaded'}});
    await new Promise(r => setTimeout(r, 3000));
    await page.goto('{parent}', {{waitUntil:'networkidle2', timeout:60000}});
    await new Promise(r => setTimeout(r, 8000));
    for (const frame of page.frames()) {{
        if (frame.url().includes('vcs')) {{
            const html = await frame.content();
            process.stdout.write('VCS:' + html);
            break;
        }}
    }}
    const html = await page.content();
    process.stdout.write('MAIN:' + html);
    await browser.close();
}})();
"""
            script_path = "/tmp/_puppeteer_sol.js"
            with open(script_path, "w") as f:
                f.write(script)
            proc = await asyncio.create_subprocess_exec(
                "node", script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=90)
            output = stdout.decode("utf-8", errors="ignore")
            if "VCS:" in output:
                html = output.split("VCS:")[1].split("MAIN:")[0]
                if html and self._is_valid(html):
                    return html
            if "MAIN:" in output:
                return output.split("MAIN:")[1]
        except Exception as e:
            print(f"[M38][PUPPETEER]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M39: pychrome raw CDP
    # ═══════════════════════════════════════════
    async def m39_pychrome(self, url: str) -> Optional[str]:
        print("[M39][PYCHROME]: Raw CDP, no WebDriver...")
        try:
            loop = asyncio.get_event_loop()
            parent = self.parent_url
            ua = self.user_agent
            def _run():
                proc = _subprocess.Popen([
                    "google-chrome", "--headless", "--no-sandbox",
                    "--remote-debugging-port=9223",
                    "--disable-dev-shm-usage",
                    f"--user-agent={ua}"
                ], stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL)
                time.sleep(2)
                try:
                    browser = pychrome_lib.Browser(url="http://127.0.0.1:9223")
                    tab = browser.new_tab()
                    tab.start()
                    tab.Page.enable()
                    tab.Page.navigate(url="https://sol.du.ac.in/home.php")
                    time.sleep(3)
                    tab.Page.navigate(url=parent)
                    time.sleep(8)
                    result = tab.Runtime.evaluate(
                        expression="document.documentElement.outerHTML"
                    )
                    html = result.get("result", {}).get("value", "")
                    tab.stop()
                    browser.close_tab(tab)
                    return html
                finally:
                    proc.terminate()
            html = await loop.run_in_executor(None, _run)
            return html if html and self._is_valid(html) else None
        except Exception as e:
            print(f"[M39][PYCHROME]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M40: CSRF + Cookie harvest
    # ═══════════════════════════════════════════
    async def m40_csrf_cookies(self, url: str, context: Any) -> Optional[str]:
        print("[M40][CSRF-COOKIES]: Extract CSRF + cookies from live session...")
        try:
            page = await context.new_page()
            await page.goto(self.parent_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)
            csrf = await page.evaluate("""() => {
                const m = document.querySelector('meta[name="csrf-token"]');
                if (m) return m.getAttribute('content');
                const i = document.querySelector('input[name="_token"],input[name="csrf_token"]');
                return i ? i.value : null;
            }""")
            cookies = await context.cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            await page.close()
            if cookie_str:
                h = self._iframe_headers()
                h["Cookie"] = cookie_str
                if csrf:
                    h["X-CSRF-Token"] = csrf
                session = cffi_requests.Session(impersonate="chrome124")
                r = session.get(url, headers=h, timeout=30)
                print(f"[M40][CSRF-COOKIES]: {r.status_code}")
                if r.status_code == 200:
                    return r.text
        except Exception as e:
            print(f"[M40][CSRF-COOKIES]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M41: AWS ALB cookie forge
    # ═══════════════════════════════════════════
    async def m41_awsalb_forge(self, url: str) -> Optional[str]:
        print("[M41][AWSALB-FORGE]: Probing for AWSALB cookie on other pages...")
        try:
            loop = asyncio.get_event_loop()
            def _run():
                for probe in [
                    "https://web.sol.du.ac.in/home",
                    "https://web.sol.du.ac.in/info/student-support",
                    "https://web.sol.du.ac.in/info/about",
                ]:
                    try:
                        session = cffi_requests.Session(impersonate="chrome124")
                        session.get(probe, headers={"User-Agent": self.user_agent}, timeout=12)
                        if session.cookies.get("AWSALB"):
                            print(f"[M41][AWSALB-FORGE]: Got AWSALB from {probe}")
                            r = session.get(url, headers=self._iframe_headers(), timeout=25)
                            if r.status_code == 200:
                                return r.text
                    except Exception:
                        continue
                return None
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            print(f"[M41][AWSALB-FORGE]: {e}")
        return None

    # ═══════════════════════════════════════════
    # M42: 3G network emulation (Playwright CDP)
    # ═══════════════════════════════════════════
    async def m42_3g_emulation(self, url: str, context: Any) -> Optional[str]:
        print("[M42][3G-EMUL]: Slow 3G network profile (more human-like timing)...")
        try:
            page = await context.new_page()
            try:
                cdp = await context.new_cdp_session(page)
                await cdp.send("Network.emulateNetworkConditions", {
                    "offline": False, "latency": 400,
                    "downloadThroughput": 1500000 // 8,
                    "uploadThroughput": 750000 // 8,
                    "connectionType": "cellular3g"
                })
            except Exception:
                pass
            bot = HumanBot(page)
            await page.goto("https://sol.du.ac.in/home.php",
                            wait_until="domcontentloaded", timeout=120000)
            await bot.read(random.uniform(3, 5))
            await page.goto(self.parent_url, wait_until="networkidle", timeout=120000)
            await bot.full_human_session(duration=15)
            response = await context.request.get(url, headers={
                "referer": self.parent_url,
                "sec-fetch-dest": "iframe",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin",
            })
            await page.close()
            print(f"[M42][3G-EMUL]: {response.status}")
            if response.ok:
                return await response.text()
        except Exception as e:
            print(f"[M42][3G-EMUL]: {e}")
        return None

    # ═══════════════════════════════════════════
    # LEGACY: fetch_cffi (used by discover_and_crawl)
    # ═══════════════════════════════════════════
    async def fetch_cffi(self, url: str) -> Optional[str]:
        self.current_url = url
        try:
            session = cffi_requests.Session(impersonate="chrome124")
            h = self._iframe_headers() if "vcs.php" in url else {"User-Agent": self.user_agent}
            r = session.get(url, headers=h, timeout=30)
            return r.text if r.status_code == 200 else None
        except Exception:
            return None

    async def fetch_wayback(self, url: str) -> Optional[str]:
        self.current_url = url
        return await self.m06_wayback(url)

    async def fetch_paid(self, url: str, provider: str) -> Optional[str]:
        self.current_url = url
        if provider == "SCRAPER_API":
            return await self.m23_scraperapi(url)
        elif provider == "ANT":
            return await self.m24_scraperант(url)
        elif provider == "WSAI":
            return await self.m25_wsai(url)
        return None

    # ═══════════════════════════════════════════
    # CRAWLER & DISCOVERY
    # ═══════════════════════════════════════════
    async def discover_and_crawl(self, max_pages: int = 50):
        print(f"[CRAWLER]: Discovering MBA content on {self.base_url}...")
        count = 0
        while self.discovery_queue and count < max_pages:
            url = self.discovery_queue.pop(0)
            if url in self.visited:
                continue
            self.visited.add(url)
            count += 1
            print(f"[CRAWLER][{count}/{max_pages}]: Visiting {url}")
            html = await self.fetch_cffi(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = self.base_url + href
                elif not href.startswith("http"):
                    href = self.base_url + "/" + href
                if ("sol.du.ac.in" in href and href not in self.visited
                        and href not in self.discovery_queue):
                    if any(ext in href.lower() for ext in [".pdf", ".php", ".html"]) or "/" in href:
                        self.discovery_queue.append(href)
            self.current_url = url
            parsed = self._parse_html(html)
            for item in parsed:
                if not any(n["link"] == item["link"] for n in self.notices):
                    print(f"  [✔ FOUND]: {item['title']}")
                    self.notices.append(item)

    # ═══════════════════════════════════════════
    # CLASS CHAIN — All 42 methods in order
    # ═══════════════════════════════════════════
    async def run_class_chain(self) -> List[Dict[str, Any]]:
        print("\n[OMNI]: ═══ CLASS SCHEDULE CHAIN — 42 Methods ═══")
        url = self.class_schedule_url
        self.current_url = url

        # ── Fast HTTP methods (no browser) ──
        fast_methods = [
            ("M01-CFFI",           lambda: self.m01_cffi(url)),
            ("M02-TLS-CLIENT",     lambda: self.m02_tls_client(url)),
            ("M03-HTTPX-H2",       lambda: self.m03_httpx(url)),
            ("M04-CLOUDSCRAPER",   lambda: self.m04_cloudscraper(url)),
            ("M05-COOKIES",        lambda: self.m05_manual_cookies(url)),
            ("M06-WAYBACK",        lambda: self.m06_wayback(url)),
            ("M07-CDX",            lambda: self.m07_cdx(url)),
            ("M08-GCACHE",         lambda: self.m08_google_cache(url)),
            ("M09-BING-CACHE",     lambda: self.m09_bing_cache(url)),
            ("M10-YANDEX",         lambda: self.m10_yandex_cache(url)),
            ("M11-COMMONCRAWL",    lambda: self.m11_commoncrawl(url)),
            ("M12-CACHEDVIEW",     lambda: self.m12_cachedview(url)),
            ("M13-CF-WORKER",      lambda: self.m13_cf_worker(url)),
            ("M14-VERCEL",         lambda: self.m14_vercel(url)),
            ("M15-NETLIFY",        lambda: self.m15_netlify(url)),
            ("M16-TOR",            lambda: self.m16_tor(url)),
            ("M17-I2P",            lambda: self.m17_i2p(url)),
            ("M18-FREEPROXY",      lambda: self.m18_freeproxy(url)),
            ("M19-IPv6",           lambda: self.m19_ipv6(url)),
            ("M20-DoH",            lambda: self.m20_doh(url)),
            ("M21-TIMING-JITTER",  lambda: self.m21_timing_jitter(url)),
            ("M22-CURL-IMPERSONATE", lambda: self.m22_curl_impersonate(url)),
            ("M23-SCRAPERAPI",     lambda: self.m23_scraperapi(url)),
            ("M24-SCRAPERАNT",     lambda: self.m24_scraperант(url)),
            ("M25-WSAI",           lambda: self.m25_wsai(url)),
            ("M41-AWSALB-FORGE",   lambda: self.m41_awsalb_forge(url)),
        ]

        for name, fn in fast_methods:
            print(f"\n[CHAIN]: ── {name} ──")
            try:
                html = await fn()
                if html and self._is_valid(html):
                    self.current_url = url
                    res = self._parse_html(html)
                    if res:
                        print(f"[CHAIN]: ✅ {name} SUCCESS — {len(res)} classes!")
                        return res
                    print(f"[CHAIN]: {name} got HTML but no classes parsed")
            except Exception as e:
                print(f"[CHAIN]: {name} crashed — {e}")

        # ── Playwright Chromium ──
        print("\n[CHAIN]: ── Launching Playwright Chromium ──")
        try:
            async with async_playwright() as p:
                is_mobile = random.choice([True, False])
                ua = random.choice(self.mobile_agents if is_mobile else self.user_agents)
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage",
                          "--disable-blink-features=AutomationControlled"]
                )
                context = await browser.new_context(
                    user_agent=ua,
                    viewport={"width": 390, "height": 844} if is_mobile
                    else {"width": 1366, "height": 768},
                    is_mobile=is_mobile, has_touch=is_mobile,
                    locale="en-IN", timezone_id="Asia/Kolkata",
                )
                await context.add_init_script(HumanBot.js_mask_script())

                browser_methods = [
                    ("M26-PW-GHOST",  lambda: self.m26_pw_ghost(url, context)),
                    ("M27-PW-HUMAN",  lambda: self.m27_pw_human(url, context)),
                    ("M40-CSRF",      lambda: self.m40_csrf_cookies(url, context)),
                    ("M42-3G-EMUL",   lambda: self.m42_3g_emulation(url, context)),
                ]
                for name, fn in browser_methods:
                    print(f"\n[CHAIN]: ── {name} ──")
                    try:
                        html = await fn()
                        if html and self._is_valid(html):
                            self.current_url = url
                            res = self._parse_html(html)
                            if res:
                                print(f"[CHAIN]: ✅ {name} SUCCESS — {len(res)} classes!")
                                await browser.close()
                                return res
                    except Exception as e:
                        print(f"[CHAIN]: {name} crashed — {e}")
                await browser.close()
        except Exception as e:
            print(f"[CHAIN]: Chromium launch failed — {e}")

        # ── Specialized browsers ──
        specialized = [
            ("M28-PATCHRIGHT",    lambda: self.m28_patchright(url)),
            ("M29-NODRIVER",      lambda: self.m29_nodriver(url)),
            ("M30-CAMOUFOX",      lambda: self.m30_camoufox(url)),
            ("M31-SELENIUMBASE",  lambda: self.m31_seleniumbase(url)),
            ("M32-UCD",           lambda: self.m32_ucd(url)),
            ("M33-DRISSIONPAGE",  lambda: self.m33_drissionpage(url)),
            ("M34-PYDOLL",        lambda: self.m34_pydoll(url)),
            ("M35-SCRAPLING",     lambda: self.m35_scrapling(url)),
            ("M36-BOTASAURUS",    lambda: self.m36_botasaurus(url)),
            ("M37-SELENIUM-WIRE", lambda: self.m37_selenium_wire(url)),
            ("M38-PUPPETEER",     lambda: self.m38_puppeteer(url)),
            ("M39-PYCHROME",      lambda: self.m39_pychrome(url)),
        ]
        for name, fn in specialized:
            print(f"\n[CHAIN]: ── {name} ──")
            try:
                html = await fn()
                if html and self._is_valid(html):
                    self.current_url = url
                    res = self._parse_html(html)
                    if res:
                        print(f"[CHAIN]: ✅ {name} SUCCESS — {len(res)} classes!")
                        return res
            except Exception as e:
                print(f"[CHAIN]: {name} crashed — {e}")

        print("\n[CHAIN]: ❌ All 42 methods exhausted for class schedule.")
        return []

    # ═══════════════════════════════════════════
    # PARSING
    # ═══════════════════════════════════════════
    def _parse_html(self, html: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        results: List[Dict[str, Any]] = []
        is_home = "home.php" in self.current_url.lower()

        if is_home:
            imp_div = soup.find(id="important-links")
            if imp_div:
                for a in imp_div.find_all("a", href=True):  # type: ignore
                    txt = a.get_text().strip()
                    if txt:
                        abs_link = urljoin(self.current_url, a["href"])
                        results.append({
                            "title": f"MBA Update: {re.sub(r'^\\[.*?\\]\\s*', '', txt).strip()}"[:100],
                            "link": abs_link,
                            "semester": self.extract_semester_logic(txt),
                            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                            "class_time": "", "description": "SOL Announcement"
                        })

        tables = soup.find_all("table")
        is_schedule = "vcs.php" in self.current_url.lower()
        if is_schedule:
            print(f"  [DEBUG]: {len(tables)} tables on schedule page")

        for tidx, table in enumerate(tables):
            rows = table.find_all("tr")
            current_date: Optional[str] = None
            for row in rows:
                txt = row.get_text().lower()
                if "date:" in txt:
                    m = re.search(r"(\d{1,2}[-/]\d{2}[-/]\d{4})", txt)
                    if m:
                        current_date = m.group(1)
                        if is_schedule:
                            print(f"    [DEBUG]: Table {tidx} date: {current_date}")
                        continue
                if not current_date:
                    continue
                cells = row.find_all(["td", "th"])
                if len(cells) < 4:
                    continue
                course = cells[0].get_text(strip=True)
                sem_raw = cells[1].get_text(strip=True)
                subj = cells[2].get_text(strip=True)
                if not any(kw.lower() in course.lower() for kw in self.keywords):
                    continue
                semester = self.extract_semester_logic(sem_raw)
                if semester == "0":
                    semester = self.extract_semester_logic(course)
                if semester == "0":
                    semester = self.extract_semester_logic(subj)
                time_txt = next(
                    (c.get_text(strip=True) for c in cells
                     if re.search(r"\d{1,2}:\d{2}", c.get_text())), ""
                )
                teacher = cells[5].get_text(strip=True) if len(cells) > 5 else "Unknown"
                raw_href = next(
                    (a["href"] for c in reversed(cells)
                     for a in [c.find("a")] if a and a.get("href")),
                    "#pending"
                )
                abs_link = urljoin(self.current_url, raw_href) if raw_href != "#pending" else "#pending"
                results.append({
                    "title": f"[{current_date}] Sem {semester}: {subj}"[:100],
                    "link": abs_link, "semester": semester,
                    "date": self.parse_date(current_date),
                    "class_time": time_txt,
                    "description": f"Live Class: {subj} (Teacher: {teacher})"
                })

        # General MBA links
        seen = {r["link"] for r in results}
        for a in soup.find_all("a", href=True):
            txt = a.get_text().strip()
            if txt and any(kw.lower() in txt.lower() for kw in self.keywords):
                abs_link = urljoin(self.current_url, a["href"])
                if abs_link not in seen:
                    seen.add(abs_link)
                    clean = re.sub(r"^\[.*?\]\s*", "", txt).strip()
                    results.append({
                        "title": f"MBA Update: {clean}"[:100],
                        "link": abs_link,
                        "semester": self.extract_semester_logic(txt),
                        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "class_time": "", "description": "Latest MBA Resource"
                    })

        # Year filter
        filtered, seen_links = [], set()
        for item in results:
            if item["link"] in seen_links:
                continue
            try:
                yr = int(item.get("date", "").split("-")[0])
            except (ValueError, IndexError):
                yr = self.current_year
            if yr == self.current_year:
                filtered.append(item)
                seen_links.add(item["link"])
        return filtered

    async def _extract_frames_html(self, page: Any) -> Optional[str]:
        """Extract raw HTML from page + all frames, return first valid one"""
        for ctx in [page] + list(page.frames):
            try:
                html = await ctx.content()
                if html and self._is_valid(html):
                    return html
            except Exception:
                continue
        return None

    def _parse_raw_tables(self, tables: List[Any]) -> List[Dict[str, Any]]:
        results = []
        for rows in tables:
            current_date = None
            for cells_raw in rows:
                cells = list(cells_raw)
                combined = " ".join(str(c.get("text", "")) for c in cells)
                if "date:" in combined.lower():
                    m = re.search(r"(\d{1,2}[-/]\d{2}[-/]\d{4})", combined)
                    if m:
                        current_date = m.group(1)
                        continue
                if not current_date or len(cells) < 4:
                    continue
                course = str(cells[0].get("text", "")).strip()
                sem_raw = str(cells[1].get("text", "")).strip()
                subj = str(cells[2].get("text", "")).strip()
                if not any(kw.lower() in course.lower() for kw in self.keywords):
                    continue
                semester = self.extract_semester_logic(sem_raw)
                if semester == "0":
                    semester = self.extract_semester_logic(course)
                time_txt = next(
                    (str(c.get("text", "")) for c in cells
                     if re.search(r"\d{1,2}:\d{2}", str(c.get("text", "")))), ""
                )
                href = next(
                    (str(c["href"]) for c in reversed(cells)
                     if c.get("href") and "teams.microsoft" in str(c["href"])),
                    "#pending"
                )
                results.append({
                    "title": f"[{current_date}] MBA Sem {semester}: {subj} ({time_txt})",
                    "link": href, "semester": semester,
                    "date": self.parse_date(current_date),
                    "class_time": time_txt,
                    "description": f"MBA Live Class: {subj} at {time_txt}"
                })
        return results

    async def _extract_frames(self, page: Any) -> List[Dict[str, Any]]:
        all_raw = []
        for ctx in [page] + list(page.frames):
            try:
                data = await ctx.evaluate("""() =>
                    Array.from(document.querySelectorAll('table')).map(t =>
                        Array.from(t.querySelectorAll('tr')).map(tr =>
                            Array.from(tr.querySelectorAll('td,th')).map(c => ({
                                text: c.innerText.trim(),
                                href: (c.querySelector('a') || {}).href || null
                            }))
                        )
                    )
                """)
                if data:
                    all_raw.extend(data)
            except Exception:
                continue
        return self._parse_raw_tables(all_raw)

    def extract_semester_logic(self, text: str) -> str:
        if not text:
            return "0"
        t = text.upper().replace("-", " ").replace(".", " ")
        if "1ST" in t or "FIRST" in t:
            return "1"
        if "2ND" in t or "SECOND" in t:
            return "2"
        if "3RD" in t or "THIRD" in t:
            return "3"
        if "4TH" in t or "FOURTH" in t:
            return "4"
        roman = {"I": "1", "II": "2", "III": "3", "IV": "4"}
        m = re.search(r"(?:SEM(?:ESTER)?|YEAR|YR|PART)\s*(IV|III|II|I|[1-4])\b", t)
        if m:
            return roman.get(m.group(1), m.group(1))
        m = re.search(r"\b([1-4])(?:ST|ND|RD|TH)\b", t)
        if m:
            return m.group(1)
        m = re.search(r"MBA\s*(IV|III|II|I|[1-4])\b", t)
        if m:
            return roman.get(m.group(1), m.group(1))
        m = re.search(r"\b(IV|III|II|I)\b", t)
        if m:
            return roman[m.group(1)]
        m = re.search(r"\b([1-4])\b", t)
        if m:
            return m.group(1)
        return "0"

    def _is_valid(self, html: Any) -> bool:
        return bool(html and "sol" in str(html).lower() and len(str(html)) > 500)

    def parse_date(self, ds: str) -> str:
        for fmt in ["%d-%m-%Y", "%d/%m/%Y"]:
            try:
                return datetime.datetime.strptime(ds.strip(), fmt).strftime("%Y-%m-%d")
            except Exception:
                continue
        return datetime.datetime.now().strftime("%Y-%m-%d")

    # ═══════════════════════════════════════════
    # MASTER RUN
    # ═══════════════════════════════════════════
    async def run(self, days_back: int = 15, mode: str = "all",
                  targets: Optional[List[str]] = None) -> list:
        if mode == "all":
            print("[OMNI]: COMPREHENSIVE scan (Classes + Notices + Discovery)")
            self.notices.extend(await self.run_class_chain())
            await self.discover_and_crawl(max_pages=500)
            print(f"[SUMMARY]: Total MBA items: {len(self.notices)}")

        elif mode == "website":
            print("[OMNI]: WEBSITE & NOTICES scan")
            for url in ["https://sol.du.ac.in/all-notices.php", "https://sol.du.ac.in/home.php"]:
                html = await self.fetch_cffi(url)
                if html:
                    self.current_url = url
                    parsed = self._parse_html(html)
                    for item in parsed:
                        if not any(n["link"] == item["link"] for n in self.notices):
                            print(f"  [✔ FOUND]: {item['title']}")
                            self.notices.append(item)
            await self.discover_and_crawl(max_pages=75)
            print(f"[SUMMARY]: {len(self.notices)} items found")

        elif mode == "classes":
            print("[OMNI]: CLASS SCHEDULE ONLY scan")
            self.notices.extend(await self.run_class_chain())

        return self.notices

    # ═══════════════════════════════════════════
    # SYNC & CLEANUP
    # ═══════════════════════════════════════════
    def sync_results(self, results: list, notifier: Any, memory_file: str):
        synced: Set[str] = set()
        if os.path.exists(memory_file):
            try:
                content = open(memory_file).read().strip()
                if content:
                    synced = set(json.loads(content))
            except Exception:
                pass
        stats = {"new": 0, "skipped": 0}
        for item in results:
            sem = item.get("semester", "0")
            title = item.get("title", "")
            dt = item.get("date", "")
            tm = item.get("class_time", "")
            h = base64.b64encode(f"{sem}:{title}:{dt}:{tm}".encode()).decode()
            if h in synced and not self.force_sync:
                stats["skipped"] += 1
                continue
            print(f"[SYNC]: {item['title'][:60]}")
            if notifier.sync_to_website(item):
                synced.add(h)
                stats["new"] += 1
                print(f"  [✅ OK]")
            else:
                stats["skipped"] += 1
                print(f"  [❌ FAILED]")
            time.sleep(1.5)
        print(f"[SYNC]: New={stats['new']} Skipped={stats['skipped']}")
        with open(memory_file, "w") as f:
            json.dump(list(synced), f)

    def cleanup_old_data(self, notifier: Any):
        print("[CLEANUP]: Auto-cleanup old records...")
        now = datetime.datetime.now()
        thirty_ago = now - datetime.timedelta(days=30)
        for sem in ["0", "1", "2", "3", "4"]:
            items = notifier.get_from_website(sem)
            if not items:
                continue
            deleted = 0
            for item in items:
                item_id = item.get("_id") or item.get("id")
                if not item_id:
                    continue
                try:
                    item_date = datetime.datetime.strptime(
                        item.get("date", ""), "%Y-%m-%d"
                    )
                    to_delete = (
                        (sem == "0" and item_date < thirty_ago) or
                        (sem != "0" and item_date.date() < now.date())
                    )
                    if to_delete and notifier.delete_from_website(sem, item_id):
                        deleted += 1
                except Exception:
                    continue
            if deleted:
                print(f"  [CLEANUP]: Sem {sem} — deleted {deleted} expired items")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    SCRAPER_KEY = os.environ.get("SCRAPER_KEY", "")
    BACKEND_URL = os.environ.get("BACKEND_URL", "https://solmates-backend.onrender.com")

    async def standalone_run():
        mode = "all"
        if "--mode" in sys.argv:
            idx = sys.argv.index("--mode")
            if idx + 1 < len(sys.argv):
                mode = sys.argv[idx + 1]
        force = "--force" in sys.argv

        scraper = MBAScraper(target_mode=mode, force_sync=force)
        results = await scraper.run(mode=mode)
        if results:
            try:
                notifier = Notifier(BACKEND_URL, SCRAPER_KEY)
                scraper.sync_results(results, notifier, "synced_ids.json")
                if mode == "all":
                    scraper.cleanup_old_data(notifier)
                print(f"[OMNI]: Scan ({mode}) complete.")
            except NameError:
                print("[ERROR]: Notifier not found. Sync skipped.")
        else:
            print(f"[OMNI]: No items for mode '{mode}'.")

    asyncio.run(standalone_run())
