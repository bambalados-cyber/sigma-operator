# sigma-operator

Sigma operator CLI for **capture → decode → plan → ABI inspection → read-only account fetch** on **BNB Chain / BSC**.

Important wording note: Sigma is on **BNB Chain / BSC**, but live fetch methods still use `eth_*` names because BNB Chain speaks standard **EVM JSON-RPC**.

## Current execution pack: Part 2

The backend-switch pass is already landed, and the repo has now moved **beyond** the original Part 2 uncertainty. Part 2 remains the historical execution pack that turned the project into evidence-backed CLI/operator testing.

Latest verified outcome from the current repo truth set:
- `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` = verified **partial repay / partial close** on position `#158`
- `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092` = verified **terminal explicit /trade close**
- the surfaced `/trade` `Close` tab is now proven distinct from `Adjust Leverage`
- the verified terminal close paid out in **USDT** (`6.792825626759770802 USDT`)
- position / NFT `#158` remains wallet-owned after the terminal close, but only as a **zero-state shell** with `rawColls = 0` and `rawDebts = 0`

If you're new to this repo, start with the Part 2 execution pack:

1. [`PART2_PLAN.md`](PART2_PLAN.md) — objective, scope, phases, and exit condition
2. [`PART2_MILESTONES_CHECKLIST.md`](PART2_MILESTONES_CHECKLIST.md) — milestone tracker
3. [`PART2_TASKS.md`](PART2_TASKS.md) — concrete work queue
4. [`PART2_OPERATOR_RUN_SEQUENCE.md`](PART2_OPERATOR_RUN_SEQUENCE.md) — exact run order, guardrails, and stop conditions
5. [`PART2_CLI_TESTING_GATE.md`](PART2_CLI_TESTING_GATE.md) — PASS/FAIL gate for moving into structured CLI testing

Supporting repo-truth files for current state:

- [`STATUS.md`](STATUS.md)
- [`SIGMA_STATUS_AND_PUBLIC_REPO_PATH.md`](SIGMA_STATUS_AND_PUBLIC_REPO_PATH.md) — maintainer/contributor status memo covering original intent, what changed, what remains open, and the path to a public repo
- [`SIGMA_VERIFICATION_CHECKLIST.md`](SIGMA_VERIFICATION_CHECKLIST.md)
- [`SIGMA_RUN_LEDGER.md`](SIGMA_RUN_LEDGER.md)
- [`SIGMA_CLI_COMMAND_SPEC_NEXT.md`](SIGMA_CLI_COMMAND_SPEC_NEXT.md) — corrected next-phase command surface for governance subcommands, `/dashboard`, `/statistics`, and `account`
- [`MINT_CLOSE_CONTRACT_MAP_2026-03-16.md`](MINT_CLOSE_CONTRACT_MAP_2026-03-16.md) — contract/state-backed mint close semantic map and repay-asset findings

The original Part 2 question was whether the repo could gather enough live evidence to truthfully classify:
- the hidden Rabby boundary behind Sigma `TRANSACTION... 5/6`
- Open Long
- Open Short
- `/earn`
- `/mintv2`

That threshold has now been cleared. These files remain the best audit trail for how the repo got there, and the latest verified close-state packaging lives in `STATUS.md`, `SIGMA_RUN_LEDGER.md`, and `SIGMA_STATUS_AND_PUBLIC_REPO_PATH.md`.

This README remains the stable project/CLI overview. The Part 2 execution pack is still the best historical execution trail, but it is no longer the whole story of the current verified repo state.

## Backend priority for live work

### Primary live backend

For real BNB Chain interaction, the canonical live backend is now:

- **MegaNode / NodeReal-compatible read-only RPC**
- practical endpoint pattern from public NodeReal docs:
  - `https://{chain}-{network}.nodereal.io/v1/{API-key}`
- practical BNB mainnet placeholder:
  - `https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY`

Evidence used for this guidance in this pass:

- the logged-in NodeReal dashboard is reachable and shows a **BSC RPC** product card in the user account
- the dashboard exposes an **API Reference Doc** link to `https://docs.nodereal.io/reference`
- the public docs describe the endpoint format above and show a BSC mainnet example

No secrets are stored in this repo, and no live connectivity is claimed unless a real user-controlled endpoint/key is supplied.

### Secondary / optional backend

Explorer fetch is still implemented, but it is now documented as **secondary / optional** on BNB Chain:

- classic BscScan proxy assumptions are no longer the default mental model here
- Etherscan-compatible explorer access may still require paid or explicit provider setup
- when in doubt, prefer `--fetch-source rpc`

## Why this exists

The current Sigma knowledge still starts from the upstream `sigma-money` skill sources:

- `../../skills/sigma-money/references/`
- `../../skills/sigma-money/scripts/`

This repo now adds its own operator-local operation catalog so mint and redeem semantics can be modeled explicitly in help, plans, and evidence output without overclaiming live routing.

What is still reused directly:

- ABI cache defaults to `skills/sigma-money/references/abi`
- ABI refresh still delegates to `skills/sigma-money/scripts/fetch_sigma_abi.py`
- route hints are still derived from the same cached ABI/doc surfaces

## Entry points

Run from this directory:

```bash
./sigma --help
python3 -m sigma_operator.cli --help
```

## BNB-native env / config support

Preferred environment variables now use BNB-native naming:

```bash
export SIGMA_OPERATOR_BNB_RPC_URL="https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY"
export SIGMA_OPERATOR_BNB_RPC_TIMEOUT="20"
```

Optional secondary explorer envs:

```bash
export SIGMA_OPERATOR_BSCTRACE_API_URL="https://your-explorer.example/api"
export SIGMA_OPERATOR_BSCTRACE_API_KEY="YOUR_OPTIONAL_KEY"
export SIGMA_OPERATOR_BSCTRACE_CHAIN_ID="56"
export SIGMA_OPERATOR_BSCTRACE_TIMEOUT="20"
```

Accepted aliases for backward compatibility:

- RPC URL aliases:
  - `SIGMA_OPERATOR_BSC_RPC_URL`
  - `SIGMA_OPERATOR_MEGANODE_RPC_URL`
  - `SIGMA_OPERATOR_NODEREAL_RPC_URL`
  - `SIGMA_OPERATOR_RPC_URL`
- explorer aliases:
  - `SIGMA_OPERATOR_EXPLORER_API_URL`
  - `SIGMA_OPERATOR_EXPLORER_API_KEY`
  - `SIGMA_OPERATOR_EXPLORER_CHAIN_ID`
  - `SIGMA_OPERATOR_EXPLORER_TIMEOUT`

CLI flags follow the same priority:

- preferred RPC flag: `--bnb-rpc-url`
- accepted aliases: `--bsc-rpc-url`, `--meganode-rpc-url`, `--nodereal-rpc-url`, `--rpc-url`
- preferred optional explorer flags: `--bsctrace-api-url`, `--bsctrace-api-key`, `--bsctrace-chain-id`

Operator-side approval policy now has a persisted config path too:

```bash
./sigma config show
./sigma config init --approval-policy exact
./sigma config set-approval-policy --approval-policy custom --approval-amount 1.25
```

Defaults:
- persisted config path: `~/.config/sigma-operator/config.json`
- default approval policy when no config exists: `exact`
- supported approval policies:
  - `unlimited`
  - `exact` (per-transaction exact approval)
  - `custom` (finite approval amount)

Important truth note:
- approval policy is now modeled as a CLI/operator preference, not as an inherent Sigma requirement
- live `mint-close` evidence still showed Rabby requesting max `bnbUSD` approval even with Sigma `Unlimited Approval` visually OFF, so finite approval policy is represented/readable in the CLI before it is fully proven on the live write path

## Mint / redeem support now

What “support” means in this repo right now:

- `mint-open`
  - explicit **plan-only** operation
  - labeled **archived / legacy** from Sigma archive docs
  - carries partial ABI hints only
  - does **not** claim current live routing
- `mint-close`
  - explicit **plan-only** operation
  - labeled **archived / legacy** from Sigma archive docs
  - distinct from `/trade` `close-position`
  - read-side semantics now encode partial repay / partial close truthfully
  - does **not** claim current live routing or final close-write implementation
- `stability-pool-redeem-normal`
  - explicit current `/earn` cooldown withdrawal / redeem path
  - high-confidence ABI hinting via `BNBUSDBasePool.requestRedeem(...)` / `redeem(...)`
- `stability-pool-redeem-instant`
  - explicit current `/earn` immediate redeem path
  - high-confidence ABI hinting via `BNBUSDBasePool.instantRedeem(...)`
  - modeled with the docs-described **1%** fast-exit fee
- `stability-pool-withdraw`
  - umbrella alias covering both `/earn` redeem modes when the exact mode is not known yet
- `bnbusd-redeem`
  - explicit **docs-described** peg/redemption operation
  - deliberately separated from Stability Pool redeem and `/trade` close flows
  - modeled with **low-confidence** ABI hints only
  - does **not** claim a current public app entrypoint or exact live routing
- `close-position` / `reduce-position`
  - remain `/trade` lifecycle actions
  - are now documented and reported as distinct from both Stability Pool redeem and peg/redemption semantics
  - the explicit `/trade` `Close` tab is now verified as a real end-to-end close path, distinct from `Adjust Leverage`
  - the verified terminal close on position `#158` paid out in `USDT` and left the NFT wallet-owned as a zero-state shell rather than a live economic position

## Core commands

### Capture helpers

```bash
./sigma capture docs
./sigma capture start first-pass --target PoolManager --target BNBUSD
./sigma capture browser-helper captures/20260313T044416Z-phase-2b-validation
./sigma capture import captures/20260313T044416Z-phase-2b-validation ./wallet-export.har
```

What capture supports now:

- `capture start` creates an operator session under `captures/`
- `capture browser-helper` writes:
  - `helpers/sigma_browser_capture.js`
  - `helpers/README-browser-capture.md`
- `capture import` normalizes practical HAR/devtools exports into `raw/imported/*.json`
- capture templates now record:
  - named Sigma operation
  - route family
  - route status (`current`, `archived`, `docs-only`, etc.)

### Decode

#### Raw calldata

```bash
./sigma decode \
  0x095ea7b30000000000000000000000001111111111111111111111111111111111111111000000000000000000000000000000000000000000000000000000000000007b \
  --to 0x5519a479Da8Ce3Af7f373c16f14870BbeaFDa265
```

#### JSON / HAR / browser export ingestion

```bash
./sigma decode --tx-json captures/20260313T040614Z-phase-2a-validation/raw/direct-tx.json
./sigma decode --tx-json captures/20260313T040614Z-phase-2a-validation/raw/devtools-export.json
```

#### Live tx-hash fetch over the canonical read-only BNB RPC path

```bash
./sigma decode \
  --tx-hash 0xf1419c52735a27c0ca7ad8d25c8a6197076f5a134d4859e4ef03b05277ee7ddf \
  --fetch-source rpc \
  --bnb-rpc-url https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY \
  --save-fetch-json /tmp/sigma-live-rpc.json
```

This mode performs **read-only** BNB Chain RPC calls only:

- `eth_chainId`
- `eth_getTransactionByHash`
- `eth_getTransactionReceipt`

#### Read-only account / portfolio fetch from live pools

```bash
./sigma account status \
  --owner 0xOWNER_ADDRESS \
  --bnb-rpc-url https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY \
  --include-history

./sigma account mint-close-readiness \
  --owner 0xOWNER_ADDRESS \
  --position-id 158 \
  --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb \
  --bnb-rpc-url https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY

./sigma account mint-close-readiness \
  --owner 0xOWNER_ADDRESS \
  --position-id 158 \
  --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb \
  --bnb-rpc-url https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY \
  --repay-amount 0.79 \
  --target-ltv 39.66%

./sigma account stability-pools \
  --owner 0xOWNER_ADDRESS \
  --bnb-rpc-url https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY

./sigma account bnbusd-trace \
  --owner 0xOWNER_ADDRESS \
  --position-id 158 \
  --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb \
  --bnb-rpc-url https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY
```

What this slice does now:

- enumerates positions across the current discovered live pool set
  - `0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb`
  - `0x6C83261d45a394475bc1f4E2C6355b8d9c621855`
  - `0x7a97B5Fad34Ca48158B79245149A0fCf664aed91`
- performs read-only BNB RPC calls only:
  - `eth_chainId`
  - `eth_call`
- uses the verified SyPool view surface against those live pools:
  - `balanceOf(address)`
  - `tokenOfOwnerByIndex(address,uint256)`
  - `getPosition(uint256)`
  - `positionData(uint256)`
  - `positionMetadata(uint256)`
- enriches each discovered position with current-app no-auth helpers:
  - `/api/position/getEntryPrice/no-auth`
  - `/api/user-event/long-short-list/no-auth` (when `--include-history` is set)
- optionally probes the still-unproven controller helper:
  - `positionIdToEntryPrice(address,uint256)` via `--include-controller-entry-price`
- can run a targeted mint close readiness check that compares:
  - wallet-held `bnbUSD` balance
  - wallet allowance to the observed live write target
  - current position debt
  - current position-NFT approval state
  - active CLI approval policy (`unlimited`, `exact`, or `custom`)
- can model a read-side partial mint close scenario from current chain state:
  - repay amount -> remaining debt
  - repay amount -> modeled max withdrawable collateral
  - resulting LTV under the current-LTV-or-target-LTV guardrail
  - explicit note when the math is a specified read-side model rather than a fully contract-validated close quote
- can read current Sigma stability-pool balances directly from chain, including:
  - share balance still deposited
  - pending delayed redeem amount via `redeemRequests(address)`
  - claimable-after-unlock vs still-pending timing
  - preview-based `bnbUSD` / stable-token outputs from `previewRedeem(...)`
- can trace observed mint-position tx history and classify:
  - origin mint flow that was routed onward in the same tx
  - wallet-held `bnbUSD`
  - approved-but-unspent wallet balance
  - residual `bnbUSD` still represented by stability-pool shares
  - pending delayed withdraw / claimable-after-unlock buckets
  - unknown repay-source gap relative to current raw debt

Important caution:

- the no-auth helpers need browser-like headers; naïve bare requests can return `403`
- controller-side entry-price binding is still experimental and may return zeroed values even when the no-auth helper succeeds
- `bnbusd-trace` separates **origin-tx routing evidence** from **current repay-source buckets**; that output is intentionally not a claim that the exact same token units can be followed perfectly across all later protocol state transitions

#### Governance namespace scaffolding

```bash
./sigma governance overview
./sigma governance xsigma overview
./sigma governance vote allocations --owner 0xOWNER_ADDRESS
./sigma governance incentivize campaigns
```

What this slice means now:
- `governance` is a **CLI umbrella namespace**, not a claim that `https://sigma.money/governance` renders correctly
- current outputs are truthful scaffolds for `xsigma`, `vote`, and `incentivize`
- deep live governance read/write bindings are still deferred until route-specific evidence improves

#### Batch decode and compare multiple operation models

```bash
./sigma decode \
  --capture-dir captures/20260313T040614Z-phase-2a-validation \
  --route-operation open-long \
  --route-operation mint-open \
  --route-operation stability-pool-redeem-normal \
  --route-operation bnbusd-redeem
```

### Plan / ABI

```bash
./sigma plan open-long --asset BNB --amount 1 --leverage 3 --slippage-bps 50
./sigma plan stability-pool-redeem-instant --amount 250
./sigma plan mint-open --asset BNB --amount 1
./sigma plan mint-close -- --repay-amount 0.79
./sigma plan mint-close -- --repay-amount 0.79 --approval-policy custom --approval-amount 1.25
./sigma plan bnbusd-redeem --amount 250
./sigma abi inspect PoolManager
./sigma abi refresh --dry-run
```

## What plan output adds now

Every `sigma plan <operation>` payload now includes:

- `operationModel`
  - label
  - category
  - entrypoint kind (`app`, `archived-app`, or `docs-only`)
  - docs status
  - operator support level
  - disambiguation notes
- `approvalPolicy`
  - resolved policy (`unlimited`, `exact`, or `custom`)
  - desired approval amount / cap when the token is known
  - explicit note that live finite-approval behavior is not yet fully proven on `mint-close`
- `closeSemantics` for `mint-close`
  - partial repay / partial close support
  - wallet-held `bnbUSD` requirement
  - reminder that max withdraw depends on repay amount and LTV / health constraints
- explicit warnings when the flow is:
  - archived / legacy
  - docs-only / routing-ambiguous
  - docs-described as currently disabled
- `routingHints` matched against the same named operation taxonomy used by decode

## What decode does now

- resolves function selectors from the Sigma ABI cache
- ingests raw transaction/request payloads from JSON and HAR files
- batch-decodes `.json` and `.har` files under capture folders / raw directories
- fetches tx hash evidence primarily from:
  - **read-only BNB RPC** (canonical live path)
- and secondarily from:
  - **explorer API** (optional / provider-dependent)
- emits machine-readable JSON plus human-readable `summary` lines
- writes per-file decoded artifacts into `decoded/` for capture sessions
- decodes first-pass event logs from cached Sigma ABIs when payloads include `topics` + `data`
- correlates tx + receipt + log evidence into `evidenceRecords`
- emits a **partial `routeEvidence` report** that compares observed decoded calls against named Sigma operations
- includes `operationModel` metadata in route-evidence comparisons so redeem ambiguity is explicit in output

## Route evidence report

`routeEvidence` is intentionally **partial** and evidence-first.

It helps answer questions like:

- “does this capture overlap with the current `stability-pool-redeem-normal` hints?”
- “is this `redeem(...)` overlap pointing at `/trade` close semantics or only a docs-described peg/redemption model?”
- “did this capture match an archived mint hint set or only current trade/earn surfaces?”

What it is **not**:

- not a trace
- not a simulation
- not proof of the exact current frontend hop order
- not proof that archived mint routes are still live
- not proof that docs-described `bnbusd-redeem` has a current public app button

## Current limitations

- browser helper is still **page-context interception**, not full browser automation
- import helper normalizes practical HAR/devtools exports, but only writes entries that actually decode as tx/receipt/log evidence
- `routeEvidence` compares against static ABI/doc hints; it is not execution certainty
- `mint-open` / `mint-close` remain **archived-docs plan models**, not live-routing claims
- `mint-close` partial-repay preview math is now exposed as a **specified read-side model**, but it is still not a contract-validated close quote
- live `mint-close` finite approval policy is **modeled and persisted in the CLI**, but the exact/custom allowance write path is still not proven end-to-end because Rabby requested max approval in the captured close attempt
- `bnbusd-redeem` remains **docs-described + low-confidence routing only**
- raw signed tx decode for `eth_sendRawTransaction` is still out of scope
- no signing / no execution tooling is implemented here
- a real MegaNode / NodeReal endpoint still requires the user’s own API key / portal access

### Secondary explorer limitation on 2026-03-13

Live probe on **2026-03-13** showed:

- classic `api.bscscan.com/api?module=proxy...` returns a **deprecated V1 endpoint** error
- `api.etherscan.io/v2/api?chainid=56...` says **free API access is not supported for this chain**

Practical consequence:

- explorer mode is still available, but it is no longer treated as the default live path for BNB Chain
- live BNB Chain explorer fetch usually requires a **paid Etherscan V2 plan** or another compatible explorer endpoint/key
- the practical BNB-friendly path is to use `--fetch-source rpc` with a MegaNode / NodeReal-compatible BNB RPC URL
- this repo does **not** fake a live explorer success when that key/endpoint is absent

Example fallback:

```bash
./sigma decode \
  --tx-hash 0x... \
  --fetch-source rpc \
  --bnb-rpc-url https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY
```

## Validation proof

Representative commands run successfully in this backend-switch pass:

```bash
python3 -m compileall sigma_operator
./sigma --help
./sigma decode --help
./sigma plan open-long --asset BNB --amount 1 --leverage 3 --slippage-bps 50
./sigma abi refresh --dry-run
```

Observed results are summarized in `STATUS.md`.
