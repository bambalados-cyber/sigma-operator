# Sigma CLI Part 2 Plan

_Last updated: 2026-03-15_

Purpose: finish the remaining verification work needed to treat `sigma-operator` V1 as credible for controlled CLI-based testing on Sigma.Money.

This document converts the current frontier into a GitHub-first execution pack.

Companion files:
- `PART2_MILESTONES_CHECKLIST.md`
- `PART2_TASKS.md`
- `PART2_OPERATOR_RUN_SEQUENCE.md`
- `PART2_CLI_TESTING_GATE.md`
- `SIGMA_VERIFICATION_CHECKLIST.md`
- `SIGMA_HANDOFF_2026-03-15.md`
- `SIGMA_RUN_LEDGER.md`
- `STATUS.md`

---

## Objective

Part 2 is complete when the project has enough live verification to move from exploration into structured CLI testing.

That means:
- wallet-connected state is stable enough to reproduce
- the hidden Rabby boundary behind Sigma `TRANSACTION... 5/6` is understood
- Open Long is classified one real step deeper than the current frontier
- Open Short is classified and compared against Long
- `/earn` is either boundary-verified or conclusively blocked with evidence
- `/mintv2` is either executable or conclusively shell-only / blocked under current conditions
- repo docs and capture evidence reflect reality and can be used as the source of truth

---

## Why Part 2 exists

Backend confidence already exists.
Read-only live app evidence already exists.
Connected shells have already been reached.

The missing piece is not generic research.
The missing piece is live boundary classification.

Current bottleneck:
- Sigma trade flow reaches in-app `TRANSACTION... 5/6`
- a hidden/backgrounded Rabby surface was later identified
- the operation seen there was `openOrAddPositionFlashLoanV2`
- the remaining uncertainty is what the real next step is and whether it can be consistently classified

Part 2 exists to remove that ambiguity and package the results cleanly enough for the next phase.

---

## Scope

### In scope
- re-establish a clean, reproducible wallet-connected baseline on BNB Chain
- classify the hidden/backgrounded Rabby boundary behind Sigma `TRANSACTION... 5/6`
- push Open Long one meaningful live step deeper
- classify Open Short and compare it against Long
- verify one real `/earn` wallet boundary or record a conclusive funded-state blocker
- determine whether `/mintv2` is executable or shell-only under current conditions
- harden the repo docs so future runs start from files, not chat memory

### Out of scope unless unlocked naturally
- full close / reduce / leverage-adjust coverage
- uncontrolled retries across unrelated Sigma surfaces
- large-size or MAX-sized testing
- any onchain submission or token approval without fresh explicit authorization
- broad feature expansion unrelated to the current verification frontier

---

## Project definition record (PDR)

### Product requirement
The first credible release of `sigma-operator` must support:
- contract / ABI inspection
- transaction decoding
- route evidence capture
- operator planning
- controlled live interaction testing with honest boundary classification

### Design requirement
- evidence-first workflow
- `captures/` and repo docs are the source of truth
- every wallet boundary must be named and classified
- unknowns must become explicit blockers, not vague prose
- current visible state beats assumptions from old runs

### Delivery requirement
Part 2 is not done until the repo contains:
- updated plan and milestone files
- updated status / ledger / checklist / handoff as needed
- capture evidence tied to every important conclusion
- a clear V1 readiness verdict for CLI testing

### Risk requirement
- preserve gas and balance discipline
- no MAX
- Unlimited Approval remains OFF unless explicitly authorized
- stop at the first token approval or tx-review boundary
- do not confuse UI rendering with execution proof

### Success definition
Enough real-path verification exists that CLI-based testing can proceed as controlled testing rather than guesswork.

---

## Guardrails

Apply these throughout Part 2:
- work depth-first on the active blocker before branching
- one run, one objective
- one state change per retry
- do not repeat the same stuck action twice without a real state change
- keep Unlimited Approval OFF
- do not use MAX or full-balance-adjacent sizing
- stop immediately and capture if any unknown approval or tx-review surface appears
- inspect the full Chrome/Rabby window stack before retrying Sigma actions
- if the popup exists but cannot be actuated, classify the blocker honestly
- update docs whenever the verification frontier materially moves

---

## Execution policy

GitHub-first working rules for Part 2:
- keep all planning and verification state in repo files
- each material frontier move should result in a doc update or new artifact
- do not rely on chat as source of truth
- if implementation work branches, use a dedicated branch and draft PR before merge
- proof-backed `done` only: screenshots, OCR, captures, notes, or ledger updates

---

## Work sequence

### Phase 1 — Re-establish baseline
Goal:
- restore the known-good connected Sigma state on BNB Chain

Expected output:
- reproducible `/trade` baseline with tiny safe sizing

### Phase 2 — Classify the hidden Rabby boundary
Goal:
- surface and classify the boundary behind `TRANSACTION... 5/6`

Expected output:
- named classification of the next live step:
  - auth/sign
  - token approval
  - tx review
  - completion back to Sigma
  - blocked control path

### Phase 3 — Open Long verification
Goal:
- push Long one real step deeper than the current verified frontier

Expected output:
- truthful Long verdict with evidence

### Phase 4 — Open Short verification
Goal:
- determine whether Short follows the same route family or a materially different one

Expected output:
- truthful Short verdict with evidence
- explicit Long vs Short comparison

### Phase 5 — `/earn` verification
Goal:
- turn `/earn` into either a verified boundary or a conclusive blocker classification

Expected output:
- `/earn` verdict with evidence

### Phase 6 — `/mintv2` verification
Goal:
- decide whether `/mintv2` is executable or shell-only / blocked in current conditions

Expected output:
- `/mintv2` verdict with evidence

### Phase 7 — Readiness package
Goal:
- close Part 2 cleanly so CLI testing can begin from repo truth

Expected output:
- final V1 readiness verdict
- synced docs and artifact references

---

## Required outputs

By the end of Part 2, the repo should contain:
- this plan package
- updated `STATUS.md` if the blocker milestone changes
- updated `SIGMA_RUN_LEDGER.md` entries for each meaningful frontier move
- updated `SIGMA_VERIFICATION_CHECKLIST.md` items or classifications
- updated handoff notes if the frontier remains incomplete
- evidence in `captures/` tied to each major claim

---

## Exit condition

Part 2 ends when the criteria in `PART2_CLI_TESTING_GATE.md` are met.

If they are not met, Part 2 remains open and the blocker must be named explicitly.
