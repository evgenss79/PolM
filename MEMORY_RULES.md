# MEMORY RULES

**Rules for AI Agents (Copilot) Working on This Repository**

This document defines how Copilot should interact with the Polymarket One-Click Bot codebase to maintain consistency, safety, and usability for non-programmers.

---

## Core Principles

### 1. Read Before Writing

**ALWAYS read these files before making ANY changes:**
- `PROJECT_STATE.md` - Current project status and what must NOT be changed
- `CHANGELOG.md` - Recent decisions and changes to avoid breaking prior work
- `TODO.md` - Planned features and completed work
- This file (`MEMORY_RULES.md`) - Process guidelines

**Why**: This ensures you understand project context and don't inadvertently break critical features or violate safety rules.

### 2. Document Every Change

**ALWAYS update documentation after code changes:**
- **Code Change** → Update `CHANGELOG.md` with entry
- **Architecture Change** → Update `PROJECT_STATE.md`
- **New Feature** → Update `README.md` if user-facing
- **Task Completion** → Move item from "In Progress" to "Done" in `TODO.md`

**Why**: Future Copilot sessions (and human developers) need to understand what changed and why.

### 3. Preserve Backward Compatibility

**DO NOT break existing functionality without explicit user request.**

If a change would break existing behavior:
1. Ask the user first
2. Document the breaking change prominently in CHANGELOG.md
3. Update README.md with migration instructions
4. Add to PROJECT_STATE.md if it affects core behavior

**Why**: Non-programmers cannot easily fix broken code. Stability is critical.

### 4. Non-Programmer First

**Every change must consider the target user: someone with NO programming experience.**

Guidelines:
- Error messages must be clear and actionable (no stack traces without explanation)
- README.md instructions must be step-by-step with screenshots/examples
- Configuration must be in `config.json`, NOT in code
- Scripts must handle environment setup automatically
- Terminal output should explain what's happening in plain English

**Why**: The bot is explicitly designed for non-technical traders.

---

## Workflow for Changes

### Before Starting Work

1. **Read Memory Files**:
   - PROJECT_STATE.md (understand current state)
   - CHANGELOG.md (see recent changes)
   - TODO.md (check if task is planned)

2. **Verify No Conflicts**:
   - Check "What NOT to Change" section in PROJECT_STATE.md
   - Ensure change doesn't violate safety rules
   - Confirm change aligns with non-programmer UX

3. **Plan Approach**:
   - If new feature → Add to TODO.md "Planned" section first
   - If bug fix → Check if root cause is documented in CHANGELOG.md
   - If refactor → Ensure backward compatibility

### During Development

1. **Make Minimal Changes**:
   - Change only what's necessary
   - Preserve existing code style
   - Add comments if logic is complex (but prefer simple code over complex code + comments)

2. **Test Incrementally**:
   - Test each module independently before integration
   - Verify edge cases (network failures, invalid data, user cancellations)
   - Ensure error handling is user-friendly

3. **Maintain Consistency**:
   - Follow existing patterns (e.g., if one module logs to CSV, all should)
   - Use existing configuration keys (don't add new config without necessity)
   - Keep file structure aligned with PROJECT_STATE.md description

### After Completing Work

1. **Update Documentation** (in this order):
   - `CHANGELOG.md` - Add entry with date and change description
   - `PROJECT_STATE.md` - Update if architecture/core logic changed
   - `README.md` - Update if user-facing behavior changed
   - `TODO.md` - Move completed items to "Done"

2. **Verify Integration**:
   - Does the bot still start without errors?
   - Does config.json.example reflect new options (if any)?
   - Are all dependencies in requirements.txt?
   - Do helper scripts still work?

3. **User Communication**:
   - Summarize changes in plain language
   - Highlight any new configuration options
   - Note any actions required by user (e.g., "run doctor.sh to check dependencies")

---

## Specific Rules for This Project

### Absolute Prohibitions

**NEVER do these things:**

1. **Remove manual confirmation**
   - The "Enter to confirm Buy" step is SACRED
   - This is a safety feature, not a bug
   - Any attempt to auto-click Buy is a security violation

2. **Add API keys or secrets to code**
   - No Polymarket API keys
   - No private keys or mnemonics
   - No hardcoded credentials
   - Login must happen via browser (Playwright profile persistence)

3. **Break config.json structure**
   - Removing existing config keys breaks user setups
   - Renaming keys requires migration script
   - Always add new keys with sensible defaults

4. **Change price source**
   - MUST use RTDS WebSocket (wss://ws-live-data.polymarket.com)
   - MUST subscribe to `crypto_prices_chainlink` topic
   - This matches Polymarket's settlement oracle

5. **Make dependencies complicated**
   - Keep requirements.txt minimal
   - Avoid exotic dependencies
   - All deps must be pip-installable without system packages (except Playwright browsers)

6. **Ignore stake system rules**
   - Max streak is 15 wins (hardcoded limit, not configurable)
   - Win resets to 2.0 if streak == 15 (no growing indefinitely)
   - Daily limits must prevent trades, not just warn
   - state.json must update atomically (write to temp file → rename)

### Encouraged Practices

**DO these things:**

1. **Add clear logging**
   - Every decision should print reasoning to console
   - Errors should suggest fixes ("Run doctor.sh" or "Check config.json")
   - Use emoji/formatting for readability in terminal

2. **Handle failures gracefully**
   - Network errors → retry with backoff
   - Parsing errors → ask user for manual input
   - Playwright timeouts → clear error message, not cryptic stack trace

3. **Make scripts idempotent**
   - run_btc.sh can be run multiple times safely
   - doctor.sh should fix issues automatically (install deps, etc.)
   - No manual cleanup required between runs

4. **Test WebSocket resilience**
   - RTDS connection drops → auto-reconnect
   - Missed messages → gracefully handle gaps
   - Stale data → detect and refresh

5. **Validate user input**
   - Config.json values should be validated at startup
   - Invalid values → clear error with example of correct format
   - state.json corruption → reset to defaults with warning

---

## Memory File Synchronization

### What Happens When Code and Docs Diverge?

**PRIORITY ORDER** (highest to lowest):
1. `PROJECT_STATE.md` - Source of truth for architecture and rules
2. `config.json.example` - Source of truth for configuration schema
3. `README.md` - Source of truth for user instructions
4. Code implementation
5. `CHANGELOG.md` - Historical record, informational only
6. `TODO.md` - Planning doc, aspirational

**Rule**: If code contradicts PROJECT_STATE.md, the code is wrong and must be fixed.

**Exception**: If PROJECT_STATE.md is outdated, update it FIRST, then change code to match.

### Detecting Drift

Ask yourself before every change:
- "Does this match what PROJECT_STATE.md says the bot does?"
- "Will this confuse a non-programmer following the README?"
- "Does this violate any rule in MEMORY_RULES.md?"

If answer to any is "yes" → stop and reconcile docs first.

---

## Communication with User

### When to Ask for Clarification

**ALWAYS ask the user if:**
- Change would break backward compatibility
- Change affects safety (manual confirmation, stake limits, etc.)
- Change requires new external dependencies
- Unclear which behavior is correct (e.g., "Should we retry 3 times or 5 times?")

**NEVER assume** you know what the user wants for critical decisions.

### How to Explain Changes

**Use plain language:**
- ❌ "Refactored strategy.py to use dependency injection for ta module"
- ✅ "Updated decision engine to make technical analysis easier to test"

**Show impact on user:**
- ❌ "Changed config schema"
- ✅ "Added new option to config.json: you can now set max_stake_usd to limit maximum bet"

**Provide examples:**
- Don't just say "update config.json"
- Show actual JSON snippet with the new setting

---

## Emergency Rollback

If a change breaks the bot and you can't fix it immediately:

1. **Revert code** to last working state
2. **Document in CHANGELOG.md**: "Rolled back feature X due to issue Y"
3. **Add to TODO.md**: Move feature from "Done" back to "Planned" with note about why it failed
4. **Update PROJECT_STATE.md**: Remove from "Active Features" if necessary
5. **Inform user**: Explain what was reverted and why

**Never leave the bot in a broken state** - rollback is always an option.

---

## Summary Checklist

Before committing any change, verify:

- [ ] Read PROJECT_STATE.md, CHANGELOG.md, TODO.md
- [ ] Change doesn't violate "What NOT to Change" rules
- [ ] Change doesn't remove manual confirmation
- [ ] Change doesn't add secrets to code
- [ ] Config.json backward compatible (or migration provided)
- [ ] Error messages are non-programmer friendly
- [ ] README.md updated if user-facing change
- [ ] CHANGELOG.md entry added
- [ ] PROJECT_STATE.md updated if architecture changed
- [ ] TODO.md status updated if task completed
- [ ] Code tested and working
- [ ] No hardcoded values that should be in config.json

**If all boxes checked** → Commit is ready.
**If any box unchecked** → Fix before committing.

---

**Remember**: This bot is used by non-programmers. Stability, clarity, and safety are more important than clever code or advanced features.
