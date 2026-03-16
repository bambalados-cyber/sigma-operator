# Sigma CLI Part 2 Tasks

_Last updated: 2026-03-15_

This is the concrete work queue for Part 2.

Principles:
- one run, one objective
- one state change per retry
- depth-first once a live wallet boundary exists
- no MAX
- Unlimited Approval stays OFF
- stop at the first approval or tx-review boundary

---

## Priority 0 — Repo and orientation

### T0.1 — Confirm truth files
- Read:
  - `STATUS.md`
  - `SIGMA_VERIFICATION_CHECKLIST.md`
  - `SIGMA_HANDOFF_2026-03-15.md`
  - `SIGMA_RUN_LEDGER.md`
  - `SIGMA_AUTONOMOUS_COMPLETION_GUIDE.md`
- Goal:
  - ensure the next run starts from repo truth, not stale assumptions
- Output:
  - one chosen run objective

### T0.2 — Confirm artifact destination
- Confirm the next run has a clear capture root under `captures/`
- Goal:
  - prevent evidence from being fragmented or lost
- Output:
  - named attempt directory for the run

---

## Priority 1 — Restore reproducible baseline

### T1.1 — Wallet and chain sanity
- Confirm Rabby is unlocked
- Confirm active chain is BNB Chain
- Confirm Sigma is the intended dapp origin
- Goal:
  - remove trivial environment blockers before deeper work
- Output:
  - baseline environment confirmation

### T1.2 — Window-stack inspection
- Inspect full Chrome/Rabby window stack before triggering new Sigma actions
- Check for already-open or backgrounded Rabby prompts
- Goal:
  - avoid restarting a flow while a pending boundary already exists
- Output:
  - explicit finding:
    - no pending boundary found
    - pending boundary found and captured

### T1.3 — Safe `/trade` setup restore
- Use tiny manual sizing only
- Keep Unlimited Approval OFF
- Do not use MAX
- Goal:
  - restore known-good cautious setup
- Output:
  - reproducible `/trade` starting state

---

## Priority 2 — Break the active blocker

### T2.1 — Reproduce Sigma `TRANSACTION... 5/6`
- Re-enter the tiny-size Long path
- Stop once the in-app `TRANSACTION... 5/6` state appears
- Goal:
  - reproduce the known frontier deterministically
- Output:
  - fresh evidence of the frontier

### T2.2 — Surface hidden/backgrounded Rabby boundary
- Inspect for popups, tabs, overlays, or focus-stealing wallet surfaces
- Goal:
  - determine whether the missing step is actually already open
- Output:
  - surfaced wallet boundary or blocker classification

### T2.3 — Actuate once, safely
- If the boundary is visible and the action is still within allowed scope, attempt exactly one controlled actuation
- Goal:
  - learn the immediate next state without drifting into repeated retries
- Output:
  - one-step-deeper classification

### T2.4 — Classify the post-`5/6` state
- Required labels:
  - auth/sign
  - token approval
  - tx review
  - completion back to Sigma
  - blocked popup focus / blocked UI loop / blocked auth state
- Goal:
  - remove ambiguity from the main blocker
- Output:
  - ledger-ready classification

---

## Priority 3 — Trade path verification

### T3.1 — Open Long classification
- Re-run Long after T2 is resolved
- Capture the first real wallet boundary after `Approve & Open`
- Goal:
  - produce a trustworthy Long verdict
- Output:
  - `VERIFIED_BOUNDARY` or an explicit blocker classification

### T3.2 — Open Short classification
- Re-run Short with the same tiny-size discipline
- Capture the first real wallet boundary after `Approve & Open`
- Goal:
  - produce a trustworthy Short verdict
- Output:
  - `VERIFIED_BOUNDARY` or an explicit blocker classification

### T3.3 — Long vs Short comparison
- Compare:
  - prompt sequence
  - operation hint
  - approval count
  - route-family similarity/difference
  - tx-review behavior
- Goal:
  - determine whether Long and Short share the same practical path family
- Output:
  - explicit comparison note in docs

---

## Priority 4 — `/earn` resolution

### T4.1 — Current-state classification
- Verify whether the current `/earn` environment can reach a real wallet boundary
- Goal:
  - separate funding blockers from product blockers
- Output:
  - one of:
    - `VERIFIED_BOUNDARY`
    - `BLOCKED_ZERO_BALANCE`
    - `BLOCKED_NO_POSITION`
    - `BLOCKED_AUTH_STATE`
    - `NOT_EXPOSED_IN_CURRENT_APP`

### T4.2 — Distinguish withdraw/redeem paths if exposed
- Check whether cooldown and instant paths are both present, or whether only one is current
- Goal:
  - avoid over-claiming path coverage
- Output:
  - path exposure note

---

## Priority 5 — `/mintv2` resolution

### T5.1 — Current-state classification
- Determine whether `/mintv2` can move beyond disabled CTA state under current balances
- Goal:
  - decide whether mint is live, blocked, or shell-only
- Output:
  - one of:
    - `VERIFIED_BOUNDARY`
    - `SHELL_ONLY_NO_EXECUTION_PATH`
    - `BLOCKED_ZERO_BALANCE`
    - `NOT_EXPOSED_IN_CURRENT_APP`

### T5.2 — Redeem path exposure check
- Only if a current entrypoint is visible
- Goal:
  - distinguish live current redeem from docs-only references
- Output:
  - current-app verdict on redeem exposure

---

## Priority 6 — Documentation and readiness

### T6.1 — Update run ledger
- Add a compact factual entry for every meaningful frontier move
- Goal:
  - keep chronology honest and reusable
- Output:
  - updated `SIGMA_RUN_LEDGER.md`

### T6.2 — Update verification checklist
- Mark resolved classifications and remaining blockers
- Goal:
  - keep the checklist aligned with reality
- Output:
  - updated `SIGMA_VERIFICATION_CHECKLIST.md`

### T6.3 — Update status / handoff if needed
- If the blocker milestone changes, update `STATUS.md`
- If Part 2 remains incomplete, update the handoff file with the new frontier
- Goal:
  - preserve continuity without chat archaeology
- Output:
  - updated status / handoff as required

### T6.4 — Evaluate testing gate
- Run through `PART2_CLI_TESTING_GATE.md`
- Goal:
  - decide whether V1 can move into CLI testing
- Output:
  - PASS / FAIL with named blocker(s)

---

## Nice-to-have only after gate pass

Do not do these before Part 2 is complete unless a prior step unlocks them directly:
- close
- reduce
- leverage adjust
- broader mint/redeem route exploration
- deeper post-boundary execution proof beyond the first credible release threshold
