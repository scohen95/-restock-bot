"""
RestockBot - Playwright-based product monitor
Monitors product pages for in-stock status and sends Discord alerts.
"""

import asyncio
import logging
import signal
import sys
from config import PRODUCTS, CHECK_INTERVAL_SECONDS, LOG_LEVEL
from monitors.product_monitor import ProductMonitor
from storage.state_store import StateStore
from alerts.discord import DiscordAlerter

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("restockbot")

shutdown_event = asyncio.Event()


def handle_signal(*_):
    log.info("Shutdown signal received.")
    shutdown_event.set()


async def main():
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    log.info("=== RestockBot starting up ===")
    log.info(f"Monitoring {len(PRODUCTS)} product(s) every {CHECK_INTERVAL_SECONDS}s")

    store = StateStore()
    alerter = DiscordAlerter()
    monitor = ProductMonitor(store=store, alerter=alerter)

    await monitor.startup()

    try:
        while not shutdown_event.is_set():
            await monitor.check_all(PRODUCTS)
            try:
                await asyncio.wait_for(
                    shutdown_event.wait(), timeout=CHECK_INTERVAL_SECONDS
                )
            except asyncio.TimeoutError:
                pass
    finally:
        await monitor.shutdown()
        log.info("=== RestockBot stopped ===")


if __name__ == "__main__":
    asyncio.run(main())
