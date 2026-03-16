# Sigma Run Ledger

Purpose: one compact, chronological source of truth for what has already been tried, what it proved, and what did not move the frontier.

Use this with:
- `PART2_PLAN.md` for the active objective, scope, and exit condition
- `PART2_MILESTONES_CHECKLIST.md` for milestone tracking
- `PART2_TASKS.md` for the current work queue
- `PART2_OPERATOR_RUN_SEQUENCE.md` for exact run order
- `PART2_CLI_TESTING_GATE.md` for the readiness decision
- `STATUS.md` for compact top-level status
- `SIGMA_VERIFICATION_CHECKLIST.md` for boundary classifications
- `SIGMA_HANDOFF_2026-03-15.md` for situational handoff context

This ledger is intentionally concrete. If a result was not observed in artifacts, it is not claimed here.

## Ledger role

This file is the historical record of what was attempted and what changed the frontier.

It does not define the next run by itself.
For active execution decisions, the Part 2 pack is authoritative.

---

## Current frontier summary

Part 2 current frontier after `20260317T0033-post-manual-sign-verify`:
- the earlier `/mintv2` exact-approval replay is still verified truthfully as a **partial repay** only (`0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d`)
- the later explicit `/trade` close path is now also verified end to end from fresh post-sign state
- Priority A is complete onchain via tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092`
- the prior Long is economically fully closed, not partially reduced and not replaced/reminted:
  - position/NFT `#158` remains wallet-owned
  - but `rawColls = 0`
  - and `rawDebts = 0`
- exact close-result asset receipt is now known rather than guessed:
  - `USDT +6.792825626759770802`
- Priority B is no longer applicable because no mint debt/collateral remains to close on the verified position shell
- residual wallet/stability-pool balances still exist independently of the closed position:
  - wallet-held `bnbUSD = 0.005238383559755168`
  - residual `SigmaSP1 = 0.004083641208352667` shares

Part 2 is no longer blocked by execution uncertainty; only final truth-packaging remains.

---

## 2026-03-13 — `20260313T032348Z-first-pass`
- Attempted:
  - establish the first operator capture workspace and target contract set for Sigma on BNB Chain
- Result:
  - baseline capture structure was created and the project shifted into a capture-first workflow
- Blocker:
  - no live wallet or app-path evidence yet; this was setup, not verification
- Key artifact root:
  - `captures/20260313T032348Z-first-pass/`
- Advanced verification frontier:
  - Yes, but only at the workflow/foundation layer

## 2026-03-13 — `20260313T040614Z-phase-2a-validation`
- Attempted:
  - validate decode intake formats and first-pass route-evidence logic on sample tx / rpc / receipt inputs
- Result:
  - batch decode succeeded on 4 files
  - correlated evidence records were produced
  - BNBUSD `approve(address,uint256)` was decoded cleanly
  - first `routeEvidence` outputs established partial overlap for `open-long` and archived `mint-open`
- Blocker:
  - still synthetic / sample-style evidence; not proof of the current live frontend route
- Key artifact root:
  - `captures/20260313T040614Z-phase-2a-validation/`
- Advanced verification frontier:
  - Yes

## 2026-03-13 — `20260313T044416Z-phase-2b-validation`
- Attempted:
  - strengthen decode correlation with tx+receipt bundles and validate live RPC fetch plumbing
- Result:
  - combined tx+receipt decode landed with success correlation
  - helper scaffolding for browser capture was added
  - live RPC-fetched bundle support was exercised successfully
- Blocker:
  - still no current Sigma app execution-surface proof; this improved evidence plumbing, not live route certainty
- Key artifact root:
  - `captures/20260313T044416Z-phase-2b-validation/`
- Advanced verification frontier:
  - Yes

## 2026-03-14 — `20260314T041557Z-live-public-20260314`
- Attempted:
  - capture real current-app public flows on `/trade`, `/earn`, and `/mintv2` without signing or executing
- Result:
  - live read-only traffic was captured from all three surfaces
  - traffic was dominated by Multicall3 `aggregate3((address,bool,bytes)[])`
  - nested inner-call extraction was produced separately
  - strongest address-matched live read recorded was `BNBUSDBasePool.totalSupply()`
- Blocker:
  - capture stayed in read phase; no pre-sign write payload or wallet boundary was proven
- Key artifact root:
  - `captures/20260314T041557Z-live-public-20260314/`
- Advanced verification frontier:
  - Yes

## 2026-03-14 — `peekaboo-view-raw-20260314T134452Z`
- Attempted:
  - click Rabby `View Raw >` to extract the exact raw sign payload from the live popup
- Result:
  - Rabby popup presence was confirmed
  - `View Raw >` was visibly present
  - two safe click attempts left the popup visually unchanged
- Blocker:
  - Rabby popup controls were visible but did not actuate through the attempted control path
- Key artifact root:
  - `captures/20260314T041557Z-live-public-20260314/peekaboo-view-raw-20260314T134452Z/`
- Advanced verification frontier:
  - No

## 2026-03-14 — `raw/live-presign`
- Attempted:
  - improve inspectability of the live Rabby sign surface after enabling Chrome Apple Events JavaScript access
- Result:
  - host Apple Events control of Chrome was confirmed working
  - the failure mode materially changed after the toggle
  - Sigma tab state remained readable enough to show selected address, chain `0x38`, and inconsistent app connection markers
- Blocker:
  - the Rabby approval/sign surface still did not become reliably inspectable; exact raw sign payload remained unexported
- Key artifact root:
  - `captures/20260314T041557Z-live-public-20260314/raw/live-presign/`
- Advanced verification frontier:
  - Slightly, but not enough to clear the blocker

## 2026-03-14 — `connected-action-pass-20260314T150431Z`
- Attempted:
  - push the connected `/trade` path to the first meaningful wallet prompt and stop safely there
- Result:
  - Sigma looked connected on BNB Chain
  - Rabby popup showed `1 transaction needs to sign`
  - the exact Sigma disclaimer/auth message was captured from the browser console
  - this established that the first prompt on the observed connected trade path was a sign-message boundary, not yet an onchain approval
- Blocker:
  - the run stopped at the first meaningful prompt by design; no actuation beyond the boundary
- Key artifact root:
  - `captures/20260314T041557Z-live-public-20260314/connected-action-pass-20260314T150431Z/`
- Advanced verification frontier:
  - Yes

## 2026-03-14 — `leap-pass-20260314T151158Z`
- Attempted:
  - sign the known non-transactional disclaimer if possible, then push `/trade`, `/earn`, and `/mintv2` to their first meaningful blockers
- Result:
  - the Rabby disclaimer/sign popup was re-confirmed live
  - repeated attempts to actuate `Sign` did not change the popup
  - `/earn` connected shell was verified to a zero-balance disabled withdraw boundary
  - `/mintv2` connected shell was verified to an insufficient-balance disabled `Approve & Open` boundary
  - `/trade` still did not move past the unresolved disclaimer popup
- Blocker:
  - sign button / popup actuation failure kept trade depth from progressing
- Key artifact root:
  - `captures/20260314T041557Z-live-public-20260314/leap-pass-20260314T151158Z/`
- Advanced verification frontier:
  - Yes

## 2026-03-14 — `live-pass-20260314T160324Z`
- Attempted:
  - verify connected balances and reach a live enabled trade CTA
- Result:
  - connected wallet value and balances were observed in Rabby
  - `/trade` order form was expanded successfully
  - an enabled `Approve & Open` boundary was reached
- Blocker:
  - this pass used a MAX-like / full-balance-adjacent input state and later became invalid for cautious verification
  - no token approval or tx review was approved or submitted
- Key artifact root:
  - `captures/20260314T041557Z-live-public-20260314/live-pass-20260314T160324Z/`
- Advanced verification frontier:
  - Yes, but its sizing path was later corrected and should not be reused

## 2026-03-14 — `attempts/20260314T165328Z-bounded-pass`
- Attempted:
  - re-run auth stabilization plus open-long and open-short under a corrected tiny-size budgeted envelope
- Result:
  - earlier MAX-like sizing was explicitly invalidated
  - both Long and Short were reproduced with `0.003 BNB` and unlimited approval OFF
  - both paths reached Sigma’s in-app `TRANSACTION... 5/6`
  - actual spend remained `0 USDT, 0 BNB`
- Blocker:
  - still no inspectable Rabby approval / tx review surface after hitting `5/6`
- Key artifact root:
  - `captures/20260314T041557Z-live-public-20260314/attempts/20260314T165328Z-bounded-pass/`
- Advanced verification frontier:
  - Yes

## 2026-03-14 — `retry-window-stack-20260314T222448`
- Attempted:
  - retry the wallet-connect path with explicit window-stack inspection before acting
- Result:
  - main Sigma window and Chrome-owned popup surfaces were inventoried first
  - Sigma wallet modal was reopened safely
  - Rabby `Connect to Dapp` on `https://sigma.money` / BNB Chain was reached and approved
  - Sigma then appeared connected again
- Blocker:
  - after connect, no new sign-message or deeper approval popup surfaced in this retry
- Key artifact root:
  - `captures/20260314T041557Z-live-public-20260314/retry-window-stack-20260314T222448/`
- Advanced verification frontier:
  - Slightly; it confirmed the safe reconnect procedure, but did not clear the missing boundary

## 2026-03-14 — `20260314T174741Z-depth-first-5of6`
- Attempted:
  - go depth-first on the hidden Rabby approval behind Sigma `TRANSACTION... 5/6`
- Result:
  - the hidden approval window was capturable
  - later continuation proved the live popup was not just auth/disclaimer; it was a pending approval for `openOrAddPositionFlashLoanV2`
- Blocker:
  - desktop/browser control could see the window but still could not reliably actuate it
- Key artifact root:
  - `captures/20260314T174741Z-depth-first-5of6/`
- Advanced verification frontier:
  - Yes

## 2026-03-14 — `first-loop-20260314T180051Z`
- Attempted:
  - continue from the hidden/backgrounded Rabby popup and push exactly one step deeper
- Result:
  - live popup was preserved and described as:
    - dapp `https://sigma.money`
    - chain `BNB Chain`
    - `Unknown Signature Type`
    - operation `openOrAddPositionFlashLoanV2`
    - simulation `-0.0030 BNB` and `+1 unknown NFT`
  - Rabby local proof showed Sigma auth/sign history entries with `isSigned: true`
  - Sigma still stayed stuck at `TRANSACTION... 5/6`
- Blocker:
  - the blocker changed from “missing popup” to “popup exists but cannot be actuated reliably”
- Key artifact root:
  - `captures/20260314T041557Z-live-public-20260314/first-loop-20260314T180051Z/`
- Advanced verification frontier:
  - Yes

## 2026-03-15 — `20260315T015651Z-breakthrough-attempt`
- Attempted:
  - re-enter the environment and check whether the pending Sigma/Rabby state was still present the next morning
- Result:
  - only a regular Chrome GitHub tab was present in the observed window state
  - no Sigma tab or Rabby approval window was present in the captured stack
- Blocker:
  - stale session / lost live context; pending approval could not be resumed from this state
- Key artifact root:
  - `captures/20260315T015651Z-breakthrough-attempt/`
- Advanced verification frontier:
  - No

## 2026-03-15 — `20260315T123115Z-part2-run2-peekaboo`
- Attempted:
  - inspect the full Chrome/Rabby window stack first, then run `capture-open-long-boundary` if no pending Rabby surface existed
- Result:
  - pre-click window stack showed the Sigma main window, a non-Rabby Chrome popup/search surface, a tiny Chrome utility window, and a separate Chrome GitHub window on another PID
  - no live Rabby approval / sign / tx-review surface was present before re-entering Sigma
  - tiny-size `/trade` Long remained set to `0.003 BNB` with leverage `3x` and Unlimited Approval OFF
  - clicking `Approve & Open` reproduced Sigma `TRANSACTION... 5/6`
  - a new `Rabby Wallet Notification` window surfaced immediately and was captured
  - the first post-click wallet boundary was Rabby `Unknown Signature Type` on `https://sigma.money` / `BNB Chain`
  - Rabby showed operation `openOrAddPositionFlashLoanV2`, simulation `-0.0030 BNB` and `+1 unknown NFT`, and action buttons `Sign` / `Cancel`
  - no token approval or onchain tx review was confirmed in this run
- Blocker:
  - the hidden `5/6` boundary is now classified as an auth/sign prompt first; the next boundary after an explicitly authorized sign remains unverified
- Key artifact root:
  - `captures/20260315T123115Z-part2-run2-peekaboo/`
- Advanced verification frontier:
  - Yes

## 2026-03-15 — `20260315T131654Z-part2-autonomous`
- Attempted:
  - resume the already-live Rabby sign boundary before touching Sigma again, then explicitly authorize one offchain `Sign` within the standing budget envelope
- Result:
  - pre-action window stack confirmed an already-open `Rabby Wallet Notification` window alongside the Sigma trade tab
  - the live popup again showed:
    - dapp `https://sigma.money`
    - chain `BNB Chain`
    - `Unknown Signature Type`
    - interact contract `0xae2658...0ff87b`
    - protocol `Sigma.Money`
    - operation `openOrAddPositionFlashLoanV2`
    - simulation `-0.0030 BNB` and `+1 unknown`
    - visible actions `Sign` / `Cancel`
  - attempt 1 to click `Sign` by accessible label failed with `ELEMENT_NOT_FOUND`
  - a window-local coordinate click was later assessed as likely mis-targeted because Peekaboo appears to interpret raw coordinates as screen coordinates
  - a corrected global coordinate click on the visible blue `Sign` button still left the popup visually unchanged
  - Sigma remained at `TRANSACTION... 5/6` after the corrected click
  - no ERC20 approval surfaced
  - no onchain tx review surfaced
  - cumulative spend remained `0 USDT / 0 BNB`
- Blocker:
  - `BLOCKED_UI_LOOP` at the visible Long offchain sign boundary: the Rabby `Sign` prompt is on-screen and matches the expected Sigma route, but the visible `Sign` button did not advance state after a corrected direct click
- Key artifact root:
  - `captures/20260315T131654Z-part2-autonomous/`
- Advanced verification frontier:
  - Yes

## 2026-03-15 — `20260315T133545Z-post-manual-sign-state`
- Attempted:
  - inspect Sigma/Rabby/current wallet state immediately after the human manually clicked Rabby `Sign` and `Confirm`, then reclassify Long from the resulting live state before attempting new entry actions
- Result:
  - no live `Rabby Wallet Notification` / approval / tx-review prompt remained visible during inspection
  - Sigma `/trade` had already advanced beyond the old `TRANSACTION... 5/6` frontier into a visible open-position state
  - Browser Relay DOM/text capture showed:
    - route `https://sigma.money/trade`
    - history item `2026-03-15 21:32:57` → `Open Long`
    - visible position summary including `0.01 BNB` size / `$5.91`, `<0.01 BNB` / `$1.90` xPOSITION, `3.11` leverage, and entry/oracle/rebalancing price fields
  - this changed Long from `BLOCKED_UI_LOOP` to a completed-in-app outcome after the human manual sign+confirm
  - `/earn` native capture showed live pools with `User Staked` values at `$0.00` and visible `Deposit / Withdraw / Claim` controls
  - `/mintv2` native capture showed a live-looking mint form, not the old disabled-shell state, with visible `Mint` CTA, `Collateral Balance: 0.07`, `4.01 bnbUSD`, `0.01 BNB` collateral, and `Health: 1.47`
  - one controlled OCR-derived click was attempted on the visible `/mintv2` `Mint` CTA area, but no new Rabby popup or first wallet boundary was captured afterward
  - cumulative confirmed spend changed from pure zero-use to an approximately `~0.003 BNB` opened long path (UI-implied), with `0 USDT` used; exact gas was not visible in Sigma UI and is not claimed here
- Blocker:
  - Long is no longer the blocker; current blockers are:
    - Short still lacks a post-open-state classification
    - `/mintv2` now looks live, but its first wallet boundary still was not cleanly captured in this pass
- Key artifact root:
  - `captures/20260315T133545Z-post-manual-sign-state/`
- Advanced verification frontier:
  - Yes

## 2026-03-15 — `20260315T141611Z-part2-short-mint`
- Attempted:
  - classify Short from the already-open Long state first, then capture the first real `/mintv2` wallet boundary with a tiny manual collateral amount and Unlimited Approval kept OFF
- Result:
  - `/trade` no longer exposed a fresh Long/Short entry form from the live-open-Long state
  - visible `/trade` state showed the existing position summary plus an `Adjust` control, but no visible `Short` entry or `Approve & Open` trade CTA
  - controlled `Adjust` actuation opened an `Adjust Leverage` modal with `Approve & Adjust`, confirming Sigma had transformed the route into position-management for the existing Long rather than exposing a concurrent Short path
  - this gave Short a precise live-state blocker verdict: `NOT_EXPOSED_IN_CURRENT_APP` for fresh concurrent entry while Long is already open
  - `/mintv2` was re-entered cleanly and the top BNB/bnbUSD form was confirmed live with balance `0.07`, Unlimited Approval OFF, and a disabled `Approve & Open` caused by zeroed input fields
  - exact DOM-targeted collateral entry of `0.003` BNB on the top form succeeded and enabled the top `Approve & Open`
  - clicking the enabled top `Approve & Open` produced Sigma `TRANSACTION... 2/6`
  - immediate post-click window-stack inspection surfaced a new Chrome window titled `Rabby Wallet Notification` (window id `1820`, bounds `1252,71 400x800`)
  - this is the first real `/mintv2` wallet boundary; no approval or onchain confirmation was attempted because the popup contents/spender summary could not be read cleanly from the current capture path
  - no new confirmed onchain spend occurred in this pass; cumulative project usage remains approximately `~0.003 BNB` from the earlier opened Long and `0 USDT`, with exact gas still not claimed
- Blocker:
  - not a missing boundary anymore; the remaining limitation is popup inspectability on the live `/mintv2` Rabby surface
- Key artifact root:
  - `captures/20260315T141611Z-part2-short-mint/`
- Advanced verification frontier:
  - Yes

## 2026-03-15 — `20260315T144048Z-position-management-pass`
- Attempted:
  - continue from the already-live `/mintv2` Rabby boundary and start next-phase position-management work without reopening the route
- Result:
  - pre-action Peekaboo window stack showed the Sigma main window plus an already-open `Rabby Wallet Notification`
  - the live Rabby surface was visibly more precise than before:
    - `NFT Approval`
    - origin `https://sigma.money`
    - chain `BNB Chain`
    - approve NFT `#158`
    - approve to `0xae2658...0ff87b`
    - protocol `Sigma.Money`
    - interacted before `Yes`
    - visible fee estimate about `$0.0018` and approximately `0.0…2797 BNB` (truncated by UI)
  - a label-based `Sign` click did not resolve the button
  - one direct visible-coordinate click aimed at the blue `Sign` button landed on macOS `loginwindow`, not Chrome
  - immediate full-screen capture proved the host was on the macOS lock screen and `loginwindow` was the active app
  - no approval was executed and no new onchain spend was confirmed
  - read-only browser relay remained reachable and yielded useful CLI-account-fetch clues:
    - current page still at `/mintv2` with `TRANSACTION... 2/6`
    - visible position stats `Health 1.47`, `4.01 bnbUSD`, `0.01 BNB` collateral
    - live no-auth entry-price endpoint:
      - `/api/position/getEntryPrice/no-auth?pool=0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb&positionId=158&owner=0xOWNER_ADDRESS`
    - live no-auth position-history endpoint:
      - `/api/user-event/long-short-list/no-auth?...position=158&pool=0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb&owner=0xOWNER_ADDRESS`
    - current frontend bundle includes live pool constants beyond the original local ABI cache, including `0x31c4...70fb`, `0x6C83...1855`, and `0x7a97...ed91`
- Blocker:
  - `NEEDS_HUMAN_ACTION` / host lock screen: the live Rabby approval still exists, but clicks are intercepted by macOS `loginwindow` until the machine is unlocked
- Key artifact root:
  - `captures/20260315T144048Z-position-management-pass/`
- Advanced verification frontier:
  - Slightly; no live position-management action completed, but the exact pending approval and the practical CLI account-fetch path are both clearer now

---

## Net takeaways from the ledger

What is now solid:
- backend and decode foundations are real
- BNB RPC / NodeReal-compatible live read validation is real
- read-only current-app evidence exists for `/trade`, `/earn`, and `/mintv2`
- connected Sigma state and Rabby connect flow are real
- corrected tiny-size Long and Short both reach Sigma `TRANSACTION... 5/6`
- the hidden wallet boundary behind trade `5/6` is real and reproducibly surfaces as a Rabby `Unknown Signature Type` / `Sign` prompt for `openOrAddPositionFlashLoanV2`
- the human manual Rabby `Sign` + `Confirm` advanced Long into a visible open-position state back in Sigma
- Short is now truthfully classified from the live-open-Long state as a transformed/non-exposed path rather than an assumed mirror of Long
- `/earn` is now truthfully classified as live-but-`BLOCKED_NO_POSITION` in the current state
- `/mintv2` now reaches a real first wallet boundary: Sigma `TRANSACTION... 2/6` plus a surfaced `Rabby Wallet Notification` window after enabling the top form with `0.003` BNB collateral and Unlimited Approval OFF

What is still missing:
- a cleaner inspectability path for live Rabby popup contents/spender summaries when the Chrome extension window goes blank under native capture
- optional next-phase live coverage beyond the Part 2 gate, such as close / reduce / leverage-adjust and deeper mint approval / tx-review inspection

What should not be repeated:
- MAX-like sizing
- broad surface hopping once a live wallet boundary has surfaced
- repeated popup clicks without first checking the actual window stack


## 2026-03-15 — `20260315T151008Z-position-management-resume-unlocked`
- Attempted:
  - resume next-phase position-management from the already-visible focused Rabby popup on the unlocked Mac, without restarting Sigma
- Result:
  - the live `NFT Approval` for token `#158` to `0xae2658...0ff87b` was continued successfully
  - Sigma advanced from `TRANSACTION... 2/6` to `5/6`
  - a second Rabby boundary (`Unknown Signature Type`, `Pay BNB 0.003 BNB`) was continued successfully
  - popup closed and Sigma returned to `/mintv2` with a confirmed live mint position (`4.01 bnbUSD`, `0.01 BNB`, health about `1.96-1.97`)
  - `/trade` `Adjust` was verified via DOM click, exposing an `Adjust Leverage` modal but not a clean standalone add-margin route
  - `/mintv2` `Close` was verified via DOM click, exposing `Approve & Close`, but repay balance was `0.00 bnbUSD`
- Blocker:
  - leveraged add-margin / close are not cleanly separated on the current `/trade` surface; mint close is blocked by zero repay balance
- Spend:
  - new confirmed principal used: `0.003 BNB`
  - cumulative confirmed principal used: about `0.006 BNB`
  - additional gas visible but not exact enough to claim precisely
- Key artifact root:
  - `captures/20260315T151008Z-position-management-resume-unlocked/`
- Advanced verification frontier:
  - Yes

## 2026-03-15 — `20260315T233611Z-mintclose-earn-governance-pass`
- Attempted:
  - continue live Sigma testing with a bounded `/mintv2` open, then re-check mint close / repay, then inspect/test `/earn` and `/governance`
- Result:
  - `/mintv2` open was re-entered on the visible live surface with `0.003 BNB` collateral and Unlimited Approval turned OFF
  - the mint flow completed a readable Rabby chain:
    - `NFT Approval`
    - approve NFT `#158`
    - approve to `0xae2658...0ff87b`
    - protocol `Sigma.Money`
    - chain `BNB Chain`
    - visible fee estimate about `$0.0018` and approximately `0.0…2797 BNB` (truncated in UI)
    - second boundary `Unknown Signature Type`
    - interact contract `0xae2658...0ff87b`
    - protocol `Sigma.Money`
    - `Pay BNB 0.003 BNB`
    - visible fee line about `$0.02` and approximately `0.0…311 BNB` (truncated in UI)
  - after the popup chain closed, Sigma returned to `/mintv2` with the live mint card still showing `4.01 bnbUSD`, `0.01 BNB`, and improved health around `2.45-2.46`
  - `/mintv2` `Close` was re-checked after a refresh and still showed repay `Balance: 0.00`; `Approve & Close` remained disabled, so mint close is still blocked
  - `/earn` is now truthfully live and actionable at least to the first wallet boundary:
    - visible pools include `bnbUSD/USDT Stability Pool - Lista-Pangolins Vault`, `bnbUSD/USDT Stability Pool - Lista Vault`, `bnbUSD Curve AMM Pool`, and `SIGMA Curve AMM Pool`
    - first stability-pool deposit accepted a bounded `1 USDT` input with Unlimited Approval turned OFF
    - live Rabby prompt surfaced as `Revoke Token Approval` for `USDT` on `BNB Chain`
    - revoke-from spender shown as `0xde1bdd...eacea7`
    - protocol `Sigma.Money`
    - visible fee estimate about `$0.0009` and approximately `0.0…1311 BNB` (truncated in UI)
    - after sign+confirm, Sigma remained stuck on in-app `TRANSACTION... 1/3` with no next Rabby popup re-surfacing during the wait window
  - `/governance` hidden-route probing found that `https://sigma.money/governance` loads the Sigma app shell but renders a black blank page with empty body text
  - console on the governance route showed JS activity (`GaugeContracts`, `VeFXNHolders`, repeated `sp undefined`) plus `WalletConnect Core is already initialized`, but no visible governance UI ever appeared
- Blockers:
  - mint close remains blocked by `bnbUSD` repay balance `0.00` even after the bounded mint/open path completed
  - earn deposit progression stalls at in-app `TRANSACTION... 1/3` after the revoke step; no follow-on wallet boundary surfaced in the observation window
  - governance route loads but stays blank / non-rendered
- Spend:
  - new confirmed principal used in this pass: `0.003 BNB`
  - cumulative confirmed principal used: about `~0.009 BNB`
  - additional visible gas was present on mint and earn prompts, but the exact BNB values were truncated by Rabby UI and are not claimed precisely here
- Key artifact root:
  - `captures/20260315T233611Z-mintclose-earn-governance-pass/`
- Advanced verification frontier:
  - Yes; mint post-open behavior, earn first wallet boundary, and governance blank-route behavior are now all truthfully classified


## 2026-03-16 — `20260316T021136Z-autonomous-nextphase`
- Attempted:
  - continue next-phase Sigma work from the current live state without restarting the whole flow, focusing on mint close reality, leverage-management exposure, earn re-check, governance route classification, and repo/doc continuity
- Result:
  - `/mintv2` live state was recovered with the existing mint position still visible
  - `/mintv2` `Close` was re-checked and still showed `Repay Balance: 0.00`; `Approve & Close` remained disabled
  - Sigma's `add bnbUSD to wallet` helper was explicitly tested from the live close surface:
    - opened `Rabby Wallet Notification`
    - popup title `Add custom token to Rabby`
    - token `bnbUSD`
    - popup showed `My Balance 0 bnbUSD`
    - after interaction, Rabby tooltip read `Token has been supported on Rabby`
    - clicking `Add` closed the popup successfully
  - conclusion from the wallet-add check:
    - wallet watch-asset / token-support handling is real
    - but it did not itself resolve the visible Sigma close repay balance blocker
  - `/trade` still showed a live leveraged position summary with only `Adjust` visible on the surface; no separate close or add-margin CTA was surfaced in this pass
  - `/earn` still rendered live pools and deposit buttons, but after Chrome relay detachment there was not enough stable DOM/AX control to truthfully replay the bounded deposit to the prior stall point
  - `/governance` was re-verified as a blank route in two environments:
    - live Chrome page remained black / empty
    - managed browser returned HTTP 200, emitted JS logs, and exposed `#root`, but body text stayed empty and root content reduced to injected RainbowKit style markup without visible governance UI
- Blockers:
  - mint close still blocked by `Repay Balance: 0.00` on Sigma's close surface even after explicit bnbUSD wallet-add handling
  - earn replay in this pass was blocked by relay loss + lack of stable AX/JS hooks, so the prior `1/3` stall could not be reclassified truthfully beyond the earlier evidence
  - governance remains non-rendered / blank despite route availability and JS boot
- Spend:
  - new confirmed principal used in this pass: `0 BNB`
  - new confirmed USDT principal used in this pass: `0 USDT`
  - cumulative confirmed principal used remains about `~0.009 BNB`
- Key artifact root:
  - `captures/20260316T021136Z-autonomous-nextphase/`
- Advanced verification frontier:
  - Yes; mint watch-asset behavior and governance blank-route status are now more tightly classified

## 2026-03-16 — `20260316T025048Z-earn-relay-recovery`
- Attempted:
  - narrow Browser Relay recovery pass focused only on the unresolved `/earn` bounded `1 USDT` deposit and the prior `TRANSACTION... 1/3` stall
- Result:
  - Browser Relay truth was restored on the live Chrome Sigma tab and `/earn` was re-entered directly
  - first pool targeted: `bnbUSD/USDT Stability Pool - Lista-Pangolins Vault`
  - bounded input remained `1 USDT`
  - Unlimited Approval was explicitly switched OFF before submission
  - Sigma reproduced the old in-app stall at `TRANSACTION... 1/3`, but this pass proved it was **not** a pure frontend dead end:
    - hidden Rabby popup surfaced as `Revoke Token Approval`
    - token `USDT`
    - chain `BNB Chain`
    - spender / revoke-from `0xde1bdd...eacea7`
    - protocol `Sigma.Money`
  - after the revoke boundary was continued, Rabby surfaced the next hidden boundary:
    - `Token Approval`
    - approve token `1.0000 USDT`
    - approve to `0xde1bdd...eacea7`
    - protocol `Sigma.Money`
    - Unlimited approval remained OFF
  - after approval confirm, Sigma advanced from `1/3` to `2/3`
  - at `2/3`, Rabby surfaced the deposit simulation / execution boundary:
    - simulation results showed `-1.0000 USDT`
    - simulation results showed `+0.9941 sigmaSP1`
    - operation `deposit`
    - protocol `Sigma.Money`
    - interact contract `0xde1bdd...eacea7`
  - after the final Rabby confirm, the popup closed and Sigma returned to the earn page with the transaction overlay cleared
  - first pool displayed Gauge TVL increasing from about `1,324.61` to about `1,325.61`
  - the visible summary still showed `User Staked 0.00`, consistent with this bounded pass completing the deposit leg rather than a separate stake leg
- Blockers:
  - the prior `/earn` `1/3` stall is no longer a blocker classification; it is now explained as a hidden popup chain
  - withdraw / claim are still not upgraded by this pass
- Spend:
  - new confirmed principal used in this pass: `1 USDT`
  - new confirmed BNB principal used in this pass: `0 BNB`
  - cumulative confirmed principal used: about `~0.009 BNB` plus `1 USDT`
  - Rabby displayed gas estimates across the popup chain, but exact confirmed gas spend is not claimed beyond screenshot evidence
- Key artifact root:
  - `captures/20260316T025048Z-earn-relay-recovery/`
- Advanced verification frontier:
  - Yes; `/earn` bounded deposit is now truthfully classified as live and completed, and the old `1/3` stall is reclassified as a hidden wallet boundary rather than a frontend-only failure

## 2026-03-16 — `20260316T034228Z-sigma-continuation`
- Attempted:
  - continue from the now-proven `/earn` deposit state and reduce remaining ambiguity across earn post-deposit classification, trade management exposure, mint close truth, governance rendering, and read-only CLI continuity
- Result:
  - `/earn` first-pool post-deposit state is now explicitly classified from the live surface:
    - first pool `bnbUSD/USDT Stability Pool - Lista-Pangolins Vault`
    - nested first-pool `Stake` tab shows `Balance: 0.99 SigmaSP1`
    - nested first-pool `Withdraw` tab shows `Withdraw / Unstake`, `Balance: 0.99`, `Estimated Receive bnbUSD: 0.00`, `Estimated Receive USDT: 0.00`, plus the visible instant-vs-delayed wording:
      - `Charge me a 1% fee to receive funds immediately`
      - `Or you can withdraw bnbUSD+USDT after 60 minutes`
    - first-pool `Claim` tab shows `xSIGMA rewards: 0.00` with disabled `Claim`
    - therefore the completed bounded deposit created an **unstaked** pool receipt balance (`0.99 SigmaSP1`) and did not auto-stake
  - `/trade` management classification tightened:
    - live long position still visible around `$10.17` size / `1.65x`
    - clicking `Adjust` opens `Adjust Leverage`
    - surfaced controls include leverage presets, slippage choices, preview math, and CTA `Approve & Adjust`
    - no explicit visible `Add Margin`, `Reduce`, or `Close Position` control was surfaced on the current management path
  - `/mintv2` close was re-checked again:
    - top BNB / bnbUSD card still shows the live mint position
    - close surface still shows `Repay Balance: 0.00`
    - CTA remains disabled as `Approve & Close`
  - read-only CLI continuity was reconfirmed by rerunning:
    - `./sigma account status --owner 0xOWNER_ADDRESS --bnb-rpc-url https://bsc-dataseed.binance.org/ --include-history --exclude-empty-pools`
    - output still confirms one active position in pool `0x31c464cfe506d44ceaa86c05cdbb94b5c94f70fb`, token id `158`, plus no-auth entry-price/history enrichments and `warnings = []`
  - `/governance` route was re-investigated:
    - route resolves to `https://sigma.money/governance`
    - after load + wait, `document.body.innerText` and `#root.innerText` remained empty
    - route still behaves as a blank / non-rendered page even though client/runtime scaffolding and console activity are present
- Blockers:
  - mint close remains blocked by zero visible repay `bnbUSD` balance on the live close surface
  - trade management still does not expose a clean explicit add-margin or close-position control beyond `Adjust Leverage`
  - governance remains visually blank / non-rendered
- Spend:
  - new confirmed principal used in this pass: `0 BNB`
  - new confirmed USDT principal used in this pass: `0 USDT`
  - cumulative confirmed principal used remains about `~0.009 BNB + 1 USDT`
- Key artifact root:
  - `captures/20260316T034228Z-sigma-continuation/`
- Advanced verification frontier:
  - Yes; earn post-deposit state is now upgraded from partial deposit proof to a concrete unstaked `SigmaSP1` / withdraw / claim classification

## 2026-03-16 — `contract-level-mint-close-mapping`
- Attempted:
  - answer the mint-close blocker from chain state + ABI semantics instead of more UI replay
  - add the next direct read-only CLI slice that exposes the answer
  - restructure governance in the CLI as a namespace umbrella over `xsigma`, `vote`, and `incentivize`
- Result:
  - direct read-only mint-close state now proves:
    - owner wallet `bnbUSD` balance is `0`
    - owner wallet `bnbUSD` allowance to observed live router `0xae2658f23176f843af11d2209dbd04cffc0ff87b` is `0`
    - live position `158` in pool `0x31c464cfe506d44ceaa86c05cdbb94b5c94f70fb` currently reports `rawDebts = 4.010571150970316112`
    - current NFT approval state to the observed router is also clear / false
  - decoded historical mint txs now tighten the semantic map:
    - initial mint/open tx `0x3ef4072cf992dd2a3cf89e1e807ece7b571f3eda738c5239765fe13feafbd097` created explicit debt via `PoolManager.Operate(... deltaDebts = 4.010571150970316112)`
    - the same tx minted `bnbUSD` to the observed router and routed it onward rather than leaving it as spendable wallet balance
    - later txs `0x53611ccbb51aab2a1fca9073b400c0fe17f64ca2cfb20084b4e14496553a94a2` and `0xd79307353d5cda0f7064d0f70a5221209d9d318b5bd88619ca54723472c10313` only added collateral with `deltaDebts = 0`
  - practical semantic conclusion is now stronger:
    - mint close is wallet-repay-asset dependent
    - the visible Sigma `Repay Balance: 0.00` blocker is consistent with real wallet state
    - repeated BNB collateral adds do not themselves satisfy close repay requirements
  - repo/code additions landed:
    - new note `MINT_CLOSE_CONTRACT_MAP_2026-03-16.md`
    - new command `sigma account mint-close-readiness`
    - new CLI namespace scaffolding:
      - `sigma governance overview`
      - `sigma governance xsigma ...`
      - `sigma governance vote ...`
      - `sigma governance incentivize ...`
- Blockers:
  - exact close tx selector / router-wrapper path is still not fully captured
  - final spender/min-coll/fee math for direct write commands remains unproven until a live close preview/tx is captured
- Spend:
  - new confirmed principal used in this pass: `0 BNB`
  - new confirmed USDT principal used in this pass: `0 USDT`
- Key artifact/doc roots:
  - `MINT_CLOSE_CONTRACT_MAP_2026-03-16.md`
  - live historical txs:
    - `0x3ef4072cf992dd2a3cf89e1e807ece7b571f3eda738c5239765fe13feafbd097`
    - `0x53611ccbb51aab2a1fca9073b400c0fe17f64ca2cfb20084b4e14496553a94a2`
    - `0xd79307353d5cda0f7064d0f70a5221209d9d318b5bd88619ca54723472c10313`
- Advanced verification frontier:
  - Yes; the mint-close question is no longer just a UI ambiguity and now has a chain-state-backed answer

## 2026-03-16 — `earn-withdraw-process-to-mint-close-check`
- Attempted:
  - unwind the visible first-pool `0.99 SigmaSP1` earn receipt on `/earn`
  - reclaim usable assets if possible
  - immediately re-check `/mintv2` close for repay readiness
- Result:
  - first pool `bnbUSD/USDT Stability Pool - Lista-Pangolins Vault` was driven from the visible unstaked receipt state through a real withdraw submission
  - bounded amount entered was `0.99` without using MAX
  - live pre-submit estimate settled to:
    - `0.80 bnbUSD`
    - `0.20 USDT`
  - Rabby popup chain was completed on the live surface:
    - offchain `requestRedeem` signature for `https://sigma.money`
    - follow-up confirm boundary
    - popup showed protocol `Sigma.Money`, operation `requestRedeem`, contract `0xde1bdd...eacea7`, and simulation `No balance change`
  - the resulting live state was **not** immediate wallet asset return
  - Sigma created a timed withdraw banner instead:
    - `Withdraw Process - Lista-Pangolins Vault`
    - `0.99 bnbUSD Stability Pool Tokens can be withdrawn after 2026-03-16 16:52:29`
    - `You will receive 0.79 bnbUSD and 0.20 USDT.`
  - `/mintv2` close was re-checked after this change and still showed:
    - `Repay Balance: 0.00`
    - CTA `Approve & Close`
  - therefore wallet-held / usable repay `bnbUSD` did **not** appear in this pass
- Blockers:
  - the chosen path materialized as delayed redeem / withdraw-process creation rather than immediate wallet-held asset return
  - mint close remains blocked by zero repay `bnbUSD` on the live close surface
- Spend:
  - new confirmed principal used in this pass: `0 BNB`
  - new confirmed USDT principal used in this pass: `0 USDT`
  - cumulative confirmed principal used remains about `~0.009 BNB + 1 USDT`
  - exact gas remains not claimed precisely
- Key artifact root:
  - `captures/20260316T071900Z-earn-unwind-mint-close-pass/`
- Advanced verification frontier:
  - Yes; earn unwind semantics are now upgraded from hypothetical receipt handling to a proven live `requestRedeem` / delayed-withdraw process with exact promised outputs and unlock time

## 2026-03-16 — `earn-unlock-claim-then-mint-close-pass`
- Attempted:
  - wait through the documented earn delayed-withdraw unlock boundary (`2026-03-16 16:52:29 Asia/Shanghai`)
  - complete the claim boundary from `/earn`
  - verify whether usable wallet-held `bnbUSD` actually appears
  - retry `/mintv2` close immediately if repay balance unlocks
- Result:
  - delayed withdraw / claim boundary **was completed** from the `Withdraw Process - Lista-Pangolins Vault` banner
  - Rabby claim popup showed Sigma redeem effects:
    - `-0.9900 sigmaSP1`
    - `+0.7952 bnbUSD`
    - `+0.2008 USDT`
    - protocol `Sigma.Money`
    - redeem contract shown as `0xde1bdd...eacea7`
  - claim signature + confirm were completed successfully
  - post-claim Sigma `/earn` wallet balances updated to:
    - `0.80 bnbUSD`
    - `49.19 USDT`
  - this is the first live proof that wallet-held / usable `bnbUSD` did appear after the delayed redeem matured
  - `/mintv2` close immediately advanced from prior dead-end state to a real repayable surface:
    - `Repay Balance: 0.80`
    - range `0.00 ~ 3.03`
    - bounded manual repay test entered: `0.79 bnbUSD`
    - `Approve & Close` became enabled with Unlimited Approval still visually OFF
  - however Rabby then requested a **max / unlimited** token approval for close:
    - approve token display `115,792,089,237,316...`
    - spender `0xae2658f23176f843af11d2209dbd04cffc0ff87b`
    - popup still showed wallet balance `0.7952 bnbUSD`
  - max approval was **not signed**
  - repeated attempts to reduce / edit the popup allowance did not succeed on the live surface
  - therefore mint close did not advance past the approval boundary in this pass
- Blockers:
  - Sigma close became actionable only after the claim, but Rabby demanded a max allowance despite Sigma `Unlimited Approval` being OFF
  - stopping condition hit: unexpected approval shape relative to the standing envelope / approval preference
- Spend:
  - new confirmed principal used in this pass: `0 BNB`
  - new confirmed USDT principal used in this pass: `0 USDT`
  - cumulative confirmed principal remains about `~0.009 BNB + 1 USDT`
  - additional gas observed this pass:
    - claim popup estimate about `0.0045 BNB` (signed)
    - close approval popup estimate about `0.0018 BNB` (not signed)
- Key artifact root:
  - `captures/20260316T164411Z-earn-unlock-claim-mint-close/`
- Advanced verification frontier:
  - Yes; claim maturity -> wallet-held `bnbUSD` -> mint-close reactivation is now proven live
  - new live blocker is narrowed to the close approval shape, not to repay-balance absence

## 2026-03-16 — `cli-semantics-encoding-pass`
- Attempted:
  - encode the newly clarified mint-close semantics directly into the CLI without overclaiming the live write path
  - add explicit approval-policy persistence/support
  - make the read-side CLI able to express partial repay / partial close truthfully
- Result:
  - `sigma config` now persists approval policy with three modes:
    - `unlimited`
    - `exact`
    - `custom`
  - `sigma plan mint-close` now reports:
    - partial repay / partial close semantics
    - wallet-held `bnbUSD` repay requirement
    - resolved approval policy and desired allowance target
    - explicit warning that live close still requested max approval in Rabby despite Sigma `Unlimited Approval` being visually OFF
  - `sigma account mint-close-readiness` now accepts:
    - `--repay-amount`
    - optional `--target-ltv`
    - optional `--withdraw-amount`
  - the readiness output now models:
    - remaining debt after repay
    - max modeled withdrawable collateral under a target/current LTV guardrail
    - resulting LTV for the modeled partial close
    - active approval policy and whether current allowance satisfies that policy
  - `sigma account bnbusd-trace` now carries the resolved approval-policy context too
- Blocker:
  - exact/custom approval is now first-class in CLI state, but the live mint-close write path still is not proven to honor it end-to-end
- Validation:
  - `python3 -m compileall sigma_operator`
  - `./sigma config show`
  - `./sigma config init --approval-policy custom --approval-amount 1.25` (under a temporary config path)
  - `./sigma plan mint-close -- --repay-amount 0.79`
  - `./sigma account mint-close-readiness --owner 0xOWNER_ADDRESS --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --bnb-rpc-url https://bsc-dataseed.binance.org/ --repay-amount 0.79`
- Spend:
  - new confirmed principal used in this pass: `0 BNB`
  - new confirmed USDT principal used in this pass: `0 USDT`
- Advanced verification frontier:
  - Yes; the CLI now encodes the clarified semantics directly instead of leaving them only in notes and handoff prose


## 2026-03-16 — `20260316T103136Z-remaining-blockers-closure`
- intent:
  - close as many remaining Sigma blockers as possible from the current documented frontier and leave a tighter repo-truthful handoff
- what was newly closed / tightened:
  - current frontend bundle evidence showed mint-close is **not** max-approval-only by design
  - close variants initialize `Unlimited Approval` ON by default, use max approval when ON, and contain an exact-approval branch when OFF
  - `/trade` still exposed only `Adjust` on the visible management surface
  - `/dashboard`, `/statistics`, `/xsigma`, `/vote`, and `/incentivize` all rendered live in the attached Chrome session
- remaining blocker reduced exactly to:
  - live mint-close finite approval is still not proven end to end because the prior wallet popup surfaced max approval despite the Sigma toggle appearing OFF
  - this is now a UI/popup-path mismatch blocker, not a blanket “no finite-approval path exists” blocker
- principal / tx effect:
  - no new confirmed approvals
  - no new confirmed onchain txs
  - no new principal deployed
- artifacts:
  - `captures/20260316T103136Z-remaining-blockers-closure/`

## 2026-03-16 — `20260316T110659Z-live-mint-close-proof`
- Attempted:
  - do the fresh repayable mint-close proof step from the live desktop state, checking first for any lingering SP1 claim/withdraw popup before taking further action
- Result:
  - native Chrome window-stack inspection found a separate already-open window titled `Rabby Wallet Notification` before any new Sigma interaction
  - after forcing focus to that window, it resolved to a real lingering Rabby close-approval popup, **not** an SP1 claim/withdraw boundary
  - popup contents were captured live as:
    - origin `https://sigma.money`
    - `Token Approval`
    - chain `BNB Chain`
    - approve token `115,792,089,237,316...`
    - wallet balance `0.7952 bnbUSD`
    - approve to `0xae2658...0ff87b`
    - protocol `Sigma.Money`
  - main Sigma Chrome tab was simultaneously sitting on `https://sigma.money/incentivize`, not `/mintv2`
  - no new click path was needed to prove the key remaining blocker again
- Blocker:
  - fresh live proof still shows a **max / unlimited** `bnbUSD` approval popup on the repayable close path, so the bounded approval could not be signed
- Spend:
  - new confirmed principal used in this pass: `0 BNB`, `0 USDT`
  - cumulative confirmed principal used remains about `~0.009 BNB + 1 USDT`
- Key artifact root:
  - `captures/20260316T110659Z-live-mint-close-proof/`
- Advanced verification frontier:
  - Slightly; it freshly proves the lingering popup state and confirms the blocker persists without needing to re-drive the full close path

## 2026-03-16 — `20260316T112241Z-fresh-mint-close-replay`
- Attempted:
  - re-drive `/mintv2` close from a fresh live state after the user canceled the stale max-approval popup, while keeping `Unlimited Approval` OFF and using bounded wallet-held `bnbUSD`
- Result:
  - returned Sigma to `https://sigma.money/mintv2`, switched the BNB/bnbUSD management widget to `Close`, and verified the close-side `Unlimited Approval` switch had defaulted back ON
  - toggled `Unlimited Approval` OFF, entered bounded repay `0.79` bnbUSD, and triggered `Approve & Close`
  - fresh Rabby sequence was captured and completed end-to-end on the exact branch:
    - `Revoke Token Approval` for `bnbUSD` to `0xae2658...0ff87b` (Sigma.Money / BNB Chain)
    - **finite** `Token Approval` for exact `0.7900` bnbUSD, wallet balance shown `0.7952 bnbUSD`, same spender `0xae2658...0ff87b`
    - `NFT Approval` for `#158` to the same spender
    - execution popup (`Unknown Signature Type`) with simulation results:
      - `-0.7900 bnbUSD`
      - `-1 Sigma BNB Long`
      - `+1 Sigma BNB Long`
  - after the final confirm, the Rabby popup disappeared and Sigma refreshed to a post-close state showing:
    - Health `3.14`
    - Size `3.22` bnbUSD
    - Collateral `0.01` BNB
    - Repay balance `0.01` bnbUSD
    - Range `0.00~2.25`
    - Rebalancing price `$244.71`
- Frontier moved materially:
  - yes — the previously stale max popup was **not** the final truth; a fresh replay with `Unlimited Approval` OFF resolved through a revoke-first exact branch and surfaced a brand-new bounded approval for **`0.7900` bnbUSD**, which was then completed successfully
- Spend:
  - new confirmed principal used in this pass: `0 BNB`, `0 USDT`
  - cumulative confirmed principal used remains about `~0.009 BNB + 1 USDT`
- Key artifact root:
  - `captures/20260316T112241Z-fresh-mint-close-replay/`
- Notes:
  - `notes.md` and `summary.json` were written under the capture root

## 2026-03-16 — `20260316T114949Z-post-close-verification-pack`
- Attempted:
  - run the full read-only verification pack immediately after the successful fresh `/mintv2` close replay
  - verify Sigma history, refreshed mint position state, current account/portfolio state, and repo truth
- Result:
  - direct CLI + no-auth verification landed under a fresh capture root with `account-status`, `account-history`, `mint-close-readiness`, `stability-pools`, `bnbusd-trace`, and tx decode artifacts
  - Sigma no-auth history for position `158` now returns `4` items and records the replay tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` as type `CLOSED`
  - the same verification pass proves the position is **still live** onchain and in the current portfolio:
    - token / position id `158`
    - `rawColls = 0.014954999999999998 BNB`
    - `rawDebts = 3.220571150970316111 bnbUSD`
    - wallet-held `bnbUSD = 0.005238383559755168`
  - decode of the replay tx proves the exact effect was:
    - wallet -> router transfer `0.79 bnbUSD`
    - router burn of `0.79 bnbUSD`
    - `PoolManager.Operate` with `deltaColls = 0`, `deltaDebts = -0.79`
    - NFT `#158` round-tripped wallet -> router -> wallet
  - practical truth tightened materially:
    - the successful replay was a **partial repay / partial close** on the same position NFT
    - it was **not** a terminal full close
    - Sigma history is truthful only at the coarse “close-side action happened” level; if `CLOSED` is read as “position is gone,” it now overstates reality
- Blocker:
  - no blocker for this verification pack itself; the remaining open question is whether the next objective is another partial repay, a true collateral-withdraw/full-close path, or unrelated next-phase management work
- Spend:
  - new confirmed principal used in this pass: `0 BNB`, `0 USDT`
  - cumulative confirmed principal used remains about `~0.009 BNB + 1 USDT`
- Key artifact root:
  - `captures/20260316T114949Z-post-close-verification-pack/`
- Advanced verification frontier:
  - Yes; this pass converts the successful replay from a UI-level claim into a direct chain/account/history-verified partial-close result


## 2026-03-17 — `20260317T001447Z-priority-ab-live-run`
- Attempted:
  - run the bounded Priority A -> Priority B verification sequence in current live state
  - capture hard before-state evidence first
  - fully close the existing long using the safest actually-supported payout asset path
  - only proceed to mint close if Priority A completed and could be verified
- Result:
  - before-state was captured from read-only CLI + live UI:
    - owner `0xOWNER_ADDRESS`
    - active pool `0x31c464cfe506d44ceaa86c05cdbb94b5c94f70fb`
    - active position/NFT `158`
    - pre-run wallet balances:
      - `BNB = 0.06677271705`
      - `WBNB = 0`
      - `USDT = 49.19075703870576`
      - `bnbUSD = 0.005238383559755168`
    - pre-run mint-close readiness still showed debt `3.220571150970316111 bnbUSD` and no full wallet-held repay asset
  - `/trade` management truth tightened materially:
    - collapsed page still surfaces `Adjust`
    - `Adjust` opens `Adjust Leverage` with a `1.00x` floor
    - expanding the long card exposes a distinct `Close` tab
    - live payout selector options observed: `BNB`, `USDT`, `WBNB`, `bnbUSD`
  - bounded full-close setup was achieved on the live surface:
    - xPOSITION input `0.014954999999999998`
    - payout asset tested to ready state on `USDT`
    - preview showed `Receive 6.807260 USDT`
    - `Minimum Receive 6.72 USDT`
    - `Unlimited Approval` switched OFF before submission
  - clicking `Approve & Close` advanced Sigma to the in-app overlay `TRANSACTION... 2/6`
  - no transaction hash can be claimed from this pass, because the Rabby confirmation boundary was not surfaced back as a controllable browser target/tab in this runtime
- Blockers:
  - wallet-popup control mismatch remains the live blocker
  - Priority A therefore started but did not finish
  - Priority B was not attempted because Priority A could not be verified complete
- Spend:
  - new confirmed principal used in this pass: `0 BNB`
  - new confirmed USDT principal used in this pass: `0 USDT`
  - new confirmed onchain approvals/txs in this pass: `0`
- Key artifact root:
  - `captures/20260317T001447Z-priority-ab-live-run/`
- Advanced verification frontier:
  - Partially; the explicit trade close path is now proven as a real surfaced UI path, but end-to-end close execution remains blocked at the wallet-confirmation boundary

## 2026-03-17 — `20260317T0033-post-manual-sign-verify`
- Attempted:
  - continue immediately after the user manually signed the previously blocked Rabby close prompts
  - verify whether Priority A actually landed onchain before attempting any mint-close follow-up
  - recompute Priority B only if the resulting live state still contained mint debt/collateral
- Result:
  - fresh post-sign read-only verification proved Priority A completed onchain
  - the verified close tx hash is:
    - `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092`
  - Sigma no-auth history now shows a newest `CLOSED` row at `2026-03-17 00:32:30` for that tx on position `#158`
  - direct account-status verification shows the same NFT shell `#158` is still wallet-owned, but its economic state is now zeroed:
    - `rawColls = 0`
    - `rawDebts = 0`
  - tx decode + wallet-delta evidence prove the final close effect precisely:
    - full collateral removed: `0.014954999999999998 BNB`
    - full debt burned: `3.2205711509703163 bnbUSD`
    - payout asset delivered to the wallet: `USDT`
    - exact wallet increase: `6.792825626759770802 USDT`
  - post-close wallet state was verified directly:
    - `BNB = 0.06672528805`
    - `WBNB = 0`
    - `USDT = 55.98358266546553`
    - `bnbUSD = 0.005238383559755168`
  - residual stability-pool state also remained visible and separate from the closed trade:
    - `SigmaSP1 = 0.004083641208352667` shares
    - preview-estimated value `= 0.003280270942998363 bnbUSD + 0.000828100723359291 USDT`
- Priority B consequence:
  - not executed, because it was no longer necessary
  - once Priority A was verified complete, there was no remaining mint debt/collateral on position `#158` to close
- Blocker:
  - none for the bounded Priority A -> Priority B objective itself
- Spend:
  - additional direct wallet delta observed in this pass relative to the pre-submit capture:
    - `USDT +6.792825626759770802`
    - `BNB -0.000047429` (gas)
    - `WBNB +0`
    - `bnbUSD +0`
- Key artifact root:
  - `captures/20260317T0033-post-manual-sign-verify/`
- Advanced verification frontier:
  - Yes; this pass resolves the previously blocked close attempt into a full onchain-verified terminal close with exact asset receipt and final state proof
