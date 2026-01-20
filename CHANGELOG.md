# CHANGELOG

All notable changes to the Polymarket One-Click Bot project.

Format: [YYYY-MM-DD] - Description of changes

---

## [2026-01-20] - CRITICAL FIX: Two-Level Discovery for 15m Crypto Markets

### Fixed
- **Two-Level Discovery System for 15m Crypto Markets**: 
  - **Issue**: 15-minute crypto markets (btc-updown-15m-*, eth-updown-15m-*) create NEW events every 15 minutes. Gamma API may not immediately index fresh events, causing discovery failures.
  - **Solution**: Implemented robust two-level discovery:
    - **LEVEL 1 (Primary)**: Enhanced Gamma API query with `order=id&ascending=false&limit=100` to find freshest events
    - **LEVEL 2 (Fallback)**: UI scraping from `polymarket.com/crypto/15m` when Gamma API fails
  - **Benefits**: Bot now reliably finds active 15m markets even during API indexing delays
  
- **Enhanced Gamma API Discovery** (`src/gamma.py`):
  - Added proper ordering parameters (`order=id`, `ascending=false`) to get newest events first
  - Increased limit from implicit to explicit 100 for better coverage
  - Added timestamp extraction from slugs for validation
  - Improved logging with detailed step-by-step output
  
- **UI Fallback Discovery** (`src/gamma.py`):
  - New method `discover_15m_event_via_ui()` scrapes event links from aggregator page
  - Finds asset-specific event cards (Bitcoin/Ethereum)
  - Extracts event URLs matching pattern `/event/{asset}-updown-15m-{timestamp}`
  - Returns structured data: {url, slug, asset, timestamp, source}
  
- **Orchestration** (`src/gamma.py`):
  - New method `discover_15m_market()` coordinates two-level discovery
  - Clear console output showing which level succeeded
  - Automatic fallback with user-friendly explanations
  
- **Main Loop Updates** (`src/main.py`):
  - Updated `_discover_market()` to use new two-level system
  - Browser now starts conditionally (only if Gamma API fails or for trading)
  - Updated `_check_for_new_market()` for watch mode compatibility
  - Fixed browser initialization order to support UI fallback

### Changed
- Discovery logic now never assumes "eternal events" - always searches dynamically
- Logging is more verbose to help non-programmers understand discovery process
- Discovery source is tracked and displayed (GAMMA_API vs UI_FALLBACK)

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
