"""
alerts/discord.py

Sends rich embed alerts to Discord via webhook.
No Discord library needed — plain HTTP POST is all we need.
"""

import logging
import aiohttp
from config import DISCORD_WEBHOOK_URL

log = logging.getLogger("discord")


class DiscordAlerter:
    def __init__(self):
        if not DISCORD_WEBHOOK_URL:
            log.warning(
                "DISCORD_WEBHOOK_URL is not set. Alerts will be logged only."
            )

    async def send_restock_alert(self, result):
        """Send a rich embed when a product comes back in stock."""
        if not DISCORD_WEBHOOK_URL:
            log.info(f"[ALERT - no webhook] IN STOCK: {result.product_name} | {result.url}")
            return

        price_line = f"**Price:** {result.price}" if result.price else ""
        title_line = result.page_title or result.product_name

        embed = {
            "title": "🟢 RESTOCK DETECTED",
            "description": (
                f"**{result.product_name}**\n"
                f"{price_line}\n\n"
                f"[🛒 Open Product Page]({result.url})"
            ),
            "color": 0x00C853,  # green
            "fields": [
                {
                    "name": "Page Title",
                    "value": title_line[:256],
                    "inline": False,
                },
                {
                    "name": "URL",
                    "value": result.url[:1024],
                    "inline": False,
                },
            ],
            "footer": {"text": "RestockBot • act fast!"},
        }

        payload = {
            "content": "@here 🚨 Item back in stock!",
            "embeds": [embed],
        }

        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.post(
                    DISCORD_WEBHOOK_URL,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                )
                if resp.status in (200, 204):
                    log.info("Discord alert sent successfully.")
                else:
                    text = await resp.text()
                    log.error(f"Discord webhook error {resp.status}: {text}")
        except Exception as e:
            log.error(f"Failed to send Discord alert: {e}")

    async def send_heartbeat(self, message: str = "RestockBot is alive ✅"):
        """Optional: send a periodic heartbeat so you know the bot is running."""
        if not DISCORD_WEBHOOK_URL:
            return
        payload = {"content": message}
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    DISCORD_WEBHOOK_URL,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                )
        except Exception as e:
            log.error(f"Heartbeat failed: {e}")
