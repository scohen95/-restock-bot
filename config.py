import os

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL", "60"))
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

PRODUCTS = [
    {
        "name": "Pokemon Prismatic Evolutions Booster Bundle",
        "url": "https://www.target.com/p/pok-233-mon-trading-card-game-scarlet-38-violet-prismatic-evolutions-booster-bundle/-/A-93954446",
        "site": "generic",
        "notify": True,
    },
    {
        "name": "Pokemon Prismatic Evolutions Super Premium Collection",
        "url": "https://www.target.com/p/pok--233-mon-trading-card-game--scarlet---38--violet--8212-prismatic-evolutions-super-premium-collection--no-aasa/-/A-94300072",
        "site": "generic",
        "notify": True,
    },
    {
        "name": "Pokemon Target Exclusive A-95093989",
        "url": "https://www.target.com/p/A-95093989",
        "site": "generic",
        "notify": True,
    },
    {
        "name": "2025 Pokemon Elite Trainer Box",
        "url": "https://www.target.com/p/2025-pok-me-2-5-elite-trainer-box/-/A-95082118",
        "site": "generic",
        "notify": True,
    },
    {
        "name": "Pokemon Mega Gardevoir Premium Poster Collection",
        "url": "https://www.target.com/p/pok-233-mon-trading-card-game-mega-evolution-ascended-heroes-premium-poster-collection-mega-gardevoir/-/A-95093982",
        "site": "generic",
        "notify": True,
    },
    {
        "name": "Pokemon Mega Lucario Premium Poster Collection",
        "url": "https://www.target.com/p/pok-233-mon-trading-card-game-mega-evolution-ascended-heroes-premium-poster-collection-mega-lucario/-/A-95093981",
        "site": "generic",
        "notify": True,
    },
]
```

File → Save. Then run these in Command Prompt one at a time:
```
git add .
```
```
git commit -m "switch to generic strategy"
```
```
git push