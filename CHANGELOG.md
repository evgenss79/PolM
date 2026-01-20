# CHANGELOG

All notable changes to the Polymarket One-Click Bot project.

Format: [YYYY-MM-DD] - Description of changes

---

## [2026-01-20] - URGENT FIX: Navigation timeout and browser handling improvements

### Fixed
- **Page navigation timeout configuration**:
  - **Issue**: `navigate_to_market()` was using hardcoded 90000ms timeout instead of configurable value, and browser closed automatically on timeout
  - **Solution**: 
    - Changed `navigate_to_market()` to use `self.timeout` (configurable from config.json)
    - Increased default `timeout_ms` in config from 30000 to 90000 for better reliability
    - Changed stabilization wait from 1500ms to 2000ms as requested
  - **Timeout Error Handling**: On TimeoutError, browser is now left open for manual intervention
    - Displays message: "Page load timeout. Browser left open for manual login. Press Enter to close."
    - Waits for Enter keypress before closing
    - Allows user to manually complete login or diagnose issues
  - **Files changed**:
    - `src/ui_oneclick.py`: Updated `navigate_to_market()` with timeout handling and configurable timeout
    - `config.json.example`: Increased default timeout_ms from 30000 to 90000
    - `CHANGELOG.md`: Documented this fix
    - `README_BOT.md`: Updated timeout troubleshooting section

### Changed
- Default browser timeout increased from 30 seconds to 90 seconds
- Page stabilization wait increased from 1.5 seconds to 2.0 seconds
- Browser no longer closes automatically on timeout - requires manual confirmation

---

## [2026-01-20] - FIX: Page.goto timeout due to networkidle never triggering

### Fixed
- **Playwright navigation timeout on Polymarket pages**:
  - **Issue**: `page.goto()` with `wait_until='networkidle'` times out because Polymarket has live websockets that prevent network idle state
  - **Solution**: Changed to `wait_until='domcontentloaded'` which waits only for DOM to be ready
  - **Timeout**: Increased from 30s to 90s for slower connections
  - **Stability**: Added `page.wait_for_timeout(1500)` after navigation for page stabilization
  - **Optional selector wait**: In `navigate_to_market()`, optionally waits for Up/Down buttons with 30s timeout
  - **Files changed**:
    - `src/ui_oneclick.py`: Updated `navigate_to_market()` method
    - `src/gamma.py`: Updated `discover_15m_event_via_ui()` fallback discovery
    - `CHANGELOG.md`: Documented this fix
    - `README_BOT.md`: Updated troubleshooting section

### Changed
- Navigation now uses `domcontentloaded` instead of `networkidle` for reliable page loading
- Logs now show "Page loaded (domcontentloaded)" instead of "Page loaded"
- Timeout increased to 90 seconds for better reliability on slow connections

---

## [2026-01-20] - FIX: Discovery filters out future markets, selects only LIVE markets

### Fixed
- **Discovery now correctly filters future markets**:
  - **Issue**: Gamma discovery was selecting future markets (e.g., "January 21...") instead of live "сейчас" (now) markets
  - **Root Cause**: Discovery selected markets by ID (newest first) without checking if they were actually LIVE now vs scheduled for future
  - **Solution**: Added time-based filtering using startDate/endDate fields from Gamma API payload
  - **Filter Logic**: Only select markets where `start <= now < end`
  - **Fallback**: If no LIVE markets found after filtering, automatically falls back to UI scraping from `/crypto/15m`
  - **Logging**: Enhanced logging to show:
    - Number of candidates before filtering
    - Number after "LIVE NOW" filter
    - Which market was selected and why (with start/end times)
    - Clear explanation when future markets are filtered out
  - **Files changed**:
    - `src/gamma.py`: 
      - Updated `find_active_market()` to filter by time after slug matching
      - Added `_is_market_live()` to check if market is currently active
      - Added `_parse_market_datetime()` to parse various datetime field formats
      - Added `_format_market_time()` to display times in logs
      - Supports multiple field patterns: startDate/endDate, startDate+startTime/endDate+endTime, startTimestamp/endTimestamp
    - `CHANGELOG.md`: Documented this fix
    - `README_BOT.md`: Added troubleshooting section about Gamma returning future rounds

### Changed
- Discovery now explicitly validates market timing instead of blindly trusting newest ID
- Logging is more detailed to help users understand why certain markets are selected or rejected
- Fallback to UI scraping is now triggered when all candidates are future/past markets

---

## [2026-01-20] - FIX: Chromium crash on macOS 15 arm64

### Fixed
- **Chromium SEGV_ACCERR crash on macOS 15 (Sequoia) arm64**:
  - **Issue**: Playwright's bundled Chromium (chromium-1097) crashes with SEGV_ACCERR on macOS 15 running on Apple Silicon (arm64)
  - **Solution**: Added support for using system Chrome channel instead of bundled Chromium
  - **Configuration**: New `browser.channel` option in config.json (default: "chrome")
  - **Fallback**: If channel is not specified, falls back to bundled Chromium for backward compatibility
  - **Files changed**:
    - `config.json.example`: Added `"channel": "chrome"` to browser section
    - `src/ui_oneclick.py`: Updated to read channel config and pass to launch_persistent_context
    - `README_BOT.md`: Added troubleshooting section for macOS 15 arm64 Chromium crashes

### Changed
- Browser launch now supports `channel` parameter for using system browsers
- Default configuration now uses Chrome channel for better macOS 15 compatibility
- Browser startup now logs which browser is being used (bundled Chromium vs Chrome channel)

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
