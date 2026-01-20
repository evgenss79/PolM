# Polymarket One-Click Bot 🚀

**Automated trading assistant for Polymarket "Up/Down 15m" markets with manual confirmation.**

This bot helps you trade BTC and ETH prediction markets on Polymarket by:
- ✅ Finding active markets automatically
- 📊 Analyzing real-time Chainlink price data
- 🎯 Recommending Up/Down decisions based on technical analysis
- 💰 Managing your stake with a progressive doubling system
- 🖱️ **Requiring your manual confirmation before every trade** (One-Click safety)

---

## ⚠️ IMPORTANT: Safety First

**This bot NEVER executes trades automatically.** After preparing each trade (selecting Up/Down and entering the amount), the bot pauses and waits for you to press **Enter**. This gives you full control while automating the analysis and decision-making.

---

## 📋 Table of Contents

1. [What This Bot Does](#what-this-bot-does)
2. [How the Stake System Works](#how-the-stake-system-works)
3. [Installation (5 Steps)](#installation-5-steps)
4. [First-Time Setup](#first-time-setup)
5. [Running the Bot](#running-the-bot)
6. [Understanding the Output](#understanding-the-output)
7. [Troubleshooting](#troubleshooting)
8. [Safety Features](#safety-features)
9. [Configuration](#configuration)
10. [FAQ](#faq)

---

## 🎯 What This Bot Does

### Market Discovery
- Connects to Polymarket's Gamma API to find active BTC/ETH "Up/Down 15m" markets
- Markets change every 15 minutes, and the bot finds the latest one automatically

### Price Analysis
- Connects to Polymarket's real-time data service (RTDS)
- Gets **Chainlink price feeds** - the same data Polymarket uses to settle markets
- Builds 1-minute candles from price ticks
- Calculates technical indicators:
  - **EMA (Exponential Moving Average)** - trend direction
  - **ATR (Average True Range)** - price volatility
  - **Returns** - recent price momentum

### Decision Engine
The bot analyzes current conditions and chooses Up or Down based on:

1. **Gap Analysis**: How far the current price is from the "price to beat"
2. **Time Pressure**: If close to market close, adjusts for realistic price movement
3. **Trend Detection**: Uses EMA crossovers and momentum to predict direction
4. **Clear Explanation**: Prints why it chose Up or Down in plain English

### Browser Automation
- Opens Polymarket in your Chrome browser
- Selects the recommended outcome (Up or Down)
- Enters your stake amount
- **Waits for you to press Enter**
- Only then clicks the "Buy" button

---

## 💰 How the Stake System Works

### Progressive Doubling Strategy

The bot uses a **streak-doubling** system to grow your stake:

1. **Start**: $2 USD
2. **Win**: Double your stake (2 → 4 → 8 → 16 → 32 → ...)
3. **Loss**: Reset to $2
4. **Max Streak**: 15 wins (then reset to $2)

### Example

| Trade | Result | Stake Before | Stake After | Streak |
|-------|--------|--------------|-------------|--------|
| 1     | WIN    | $2           | $4          | 1      |
| 2     | WIN    | $4           | $8          | 2      |
| 3     | LOSS   | $8           | $2          | 0      |
| 4     | WIN    | $2           | $4          | 1      |
| 5     | WIN    | $4           | $8          | 2      |
| 6     | WIN    | $8           | $16         | 3      |

### Safety Limits

- **Max Stake**: $1,024 (configurable in config.json)
- **Daily Trade Limit**: 10 trades per day (configurable)
- **Daily Loss Limit**: Stop if losses exceed $20 per day (configurable)

If any limit is hit, the bot stops and alerts you.

### Result Tracking

After each trade, the bot asks you to report the result:
- **W** = Win (price beat target, you won)
- **L** = Loss (price didn't beat target, you lost)
- **S** = Skip (trade cancelled or unknown)

The stake is adjusted accordingly, and the result is logged in `logs/trades.csv`.

---

## 🛠️ Installation (5 Steps)

### Prerequisites

- **Mac** (tested) or Linux (should work)
- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Internet connection**
- **Polymarket account** - [Sign up here](https://polymarket.com)

### Step 1: Download the Code

```bash
# Clone this repository
git clone https://github.com/evgenss79/PolM.git
cd PolM
```

### Step 2: Check Your Environment

Run the doctor script to verify everything is ready:

```bash
./scripts/doctor.sh
```

This will check:
- ✅ Python installation
- ✅ pip (Python package manager)
- ✅ Network connectivity to Polymarket
- ✅ Configuration files

If you see errors, follow the suggestions to fix them.

### Step 3: Create Configuration

Copy the example config and customize it:

```bash
cp config.json.example config.json
```

Open `config.json` in any text editor and review the settings. The defaults are good for beginners, but you can adjust:

- `base_stake_usd`: Starting stake (default: $2)
- `max_stake_usd`: Maximum allowed stake (default: $1,024)
- `daily_max_trades`: Max trades per day (default: 10)
- `daily_max_loss_usd`: Stop if daily losses exceed this (default: $20)

**Don't change** settings you don't understand - the defaults are safe!

### Step 4: Test the Environment

Run the doctor script again to make sure config.json is valid:

```bash
./scripts/doctor.sh
```

You should see: ✅ All checks passed!

### Step 5: You're Ready!

Proceed to "First-Time Setup" below to log into Polymarket.

---

## 🔐 First-Time Setup

### Logging Into Polymarket

The bot needs you to be logged into Polymarket so it can place trades on your behalf.

**First Run Only:**

1. Run the bot (we'll use BTC as an example):
   ```bash
   ./scripts/run_btc.sh
   ```

2. A Chrome window will open showing Polymarket
3. The bot will detect you're not logged in and pause
4. **Manually log into Polymarket** using your wallet or credentials
5. Once logged in, return to the terminal and press **Enter**

Your login session is saved in `.pw_profile/` and will persist for future runs. You won't need to log in again unless you clear this folder.

---

## 🚀 Running the Bot

### For Bitcoin (BTC)

```bash
./scripts/run_btc.sh
```

### For Ethereum (ETH)

```bash
./scripts/run_eth.sh
```

### Watch Mode (Continuous Trading)

To run the bot continuously and monitor for new markets:

```bash
./scripts/run_btc.sh --watch
```

In watch mode, the bot will:
- Check for new markets every 30 seconds
- Prepare a new trade when a fresh market appears
- Continue until you press Ctrl+C or daily limits are hit

**Note**: Even in watch mode, you must manually confirm each trade!

---

## 📊 Understanding the Output

### What You'll See

When you run the bot, it prints detailed information:

```
🚀 Polymarket One-Click Bot
======================================================================
✅ Configuration loaded from config.json
✅ State loaded: stake=$2.0, streak=0

🔍 Discovering active Bitcoin market...
✅ Found active market: btc-updown-15m-jan20-1430
✅ Market URL: https://polymarket.com/event/btc-updown-15m-jan20-1430

📡 Starting price feed for Bitcoin...
⏳ Collecting initial price data (60 seconds)...
  📊 10 ticks collected, latest: $43,250.50
  📊 20 ticks collected, latest: $43,251.00
  ...
✅ Collected 65 price ticks
✅ Built 2 complete 1-minute candles

🌐 Starting browser...
✅ Browser started (visible)
📍 Navigating to: https://polymarket.com/event/btc-updown-15m-jan20-1430
✅ Page loaded
✅ User appears to be logged in

======================================================================
🎯 TRADING CYCLE - BITCOIN
======================================================================
🔍 Parsing market information...
✅ Found price to beat: $43,250.46
✅ Found countdown: 8m 49s (529s)

======================================================================
🎯 TRADING DECISION
======================================================================
Current Price: $43,251.00
Price to Beat: $43,250.46
Gap: +$0.54
Seconds Left: 529s (8m 49s)

Technical Indicators:
  EMA(9): $43,250.80
  EMA(20): $43,249.20
  ATR: $12.50
  Gap/ATR: 0.04
  Return 3m: +0.12%
  Return 5m: +0.18%

💡 Reasoning:
  📊 Default: Current price $43,251.00 >= price to beat $43,250.46 → Betting UP (Yes will beat)

✅ DECISION: UP
======================================================================

======================================================================
💰 STAKE INFORMATION
======================================================================
Current Stake: $2.00
Win Streak: 0/15
Base Stake: $2.00
Max Stake: $1024.00

Projection:
  If WIN:  Stake → $4.00, Streak → 1
  If LOSS: Stake → $2.00, Streak → 0
======================================================================

🎯 Preparing trade: UP $2.00
  Step 1: Selecting UP...
  ✅ UP selected
  Step 2: Entering amount $2.00...
  ✅ Amount $2.00 entered

======================================================================
🚨 ONE-CLICK CONFIRMATION
======================================================================
Decision: UP
Amount: $2.00
Current Price: $43,251.00
Price to Beat: $43,250.46
Time Left: 529s (8m 49s)
Win Streak: 0

⚠️  Please verify the trade details in the browser window.
======================================================================

Press ENTER to execute the trade, or close the browser to cancel...
======================================================================
```

### At This Point

1. **Look at the browser window** - verify the bot selected the right outcome and amount
2. **Review the decision reasoning** - does it make sense?
3. **Press Enter** if you want to execute, or **close the browser** to cancel

After pressing Enter:

```
💰 Executing trade...
  Clicking Buy button...
  ✅ Buy button clicked!

✅ Trade executed successfully!

======================================================================
📊 TRADE RESULT
======================================================================
Please enter the result of your trade:
  W = Win (price beat target)
  L = Loss (price did not beat target)
  S = Skip (unknown or cancelled)
======================================================================
Result (W/L/S):
```

Enter **W**, **L**, or **S** and the bot will update your stake and streak accordingly.

---

## 🔧 Troubleshooting

### "Python 3 not found"

**Mac:**
```bash
brew install python3
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### "Could not find active market" or "Discovery failed"

**This happens when the bot cannot find a fresh 15-minute crypto market.**

The bot uses a **two-level discovery system**:

**LEVEL 1 (UI Scraping - Primary)**:
- Opens `https://polymarket.com/crypto/15m` in browser
- Finds the Bitcoin or Ethereum "Up or Down – 15 minute" card
- Extracts the event link directly from the current LIVE market
- **Always returns the current round**, never future markets
- Most reliable method

**LEVEL 2 (Gamma API - Fallback)**:
- Used only if browser is unavailable or UI scraping fails
- Queries Polymarket's Gamma API for active markets
- Searches for events matching `btc-updown-15m-*` or `eth-updown-15m-*`
- Filters by time to get LIVE markets only
- May have indexing delays or return future markets

**Why UI scraping is now PRIMARY:**
- Polymarket's UI always shows the current LIVE round
- Eliminates issues with Gamma API returning future markets
- More reliable for 15m markets that rotate every 15 minutes

**What to do if discovery fails:**
1. **Check browser** - Make sure Chrome is installed and accessible
2. **Check network** - Verify you can access `https://polymarket.com/crypto/15m`
3. **Check the logs** - Look for "PRIMARY DISCOVERY" (UI) and "FALLBACK DISCOVERY" (Gamma) messages
4. **Try again** - The bot will automatically try both methods

**Example output when primary UI discovery works:**
```
🔍 PRIMARY DISCOVERY: Scraping UI for BTC 15m event...
   📍 Navigating to: https://polymarket.com/crypto/15m
   ✅ Found BTC event link: /event/btc-updown-15m-jan20-1430
✅ PRIMARY DISCOVERY SUCCESS!
```

**Example output when fallback is used:**
```
🔍 PRIMARY DISCOVERY: Scraping UI for BTC 15m event...
❌ PRIMARY DISCOVERY FAILED: Could not find BTC event on page

🔄 FALLBACK DISCOVERY: Searching Gamma API for prefix: btc-updown-15m-
   📊 Gamma API returned 50 total markets
   📊 Found 10 markets matching prefix 'btc-updown-15m-'
   📊 After LIVE NOW filter: 1 markets (filtered out 9 future/past markets)
✅ FALLBACK DISCOVERY SUCCESS!
```

### "Gamma returns future rounds" or "Selected wrong market time"

**This issue is now largely resolved by making UI scraping the PRIMARY discovery method.**

The UI always shows the current LIVE market, so you should no longer see future markets being selected. The Gamma API is only used as a fallback when UI scraping is unavailable.

**If you still see future markets:**
This means UI discovery failed and Gamma API fallback was used. Check:
1. Browser is working correctly
2. `https://polymarket.com/crypto/15m` is accessible
3. Page layout hasn't changed (may need selector updates)

The bot will automatically prefer UI scraping which always gets the correct LIVE market.

### "Page navigation timeout" or "Timeout waiting for networkidle"

**This happens when navigating to Polymarket pages takes too long or never completes.**

**The Issue:**
- Polymarket pages have live websockets (for real-time price updates, activity feeds, etc.)
- The `networkidle` wait condition waits for all network activity to stop
- With active websockets, network is never idle, so the page never finishes loading
- This causes navigation to timeout

**The Fix (Implemented):**
- Navigation now uses `wait_until='domcontentloaded'` instead of `networkidle`
- This waits only for the DOM to be ready, not for all network activity to stop
- Default timeout is now 90 seconds (configurable via `timeout_ms` in config.json)
- Added 2 second stabilization wait after DOM loads
- Optionally waits for key page elements (Up/Down buttons) to ensure page is interactive
- **NEW**: On timeout, browser is left open for manual intervention

**What you'll see in logs:**
```
📍 Navigating to: https://polymarket.com/event/btc-updown-15m-jan20-1430
✅ Page loaded (domcontentloaded)
```

**If a timeout occurs:**
The browser will stay open and you'll see:
```
======================================================================
⚠️  PAGE LOAD TIMEOUT
======================================================================
Page load timeout. Browser left open for manual login.
Press Enter to close browser and exit...
======================================================================
```

This gives you a chance to:
1. **Manually complete any login/captcha** if needed
2. **Diagnose network issues** by checking if the page loads in the browser
3. **Verify Polymarket is accessible** before trying again

**If you still experience timeouts:**
1. **Check your internet connection** - Slow connections may need more time
2. **Increase timeout in config.json** - Change `"timeout_ms": 90000` to 120000 (2 minutes) or higher
3. **Try again** - Polymarket servers may be slow or experiencing issues
4. **Verify Polymarket is accessible** - Visit `https://polymarket.com` in your browser
5. **Check firewall settings** - Ensure your firewall allows connections to Polymarket

### "Could not find UP/DOWN button"

This means the page layout changed. Possible fixes:

1. **Manually select the outcome** in the browser, then let the bot continue
2. Check if you're on the correct market page
3. Wait a few seconds for the page to fully load
4. Report the issue so we can update the selectors

### "WebSocket connection failed"

Check your internet connection and firewall settings. The bot needs to connect to:
- `wss://ws-live-data.polymarket.com` (price feed)
- `https://gamma-api.polymarket.com` (market discovery)

### "Browser closes immediately"

Make sure you have enough disk space. Playwright downloads Chromium (~300MB) on first run.

### "Chromium crashes on macOS 15 arm64" or "SEGV_ACCERR error"

**macOS 15 (Sequoia) on Apple Silicon (arm64) has a known issue with Playwright's bundled Chromium (chromium-1097).**

**Solution**: Use system Chrome instead of bundled Chromium:

1. Install Google Chrome if not already installed: [Download Chrome](https://www.google.com/chrome/)
2. Update your `config.json` to use the Chrome channel:
   ```json
   "browser": {
     "channel": "chrome"
   }
   ```
3. Run the bot again - it will use your installed Chrome instead of bundled Chromium

**Note**: The example `config.json.example` already has `"channel": "chrome"` by default. If you created your config before this fix, add the `"channel": "chrome"` line to the `"browser"` section.

If you still experience issues, try:
- Updating Google Chrome to the latest version
- Removing the `.pw_profile` directory and logging in again

### "Daily loss limit exceeded"

The bot stops trading to protect you. This is intentional! Reset happens automatically at midnight UTC, or you can manually edit `state.json` (advanced users only).

### "Config file not found"

Run this:
```bash
cp config.json.example config.json
```

Then run the bot again.

---

## 🛡️ Safety Features

### 1. Manual Confirmation (One-Click)

**Every single trade requires your Enter key press.** There is no way to bypass this. The bot will never click "Buy" without your explicit confirmation.

### 2. No API Keys or Private Keys

The bot does NOT:
- Store your private keys
- Access your wallet directly
- Make on-chain transactions programmatically

All trades happen through Polymarket's web UI, just as if you were clicking manually.

### 3. Session Persistence

Your Polymarket login is saved in `.pw_profile/` for convenience, but this is a standard browser profile - the same security as Chrome/Firefox profiles on your computer.

### 4. Daily Limits

- **Max trades per day**: Prevents over-trading
- **Max loss per day**: Stops if you lose too much
- **Max stake**: Prevents accidental huge bets

All configurable in `config.json`.

### 5. Stake Reset

Even on a winning streak, the stake resets after 15 wins. This prevents exponential growth from becoming risky.

### 6. Logging

All decisions and trades are logged to `logs/` folder:
- `decisions.csv` - Every decision the bot makes
- `trades.csv` - Every trade you execute

Review these files to track performance and debug issues.

---

## ⚙️ Configuration

### config.json Structure

```json
{
  "assets": {
    "btc": {
      "enabled": true,
      "slug_prefix": "btc-updown-15m-",
      "symbol": "btc/usd",
      "display_name": "Bitcoin"
    },
    "eth": { ... }
  },

  "stake": {
    "base_stake_usd": 2.0,           // Starting stake
    "max_stake_usd": 1024.0,         // Maximum allowed
    "max_win_streak": 15,             // Reset after N wins
    "reset_on_max_streak": true,      // Auto-reset (vs pause)
    "result_mode": "manual"           // "manual" or "auto"
  },

  "safety": {
    "daily_max_trades": 10,           // Max trades per day
    "daily_max_loss_usd": 20.0,       // Stop if loss exceeds
    "require_manual_confirmation": true  // MUST be true
  },

  "trading": {
    "watch_mode": false,              // Auto-detect new markets
    "watch_interval_seconds": 30,
    "min_seconds_before_close": 120,  // Don't trade if <2min left
    "max_seconds_before_close": 840   // Don't trade if >14min left
  },

  "technical_analysis": {
    "candle_interval_seconds": 60,    // 1-minute candles
    "max_candles": 1000,
    "ema_fast": 9,                    // Fast EMA period
    "ema_slow": 20,                   // Slow EMA period
    "atr_period": 14,                 // ATR period
    "return_periods": [3, 5]          // Calculate 3m and 5m returns
  },

  "strategy": {
    "gap_atr_threshold": 0.8,         // Gap/ATR ratio threshold
    "time_pressure_seconds": 600      // Time pressure kicks in at 10min
  },

  "browser": {
    "headless": false,                // Show browser window
    "profile_dir": ".pw_profile",     // Browser profile location
    "timeout_ms": 90000,              // Element wait timeout (90s)
    "retry_attempts": 3,              // Retry clicks N times
    "slow_mo_ms": 500,                // Slow down actions (ms)
    "channel": "chrome"               // Use system Chrome (vs bundled Chromium)
  }
}
```

### Beginner-Friendly Tweaks

**To be more aggressive:**
- Increase `daily_max_trades` to 20
- Increase `daily_max_loss_usd` to 50

**To be more conservative:**
- Decrease `base_stake_usd` to 1
- Decrease `max_stake_usd` to 256
- Decrease `daily_max_trades` to 5

**To change time window:**
- `min_seconds_before_close`: Don't trade if market closes in less than this (prevents last-second volatility)
- `max_seconds_before_close`: Don't trade if market closes in more than this (avoid early trades)

---

## ❓ FAQ

### Q: Do I need a Polymarket account?

**A:** Yes. Sign up at [polymarket.com](https://polymarket.com) and fund your account.

### Q: How much money do I need?

**A:** Start with $50-100. The bot begins with $2 stakes, so you have plenty of runway.

### Q: Can this bot run 24/7 automatically?

**A:** **NO.** The bot requires manual confirmation for every trade. This is a safety feature, not a bug.

### Q: What if I want to change the decision logic?

**A:** Edit `src/strategy.py`. But be careful - wrong changes can lead to bad trades!

### Q: How accurate is the bot?

**A:** The bot is a **decision assistant**, not a crystal ball. It uses technical analysis, which works sometimes but not always. **Trade at your own risk.**

### Q: What happens if my internet disconnects?

**A:** The bot will stop. It cannot reconnect mid-trade. Close it and restart.

### Q: Can I run BTC and ETH bots simultaneously?

**A:** Technically yes (in separate terminals), but not recommended for beginners. Stick to one at a time.

### Q: What's the "watch mode"?

**A:** Normal mode runs once and exits. Watch mode continuously monitors for new markets and offers to trade each one. You still confirm each trade manually.

### Q: Where are my trade results stored?

**A:** In `logs/trades.csv` and `state.json`. Back these up if you want to preserve history.

### Q: Can I customize the stake amounts?

**A:** Yes! Edit `config.json`:
- `base_stake_usd`: Change starting amount
- `max_stake_usd`: Change maximum

But be careful with high values - you can lose real money!

### Q: What if the bot makes a wrong decision?

**A:** You can always **close the browser** instead of pressing Enter. The trade won't execute.

### Q: How do I update the bot?

**A:** Pull the latest code:
```bash
git pull origin main
```

Then re-run `./scripts/doctor.sh` to check for new dependencies.

---

## 📁 Project Structure

```
PolM/
├── config.json.example       # Configuration template
├── state.json.example        # State template
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── PROJECT_STATE.md          # Project status (for developers)
├── CHANGELOG.md              # Change history
├── TODO.md                   # Planned features
├── MEMORY_RULES.md           # Development guidelines
├── src/
│   ├── main.py              # Main entry point
│   ├── config.py            # Config and state loader
│   ├── gamma.py             # Market discovery
│   ├── rtds.py              # Price feed (WebSocket)
│   ├── candles.py           # Candle builder
│   ├── ta.py                # Technical analysis
│   ├── strategy.py          # Decision engine
│   ├── stake_manager.py     # Stake doubling logic
│   ├── ui_oneclick.py       # Browser automation
│   ├── selectors.py         # Element selectors
│   └── logger.py            # CSV logging
├── scripts/
│   ├── run_btc.sh           # Run BTC bot
│   ├── run_eth.sh           # Run ETH bot
│   └── doctor.sh            # Environment checker
└── logs/                    # Trade logs (created automatically)
    ├── decisions.csv
    └── trades.csv
```

---

## 🙏 Support

If you encounter issues:

1. **Run doctor.sh** to diagnose
2. Check **Troubleshooting** section above
3. Review `logs/` for error details
4. Open an issue on GitHub with:
   - Your OS (Mac/Linux)
   - Python version (`python3 --version`)
   - Error message
   - Steps to reproduce

---

## ⚖️ Disclaimer

**This bot is for educational purposes.**

- Trading involves risk of loss
- Past performance does not guarantee future results
- The bot's decisions are based on technical analysis, which is not always accurate
- You are responsible for your own trades
- The developers are not liable for any losses

**Trade responsibly. Never risk more than you can afford to lose.**

---

## 📜 License

MIT License - See LICENSE file for details.

---

**Happy Trading! 🚀**

Remember: The bot is your assistant, not your boss. Always review each trade before confirming!
