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

- [x] Create project memory system (PROJECT_STATE.md, CHANGELOG.md, TODO.md, MEMORY_RULES.md)
- [ ] Build core module structure (src/ directory with all Python modules)
- [ ] Implement Gamma API market discovery (src/gamma.py)
- [ ] Implement RTDS WebSocket price feed (src/rtds.py)
- [ ] Implement candle builder and technical analysis (src/candles.py, src/ta.py)
- [ ] Implement decision engine (src/strategy.py)
- [ ] Implement stake manager with progressive doubling (stake manager integration)
- [ ] Implement Playwright browser automation (src/ui_oneclick.py, src/selectors.py)
- [ ] Create helper scripts (scripts/run_btc.sh, scripts/run_eth.sh, scripts/doctor.sh)
- [ ] Write comprehensive README.md for non-programmers
- [ ] Create requirements.txt and config.json.example

---

## Done

- [x] Define project architecture and safety rules
- [x] Establish development guidelines for Copilot
- [x] Create long-term memory documentation system

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
