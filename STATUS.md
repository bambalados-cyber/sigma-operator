# STATUS

## Current blocker milestone

The active blocker milestone is now:

**Priority A is verified complete onchain — the prior Long is fully closed and Priority B is no longer applicable**

Part 2 is already surpassed. The current frontier is no longer “can Sigma close replay at all?” or even “did the trade close actually complete?” The verified state is now “the trade close did complete; the remaining work is packaging the final truth cleanly and deciding what post-close follow-up, if any, matters.”

Current source-of-truth pack:
- `PART2_PLAN.md`
- `PART2_MILESTONES_CHECKLIST.md`
- `PART2_TASKS.md`
- `PART2_OPERATOR_RUN_SEQUENCE.md`
- `PART2_CLI_TESTING_GATE.md`

What is already true:
- backend / BNB RPC validation is real
- current-app read-only evidence exists for `/trade`, `/earn`, and `/mintv2`
- the earlier `/mintv2` exact-approval replay tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` is still verified as a **partial repay** only (`deltaColls = 0`, debt reduced by `0.79 bnbUSD`)
- the later explicit `/trade` close path is now verified complete onchain via tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092`
- direct read-only verification now proves the former live position `#158` is economically closed:
  - `rawColls = 0`
  - `rawDebts = 0`
- the position NFT `#158` still exists and is still wallet-owned, but it is now a zero-state shell rather than a live economic position
- decode + wallet-delta evidence for the verified trade close now shows:
  - full debt burn: `3.2205711509703163 bnbUSD`
  - full collateral removal: `0.014954999999999998 BNB`
  - exact received asset: `USDT`
  - exact received amount: `6.792825626759770802 USDT`
- live `/trade` management truth is now complete enough to classify the surfaced close path honestly:
  - the collapsed page summary still starts at `Adjust`
  - expanding the long card exposes a distinct `Open` / `Close` widget
  - live `Adjust Leverage` bottoms at `1.00x`, so full close is **not** merely an adjust-to-zero variant
  - the live close payout selector was observed with `BNB`, `USDT`, `WBNB`, and `bnbUSD` options
- current wallet / residual state after the verified close is:
  - `BNB = 0.06672528805`
  - `WBNB = 0`
  - `USDT = 55.98358266546553`
  - `bnbUSD = 0.005238383559755168`
  - residual `SigmaSP1 = 0.004083641208352667` shares (preview-estimated `0.003280270942998363 bnbUSD` + `0.000828100723359291 USDT`)
- Sigma no-auth history now shows a newest `CLOSED` row at `2026-03-17 00:32:30` for tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092`, which now matches the verified terminal trade-close outcome rather than just a coarse partial-close signal

What is still missing:
- no blocker remains for the bounded Priority A -> Priority B objective itself
- only contributor-facing packaging / cleanup remains if the repo should present this as the final verified close outcome

## Status framing

`STATUS.md` is now a compact status dashboard only.

For active execution:
- use `PART2_PLAN.md` for scope and exit condition
- use `PART2_TASKS.md` for the work queue
- use `PART2_OPERATOR_RUN_SEQUENCE.md` for the exact run order
- use `PART2_CLI_TESTING_GATE.md` for the readiness verdict
- use `SIGMA_STATUS_AND_PUBLIC_REPO_PATH.md` for the maintainer/contributor-oriented status + trajectory memo

## Phase status

- Phase 2a: real
- Phase 2b: real
- Phase 2c: **landed on 2026-03-13**
- Mint / redeem operator modeling pass: **landed on 2026-03-13**
- MegaNode / NodeReal / BSCTrace backend-switch pass: **landed on 2026-03-14**
- Live validation on a real user-supplied NodeReal BNB RPC endpoint: **landed on 2026-03-14**
- Read-only live current-app public-flow capture/evidence pass: **landed on 2026-03-14**

## Implemented now

- runnable Python CLI scaffold with launcher: `./sigma`
- capture workspace generator: `capture start`
- browser-side request capture helper: `capture browser-helper`
- HAR / devtools import helper: `capture import`
- raw calldata decode against the Sigma ABI cache
- `decode --tx-json <file>` for JSON and HAR ingestion
- `decode --tx-hash <hash>` using read-only BNB RPC or secondary explorer API
- batch decode for capture folders / raw directories over both `.json` and `.har`
- correlated tx / receipt / log evidence via `evidenceRecords`
- partial `routeEvidence` reporting that compares observed decoded calls against named Sigma operations
- `routeEvidence.operations[*].operationModel` metadata for:
  - current trade flows
  - current `/earn` redeem modes
  - archived mint flows
  - docs-described `bnbusd-redeem`
- local operator preflight planner in `sigma_operator/operations.py`
- read-only `account status` surface in `sigma_operator/account.py` + `sigma account status`
  - enumerates owner positions across the discovered live pool set
  - uses SyPool `balanceOf` / `tokenOfOwnerByIndex` / `getPosition` / `positionData` / `positionMetadata`
  - enriches with Sigma current-app no-auth entry-price/history helpers
  - exposes controller `positionIdToEntryPrice(address,uint256)` as an experimental optional hint
- explicit first-class plan operations for:
  - `stability-pool-redeem-normal`
  - `stability-pool-redeem-instant`
  - `mint-open`
  - `mint-close`
  - `bnbusd-redeem`
- `stability-pool-withdraw` retained as an umbrella alias for generic `/earn` withdraw intent
- CLI help now exposes the named operation set directly via `choices=` on `plan` and `decode --route-operation`
- ABI inspect / refresh still reuse the existing Sigma skill cache and fetch helper
- read-only live validation now confirmed on a real NodeReal BNB RPC path:
  - `eth_chainId` returned `0x38` / `56`
  - `decode --tx-hash <hash> --fetch-source rpc --bnb-rpc-url <redacted-endpoint>` fetched tx + receipt successfully
  - decode completed successfully against the live-fetched bundle without persisting the secret-bearing RPC URL

## Backend-switch changes landed in this pass

- MegaNode / NodeReal-compatible **BNB RPC** is now the primary documented live backend
- README and CLI wording now explicitly describe **RPC as the canonical live path** on BNB Chain
- explorer mode is now clearly marked **secondary / optional**
- BNB-native config/env support is now first-class:
  - `SIGMA_OPERATOR_BNB_RPC_URL`
  - `SIGMA_OPERATOR_BNB_RPC_TIMEOUT`
  - `SIGMA_OPERATOR_BSCTRACE_API_URL`
  - `SIGMA_OPERATOR_BSCTRACE_API_KEY`
  - `SIGMA_OPERATOR_BSCTRACE_CHAIN_ID`
  - `SIGMA_OPERATOR_BSCTRACE_TIMEOUT`
- accepted RPC aliases now include:
  - `SIGMA_OPERATOR_BSC_RPC_URL`
  - `SIGMA_OPERATOR_MEGANODE_RPC_URL`
  - `SIGMA_OPERATOR_NODEREAL_RPC_URL`
  - `SIGMA_OPERATOR_RPC_URL`
- accepted explorer aliases still include legacy `SIGMA_OPERATOR_EXPLORER_*`
- CLI flag aliases now include:
  - `--bnb-rpc-url` (preferred)
  - `--bsc-rpc-url`
  - `--meganode-rpc-url`
  - `--nodereal-rpc-url`
  - `--rpc-url` (legacy)
  - `--bsctrace-api-url` / `--bsctrace-api-key` / `--bsctrace-chain-id`
- fetch metadata now labels:
  - `BNB Chain RPC (MegaNode / NodeReal compatible)`
  - `Explorer API (secondary / optional)`
- explorer config no longer silently defaults the repo to an Etherscan-first stance

## Implemented, but still limited / partial

- explorer fetch is implemented, but live BNB Chain availability is currently **provider-limited**
  - classic BscScan proxy endpoints have been deprecated in favor of newer API paths
  - Etherscan V2 free access reports chain `56` as paid-only coverage
  - practical workaround: use `--fetch-source rpc` with a MegaNode / NodeReal-compatible BNB RPC URL
- browser/network capture automation is still **page-context interception**, not full browser control
- `routeEvidence` is useful for ABI/routing comparison, but it is **not** a trace, simulation, or exact frontend-hop proof
- `mint-open` / `mint-close` are modeled as **archived-docs plan flows only**
- `bnbusd-redeem` is modeled as **docs-described + low-confidence ABI hinting only**
- `stability-pool-deposit` remains modeled, but the consulted Sigma docs still say deposits are disabled during an ongoing upgrade
- real current-app evidence now exists for public read-phase flows (`/trade`, `/earn`, `/mintv2`), but the captured traffic is dominated by Multicall3 `aggregate3` read bundles and does not yet prove the exact write-path / pre-sign execution route
- late 2026-03-14 connected UI verification also confirmed live connected shells on `/earn` and `/mintv2` with first blockers captured (`Withdraw` disabled on zero balance; `Approve & Open` disabled on insufficient collateral), while the Rabby Sigma disclaimer sign-message still resisted automation and blocked deeper `/trade` execution-surface verification

## Explicitly not implemented yet

- deeper live popup inspection / decode for Rabby extension windows when native capture renders blank
- calldata generation for execution
- transaction simulation / trace comparison
- wallet execution integration
- exact proof that archived mint routes or `bnbusd-redeem` remain live in the current app

## Read-only evidence used for backend guidance

- Browser Relay Chrome tab shows the logged-in **NodeReal dashboard** is reachable
- the dashboard exposes a **BSC RPC** product card and an **API Reference Doc** link
- public NodeReal docs describe the endpoint format:
  - `https://{chain}-{network}.nodereal.io/v1/{API-key}`
- public BSC mainnet example pattern observed from docs:
  - `https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY`

Important boundary:

- no real user key is written into repo files
- no fetched bundle with a secret-bearing RPC URL was persisted from the live validation pass
- this pass now claims successful **read-only** live connectivity and decode on a real user-controlled endpoint/key, but the endpoint itself remains redacted and was not written into repo files

## Validation proof

Representative commands run successfully on **2026-03-14**:

```bash
python3 -m compileall sigma_operator
./sigma --help
./sigma decode --help
./sigma plan open-long --asset BNB --amount 1 --leverage 3 --slippage-bps 50
./sigma abi refresh --dry-run
./sigma decode --tx-hash 0xf1419c52735a27c0ca7ad8d25c8a6197076f5a134d4859e4ef03b05277ee7ddf --fetch-source rpc --bnb-rpc-url <redacted-endpoint>
./sigma account status --owner 0xOWNER_ADDRESS --bnb-rpc-url https://bsc-dataseed.binance.org/ --include-history --exclude-empty-pools
```

Observed results:

- `compileall` compiled all `sigma_operator/*.py` modules successfully
- `./sigma --help` now describes the CLI as **MegaNode/NodeReal-first** and calls out explorer mode as secondary/optional
- `./sigma decode --help` now exposes `--bnb-rpc-url`, `--bsc-rpc-url`, `--meganode-rpc-url`, `--nodereal-rpc-url`, and `--bsctrace-*` flags
- `plan open-long` still returned the expected plan JSON with `operationModel.entrypoint.kind="app"`
- `abi refresh --dry-run` still returned the expected skill-bridge dry-run JSON
- direct read-only RPC probe against the real user-supplied NodeReal BNB endpoint returned `eth_chainId = 0x38` (`56`)
- live `decode --tx-hash` over the same redacted NodeReal path returned:
  - `fetch.source = "rpc"`
  - `fetch.backendLabel = "BNB Chain RPC (MegaNode / NodeReal compatible)"`
  - `fetch.chainId = 56`
  - `transactionCount = 1`
  - `receiptCount = 1`
  - `evidenceRecords[0].status = "success"`
- live `account status` over public read-only BNB RPC returned:
  - `portfolio.positionCount = 1`
  - `portfolio.poolsWithPositions = ["0x31c464cfe506d44ceaa86c05cdbb94b5c94f70fb"]`
  - discovered `tokenId = 158` via `tokenOfOwnerByIndex(address,uint256)`
  - current-app `entryPriceNoAuth.response.data` resolved successfully
  - current-app `historyNoAuth.response.count = 3`
  - `warnings = []`
- the validated tx hash used for the live read-only pass was:
  - `0xf1419c52735a27c0ca7ad8d25c8a6197076f5a134d4859e4ef03b05277ee7ddf`


## Latest live update — 2026-03-16 autonomous continuation pass
New capture root:
- `projects/sigma-operator/captures/20260316T021136Z-autonomous-nextphase`

What changed in this pass:
- live `/mintv2` state was re-established and the existing mint position remained visible
- the `/mintv2` `Close` surface was re-checked directly and still showed:
  - `Repay Balance: 0.00`
  - disabled `Approve & Close`
- Sigma's explicit `add bnbUSD to wallet` helper was tested on the live close surface:
  - it opened `Rabby Wallet Notification`
  - the popup title was `Add custom token to Rabby`
  - token shown was `bnbUSD`
  - `My Balance` in the popup was `0 bnbUSD`
  - interaction produced the message `Token has been supported on Rabby`
  - clicking `Add` closed the popup successfully
- practical mint-close conclusion after the wallet-add test:
  - Sigma does expose a real wallet watch-asset helper for `bnbUSD`
  - but confirming token support in Rabby did **not** change the Sigma close repay balance on the visible surface
  - therefore the current mint-close blocker is not explained only by missing watch-asset visibility
- `/trade` still shows a live leveraged position summary and only a small `Adjust` affordance; no clean standalone add-margin or close CTA surfaced on the current page
- `/earn` still shows live pools and `Deposit` buttons, but after Chrome relay detachment the page no longer exposed stable automation hooks; this pass could not truthfully replay the bounded deposit deep enough to decide whether the prior `TRANSACTION... 1/3` stall is a hidden wallet boundary or a product-state/frontend issue
- `/governance` was re-checked in both live user Chrome and managed OpenClaw browser:
  - live Chrome still renders a black blank page
  - managed browser returns HTTP 200 and JS logs, but body text is empty and `#root` contains only injected RainbowKit style markup with no mounted governance UI

Current truthful frontier after this pass:
- mint open path: still confirmed live
- mint close path: still blocked by Sigma repay `Balance: 0.00`, even after explicit bnbUSD wallet-add handling
- leveraged position management: current `/trade` surface still exposes only `Adjust` as the visible management entrypoint
- earn: still not cleanly resolved beyond the previously proven first wallet boundary because this pass lost relay-grade page control before the bounded replay could be completed
- governance: route exists and boots partial app scaffolding, but remains `BLANK_ROUTE / NON_RENDERED`
- cumulative confirmed principal used remains about `~0.009 BNB`; this pass added **0** new principal and **0** new onchain approvals/txs

Operational refinement from this pass:
- Chrome relay loss was not fully recoverable in-session; even after clicking Chrome's exposed `Allow JavaScript from Apple Events` menu path, immediate AppleScript JS execution still reported disabled. Treat stable relay/DOM control as a real prerequisite for upgrading the `/earn` classification further.

## Latest live update — 2026-03-16 Sigma continuation classification pass
New capture root:
- `projects/sigma-operator/captures/20260316T034228Z-sigma-continuation`

What changed in this pass:
- `/earn` first-pool post-deposit state is now truthfully classified, not just inferred:
  - first pool remained `bnbUSD/USDT Stability Pool - Lista-Pangolins Vault`
  - switching the nested first-pool control from deposit-side state to `Stake` surfaced `Balance: 0.99 SigmaSP1`
  - switching the same first-pool control to `Withdraw` surfaced:
    - `Withdraw / Unstake`
    - `Balance: 0.99`
    - `Estimated Receive bnbUSD: 0.00`
    - `Estimated Receive USDT: 0.00`
    - `Charge me a 1% fee to receive funds immediately`
    - `Or you can withdraw bnbUSD+USDT after 60 minutes`
  - switching the same first-pool control to `Claim` surfaced `xSIGMA rewards: 0.00` with disabled `Claim`
  - practical conclusion: the bounded 1 USDT deposit created an **unstaked** receipt balance (`0.99 SigmaSP1`); it did not auto-stake, and there are no claimable rewards yet
- `/trade` management classification tightened:
  - live position still visible at roughly `$10.17` size and `1.65x` leverage
  - clicking `Adjust` opened `Adjust Leverage` with leverage presets, slippage, preview math, and `Approve & Adjust`
  - no explicit `Add Margin`, `Reduce`, or `Close Position` surface was exposed on the current visible trade management path
- `/mintv2` close was re-checked again and still truthfully shows:
  - live mint position on the top BNB / bnbUSD card
  - `Repay Balance: 0.00`
  - disabled `Approve & Close`
- read-only CLI account/portfolio status was re-run successfully and still confirms:
  - one active position
  - pool `0x31c464cfe506d44ceaa86c05cdbb94b5c94f70fb`
  - token id `158`
  - successful no-auth entry price + history enrichments
  - `historyNoAuth.response.count = 3`
  - `warnings = []`
- `/governance` remained blank / non-rendered even after direct route load + wait:
  - `https://sigma.money/governance` resolves
  - `document.body.innerText.length = 0`
  - `#root.innerText.length = 0`
  - body still contains a root + iframe scaffold, so the route boots some client/runtime pieces but does not render visible governance UI
  - console inspection still showed app activity/warnings rather than a normal visible governance page

Current truthful frontier after this pass:
- mint open path: still confirmed live
- mint close path: still blocked by visible repay `Balance: 0.00 bnbUSD`
- leveraged position management: still exposed primarily as `Adjust Leverage`, not a clean explicit add-margin / close flow
- earn: bounded deposit leg is completed and now post-deposit classification is upgraded — current state is unstaked `0.99 SigmaSP1`, withdraw path is real, claim remains zero
- governance: route still exists but remains `BLANK_ROUTE / NON_RENDERED`
- cumulative confirmed principal used remains about `~0.009 BNB + 1 USDT`; this pass added **0** new BNB principal, **0** new USDT principal, and no new confirmed approvals/txs

Best next step from this frontier:
1. if continuing live UI work, use the proven first-pool `0.99 SigmaSP1` balance to classify whether a tiny bounded stake / withdraw test is worth doing inside the existing envelope
2. in parallel, move the mint-close question further into backend/read-only investigation, because the visible close blocker still points to wallet-held bnbUSD semantics not yet satisfied on the current surface
3. keep governance classified as broken / non-rendered until a visible alternate route or render precondition is found

## Latest contract-level / CLI update — 2026-03-16

What changed in this pass:
- mint close was reduced from a UI-only blocker into a direct chain-state/read-only result
- new repo note added:
  - `MINT_CLOSE_CONTRACT_MAP_2026-03-16.md`
- new read-only CLI commands added:
  - `sigma account mint-close-readiness`
  - `sigma account stability-pools`
  - `sigma account bnbusd-trace`
- `sigma account mint-close-readiness` now also supports a read-side partial-close preview model via:
  - `--repay-amount`
  - optional `--target-ltv`
  - optional `--withdraw-amount`
- operator approval policy is now persisted/configurable in the CLI via:
  - `sigma config show`
  - `sigma config init --approval-policy ...`
  - `sigma config set-approval-policy --approval-policy ...`
- `sigma plan mint-close` now reflects:
  - partial repay / partial close semantics
  - resolved approval policy (`unlimited`, `exact`, `custom`)
  - the known gap between modeled finite approval intent and the still-unproven live close write path
- new CLI namespace scaffolding added:
  - `sigma governance overview`
  - `sigma governance xsigma ...`
  - `sigma governance vote ...`
  - `sigma governance incentivize ...`

Direct mint-close / repay-source findings now backed by chain state:
- live pool / position:
  - pool `0x31c464cfe506d44ceaa86c05cdbb94b5c94f70fb`
  - token / position id `158`
- current direct CLI validation for the owner observed:
  - wallet-held `bnbUSD` = `0.795238383559755168`
  - `bnbUSD` allowance to observed live router `0xae2658f23176f843af11d2209dbd04cffc0ff87b` = `0`
  - `getApproved(158)` = zero address
  - `isApprovedForAll(owner, router)` = `false`
  - SigmaSP1 residual share balance = `0.004083641208352667`
  - SigmaSP1 preview-based residual `bnbUSD` still deposited = `0.003280270942998363`
  - no current pending SigmaSP1 delayed redeem remained at validation time
- current onchain position state:
  - `rawColls = 0.014954999999999998`
  - `rawDebts = 4.010571150970316112`
- tx-history / origin-trace finding:
  - earliest observed mint tx `0x3ef4072cf992dd2a3cf89e1e807ece7b571f3eda738c5239765fe13feafbd097` minted `4.010571150970316112 bnbUSD`
  - that mint did **not** land directly in the wallet; it was routed onward in the same tx bundle through the observed Sigma router path
- practical conclusion:
  - current evidence supports **wallet-held `bnbUSD` repay semantics**, not hidden internal auto-netting
  - the CLI can now distinguish wallet-held vs residual-pool vs pending/claimable buckets directly from chain state
  - the CLI now also exposes a truthful **partial repay / partial close preview model**: repay amount changes remaining debt, modeled max withdraw, and resulting LTV, while clearly marking the math as read-side modeling rather than a captured close quote
  - approval policy is now treated as a **user-controlled preference** (`unlimited`, `exact`, `custom`), not as an inherent Sigma rule
  - mint close is still **not** fully execution-ready because the live close path requested max approval in Rabby even when Sigma Unlimited Approval was visually OFF

Governance CLI truth note:
- the app route `/governance` remains `BLANK_ROUTE / NON_RENDERED`
- the new `governance` CLI family is an **organizational umbrella only**, not a claim that the app route itself renders or is execution-ready


## Latest live update — 2026-03-16 remaining-blockers closure pass
New capture root:
- `projects/sigma-operator/captures/20260316T103136Z-remaining-blockers-closure`

What changed in this pass:
- the mint-close max-approval blocker was reduced with direct frontend-bundle evidence:
  - current close variants in the live bundle are **not** max-only by design
  - when `Unlimited Approval` is ON, the bundle uses max uint approval
  - when `Unlimited Approval` is OFF, the bundle contains an exact-approval branch (`approve(0)` then `approve(repayAmount)`)
- practical mint-close conclusion is now tighter:
  - remaining blocker is the **live UI / wallet-popup mismatch**
  - it is no longer repo-truthful to describe Sigma close as inherently max-approval-only
- `/trade` was re-checked live and still only exposed `Adjust` on the visible management surface
- governance/dashboard/stats route truth improved materially:
  - `/dashboard` renders live account/rebase/reward/unwrap content
  - `/statistics` renders live public analytics content
  - `/xsigma`, `/vote`, and `/incentivize` all render real product surfaces
  - `/governance` should still be treated as the broken / non-rendered umbrella route
- cumulative confirmed principal used remains about `~0.009 BNB + 1 USDT`; this pass added **0** new principal and **0** new confirmed approvals/txs

Current truthful frontier after this pass:
- mint-close exact-approval path exists in code, but still needs live end-to-end popup proof
- trade-management visible truth remains `Adjust` only
- `/dashboard`, `/statistics`, `/xsigma`, `/vote`, and `/incentivize` are now route-render-observed
- `/governance` remains `BLANK_ROUTE / NON_RENDERED`
- best next step is a fresh bounded mint-close replay specifically to prove whether the live popup can be made to honor the finite-approval branch

## Latest read-only verification update — 2026-03-16 post-close verification pack
New capture root:
- `projects/sigma-operator/captures/20260316T114949Z-post-close-verification-pack`

What changed in this pass:
- direct CLI + no-auth verification was run after the successful fresh replay at `20260316T112241Z-fresh-mint-close-replay`
- Sigma no-auth history for position `158` now returns **4** items and records the newest replay tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` as type `CLOSED`
- the same read-only pass also proves the position is still live:
  - token / position id `158` still owned by the wallet
  - `rawColls = 0.014954999999999998`
  - `rawDebts = 3.220571150970316111`
- decode of the replay tx proves the effect precisely:
  - wallet -> router transfer `0.79 bnbUSD`
  - burn of `0.79 bnbUSD`
  - `PoolManager.Operate` with `deltaColls = 0`, `deltaDebts = -0.79`
  - NFT `#158` round-tripped wallet -> router -> wallet
- current account state now reads as:
  - one active position
  - wallet-held `bnbUSD = 0.005238383559755168`
  - allowance to observed router `= 0`
  - `getApproved(158) = 0x0`
  - residual `SigmaSP1 = 0.004083641208352667`
  - preview-estimated residual pool value `= 0.003280270942998363 bnbUSD + 0.000828100723359291 USDT`

Current truthful frontier after this pass:
- the successful fresh replay was a **partial repay / partial close**, not a terminal full close
- Sigma history is truthful only at the coarse “close-side action happened” level; it is misleading if `CLOSED` is read as “position no longer exists”
- the same position NFT remains open with lower debt and unchanged raw collateral
- exact-approval replay proof is no longer missing; the new open question is whether the next objective is another partial repay, a true collateral-withdraw/full-close path, or separate trade-management work


## Latest live update — 2026-03-17 post-manual-sign verification pass
New capture roots:
- `projects/sigma-operator/captures/20260317T001447Z-priority-ab-live-run`
- `projects/sigma-operator/captures/20260317T0033-post-manual-sign-verify`

What changed in this pass:
- the earlier bounded Priority A submission was manually signed past the Rabby boundary, then re-verified from fresh live state rather than guessed from the UI overlay
- direct read-only account/history verification now shows the prior live long is closed onchain:
  - newest Sigma history row is `CLOSED` at `2026-03-17 00:32:30`
  - tx hash is `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092`
  - position NFT `#158` is still wallet-owned but now has:
    - `rawColls = 0`
    - `rawDebts = 0`
- direct decode of the verified close tx now proves the close effect precisely:
  - full collateral removed: `0.014954999999999998 BNB`
  - full debt burned: `3.2205711509703163 bnbUSD`
  - payout asset delivered to wallet: `USDT`
- exact received amount was established from both decode evidence and direct wallet balance delta:
  - before: `USDT = 49.19075703870576`
  - after: `USDT = 55.98358266546553`
  - exact increase: `6.792825626759770802 USDT`
- current post-close wallet state is now:
  - `BNB = 0.06672528805`
  - `WBNB = 0`
  - `USDT = 55.98358266546553`
  - `bnbUSD = 0.005238383559755168`
- residual non-position repay sources still remain separate from the closed trade itself:
  - wallet-held `bnbUSD = 0.005238383559755168`
  - residual `SigmaSP1 = 0.004083641208352667` shares (preview-estimated `0.003280270942998363 bnbUSD` + `0.000828100723359291 USDT`)

Current truthful frontier after this pass:
- the explicit `/trade` close path is now verified end to end, not just surface-classified
- the prior Long is fully closed economically; it was not merely reduced, and it was not replaced/reminted
- Priority B is no longer needed because no mint debt/collateral remains on position `#158`
- the only remaining work is documentation cleanup / contributor-facing packaging of the final verified outcome

Operational consequence:
- future work, if any, should not be framed as “continue Priority B mint close”
- it should instead be framed as either post-close cleanup, historical interpretation, or an unrelated next-phase Sigma task
