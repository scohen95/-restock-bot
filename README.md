# RestockBot 🤖

A Playwright-based product restock monitor. Watches product pages (Target, Walmart, Best Buy, or any generic site) and sends instant Discord alerts when items come back in stock. Designed to run 24/7 on Railway.

---

## Project Structure

```
restock-bot/
├── main.py                  # Entry point — runs the bot loop
├── config.py                # ⭐ Edit this to add products & set intervals
├── requirements.txt
├── Dockerfile               # Railway deployment
├── railway.toml             # Railway config
├── test_check.py            # Test a single product locally
├── test_discord.py          # Test your Discord webhook
├── monitors/
│   └── product_monitor.py   # Playwright logic, per-site strategies
├── alerts/
│   └── discord.py           # Discord webhook sender
└── storage/
    └── state_store.py       # SQLite state tracker (prevents duplicate alerts)
```

---

## Step 1 — Local Setup

### Prerequisites
- Python 3.11+
- Git

### Install dependencies

```bash
# Clone or copy this project
cd restock-bot

# Create a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install packages
pip install -r requirements.txt

# Install Playwright's Chromium browser
playwright install chromium
playwright install-deps chromium   # installs system libs (Linux only, skip on Mac)
```

---

## Step 2 — Configure Your Products

Open `config.py` and edit the `PRODUCTS` list:

```python
PRODUCTS = [
    {
        "name": "PS5 Console",                          # shown in alert
        "url": "https://www.target.com/p/...",          # full product URL
        "site": "target",                               # target | walmart | bestbuy | generic
        "notify": True,                                 # False = skip this product
    },
]
```

**Supported `site` values:**
| Value | Works on |
|-------|----------|
| `target` | target.com |
| `walmart` | walmart.com |
| `bestbuy` | bestbuy.com |
| `generic` | Any other site (text-based detection) |

---

## Step 3 — Discord Webhook Setup

1. Open Discord and go to the server/channel where you want alerts
2. Click the ⚙️ gear icon next to the channel name → **Edit Channel**
3. Go to **Integrations** → **Webhooks** → **New Webhook**
4. Give it a name (e.g., "RestockBot") and click **Copy Webhook URL**
5. Save that URL — it looks like:
   ```
   https://discord.com/api/webhooks/1234567890/abcdefghijklmnop
   ```

---

## Step 4 — Test Locally

### Test your Discord webhook first:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR/URL"
python test_discord.py
```

You should see a green embed in your Discord channel. ✅

### Test a product check:

Edit `test_check.py` to point at your product URL, then:

```bash
python test_check.py
```

This prints whether the bot detects the item as in-stock or out-of-stock. No alert is sent.

### Run the full bot locally:

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR/URL"
export CHECK_INTERVAL=30   # check every 30 seconds for testing
python main.py
```

---

## Step 5 — Deploy to Railway (24/7)

### 5a. Push code to GitHub

```bash
git init
git add .
git commit -m "initial restockbot"
git remote add origin https://github.com/YOUR_USERNAME/restock-bot.git
git push -u origin main
```

### 5b. Create Railway project

1. Go to [railway.app](https://railway.app) and log in
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `restock-bot` repo
4. Railway will auto-detect the Dockerfile and start building

### 5c. Set environment variables on Railway

In your Railway project → **Variables** tab, add:

| Variable | Value |
|----------|-------|
| `DISCORD_WEBHOOK_URL` | Your full webhook URL |
| `CHECK_INTERVAL` | `60` (seconds between checks) |
| `LOG_LEVEL` | `INFO` |
| `HEADLESS` | `true` |

### 5d. Verify it's running

- Go to the **Deployments** tab → click the active deployment
- Open **Logs** — you should see:
  ```
  === RestockBot starting up ===
  Monitoring 1 product(s) every 60s
  Browser ready.
  --- Starting check cycle ---
  Checking: PS5 Console
    ❌ Out of stock
  --- Check cycle complete ---
  ```

**That's it.** Railway keeps it running 24/7 and auto-restarts on crashes.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | *(required)* | Your Discord webhook URL |
| `CHECK_INTERVAL` | `60` | Seconds between full check cycles |
| `HEADLESS` | `true` | Set `false` to see the browser (local only) |
| `LOG_LEVEL` | `INFO` | `DEBUG` for verbose, `WARNING` for quiet |

---

## How It Works

1. **Bot starts** → launches a headless Chromium browser
2. **Each cycle** → opens each product URL in a fresh browser context
3. **Per-site strategy** → looks for specific buttons/selectors to determine stock status
4. **State tracking** → SQLite records last known status per URL
5. **Alert on change** → only sends Discord alert when status flips OOS → In Stock (no spam)
6. **Waits `CHECK_INTERVAL`** → repeats

---

## Adding More Products

Just add more entries to the `PRODUCTS` list in `config.py`:

```python
PRODUCTS = [
    {"name": "PS5", "url": "...", "site": "target", "notify": True},
    {"name": "RTX 5090", "url": "...", "site": "bestbuy", "notify": True},
    {"name": "Switch 2", "url": "...", "site": "walmart", "notify": True},
]
```

Redeploy to Railway (push to GitHub → Railway auto-deploys).

---

## Adding a New Site

Open `monitors/product_monitor.py` and add a new function:

```python
async def _check_mysite(page: Page, product: dict) -> CheckResult:
    url, name = product["url"], product["name"]
    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    # ... your logic here ...
    return CheckResult(in_stock=True/False, product_name=name, url=url)
```

Then register it:

```python
STRATEGIES = {
    ...
    "mysite": _check_mysite,
}
```

---

## Limitations & Honest Notes

- **Anti-bot detection**: Target, Walmart, etc. use Akamai, Cloudflare, and other protections. This bot works well for many products but *may* get blocked on high-demand drops (PS5 launch day, etc.). There's no reliable free fix for this — paid proxies or residential IPs are the next step if needed.
- **No auto-checkout**: The bot opens the product page link in the alert. Checkout automation on major retailers requires significantly more complexity (login sessions, CAPTCHA solving) and is out of scope here.
- **Selector drift**: Retailers redesign their sites. If the bot stops detecting stock correctly, run `test_check.py` and update the selectors in `product_monitor.py`.

---

## Roadmap (Future Expansion)

- [ ] Add proxy rotation support
- [ ] Add auto open-in-browser on desktop alert
- [ ] Web dashboard (FastAPI + SQLite)
- [ ] Telegram / SMS alert channels
- [ ] Auto-checkout module (Playwright form fill)
