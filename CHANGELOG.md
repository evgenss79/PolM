# CHANGELOG

All notable changes to the Polymarket One-Click Bot project.

Format: [YYYY-MM-DD] - Description of changes

---

## [2026-01-20]

### Added
- **Project Memory System**: Created PROJECT_STATE.md, CHANGELOG.md, TODO.md, MEMORY_RULES.md for long-term project context
- **Core Python Modules** (src/):
  - `config.py` - Configuration and state management with validation
  - `logger.py` - CSV logging for decisions and trades
  - `gamma.py` - Polymarket Gamma API client for market discovery
  - `rtds.py` - RTDS WebSocket client for real-time Chainlink prices
  - `candles.py` - 1-minute OHLC candle builder from price ticks
  - `ta.py` - Technical analysis: EMA, ATR, returns calculation
  - `strategy.py` - Decision engine with clear reasoning output
  - `stake_manager.py` - Progressive doubling with 15-win cap and daily limits
  - `selectors.py` - Robust Playwright element selectors
  - `ui_oneclick.py` - Browser automation with manual confirmation
  - `main.py` - Main orchestrator integrating all components
- **Helper Scripts** (scripts/):
  - `run_btc.sh` - One-command BTC bot launcher with auto-setup
  - `run_eth.sh` - One-command ETH bot launcher with auto-setup
  - `doctor.sh` - Environment checker with detailed diagnostics
- **Configuration Files**:
  - `config.json.example` - Comprehensive configuration template
  - `state.json.example` - Stake state persistence template
  - `.gitignore` - Proper Python gitignore
  - `requirements.txt` - Python dependencies
- **Documentation**:
  - `README_BOT.md` - Complete user guide for non-programmers
- **Architecture Features**:
  - Market discovery via Gamma API
  - Real-time Chainlink prices via RTDS WebSocket
  - Technical analysis with 1-minute candles, EMA, ATR
  - Progressive stake doubling system (2 → 4 → 8 → ... → max 15 wins)
  - Playwright browser automation with manual confirmation
  - Watch mode for continuous market monitoring
  - CSV logging of all decisions and trades
  - Daily trading limits (max trades, max loss)
  - Persistent browser profile for saved login sessions
- **Safety Rules**:
  - One-Click manual confirmation requirement (Enter before Buy)
  - No API keys or blockchain signing
  - All settings in config.json
  - Non-programmer friendly design
  - Stake limits and daily limits

### Changed
- N/A (initial creation)

### Fixed
- N/A (initial creation)

### Removed
- N/A (initial creation)

---

## Notes

- This project is built from scratch for the PolM repository
- All development follows "non-programmer first" principle
- Manual trade confirmation is a non-negotiable safety feature
