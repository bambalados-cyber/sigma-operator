# Sigma Verification Checklist

_Last updated: 2026-03-15_

This file is the execution checklist for finishing Sigma.Money verification so the `sigma-operator` CLI can be considered trustworthy for real operator use.

It is intentionally practical.

- Use it to decide what to test next.
- Use it to classify outcomes consistently.
- Do not mark an item complete unless the wallet boundary or blocker was actually observed.

---

## Scope note

This file defines verification targets and allowed classifications.

It is not the full execution plan.
For active sequencing and readiness decisions, use:
- `PART2_PLAN.md`
- `PART2_TASKS.md`
- `PART2_OPERATOR_RUN_SEQUENCE.md`
- `PART2_CLI_TESTING_GATE.md`

---

## Current Verification Frontier

Already established:
- BNB Chain backend works through NodeReal / MegaNode-compatible RPC.
- Read-only current-app capture exists for `/trade`, `/earn`, and `/mintv2`.
- Wallet connection can be initiated through Sigma → Rabby.
- Connected `/trade` can reach an enabled `Approve & Open` boundary.
- The hidden/backgrounded Rabby surface behind Sigma `TRANSACTION... 5/6` is reproducibly capturable.
- Open Long’s first post-click wallet boundary was a Rabby `Unknown Signature Type` / `Sign` prompt for `openOrAddPositionFlashLoanV2` on BNB Chain.
- After the human manually clicked Rabby `Sign` and `Confirm`, Sigma `/trade` was observed in a completed-in-app open-position state rather than the old `BLOCKED_UI_LOOP` state.
- Current Long evidence now includes:
  - route `https://sigma.money/trade`
  - history item `2026-03-15 21:32:57` → `Open Long`
  - visible position summary with `0.01 BNB` size / `$5.91`, `<0.01 BNB` / `$1.90` xPOSITION, and `3.11` leverage
- Short is now truthfully classified from the live-open-Long state as `NOT_EXPOSED_IN_CURRENT_APP` for fresh concurrent/additional entry:
  - visible `/trade` state shows position summary plus `Adjust`, not a fresh Short form
  - controlled `Adjust` actuation opens `Adjust Leverage` / `Approve & Adjust`, i.e. position-management for the existing Long
- Connected `/earn` is now truthfully classified as a live page with `User Staked` at `$0.00`, so withdraw/claim is currently `BLOCKED_NO_POSITION` rather than a vague shell-only state.
- `/mintv2` is no longer truthfully described as disabled-shell-only in the current live session; it presents a live-looking mint form with visible `Mint` CTA, `Collateral Balance: 0.07`, `4.01 bnbUSD`, `0.01 BNB` collateral, and `Health: 1.47`.
- `/mintv2` now reaches a real first wallet boundary:
  - exact top-form collateral entry of `0.003` BNB enabled `Approve & Open` with Unlimited Approval kept OFF
  - clicking it produced Sigma `TRANSACTION... 2/6`
  - a surfaced Chrome window titled `Rabby Wallet Notification` appeared immediately afterward
- A Sigma auth/disclaimer sign flow exists, but its completion behavior has been inconsistent / looping outside the now-completed Long path.

Still missing:
- a cleaner inspectability path for live Rabby popup contents / spender summaries when the extension window blanks under native capture
- final Part 2 readiness evaluation aligned to the latest repo state

---

## Success standard

This checklist is satisfied enough for Part 2 only when the evidence is strong enough to pass `PART2_CLI_TESTING_GATE.md`.

Minimum required truths:
1. the hidden Rabby boundary behind Sigma `TRANSACTION... 5/6` is classified with evidence
2. Open Long reaches a real first wallet boundary or a precise blocker classification
3. Open Short reaches a real first wallet boundary or a precise blocker classification
4. one `/earn` path is boundary-verified or conclusively blocked with evidence
5. `/mintv2` is proven executable or conclusively classified as shell-only / disabled / blocked under current conditions
6. repo truth is aligned across ledger, status, handoff, and Part 2 gate inputs

The final readiness verdict must be written using `PART2_CLI_TESTING_GATE.md`.

---

## Global Guardrails

### Never do without fresh explicit authorization
- token spend approvals
- onchain transaction submission
- deposits
- withdrawals
- trade execution
- any action that moves funds

### Allowed without further authorization
- wallet connection attempts
- offchain auth/disclaimer signing only if explicitly approved in-chat for that step
- reading balances
- navigating Sigma UI
- opening wallet popups
- capturing screenshots / OCR / notes / JSON / decode artifacts

### Stop conditions
Stop immediately and capture evidence if any of these appear:
- ERC20 approval screen
- onchain transaction review
- gas fee confirmation for an onchain action
- any prompt whose consequence is not clearly non-transactional

---

## Execution Loop

Sequencing rule:
- use `PART2_OPERATOR_RUN_SEQUENCE.md` for run order
- do not use this checklist as permission to broaden scope out of sequence

For each function under test:

1. Check preconditions.
2. Navigate to the correct page.
3. Verify wallet/app state.
4. Trigger the action.
5. Stop at the first wallet boundary.
6. Capture evidence.
7. Classify the result.
8. Move on only after the result is classified.

### Allowed classifications
- VERIFIED_BOUNDARY
- BLOCKED_ZERO_BALANCE
- BLOCKED_NO_POSITION
- BLOCKED_UI_LOOP
- BLOCKED_POPUP_FOCUS
- BLOCKED_AUTH_STATE
- NOT_EXPOSED_IN_CURRENT_APP
- SHELL_ONLY_NO_EXECUTION_PATH
- NEEDS_HUMAN_ACTION

Do not keep retrying the same stuck action without a state change.

---

## Preconditions Matrix

### Needed now
- Rabby unlocked
- Sigma tab open
- Browser Relay on when browser-side evidence is needed
- enough gas on BNB Chain

### Needed for trade verification
- enough usable balance to surface real approval / tx review

### Needed for earn verification
- actual earn/stability-pool balance if withdraw/redeem is to be meaningfully verified

### Needed for close/reduce/leverage-adjust verification
- actual open position first

### Needed for mint verification
- sufficient collateral / balance for `/mintv2` to move beyond disabled state

---

## Priority Test Order

### Phase A — Stabilize wallet auth

#### A1. Sigma auth/sign completes once
Goal:
- clear the Sigma auth/disclaimer flow once
- confirm Sigma stays connected afterward

Capture:
- screenshot before prompt
- screenshot of auth prompt
- screenshot after completion or loop-back
- notes describing whether the app remained connected

Pass if:
- Sigma remains connected after auth step
- no immediate loop back to the same sign prompt

Fail if:
- same sign prompt loops
- Sigma and wallet state disagree

---

### Phase B — Trade entry verification

#### B1. Open Long boundary
Goal:
- reach the first real wallet boundary after `Approve & Open`

Capture:
- order form screenshot
- preview values
- first Rabby prompt after clicking `Approve & Open`
- whether it is auth / token approval / tx review

Pass if:
- first post-click wallet boundary is captured and understood

#### B2. Open Short boundary
Same as B1, but verify whether its wallet path differs from long.

Pass if:
- first post-click wallet boundary is captured and compared against long

---

### Phase C — Earn verification

#### C1. Withdraw / redeem (cooldown path)
Goal:
- verify one real withdraw/redeem flow

Pass if:
- wallet boundary appears and is captured
OR
- zero-balance blocker is confirmed with evidence

#### C2. Instant redeem / withdraw
Goal:
- determine whether instant path is distinct and live

Pass if:
- separate boundary is observed
OR
- not exposed / unavailable is confirmed

#### C3. Deposit path
Goal:
- verify whether deposit is live or still effectively disabled

Pass if:
- deposit wallet boundary appears
OR
- current-app disabled state is confirmed

---

### Phase D — Mint / redeem verification

#### D1. Mint open (`/mintv2`)
Goal:
- determine whether `/mintv2` is truly executable

Pass if:
- wallet boundary appears
OR
- disabled/insufficient-balance state is conclusively documented

#### D2. Mint close / redeem
Goal:
- determine whether current app exposes a real close/redeem path

Pass if:
- real boundary appears
OR
- no current entrypoint is found and documented

#### D3. `bnbUSD redeem`
Goal:
- verify whether this is current-app real or docs-only

Pass if:
- a real current UI path is found and tested
OR
- it is downgraded to docs-only with evidence

---

### Phase E — Position-management verification

Only execute after a real position exists.

#### E1. Close
#### E2. Reduce
#### E3. Adjust leverage

Pass if:
- each reaches a clear wallet boundary and is captured

---

## Concrete What-To-Do-If Rules

### If Sigma looks connected but app storage says disconnected
- refresh once
- re-check top-right wallet UI
- re-check Rabby connection state
- record both states side by side
- classify as `BLOCKED_AUTH_STATE` if mismatch persists

### If a Chrome-owned popup steals focus
- stop clicking
- inspect current window stack first
- identify main Sigma window vs popup
- only continue once the target window is confirmed

### If Rabby popup is visible but buttons do not respond
- try one alternate interaction method
- if unchanged, capture before/after screenshots
- classify as `BLOCKED_UI_LOOP` or `BLOCKED_POPUP_FOCUS`
- do not spam clicks

### If `Approve & Open` becomes enabled
- click once only
- capture the very next wallet boundary
- do not approve further if it becomes token approval / tx review

### If a sign/auth message appears
- compare it with prior known Sigma disclaimer/auth message
- if it is the same non-transactional auth step and explicitly authorized, complete it
- otherwise stop and capture

### If a token approval screen appears
- stop
- capture everything
- mark spender/token/prompt text
- require explicit approval before continuing

### If an onchain tx review appears
- stop
- capture everything
- mark target/action/gas/summary text
- require explicit approval before continuing

### If a page is reachable but all actions are disabled
- record balances shown
- record disabled CTA state
- classify as `BLOCKED_ZERO_BALANCE` or `SHELL_ONLY_NO_EXECUTION_PATH`

### If an action path is not exposed at all
- capture page state
- record route and current UI
- classify as `NOT_EXPOSED_IN_CURRENT_APP`

---

## Artifact Requirements For Every Attempt

Each verification attempt should leave:
- screenshots of the starting state
- screenshots of the first wallet boundary
- notes describing exactly what changed
- one final classification

Preferred artifact structure:
- attempt folder under the current capture root
- `notes.md`
- `summary.json`
- before/after screenshots
- OCR text when useful

---

## Immediate Next Actions

1. Sync the latest Short + `/mintv2` results across `STATUS.md`, the handoff, milestones, and the gate file so repo truth matches the live frontier.
2. Treat Part 2 as gate-ready / complete once the repo sync is done.
3. Keep `/earn` withdraw/claim recorded as `BLOCKED_NO_POSITION` unless a real earn stake appears, but treat the bounded SP1 deposit path as separately verified once it completes.
4. For next-phase live work, improve the inspectability path for Rabby extension popups so spender / target summaries can be captured without relying on manual intervention.
5. Only after that, branch into optional next-phase coverage such as close / reduce / leverage-adjust or deeper `/mintv2` approval / tx-review inspection.

---

## Completion Rule

Do not say the Sigma CLI is fully verified until:
- auth is stable,
- long is captured,
- short is captured,
- one earn path is captured or conclusively blocked,
- mint is proven live or downgraded honestly.

Everything else can be Phase 2 verification.


## Update — 2026-03-16 autonomous continuation pass
New capture root:
- `projects/sigma-operator/captures/20260316T021136Z-autonomous-nextphase`

What this pass proved:
- the live `/mintv2` close blocker is still real on the current Sigma surface:
  - `Repay Balance: 0.00`
  - disabled `Approve & Close`
- Sigma's `add bnbUSD to wallet` helper is a real actionable path:
  - it opens a Rabby `Add custom token to Rabby` popup for `bnbUSD`
  - popup shows `My Balance 0 bnbUSD`
  - Rabby reports the token is already supported after the add interaction
- therefore, the visible mint-close blocker is **not** just a missing watch-asset / token-registration problem
- current `/trade` still does not expose a clean standalone close or add-margin surface on the visible page; only `Adjust` remains surfaced
- current `/governance` route remains a blank/non-rendered route, not a normal visible UI hidden behind routine navigation:
  - live Chrome = black blank page
  - managed browser = HTTP 200 + JS logs + empty body text + root containing only injected style markup

Spend accounting update:
- new confirmed principal used in this pass: `0`
- cumulative confirmed principal used remains approximately `~0.009 BNB`
- no new confirmed onchain approvals or transactions were executed in this pass

Best next step:
1. restore a relay-grade or JS-grade control path on the live Chrome Sigma tab
2. replay the bounded `/earn` deposit from the proven revoke boundary so the `TRANSACTION... 1/3` stall can be classified as either hidden wallet boundary vs frontend/product-state failure
3. in parallel, inspect whether Sigma close expects wallet-held bnbUSD acquired by some separate transfer/mint receipt path rather than mere token registration in Rabby

## Update — 2026-03-16 earn relay recovery pass
New capture root:
- `projects/sigma-operator/captures/20260316T025048Z-earn-relay-recovery`

What this pass proved:
- the previously documented Sigma `/earn` `TRANSACTION... 1/3` stall was a **hidden wallet boundary**, not a frontend-only dead end
- Browser Relay + popup recovery exposed the full bounded wallet chain for the first pool deposit:
  - `Revoke Token Approval` for `USDT`
  - bounded `Token Approval` for `1.0000 USDT` to `0xde1bdd...eacea7`
  - deposit simulation / execution showing `-1.0000 USDT` and `+0.9941 sigmaSP1`
- Unlimited Approval remained OFF throughout the replay
- Sigma advanced from `1/3` to `2/3` and then cleared the overlay entirely after the final deposit confirm
- Rabby popup disappeared from the Chrome window stack at the end of the pass
- first pool Gauge TVL increased from about `1,324.61` to about `1,325.61`

Classification update:
- `/earn` deposit path is now `LIVE_COMPLETED` for a bounded `1 USDT` pass
- `/earn` withdraw / claim should remain separately classified until a real user stake / redeemable balance is surfaced
- governance remains `BLANK_ROUTE / NON_RENDERED`
- mint close remains blocked by Sigma repay `Balance: 0.00`

## Update — 2026-03-16 Sigma continuation classification pass
New capture root:
- `projects/sigma-operator/captures/20260316T034228Z-sigma-continuation`

What this pass newly proves:
- the first `/earn` pool is no longer just "deposit completed somewhere" — the post-deposit state is visible and classifiable:
  - nested `Stake` tab for the first pool shows `Balance: 0.99 SigmaSP1`
  - nested `Withdraw` tab for the first pool shows `Balance: 0.99` plus withdraw semantics
  - first-pool `Claim` shows `xSIGMA rewards: 0.00`
- therefore the bounded 1 USDT earn pass should now be classified as:
  - `DEPOSIT_LIVE_COMPLETED`
  - `POST_DEPOSIT_RECEIPT_VISIBLE`
  - `AUTO_STAKE_NOT_OBSERVED`
- first-pool withdraw semantics are now truthfully evidenced on the live UI:
  - instant path wording: `Charge me a 1% fee to receive funds immediately`
  - delayed path wording: `Or you can withdraw bnbUSD+USDT after 60 minutes`
- trade management classification also tightened:
  - `Adjust` is real and opens `Adjust Leverage`
  - no explicit visible `Add Margin`, `Reduce`, or clean `Close Position` surface was observed on the current page
- governance remains blank even after direct route load + wait:
  - `document.body.innerText.length = 0`
  - `#root.innerText.length = 0`
  - route resolves but still does not render visible governance content

Refined checklist consequences:
- `/earn` no longer belongs under a generic unresolved deposit stall
- `/earn` stake / withdraw / claim should now be tracked as separate sub-questions from the already-proven deposit leg:
  1. stake leg is available because `0.99 SigmaSP1` is visible
  2. withdraw leg is available in principle because the unstaked balance and withdraw wording are visible
  3. claim currently remains zero / disabled
- `/mintv2` close remains a separate blocker unrelated to the `/earn` receipt visibility improvement
- `/trade` close/add-margin remains `NOT_EXPOSED_IN_CURRENT_APP` on the currently visible management surface unless a deeper hidden path is later proven
