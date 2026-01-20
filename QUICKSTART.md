# Polymarket One-Click Bot - Quick Start Guide

## ✅ Repository Complete!

This repository contains a fully functional Polymarket One-Click trading bot built from scratch for non-programmers.

## 📁 What's Included

### Core Modules (src/)
- ✅ **main.py** - Main orchestrator
- ✅ **config.py** - Configuration and state management
- ✅ **gamma.py** - Market discovery via Gamma API
- ✅ **rtds.py** - Real-time Chainlink price feed
- ✅ **candles.py** - 1-minute candle builder
- ✅ **ta.py** - Technical analysis (EMA, ATR)
- ✅ **strategy.py** - Decision engine
- ✅ **stake_manager.py** - Progressive doubling system
- ✅ **selectors.py** - Playwright element selectors
- ✅ **ui_oneclick.py** - Browser automation
- ✅ **logger.py** - CSV logging

### Helper Scripts (scripts/)
- ✅ **run_btc.sh** - BTC bot launcher
- ✅ **run_eth.sh** - ETH bot launcher
- ✅ **doctor.sh** - Environment checker

### Documentation
- ✅ **README_BOT.md** - Complete user guide (18,000+ words)
- ✅ **PROJECT_STATE.md** - Project status for developers
- ✅ **CHANGELOG.md** - Change history
- ✅ **TODO.md** - Task tracker
- ✅ **MEMORY_RULES.md** - Development guidelines

### Configuration
- ✅ **config.json.example** - Template with all settings
- ✅ **state.json.example** - Stake state template
- ✅ **requirements.txt** - Python dependencies
- ✅ **.gitignore** - Proper exclusions

## 🚀 Getting Started

### 1. Read the Documentation

Start with **README_BOT.md** - it has everything you need:
- Installation guide (5 steps)
- How to run the bot
- Understanding the stake system
- Safety features
- Troubleshooting
- FAQ

### 2. Check Your Environment

```bash
./scripts/doctor.sh
```

This will verify:
- ✅ Python 3.8+ installed
- ✅ pip available
- ✅ Network connectivity
- ✅ Configuration files present

### 3. Create Configuration

```bash
cp config.json.example config.json
```

Edit `config.json` to customize (or keep defaults for beginners).

### 4. Run the Bot

For Bitcoin:
```bash
./scripts/run_btc.sh
```

For Ethereum:
```bash
./scripts/run_eth.sh
```

The scripts will:
1. Create virtual environment (if needed)
2. Install dependencies
3. Install Playwright browsers
4. Launch the bot

### 5. First Trade

1. Browser opens with Polymarket
2. Log in manually (first time only)
3. Bot finds market and analyzes
4. Bot shows decision and reasoning
5. **You press Enter to confirm**
6. Bot clicks Buy
7. You report result (W/L/S)

That's it! 🎉

## 🛡️ Safety Features

**Manual Confirmation Required**: Bot NEVER trades without your Enter key press.

**Daily Limits**: Stops after 10 trades or $20 loss per day (configurable).

**Stake Cap**: Maximum $1,024 stake (configurable).

**No Secrets**: No API keys, private keys, or blockchain interactions.

## 📊 How It Works

1. **Discovers Market** → Finds latest BTC/ETH 15m Up/Down market via Gamma API
2. **Gets Prices** → Connects to RTDS WebSocket for real-time Chainlink prices
3. **Builds Candles** → Creates 1-minute OHLC candles from price ticks
4. **Analyzes** → Calculates EMA, ATR, returns
5. **Decides** → Chooses Up or Down based on technical analysis
6. **Prepares Trade** → Opens browser, selects outcome, enters amount
7. **Waits for You** → Shows info and waits for Enter
8. **Executes** → Clicks Buy only after your confirmation
9. **Tracks Result** → You report W/L/S, bot updates stake

## 🎲 Stake System Example

| Trade | Result | Stake | Next Stake | Streak |
|-------|--------|-------|------------|--------|
| 1     | WIN    | $2    | $4         | 1      |
| 2     | WIN    | $4    | $8         | 2      |
| 3     | LOSS   | $8    | $2         | 0      |
| 4     | WIN    | $2    | $4         | 1      |

Max 15 wins → reset to $2.

## 📝 Logs

All decisions and trades logged to:
- `logs/decisions.csv` - Every decision
- `logs/trades.csv` - Every executed trade

## 🔧 Customization

Edit `config.json`:

```json
{
  "stake": {
    "base_stake_usd": 2.0,      // Starting amount
    "max_stake_usd": 1024.0,    // Maximum allowed
    "max_win_streak": 15        // Reset after N wins
  },
  "safety": {
    "daily_max_trades": 10,     // Max trades per day
    "daily_max_loss_usd": 20.0  // Stop if loss exceeds
  }
}
```

## 🆘 Troubleshooting

Run the doctor:
```bash
./scripts/doctor.sh
```

Common issues:

**"Python not found"**: Install Python 3.8+ from [python.org](https://python.org)

**"Could not find button"**: Page layout changed, select manually or report issue

**"WebSocket failed"**: Check internet and firewall

**Full guide**: See README_BOT.md Troubleshooting section

## 🎓 Understanding the Code

### For Developers

**Project Memory Files**:
- `PROJECT_STATE.md` - Current architecture and rules
- `CHANGELOG.md` - What changed and when
- `TODO.md` - Planned features
- `MEMORY_RULES.md` - How Copilot should work with this repo

**Module Overview**:
- **Market Discovery**: `gamma.py` queries Polymarket API
- **Price Feed**: `rtds.py` WebSocket client for Chainlink data
- **Analysis**: `candles.py` + `ta.py` build indicators
- **Strategy**: `strategy.py` decision logic with explanations
- **Stakes**: `stake_manager.py` progressive doubling + limits
- **UI**: `ui_oneclick.py` + `selectors.py` browser automation
- **Orchestration**: `main.py` ties everything together

**Testing**:
```bash
# Syntax check
python3 -m py_compile src/*.py

# Environment check
./scripts/doctor.sh

# Dry run (Ctrl+C before trade)
./scripts/run_btc.sh
```

## ⚠️ Disclaimer

**Educational purposes only.**

- Trading involves risk
- Bot decisions are based on technical analysis (not always accurate)
- You are responsible for your trades
- Never risk more than you can afford to lose

## 📜 License

MIT License - free to use and modify.

## 🙏 Support

Issues? Check README_BOT.md first, then open a GitHub issue.

---

**Happy Trading! 🚀**

Remember: This bot assists you, but YOU make the final decision. Always review before pressing Enter!
