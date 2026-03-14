"""
Smart URL Visitor
Reads URLs from load_url.json, visits each website, detects login requirements,
and skips sites that need authentication.

Uses async Playwright so it works both from the main thread (CLI)
and from background threads (Streamlit).
"""

import sys
import os

_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _sub in ("agents", "extractors", "scrapers", "pipeline"):
    sys.path.insert(0, os.path.join(_src, _sub))
sys.path.insert(0, _src)

import json
import asyncio
import os
os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "/opt/render/.cache/ms-playwright")
from typing import List, Dict
from logger import setup_logger
from full_content_extractor import FullContentExtractor

logger = setup_logger(__name__)


class SmartURLVisitor:
    """
    Intelligently visits URLs from load_url.json.
    - Detects login / authentication pages  → skip
    - Detects 403 / paywall pages           → skip
    - Extracts full content from valid pages
    - Stops as soon as target_count items are collected
    """

    def __init__(self, load_url_path: str = "output/load_url.json"):
        self.load_url_path = load_url_path
        self.content_extractor = FullContentExtractor()
        logger.info(f"SmartURLVisitor initialized (reading from: {load_url_path})")

    # ── Detection helpers (sync, called on page objects) ─────────────────────

    @staticmethod
    def _is_login_page(url: str, content: str, password_inputs: int) -> bool:
        login_url_patterns = [
            'login', 'signin', 'sign-in', 'auth', 'authenticate',
            'register', 'signup', 'sign-up', 'account/login'
        ]
        if any(p in url for p in login_url_patterns):
            return True
        if password_inputs > 0:
            return True
        login_keywords = [
            'sign in to continue', 'log in to continue', 'login required',
            'please login', 'authentication required', 'members only',
            'subscription required', 'subscribe to continue'
        ]
        hits = sum(1 for kw in login_keywords if kw in content)
        return hits >= 2

    @staticmethod
    def _is_blocked_page(title: str, content: str) -> tuple:
        blocked_titles = ['403', '401', 'forbidden', 'access denied',
                          'unauthorized', 'not found', '404']
        if any(t in title for t in blocked_titles):
            return True, f"Blocked: {title}"
        paywall_keywords = ['subscribe to continue', 'subscription required',
                            'premium content', 'members only', 'paywall',
                            'paid content', 'unlock this article']
        if any(kw in content for kw in paywall_keywords):
            return True, "Paywall/subscription required"
        return False, ""

    # ── URL loader ────────────────────────────────────────────────────────────

    def load_urls_from_json(self) -> List[Dict]:
        try:
            if not os.path.exists(self.load_url_path):
                logger.error(f"❌ File not found: {self.load_url_path}")
                return []
            with open(self.load_url_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            urls = data.get('urls', [])
            logger.info(f"✅ Loaded {len(urls)} URLs from {self.load_url_path}")
            logger.info(f"🔍 Search query: {data.get('search_query', 'N/A')}")
            return urls
        except Exception as e:
            logger.error(f"❌ Failed to load URLs: {e}")
            return []

    # ── Async core ────────────────────────────────────────────────────────────

    async def _visit_async(
        self,
        url_data: List[Dict],
        content_type: str,
        target_count: int,
        timeout: int
    ) -> List[Dict]:
        from playwright.async_api import async_playwright, TimeoutError as PWTimeout

        all_items = []
        skipped = 0
        failed = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )

            for i, url_info in enumerate(url_data, 1):
                if len(all_items) >= target_count:
                    logger.info(f"🎯 Target of {target_count} items reached — stopping early")
                    break

                url = url_info['url']
                title = url_info.get('title', 'Unknown')
                remaining = target_count - len(all_items)

                logger.info(f"\n{'='*70}")
                logger.info(f"🌐 [{i}/{len(url_data)}] Visiting: {title[:50]}")
                logger.info(f"🔗 URL: {url}")
                logger.info(f"📊 Progress: {len(all_items)}/{target_count} ({remaining} remaining)")
                logger.info(f"{'='*70}")

                try:
                    page = await context.new_page()
                    logger.info("📡 Loading page...")
                    await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
                    await page.wait_for_timeout(2000)

                    page_url   = page.url.lower()
                    page_title = (await page.title()).lower()
                    content    = (await page.content()).lower()
                    pw_inputs  = await page.locator('input[type="password"]').count()

                    # Login check
                    if self._is_login_page(page_url, content, pw_inputs):
                        logger.warning("⏭️  SKIPPED: Login required — moving to next URL")
                        skipped += 1
                        await page.close()
                        continue

                    # Blocked / paywall check
                    is_blocked, reason = self._is_blocked_page(page_title, content)
                    if is_blocked:
                        logger.warning(f"⏭️  SKIPPED: {reason} — moving to next URL")
                        skipped += 1
                        await page.close()
                        continue

                    # Extract
                    logger.info("📄 Extracting content...")
                    html = await page.content()
                    await page.close()

                    item = self.content_extractor.extract_full_content(
                        html=html, url=url, content_type=content_type
                    )

                    if item and item.get('title') and item.get('content'):
                        all_items.append(item)
                        logger.info(f"✅ SUCCESS [{len(all_items)}/{target_count}]: {item['title'][:60]}")
                        logger.info(f"📊 Content: {len(item['content'])} chars")
                    else:
                        logger.warning("⚠️  No usable content — skipping")
                        failed += 1

                except PWTimeout:
                    logger.error("⏱️  TIMEOUT — moving to next URL")
                    failed += 1
                except Exception as e:
                    logger.error(f"❌ ERROR: {str(e)[:120]} — moving to next URL")
                    failed += 1

            await browser.close()

        logger.info("\n" + "="*70)
        logger.info("SMART URL VISITOR - SUMMARY")
        logger.info(f"🎯 Target: {target_count} | ✅ Collected: {len(all_items)} | "
                    f"🔒 Skipped: {skipped} | ❌ Failed: {failed}")
        if len(all_items) < target_count:
            logger.warning(f"⚠️  Only {len(all_items)}/{target_count} items collected")
        logger.info("="*70)

        return all_items

    # ── Public entry point ────────────────────────────────────────────────────

    def visit_and_scrape(
        self,
        content_type: str,
        fields: List[Dict],
        target_count: int = 10,
        timeout: int = 30000
    ) -> List[Dict]:
        """
        Visit URLs from load_url.json and scrape content.
        Works from both the main thread (CLI) and background threads (Streamlit).
        """
        logger.info("\n" + "="*70)
        logger.info("SMART URL VISITOR - STARTING")
        logger.info(f"🎯 Target: {target_count} valid items")
        logger.info("="*70)

        url_data = self.load_urls_from_json()
        if not url_data:
            logger.error("❌ No URLs to visit")
            return []

        # On Windows, SelectorEventLoop can't spawn subprocesses (Playwright needs this).
        # Force ProactorEventLoop which supports subprocess creation on Windows.
        if sys.platform == "win32":
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._visit_async(url_data, content_type, target_count, timeout)
            )
        finally:
            loop.close()
            asyncio.set_event_loop(None)


def main():
    visitor = SmartURLVisitor()
    items = visitor.visit_and_scrape(
        content_type='article',
        fields=['title', 'description', 'content', 'source_url'],
        target_count=5
    )
    print(f"\n✅ Scraped {len(items)} items")
    for i, item in enumerate(items, 1):
        print(f"{i}. {item.get('title', '')[:60]} ({len(item.get('content', ''))} chars)")


if __name__ == "__main__":
    main()
