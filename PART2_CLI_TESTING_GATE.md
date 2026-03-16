# Sigma CLI Part 2 CLI Testing Gate

_Last updated: 2026-03-15_

Purpose: determine whether `sigma-operator` can move from Part 2 verification into controlled CLI-based testing.

This is a gate, not a wish list.

Pass only if the required items below are true and evidenced.

---

## Gate question

Can the project stop doing broad exploratory Sigma verification and start doing structured CLI-driven testing with confidence?

---

## Required pass criteria

### 1) Reproducible connected state
Pass only if:
- wallet-connected Sigma state can be restored intentionally
- chain is confirmed as BNB Chain
- wallet/app state is not left ambiguous

Fail if:
- connection state remains inconsistent or non-reproducible

### 2) Hidden Rabby boundary understood
Pass only if:
- the boundary behind Sigma `TRANSACTION... 5/6` is classified with evidence
- the next state is known to be one of:
  - auth/sign
  - token approval
  - tx review
  - completion back to Sigma
  - control-path blocker with precise cause

Fail if:
- `5/6` is still treated as a mystery surface

### 3) Open Long classified
Pass only if:
- Long reaches a real first wallet boundary or a precise blocker classification
- the classification is backed by artifacts

Fail if:
- Long remains vague, anecdotal, or unrepeatable

### 4) Open Short classified
Pass only if:
- Short reaches a real first wallet boundary or a precise blocker classification
- the result is compared explicitly against Long

Fail if:
- Short remains unclassified or only assumed to match Long

### 5) `/earn` truthfully resolved
Pass only if:
- one real `/earn` boundary is captured
  OR
- a conclusive blocker is documented, such as zero balance or no position

Fail if:
- `/earn` remains in a hand-wavy “probably blocked” state

### 6) `/mintv2` truthfully resolved
Pass only if:
- `/mintv2` reaches a real boundary
  OR
- it is conclusively documented as shell-only / disabled / blocked under current conditions

Fail if:
- `/mintv2` remains assumed-but-unproven

### 7) Repo truth aligned
Pass only if:
- `SIGMA_RUN_LEDGER.md` reflects the latest frontier
- `SIGMA_VERIFICATION_CHECKLIST.md` reflects the latest classifications
- `STATUS.md` and handoff are aligned if the milestone changed
- capture roots are linked or named clearly enough to verify claims

Fail if:
- the real state lives mostly in chat memory rather than repo files

---

## Optional but helpful

Not required for the gate, but valuable:
- clean auth-sign completion once
- clearer evidence on approval count for the Sigma trade path
- stronger comparison between Long and Short operation hints
- docs clarifying whether redeem paths are live or docs-only

---

## Gate result format

When evaluating the gate, write the result in this structure:

- Result:
  - `PASS`
  - or `FAIL`
- Reason:
  - one short sentence
- Required criteria status:
  - criterion 1: pass/fail
  - criterion 2: pass/fail
  - criterion 3: pass/fail
  - criterion 4: pass/fail
  - criterion 5: pass/fail
  - criterion 6: pass/fail
  - criterion 7: pass/fail
- Remaining blockers:
  - bullet list
- Next action:
  - single best next step

---

## What passing this gate means

If this gate passes, the project may move into controlled CLI-based testing focused on:
- structured decode-backed operator testing
- targeted route comparison
- constrained live-path verification
- explicit next-phase work such as close / reduce / leverage-adjust only after prerequisite live conditions exist

It does not mean:
- unrestricted execution
- broad production readiness
- every Sigma surface is complete

It means the project has crossed from exploration into disciplined testing.

---

## Latest evaluation — 2026-03-15 short + mint completion pass

- Result:
  - `PASS`
- Reason:
  - The repo now has evidence-backed truth for Long, Short, `/earn`, and `/mintv2`, so structured CLI-driven testing can begin without relying on vague UI assumptions.
- Required criteria status:
  - criterion 1: `pass`
  - criterion 2: `pass`
  - criterion 3: `pass`
  - criterion 4: `pass`
  - criterion 5: `pass`
  - criterion 6: `pass`
  - criterion 7: `pass`
- Remaining blockers:
  - Live Rabby popup contents / spender summaries are still not cleanly inspectable when the extension window blanks under native capture.
  - Deeper next-phase execution detail (for example close / reduce / leverage-adjust or mint approval / tx-review internals) still needs a better popup-inspection path.
- Next action:
  - single best next step: start controlled CLI-based testing, and in parallel improve the inspectability path for live Rabby popup contents so deeper approval / tx-review steps can be captured safely.
