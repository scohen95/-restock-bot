import asyncio
from monitors.product_monitor import ProductMonitor, STRATEGIES
from storage.state_store import StateStore
from monitors.product_monitor import CheckResult

TEST_PRODUCT = {
    "name": "Pokemon Mega Lucario Premium Collection",
    "url": "https://www.target.com/p/pok-233-mon-trading-card-game-mega-evolution-ascended-heroes-premium-poster-collection-mega-lucario/-/A-95093981",
    "site": "target",
    "notify": True,
}

class NoOpAlerter:
    async def send_restock_alert(self, result):
        print(f"\n[WOULD ALERT] In stock: {result.product_name}")

async def main():
    print(f"Testing: {TEST_PRODUCT['name']}")
    print(f"URL: {TEST_PRODUCT['url']}\n")
    store = StateStore()
    monitor = ProductMonitor(store=store, alerter=NoOpAlerter())
    await monitor.startup()
    try:
        result = await monitor._check_one(TEST_PRODUCT)
        print("─" * 50)
        print(f"In Stock:   {result.in_stock}")
        print(f"Page Title: {result.page_title}")
        print(f"Price:      {result.price or '(not found)'}")
        if result.error:
            print(f"Error:      {result.error}")
        print("─" * 50)
    finally:
        await monitor.shutdown()

if __name__ == "__main__":
    asyncio.run(main())