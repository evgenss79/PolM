# PROJECT STATE

## Purpose

This is a **Polymarket One-Click Bot** for BTC and ETH 15-minute "Up/Down" prediction markets. The bot is designed for **non-programmers** who want to trade on Polymarket with intelligent automation assistance while maintaining full manual control over the final trade execution.

The bot automates market discovery, real-time price analysis, technical indicator calculation, and decision-making (Up or Down), but **critically requires manual user confirmation** before executing any trade. This "One-Click" approach combines automation convenience with human oversight for safety.

## Current Status

**CORE IMPLEMENTATION COMPLETE - TESTING PHASE**

The repository has been built from scratch with a complete implementation of:
- Market discovery via Polymarket Gamma API
- Real-time Chainlink price feeds via RTDS WebSocket
- Technical analysis using 1-minute candles, EMA, and ATR indicators
- Automated Up/Down decision engine
- Progressive stake management with streak-doubling
- Browser automation using Playwright (headless=false)
- Manual confirmation system (Enter key before Buy)

## Active Features

### Market Discovery

**Two-Level Discovery System for 15m Crypto Markets**

- **Module**: `src/gamma.py`
- **Challenge**: 15-minute crypto markets create new events every 15 minutes with rotating slugs (e.g., `btc-updown-15m-jan20-1430`). Gamma API may not immediately index fresh events due to timing/caching.
  
**LEVEL 1 - Gamma API (Primary)**:
- Endpoint: `https://gamma-api.polymarket.com/markets`
- Parameters:
  - `closed=false` - Only active markets
  - `order=id` - Order by market ID (higher IDs = newer)
  - `ascending=false` - Descending order (newest first)
  - `limit=100` - Increased coverage for better discovery
- Filters results by slug prefix (`btc-updown-15m-` or `eth-updown-15m-`)
- Selects the most recent matching event
- Extracts timestamp from slug for validation

**LEVEL 2 - UI Scraping (Fallback)**:
- Triggers when Gamma API returns no matching events
- Opens `https://polymarket.com/crypto/15m` (aggregator page)
- Finds asset-specific event card (Bitcoin or Ethereum)
- Extracts `href` from event link (format: `/event/btc-updown-15m-XXXXXXXX`)
- Returns structured event data

**Orchestration** (`discover_15m_market()` method):
1. Try LEVEL 1 (Gamma API) first
2. If fails, fall back to LEVEL 2 (UI scraping)
3. Return: `{url, slug, asset, timestamp, source}`
4. Clear logging at each step for troubleshooting

**Watch Mode**: Uses same two-level discovery to detect new markets every 30 seconds

### Real-Time Price Feed
- **Module**: `src/rtds.py`
- Connects to `wss://ws-live-data.polymarket.com`
- Subscribes to `crypto_prices_chainlink` topic for BTC/USD and ETH/USD
- Uses the **same price source** that Polymarket uses for settlements

### Technical Analysis
- **Module**: `src/candles.py` - Builds 1-minute OHLC candles from price ticks
- **Module**: `src/ta.py` - Calculates EMA(9), EMA(20), ATR(14), percent returns
- Stores 500-1000 candles for historical analysis

### Trading Logic Summary

**Price Source**: Chainlink via Polymarket RTDS WebSocket (crypto_prices_chainlink topic)

**Decision Engine** (`src/strategy.py`):
1. Parse target price (`price_to_beat`) and time remaining from Polymarket page
2. Calculate gap: `current_price - price_to_beat`
3. Normalize gap by ATR: `gap_atr = gap / ATR`
4. Decision rules:
   - If `seconds_left <= 600` and `gap_atr > 0.8` → Choose DOWN (price unlikely to rise enough)
   - Trend analysis:
     - Downtrend (EMA9 < EMA20, return_3m < 0, close < EMA9) → DOWN
     - Uptrend (EMA9 > EMA20, return_3m > 0, close > EMA9) → UP
   - Default: If `current_price < price_to_beat` → DOWN, else UP
5. Print clear explanation to console for user understanding

**Amount**: Determined by progressive stake manager, NOT fixed

### Risk & Safety Rules

**CRITICAL: One-Click Manual Confirmation**
- Bot NEVER executes trades automatically
- After preparing the trade (selecting Up/Down, entering amount), bot PAUSES
- User sees: decision, amount, price_to_beat, current_price, time remaining
- User must press **Enter** to confirm, or close window to cancel
- This is the ONLY way to execute a trade

**No API Keys or On-Chain Signing**
- Zero blockchain interactions from code
- All trading happens through Polymarket's web UI via Playwright browser automation
- User must manually log into Polymarket once (session persists in `.pw_profile/`)

**Configuration-Only Settings**
- All parameters in `config.json` (no code editing required)
- Non-programmers can adjust: stake amounts, limits, slug prefixes, timeouts

**Browser Visibility**
- `headless=false` by default - user sees everything
- Persistent browser profile maintains login session

### Stake System Summary

**Progressive Doubling Strategy**:
- Base stake: **$2 USD**
- After each WIN: stake doubles (2 → 4 → 8 → 16 → 32 → ...)
- After each LOSS: reset to $2
- Maximum streak: **15 wins** (then auto-reset to $2)
- Hard limit: `max_stake_usd` from config (default: 1024)
- If doubling exceeds limit → bot refuses trade and alerts user

**State Persistence** (`state.json`):
```json
{
  "current_stake": 2.0,
  "win_streak": 0,
  "last_asset": "btc",
  "last_slug": "...",
  "last_decision": "UP",
  "last_timestamp": "...",
  "last_result": null
}
```

**Result Determination**:
- **Manual mode** (default): Bot asks user for W/L/S after trade settles
  - W = win (double stake)
  - L = loss (reset to $2)
  - S = skip/unknown (no change)
- **Auto mode** (optional): Bot attempts to scrape Polymarket portfolio/activity
  - Falls back to manual if auto-detection fails

**Safety Limits**:
- `daily_max_trades`: Stop after N trades per day
- `daily_max_loss_usd`: Stop if total losses exceed limit
- Strategy no-trade conditions do NOT count toward limits and do NOT affect stake/streak

### What NOT to Change

**ABSOLUTE RULES - DO NOT VIOLATE**:

1. **Manual Confirmation is Sacred**
   - NEVER auto-click Buy without Enter confirmation
   - NEVER bypass the pause before trade execution
   - This is a safety feature, not a convenience issue

2. **No Secrets in Code**
   - NO API keys
   - NO private keys
   - NO wallet mnemonics
   - Login happens manually in browser, session persists via browser profile

3. **Non-Programmer First**
   - All changes must preserve simplicity for non-technical users
   - README must stay understandable (no jargon)
   - Scripts must "just work" without complex setup

4. **Price Source Integrity**
   - MUST use Polymarket RTDS Chainlink feed (wss://ws-live-data.polymarket.com)
   - MUST subscribe to `crypto_prices_chainlink` topic
   - This matches Polymarket's settlement source

5. **No Breaking Changes to Config**
   - config.json structure is user-facing
   - Breaking changes require migration script + README update

6. **Stake System Discipline**
   - Win/loss must update state.json atomically
   - Streak counter must enforce 15-win ceiling
   - Daily limits must be checked before trade preparation

## Development Guidelines for Copilot

**Before ANY code change**:
1. Read this PROJECT_STATE.md in full
2. Check CHANGELOG.md for recent decisions
3. Verify change doesn't violate "What NOT to Change"

**After ANY code change**:
1. Update PROJECT_STATE.md if architecture/logic changes
2. Add entry to CHANGELOG.md
3. Update TODO.md status

**When Adding Features**:
1. Add to TODO.md first (Planned section)
2. Implement with non-programmer UX in mind
3. Update README.md if user-facing
4. Move to Done in TODO.md

**Testing Priority**:
1. WebSocket connectivity (RTDS)
2. Gamma API market discovery
3. Stake calculation edge cases (streaks, limits)
4. Playwright element selection robustness
5. Manual confirmation flow (CRITICAL)

---

**Last Updated**: 2026-01-20 (Initial creation)
**Status**: Building initial implementation
