"""
test_discord.py

Sends a test message to your Discord webhook to confirm it's working.

    python test_discord.py

Make sure DISCORD_WEBHOOK_URL is set in your environment first:
    export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
"""

import asyncio
from alerts.discord import DiscordAlerter
from monitors.product_monitor import CheckResult


async def main():
    alerter = DiscordAlerter()
    fake_result = CheckResult(
        in_stock=True,
        product_name="TEST PRODUCT — RestockBot is working!",
        url="https://example.com",
        page_title="Test Page",
        price="$499.99",
    )
    print("Sending test alert to Discord...")
    await alerter.send_restock_alert(fake_result)
    print("Done. Check your Discord channel.")


if __name__ == "__main__":
    asyncio.run(main())
