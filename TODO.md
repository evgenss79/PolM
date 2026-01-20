# TODO

Task tracking for Polymarket One-Click Bot development.

---

## Planned

- [ ] Add optional Discord/Telegram notifications for trade decisions
- [ ] Implement auto mode for result determination (scrape Polymarket portfolio)
- [ ] Add backtesting mode using historical Chainlink data
- [ ] Multi-asset support beyond BTC/ETH
- [ ] Configurable technical indicators (allow custom EMA periods, ATR periods)
- [ ] Trade history visualization dashboard
- [ ] Mobile app companion (view decisions, approve trades remotely)

---

## In Progress

- [ ] Comprehensive testing of all modules
- [ ] End-to-end integration testing
- [ ] Code review and security audit
- [ ] Final documentation review

---

## Done

- [x] Define project architecture and safety rules
- [x] Establish development guidelines for Copilot
- [x] Create long-term memory documentation system
- [x] Create project memory system (PROJECT_STATE.md, CHANGELOG.md, TODO.md, MEMORY_RULES.md)
- [x] Build core module structure (src/ directory with all Python modules)
- [x] Implement Gamma API market discovery (src/gamma.py)
- [x] Implement RTDS WebSocket price feed (src/rtds.py)
- [x] Implement candle builder and technical analysis (src/candles.py, src/ta.py)
- [x] Implement decision engine (src/strategy.py)
- [x] Implement stake manager with progressive doubling (src/stake_manager.py)
- [x] Implement Playwright browser automation (src/ui_oneclick.py, src/selectors.py)
- [x] Create main orchestrator (src/main.py)
- [x] Create helper scripts (scripts/run_btc.sh, scripts/run_eth.sh, scripts/doctor.sh)
- [x] Write comprehensive README_BOT.md for non-programmers
- [x] Create requirements.txt and config.json.example
- [x] Create state.json.example for stake persistence
- [x] Create .gitignore for Python project
- [x] Make scripts executable
- [x] Validate Python syntax in all modules

---

## Rejected / Won't Do

- ~~Full automation without manual confirmation~~ - VIOLATES safety principle
- ~~Direct blockchain integration via web3.py~~ - Conflicts with UI-only approach
- ~~Windows-specific scripts~~ - Focused on Mac/Linux first (cross-platform Python works anyway)
- ~~Mobile-first development~~ - Desktop browser automation is core requirement

---

## Notes

- Items move from Planned → In Progress → Done as work proceeds
- Rejected items documented to avoid revisiting bad ideas
- User requests go to Planned first, then prioritized
