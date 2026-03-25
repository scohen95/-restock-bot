"""
monitors/product_monitor.py

Manages the Playwright browser and dispatches per-site check strategies.
Each "strategy" is a function that receives a Playwright Page and returns
a CheckResult. Adding a new site = adding one new function.
"""

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PWTimeout

from config import HEADLESS

log = logging.getLogger("monitor")

# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    in_stock: bool
    product_name: str          # name from config
    url: str
    page_title: str = ""
    price: str = ""
    error: Optional[str] = None


# ── Per-site strategies ───────────────────────────────────────────────────────

async def _check_target(page: Page, product: dict) -> CheckResult:
    """
    Target uses dynamic React rendering. We wait for the ATC button to appear
    and inspect its disabled state or aria-label.
    """
    url = product["url"]
    name = product["name"]

    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    # Wait for the add-to-cart button area (Target's selector as of 2025)
    # Selectors may drift over time - update if Target redesigns.
    ATC_SELECTOR = '[data-test="shelfAddToCartButton"], [data-test="addToCartButton"]'
    OOS_SELECTOR = '[data-test="outOfStockButton"], [data-test="shipItButton"][disabled]'

    try:
        await page.wait_for_selector(
            f"{ATC_SELECTOR}, {OOS_SELECTOR}, [data-test='soldOutButton']",
            timeout=15_000,
        )
    except PWTimeout:
        # Couldn't find any button - likely bot detection or slow load
        return CheckResult(
            in_stock=False,
            product_name=name,
            url=url,
            error="Timeout waiting for ATC/OOS button",
        )

    page_title = await page.title()

    # Check for explicit OOS / sold out state
    sold_out = await page.query_selector('[data-test="soldOutButton"]')
    disabled_ship = await page.query_selector('[data-test="shipItButton"][disabled]')
    oos_msg = await page.query_selector('[data-test="outOfStockButton"]')

    if sold_out or oos_msg or disabled_ship:
        return CheckResult(in_stock=False, product_name=name, url=url, page_title=page_title)

    # Check for active ATC button
    atc = await page.query_selector(ATC_SELECTOR)
    if atc:
        is_disabled = await atc.get_attribute("disabled")
        if is_disabled is None:  # not disabled = in stock
            price = ""
            try:
                price_el = await page.query_selector('[data-test="product-price"]')
                if price_el:
                    price = (await price_el.inner_text()).strip()
            except Exception:
                pass
            return CheckResult(
                in_stock=True, product_name=name, url=url, page_title=page_title, price=price
            )

    return CheckResult(in_stock=False, product_name=name, url=url, page_title=page_title)


async def _check_walmart(page: Page, product: dict) -> CheckResult:
    """
    Walmart: look for 'Add to cart' button that is not disabled.
    """
    url = product["url"]
    name = product["name"]

    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    try:
        await page.wait_for_selector(
            "button[data-automation-id='add-to-cart-btn'], [data-automation-id='out-of-stock-btn']",
            timeout=15_000,
        )
    except PWTimeout:
        return CheckResult(in_stock=False, product_name=name, url=url, error="Timeout on Walmart page")

    page_title = await page.title()

    oos = await page.query_selector("[data-automation-id='out-of-stock-btn']")
    if oos:
        return CheckResult(in_stock=False, product_name=name, url=url, page_title=page_title)

    atc = await page.query_selector("button[data-automation-id='add-to-cart-btn']")
    if atc:
        disabled = await atc.get_attribute("disabled")
        if disabled is None:
            price = ""
            try:
                price_el = await page.query_selector('[itemprop="price"]')
                if price_el:
                    price = (await price_el.get_attribute("content") or "").strip()
            except Exception:
                pass
            return CheckResult(
                in_stock=True, product_name=name, url=url, page_title=page_title, price=price
            )

    return CheckResult(in_stock=False, product_name=name, url=url, page_title=page_title)


async def _check_bestbuy(page: Page, product: dict) -> CheckResult:
    """
    Best Buy: 'Add to Cart' button vs 'Sold Out' / 'Coming Soon'.
    """
    url = product["url"]
    name = product["name"]

    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    try:
        await page.wait_for_selector(
            ".add-to-cart-button, .btn-disabled, .sold-out-button",
            timeout=15_000,
        )
    except PWTimeout:
        return CheckResult(in_stock=False, product_name=name, url=url, error="Timeout on BB page")

    page_title = await page.title()

    sold_out = await page.query_selector(".sold-out-button, .coming-soon-button")
    if sold_out:
        return CheckResult(in_stock=False, product_name=name, url=url, page_title=page_title)

    atc = await page.query_selector(".add-to-cart-button:not(.btn-disabled)")
    if atc:
        price = ""
        try:
            price_el = await page.query_selector(".priceView-customer-price span")
            if price_el:
                price = (await price_el.inner_text()).strip()
        except Exception:
            pass
        return CheckResult(
            in_stock=True, product_name=name, url=url, page_title=page_title, price=price
        )

    return CheckResult(in_stock=False, product_name=name, url=url, page_title=page_title)


async def _check_generic(page: Page, product: dict) -> CheckResult:
    """
    Fallback: look for common in-stock / OOS text patterns on the page.
    Works surprisingly well for smaller retailer sites.
    """
    url = product["url"]
    name = product["name"]

    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    await page.wait_for_timeout(3_000)  # let JS settle

    page_title = await page.title()
    body_text = (await page.inner_text("body")).lower()

    OOS_PHRASES = ["out of stock", "sold out", "unavailable", "notify me when available", "coming soon"]
    IN_STOCK_PHRASES = ["add to cart", "add to bag", "buy now", "in stock"]

    for phrase in OOS_PHRASES:
        if phrase in body_text:
            return CheckResult(in_stock=False, product_name=name, url=url, page_title=page_title)

    for phrase in IN_STOCK_PHRASES:
        if phrase in body_text:
            return CheckResult(in_stock=True, product_name=name, url=url, page_title=page_title)

    return CheckResult(in_stock=False, product_name=name, url=url, page_title=page_title)


# ── Strategy dispatcher ───────────────────────────────────────────────────────

STRATEGIES = {
    "target": _check_target,
    "walmart": _check_walmart,
    "bestbuy": _check_bestbuy,
    "generic": _check_generic,
}


# ── ProductMonitor class ──────────────────────────────────────────────────────

class ProductMonitor:
    def __init__(self, store, alerter):
        self.store = store
        self.alerter = alerter
        self._playwright = None
        self._browser: Optional[Browser] = None

    async def startup(self):
        log.info("Launching Playwright browser...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=HEADLESS,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",  # critical for Railway/Docker
                "--disable-gpu",
                "--no-first-run",
                "--no-zygote",
            ],
        )
        log.info("Browser ready.")

    async def shutdown(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        log.info("Browser closed.")

    async def _new_context(self) -> BrowserContext:
        """Create a fresh browser context with realistic headers."""
        ctx = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/Los_Angeles",
            # Stealth: don't send webdriver flag
            java_script_enabled=True,
        )
        # Mask automation signals
        await ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        return ctx

    async def _check_one(self, product: dict) -> CheckResult:
        strategy_fn = STRATEGIES.get(product.get("site", "generic"), _check_generic)
        context = await self._new_context()
        page = await context.new_page()
        try:
            result = await strategy_fn(page, product)
        except Exception as e:
            log.exception(f"Error checking {product['name']}: {e}")
            result = CheckResult(
                in_stock=False,
                product_name=product["name"],
                url=product["url"],
                error=str(e),
            )
        finally:
            await page.close()
            await context.close()
        return result

    async def check_all(self, products: list):
        log.info(f"--- Starting check cycle for {len(products)} product(s) ---")
        for product in products:
            if not product.get("notify", True):
                log.debug(f"Skipping (notify=False): {product['name']}")
                continue

            log.info(f"Checking: {product['name']}")
            result = await self._check_one(product)

            if result.error:
                log.warning(f"  ERROR: {result.error}")
            elif result.in_stock:
                log.info(f"  ✅ IN STOCK — {result.product_name}")
            else:
                log.info(f"  ❌ Out of stock")

            # Only alert on state CHANGE (OOS → In Stock)
            was_in_stock = self.store.get_state(product["url"])
            now_in_stock = result.in_stock

            if now_in_stock and not was_in_stock:
                log.info(f"  🔔 STATE CHANGE detected — sending alert!")
                await self.alerter.send_restock_alert(result)

            self.store.set_state(product["url"], now_in_stock)

            # Small random delay between products to look less bot-like
            await asyncio.sleep(random.uniform(2.0, 5.0))

        log.info("--- Check cycle complete ---")
