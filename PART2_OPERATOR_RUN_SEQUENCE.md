# Sigma CLI Part 2 Operator Run Sequence

_Last updated: 2026-03-15_

Use this as the exact operating sequence during Part 2 runs.

This is meant to reduce drift.

---

## Core rules

- One run = one question.
- One retry = one real state change.
- If a live wallet boundary exists, go depth-first.
- Do not use MAX.
- Keep Unlimited Approval OFF.
- Stop at the first token approval or tx-review boundary.
- If the visible state contradicts old assumptions, trust the visible state.

---

## Pre-run orientation

Before touching Sigma:
- read `SIGMA_RUN_LEDGER.md`
- read `SIGMA_VERIFICATION_CHECKLIST.md`
- read `SIGMA_HANDOFF_2026-03-15.md`
- confirm current milestone in `STATUS.md`
- choose exactly one run objective

Allowed run objectives:
- `resume-pending-rabby-approval`
- `stabilize-auth`
- `capture-open-long-boundary`
- `capture-open-short-boundary`
- `classify-earn-current-state`
- `classify-mint-current-state`

Not allowed:
- “see how far everything goes”

---

## Phase 1 — Re-entry check

Before any click path:
- confirm Rabby is unlocked
- confirm chain is BNB Chain
- inspect the full Chrome/Rabby window stack
- check for already-open approval, sign, or tx-review surfaces
- confirm the Sigma tab is the intended current tab
- confirm evidence tooling is attached if needed
- confirm the allowed budget boundary for the run

Decision:
- if a pending wallet boundary already exists, skip directly to Phase 2
- if not, continue to Phase 3 or Phase 4 depending on the chosen objective

---

## Phase 2 — Existing boundary first

If any live Rabby approval / sign / tx-review surface already exists:
- capture it before touching Sigma again
- identify exactly what it is
- if allowed, attempt one control-path improvement only
- capture the immediate next state
- classify the outcome honestly

Do not reopen Sigma flows while a live pending boundary exists unless it is confirmed stale or gone.

---

## Phase 3 — Auth stabilization only if needed

Use this phase only if:
- there is no live pending boundary
- auth state is still unresolved

Procedure:
- trigger the current auth/sign step only if the run objective is auth-related
- capture the prompt cleanly
- stop unless authorization explicitly covers that non-transactional sign step
- classify the result as one of:
  - auth completed cleanly
  - auth loop
  - app-state mismatch
  - auth not required in this path

Output:
- a truthful auth-state verdict

---

## Phase 4 — Trade boundary capture

Order matters:
1. Open Long
2. Open Short

Setup rules:
- use tiny manual sizing only
- default reference amount: `0.003 BNB`
- Unlimited Approval OFF
- never use MAX

Procedure for each side:
- restore the known-good order form state
- click `Approve & Open`
- stop at the first meaningful wallet boundary
- if Sigma reaches `TRANSACTION... 5/6`, immediately inspect for hidden/backgrounded Rabby surfaces
- if a popup is found, capture it before acting
- if an action is still within allowed scope, attempt exactly one actuation
- capture the immediate next state
- classify the path

Valid classification targets:
- auth/sign
- token approval
- tx review
- completion back to Sigma
- blocked popup focus
- blocked UI loop
- blocked auth state

---

## Phase 5 — `/earn` classification

Only after trade boundary work is classified.

Procedure:
- navigate to `/earn`
- determine whether a real wallet boundary is reachable in current conditions
- if not, identify the blocker family
- capture the visible proof

Valid blocker families:
- zero balance
- no position
- auth/state mismatch
- disabled path
- not exposed in current app

Output:
- a truthful `/earn` verdict

---

## Phase 6 — `/mintv2` classification

Only after trade and `/earn` are classified.

Procedure:
- navigate to `/mintv2`
- determine whether a real wallet boundary is reachable
- if not, determine whether the current surface is merely shell-only or balance-blocked
- capture evidence

Possible outcomes:
- verified boundary
- shell-only / no execution path
- insufficient balance blocker
- not exposed in current app

Output:
- a truthful `/mintv2` verdict

---

## Phase 7 — End-of-run packaging

At the end of every run:
- save screenshots / OCR / notes / capture outputs
- name the attempt directory clearly
- write one compact run summary
- update `SIGMA_RUN_LEDGER.md` if the frontier moved
- update checklist / handoff / status if required
- decide whether the testing gate has moved closer to pass or remains blocked

---

## Stop conditions

Stop immediately and capture evidence if any of these appear:
- ERC20 approval screen
- onchain transaction review
- gas fee confirmation
- unexpected spender
- unexpected contract
- unexpected chain behavior
- unresponsive popup after one state-changing retry

If stopped:
- classify the blocker
- do not narrate optimism
- do not keep poking the same surface without a changed condition

---

## Honesty rule

The correct outcome of a run is not “progress happened.”
The correct outcome is one of these:
- the frontier moved and the evidence proves it
- the blocker became clearer and the evidence proves it
- the run failed to move the frontier and the blocker is now named precisely

That is still useful progress if it is captured honestly.
