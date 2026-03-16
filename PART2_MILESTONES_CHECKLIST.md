# Sigma CLI Part 2 Milestones Checklist

_Last updated: 2026-03-15_

Use this as the high-level completion tracker for Part 2.

---

## M0 — Plan pack landed

- [x] `PART2_PLAN.md` created
- [x] `PART2_MILESTONES_CHECKLIST.md` created
- [x] `PART2_TASKS.md` created
- [x] `PART2_OPERATOR_RUN_SEQUENCE.md` created
- [x] `PART2_CLI_TESTING_GATE.md` created

Done when:
- the repo contains a clear Part 2 execution pack aligned with current Sigma docs

---

## M1 — Baseline restored

- [x] Read current truth files before the run:
  - [x] `STATUS.md`
  - [x] `SIGMA_VERIFICATION_CHECKLIST.md`
  - [x] `SIGMA_HANDOFF_2026-03-15.md`
  - [x] `SIGMA_RUN_LEDGER.md`
  - [x] `SIGMA_AUTONOMOUS_COMPLETION_GUIDE.md`
- [x] Confirm Rabby unlocked
- [x] Confirm BNB Chain selected
- [x] Confirm Sigma tab is current and not stale
- [x] Inspect window stack for already-open Rabby approval surfaces
- [ ] Restore known-good `/trade` tiny-size setup
- [x] Confirm Unlimited Approval is OFF
- [x] Confirm MAX is not used

Done when:
- `/trade` can be re-entered in a safe, reproducible state without ambiguity about wallet/app status

---

## M2 — Hidden `5/6` boundary classified

- [x] Reproduce Sigma `TRANSACTION... 5/6`
- [x] Surface the hidden/backgrounded Rabby boundary if present
- [x] Capture the live surface
- [x] Classify it as one of:
  - [x] auth/sign
  - [ ] token approval
  - [ ] tx review
  - [ ] completion back to Sigma
  - [x] blocked control path
- [x] Record the result in `SIGMA_RUN_LEDGER.md`

Done when:
- the post-`5/6` state is no longer mysterious

---

## M3 — Open Long classified

- [x] Re-run Long after the hidden boundary is understood
- [x] Capture first post-click wallet boundary or blocker
- [x] Record the exact operation / prompt type
- [x] Tie the conclusion to artifacts in `captures/`
- [x] Update checklist / ledger if the frontier moved

Done when:
- Long is pushed one meaningful step deeper or blocked at a named, evidenced step

---

## M4 — Open Short classified

- [x] Re-run Short with the same tiny-size discipline
- [x] Capture first post-click wallet boundary or blocker
- [x] Compare Long vs Short across:
  - [x] route family
  - [x] prompt type
  - [x] operation / contract hint
  - [x] approval count or sequence
  - [x] tx-review behavior
- [x] Record the comparison in repo docs

Done when:
- Short is classified and its relationship to Long is explicitly documented

---

## M5 — `/earn` resolved

- [x] Verify whether a real `/earn` boundary is reachable
- [x] If not, classify the blocker as one of:
  - [ ] zero balance
  - [x] no position
  - [ ] auth/state mismatch
  - [ ] disabled path
  - [ ] not exposed in current app
- [x] Capture evidence for the verdict
- [x] Update docs with the conclusion

Done when:
- `/earn` is boundary-verified or conclusively blocked with evidence

---

## M6 — `/mintv2` resolved

- [x] Verify whether `/mintv2` can reach a real wallet boundary
- [ ] If not, classify the blocker as one of:
  - [ ] insufficient balance
  - [ ] disabled CTA
  - [ ] shell-only surface
  - [ ] missing current entrypoint
- [x] Capture evidence for the verdict
- [x] Update docs with the conclusion

Done when:
- `/mintv2` is classified as executable or shell-only / blocked under current conditions

---

## M7 — Readiness package complete

- [x] Update `STATUS.md` if the blocker milestone changes
- [x] Update `SIGMA_RUN_LEDGER.md`
- [x] Update `SIGMA_VERIFICATION_CHECKLIST.md`
- [x] Update handoff doc if needed
- [x] Confirm all major claims point to capture roots
- [x] Evaluate `PART2_CLI_TESTING_GATE.md`
- [x] Write final Part 2 readiness verdict

Done when:
- the repo truth is aligned and the CLI testing gate is either passed or clearly failed with a named blocker
