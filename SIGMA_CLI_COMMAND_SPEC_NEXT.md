# SIGMA CLI command spec — next phase

## Purpose

Define the next concrete CLI surface after Part 2 verification.

This document is for the **next build-planning layer**, not for overclaiming live product coverage. It translates the current verified Sigma route truth into a practical command map for the repo.

Key rule: build around the **real route-specific surfaces** that are visible now, and do **not** build around generic `/governance` as if it were a working top-level product surface.

---

## Verified route truth snapshot

### Execution-verified live surfaces
These are already proven real in the current repo evidence:
- `/trade`
- `/earn`
- `/mintv2`

### Route-specific next-phase surfaces to target
These are the corrected governance/account/analytics targets for the next CLI phase:
- `/xsigma`
- `/vote`
- `/incentivize`
- `/dashboard`
- `/statistics`

### Route to avoid as a CLI namespace
- `/governance`
  - route exists at `https://sigma.money/governance`
  - current observed behavior remains `BLANK_ROUTE / NON_RENDERED`
  - JS/app scaffolding appears to boot, but no visible governance UI materializes
  - **do not** use `governance` as the primary CLI command family

Practical implication:
- prefer route-specific command families: `xsigma`, `vote`, `incentivize`, `dashboard`, `stats`
- keep `account` as the cross-route owner/account aggregation family

---

## Governance / dashboard / statistics route map

### `/governance`
- Status: broken or non-rendered route shell
- CLI consequence: no top-level `governance` family
- Honesty rule: do not describe this as a working governance panel until a visible UI is actually observed

### `/xsigma`
- Best current reading: xSIGMA staking / convert / exit mechanics
- CLI family: `xsigma`
- Expected mode: mixed read + wallet-required write
- Verification status: route-level target is real enough to plan for, but deep execution has not yet been verified in this repo

### `/vote`
- Best current reading: emissions voting / gauge vote surface
- CLI family: `vote`
- Expected mode: mixed read + wallet-required write
- Verification status: route-level target is real enough to plan for, but deep execution has not yet been verified in this repo

### `/incentivize`
- Best current reading: gauge incentives / bribing surface
- CLI family: `incentivize`
- Expected mode: mixed read + wallet-required write
- Verification status: route-level target is real enough to plan for, but deep execution has not yet been verified in this repo

### `/dashboard`
- Best current reading: wallet/account rewards, points, and unwrap panel
- CLI family: `dashboard`
- Expected mode: mixed read + wallet-required write
- Verification status: route-level target is real enough to plan for, but deep execution has not yet been verified in this repo

### `/statistics`
- Best current reading: public protocol analytics surface
- CLI family: `stats`
- Expected mode: public read-only
- Best current source model:
  - Sigma backend API
  - third-party DeFi analytics APIs
  - chain/RPC-backed reads
  - Dune as deeper analytics handoff
- Observed source hints include:
  - `https://sigma.money/api/binance-api`
  - Pendle API
  - PancakeSwap explorer/cached pool API
  - Curve pool API
  - BNB RPC / Alchemy-backed paths
  - Dune handoff
- Honesty rule: treat this as a live analytics surface, but **not** as a frozen documented API contract yet

---

## Verified leverage asset map

### Verified prod-live leverage asset family
- **BNB**
  - this is the only leverage asset family verified live in the current evidence set
  - BNB long is fully confirmed as live and observable in-app
  - BNB short also surfaced in bounded testing as part of the live BNB leverage path
  - once a live long was already open, the visible app no longer exposed a fresh concurrent short-entry surface; do not misread that later state as proof that BNB short never existed

### Not verified as prod-live
- **BTC**
  - appears code-present / hinted in product surface discussions
  - **not** verified as prod-live in this repo
  - do not expose BTC as a default supported live leverage asset in CLI help or docs

### Anything else
- unverified
- do not list as supported until route/UI/API evidence is captured

CLI design consequence:
- initial leverage-aware command help should default to `BNB`
- future asset expansion should come from explicit verified route truth, not assumptions from code presence alone

---

## Verified mint asset map

### Verified prod-live mint lane
- **BNB -> bnbUSD**
  - this is the only mint lane verified live in the current evidence set
  - `/mintv2` open flow is real
  - repeated bounded tests reached real wallet boundaries and returned to a visible live mint position

### Current close-path truth
- the repo now holds two distinct verified close-side events on the same position shell:
  - `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` = partial repay / partial close only
  - `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092` = terminal explicit `/trade` close
- earlier `Repay Balance: 0.00` observations were real, but they are no longer the whole repo-level story
- current truthful semantics are:
  - mint **open** is verified live on `BNB -> bnbUSD`
  - mint **close** read-side semantics still matter because repay-source classification and partial-close modeling are real CLI value
  - the verified position `#158` no longer carries live mint debt/collateral; the NFT remains only as a zero-state shell
  - the verified terminal close did **not** come from a `/mintv2` full-close proof; it came from the explicit `/trade` `Close` path

### Other mint lanes
- unverified
- do not present other collateral/mint pairs as live until they are actually surfaced and tested

CLI design consequence:
- initial mint-aware command help should still default to `BNB -> bnbUSD`
- mint-close/readiness commands should be described as **read-first repay-semantics tooling**, not as a current mysterious blocker
- docs/help should distinguish clearly between:
  - mint-side partial repay / partial close evidence
  - terminal trade-close evidence
  - shell-NFT post-close state

---

## Command families

Important naming decision:
- use `stats`, not `statistics`, for the CLI group
- it is now acceptable to expose a **CLI** `governance` namespace as a structural umbrella
- but that umbrella must **not** be described as proof that the `/governance` app route itself works

### `governance xsigma`
Recommended first commands:
- `sigma governance xsigma overview`
- `sigma governance xsigma position --owner <address>`
- `sigma governance xsigma claimable --owner <address>`
- `sigma governance xsigma convert-preview --amount <amount>`

Deferred wallet-required commands:
- `sigma governance xsigma convert`
- `sigma governance xsigma exit`
- `sigma governance xsigma claim`

### `governance vote`
Recommended first commands:
- `sigma governance vote gauges`
- `sigma governance vote epoch`
- `sigma governance vote allocations --owner <address>`
- `sigma governance vote preview --owner <address> ...`

Deferred wallet-required commands:
- `sigma governance vote cast`
- `sigma governance vote clear`

### `governance incentivize`
Recommended first commands:
- `sigma governance incentivize gauges`
- `sigma governance incentivize campaigns`
- `sigma governance incentivize positions --owner <address>`
- `sigma governance incentivize preview ...`

Deferred wallet-required commands:
- `sigma governance incentivize create`
- `sigma governance incentivize topup`
- `sigma governance incentivize claim`

### `dashboard`
Recommended first commands:
- `sigma dashboard summary --owner <address>`
- `sigma dashboard rewards --owner <address>`
- `sigma dashboard points --owner <address>`
- `sigma dashboard unwrap-preview --owner <address>`

Deferred wallet-required commands:
- `sigma dashboard unwrap`
- `sigma dashboard claim`

### `stats`
Recommended first commands:
- `sigma stats overview`
- `sigma stats tvl`
- `sigma stats pools`
- `sigma stats sources`
- `sigma stats raw --dataset <name>`

Notes:
- `stats` should stay read-only
- it is the safest next family to implement because it does not depend on wallet execution

### `account`
Recommended first commands:
- `sigma account status --owner <address>`
- `sigma account mint-close-readiness --owner <address> --position-id <id> --pool <address>`
- `sigma account mint-close-readiness --owner <address> --position-id <id> --pool <address> --repay-amount <bnbUSD> [--target-ltv <ratio|percent>] [--withdraw-amount <BNB>]`
- `sigma account stability-pools --owner <address>`
- `sigma account bnbusd-trace --owner <address> --position-id <id> --pool <address>`
- `sigma account positions --owner <address>`
- `sigma account history --owner <address>`
- `sigma account rewards --owner <address>`
- `sigma account exposure --owner <address>`

Notes:
- `account status` already exists and should remain the anchor
- `account mint-close-readiness` is the first targeted read-only position-management check because it answers the repay-asset question directly from chain state
- the extended `account mint-close-readiness --repay-amount ...` form is the truthful place to encode partial repay / partial close semantics without overclaiming a live write path
- `account stability-pools` should be the canonical direct-CLI way to distinguish wallet-deposited shares, pending delayed redeem, and claimable-after-unlock state on `/earn`
- `account bnbusd-trace` should combine tx-receipt evidence with current pool/wallet state so the CLI can say whether observed mint-origin `bnbUSD` was routed onward and what repay sources are visible now
- `account status` / `account positions` should distinguish a live economic position from a wallet-owned **zero-state shell NFT** whose `rawColls` and `rawDebts` are both zero
- this family should aggregate data from `/trade`, `/earn`, `/mintv2`, `/dashboard`, and later governance-related read surfaces where feasible

### `config`
Recommended first commands:
- `sigma config show`
- `sigma config init --approval-policy exact`
- `sigma config set-approval-policy --approval-policy custom --approval-amount <amount>`

Notes:
- approval policy is now explicit repo truth, not hidden UI lore
- supported policies are:
  - `unlimited`
  - `exact`
  - `custom`
- live `mint-close` still needs honest warnings because finite approval is modeled/persisted in the CLI before it is fully proven on the live write path

---

## Public/read-only vs wallet-required classification

### Safe public/read-only first wave
These fit the current repo posture best:
- `stats *`
- `account status`
- `account mint-close-readiness`
- `account stability-pools`
- `account bnbusd-trace`
- `account positions`
- `account history`
- `account rewards`
- `dashboard summary`
- `dashboard rewards`
- `dashboard points`
- `governance xsigma overview`
- `governance xsigma position`
- `governance vote gauges`
- `governance vote epoch`
- `governance vote allocations`
- `governance incentivize gauges`
- `governance incentivize campaigns`

### Wallet-required second wave
These should wait until route semantics and wallet boundaries are explicitly verified:
- `xsigma convert`
- `xsigma exit`
- `xsigma claim`
- `vote cast`
- `vote clear`
- `incentivize create`
- `incentivize topup`
- `incentivize claim`
- `dashboard unwrap`
- `dashboard claim`

Rule:
- if a command can move funds, alter vote state, lock/unlock positions, or claim rewards, it belongs in the wallet-required bucket until proven otherwise

---

## Recommended implementation / module split

Keep the existing CLI shape, but split the next phase by surface instead of by one generic governance abstraction.

### Recommended modules
- `sigma_operator/surface_truth.py`
  - canonical route truth snapshot
  - verified asset maps
  - live-vs-unverified flags
- `sigma_operator/app_api.py`
  - shared Sigma HTTP/API helpers
  - reusable request wrappers for no-auth/current-app endpoints and statistics datasets
- `sigma_operator/stats.py`
  - `/statistics` read-only fetch + normalization
- `sigma_operator/dashboard.py`
  - `/dashboard` read models and account/reward aggregation
- `sigma_operator/governance.py`
  - shared read models for `/xsigma`, `/vote`, `/incentivize`
  - keep route-specific functions separate inside this module or split later if it grows
- `sigma_operator/account.py`
  - keep as the owner-centric aggregation layer
  - extend it rather than re-creating overlapping account summary logic elsewhere
- `sigma_operator/cli.py`
  - add `governance` as a structural umbrella with subcommands for `xsigma`, `vote`, and `incentivize`
  - keep `dashboard` and `stats` as separate read-first groups

### Optional later split if governance code grows
If the governance-side surface becomes large, split further into:
- `sigma_operator/xsigma.py`
- `sigma_operator/vote.py`
- `sigma_operator/incentivize.py`

Do that only after the shared read-path patterns stabilize.

---

## Priority order for implementation

### Priority 1 — route truth registry
Implement the static truth layer first:
- corrected route map
- verified leverage asset map
- verified mint asset map
- explicit `unsupported / unverified` annotations

This prevents future help text and docs from drifting back toward fake generic `/governance` support.

### Priority 2 — `stats` read-only family
Build `stats` next:
- public analytics surface
- safest implementation target
- useful immediately for operators
- no wallet flow dependency

### Priority 3 — expand `account`
Extend the existing `account` family:
- stability-pool state (`wallet-held share balance`, `pending redeem`, `claimable after unlock`)
- `bnbusd` repay-source trace (`wallet-held`, `approved but unspent`, `deposited elsewhere`, `pending/claimable`, `unknown`)
- positions
- history
- rewards
- exposure summary

This keeps the repo anchored in owner-centric read value before adding more route-specific namespaces.

### Priority 4 — `dashboard` read models
Add:
- summary
- rewards
- points
- unwrap preview

Reason:
- high operator value
- route-specific target is clearer than generic governance
- still mostly compatible with read-first implementation

### Priority 5 — governance-side read models
Add read-only coverage for:
- `xsigma`
- `vote`
- `incentivize`

Reason:
- valid next surface area
- but route existence is clearer than execution semantics right now

### Priority 6 — wallet-required governance/dashboard writes
Only after the read surfaces are stable and truthful:
- claim
- convert
- vote
- incentivize
- unwrap

These should be deferred until wallet boundary behavior is verified and the repo has an explicit execution safety design for them.

---

## Honesty notes / known gaps

- The **app route** `/governance` is still blank/non-rendered.
- A **CLI namespace** called `governance` is acceptable only as a structural umbrella over `xsigma`, `vote`, and `incentivize`; do not present it as proof of a working app page.
- `/xsigma`, `/vote`, `/incentivize`, and `/dashboard` are the corrected route targets, but this repo does **not** yet have deep execution verification for them.
- `/statistics` is real enough to target, but the exact backing data contracts are still best-current-read rather than frozen schema guarantees.
- BNB is the only leverage asset family verified live right now.
- BTC may be code-present, but it is **not** verified as prod-live and must stay out of default supported-asset claims.
- BNB -> bnbUSD is the only verified mint lane right now.
- Earlier `Repay Balance: 0.00 bnbUSD` observations were real, but the repo now distinguishes them from later verified close-side outcomes:
  - `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` = partial repay / partial close
  - `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092` = terminal explicit `/trade` close
- Trade management is no longer just a surfaced hypothesis: the explicit `/trade` `Close` panel is now verified end to end onchain, distinct from `Adjust Leverage`, with payout-asset selection observed and the verified terminal close settling to `USDT`.
- Post-close account handling still needs clear read-side packaging because a fully closed position can leave a wallet-owned **zero-state shell NFT** rather than disappearing.

---

## Practical repo decision

For the next phase, the honest CLI expansion is:
1. keep `account` as the owner/account anchor,
2. add targeted read-only checks such as `account mint-close-readiness`,
3. add `stats` as the safest public read-only family,
4. expose `governance` as a structural umbrella over `xsigma`, `vote`, and `incentivize`, plus `dashboard` separately,
5. keep all wallet-required actions explicitly deferred until they are evidence-backed.

That is the cleanest path that matches current Sigma truth without pretending the blank `/governance` route is itself a working app surface.


## Update — 2026-03-16 route-render verification pass

New route truth from the latest live pass:
- `/dashboard` rendered live account/rebase/reward/unwrap content
- `/statistics` rendered live protocol analytics content
- `/xsigma`, `/vote`, and `/incentivize` also rendered live route content
- `/governance` should still remain treated as the broken umbrella route

CLI consequence:
- keep `/governance` as umbrella-only / honesty-guarded
- it is now stronger repo truth to describe `/dashboard`, `/statistics`, `/xsigma`, `/vote`, and `/incentivize` as **route-render-observed** rather than merely route-target-only
- deep execution/read normalization work is still pending, but route existence/rendering has improved from speculative to directly observed
