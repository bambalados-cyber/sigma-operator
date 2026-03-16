# SigmaCLI repo spec

_Last updated: 2026-03-17_

## 1) Purpose

SigmaCLI (`sigma-operator`) is an operator-first CLI for **Sigma on BNB Chain / BSC**.

Its job is to help an operator:

- capture Sigma app and network evidence
- decode calldata, txs, receipts, and logs against cached ABIs
- model named Sigma operations without pretending they are all fully executable
- inspect current account, position, and repay-readiness state via read-only RPC and current-app helper data
- keep route truth, command truth, and repo claims aligned

This repo is intentionally **founder/operator-grade**, not a corporate SDK and not a generic autotrader.

## 2) Trust model

SigmaCLI follows a **read-first, execution-later** trust model.

That means:

1. prefer read-only evidence over assumptions
2. prefer decoded receipts over frontend guesswork
3. prefer route-specific truth over generic product language
4. prefer honest partial support over fake completeness
5. treat wallet-required execution as a separate, higher-confidence bar

In practice:

- a route may be **render-observed** without being execution-ready
- a command may be useful and shipped even if it is still **alpha/read-first**
- a route or command should not be upgraded to “verified” unless the repo has evidence to justify it

## 3) Current verified capabilities

### Core CLI foundation

The repo already ships useful operator tooling for:

- capture-session scaffolding
- HAR / devtools import normalization
- calldata / tx / receipt / log decode
- live tx-hash fetch over read-only BNB RPC
- ABI inspection and refresh helpers
- plan-only modeling for named Sigma operations
- read-only owner / position / stability-pool inspection
- mint-close readiness and bnbUSD repay-source analysis

### Verified route truth

#### `/trade`

Verified today:

- explicit `Close` exists as a real surfaced path
- explicit `Close` is distinct from `Adjust Leverage`
- the surfaced close path is proven end to end onchain
- verified terminal close settled to **USDT**

Important nuance:

- tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` is **not** the final close story; it is a verified partial repay / partial close
- tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092` is the verified terminal `/trade` close

#### `/earn`

Verified today:

- bounded deposit semantics were observed live
- delayed withdraw / redeem timing semantics were observed live
- the repo can classify wallet-held balance vs deposited shares vs pending delayed withdraw vs claimable-after-unlock

#### `/mintv2`

Verified today:

- BNB -> bnbUSD mint open is real
- read-side mint-close readiness is useful and implemented
- partial repay / partial close semantics are real and distinct from terminal trade close

Important nuance:

- the repo should not present `/mintv2` as a fully generalized write surface
- mint-close is now best understood as a **read-first repay-semantics problem** unless fresh repay-ready live evidence is being collected

#### Governance-related surfaces

Current repo stance:

- `/governance` remains the broken / blank umbrella route
- route-specific children such as `/xsigma`, `/vote`, `/incentivize`, `/dashboard`, and `/statistics` are better next-phase targets
- governance is **not** the center of the repo’s current credibility story

## 4) Command surface model

SigmaCLI’s command surface is organized into a few practical families.

### `capture`

Use when you need:

- a capture workspace
- browser helper scaffolding
- import of HAR/devtools exports into decode-ready artifacts

### `decode`

Use when you need:

- raw calldata decode
- JSON / HAR tx ingest
- tx-hash fetch + decode over read-only BNB RPC
- evidence-first interpretation of what happened onchain

### `plan`

Use when you need:

- named operation planning
- disambiguation between similar-looking product actions
- warnings and operator notes without claiming execution certainty

### `account`

Use when you need:

- current positions
- Sigma no-auth history overlays
- stability-pool state
- mint-close readiness
- repay-source tracing for bnbUSD

### `abi`

Use when you need:

- manifest inspection
- ABI refresh through the upstream helper bridge

### `config`

Use when you need:

- persisted operator-side approval policy
- explicit `unlimited`, `exact`, or `custom` approval stance

### `governance`

Current meaning:

- a **structural CLI umbrella** only
- route-truth and scaffold output today
- not deep live governance support

## 5) Maturity labels

This repo uses a small, explicit maturity model.

### Verified

- shipped in the CLI
- exercised against real repo evidence
- safe to describe as current repo capability

### Alpha / read-first

- shipped and useful
- may rely on evolving route, RPC, or app-helper assumptions
- should still be described with caution

### Scaffold

- command exists
- output is structural / truthful / useful for orientation
- not yet deep live data support

### Planned

- intentionally not implemented yet
- may appear in design docs, not as present-tense support

See [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md) for the current mapping.

## 6) Operator workflow model

The intended operator loop is:

1. **capture** a route, popup, or tx bundle if needed
2. **decode** what actually happened
3. **inspect account state** read-only
4. **plan** the named operation with explicit warnings
5. **compare route truth vs command truth**
6. only then consider bounded manual wallet execution

This workflow exists to stop the repo from drifting into frontend mythology.

## 7) Current credibility boundary

SigmaCLI is already credible when it says:

- “here is the decoded tx evidence”
- “here is the current onchain position state”
- “here is the repay-ready vs not-repay-ready distinction”
- “here is the difference between partial close and terminal close”

SigmaCLI is **not** yet trying to be credible when it says:

- “every route is supported”
- “all governance surfaces are live-integrated”
- “write execution is generic and safe”
- “visible route equals verified route”

## 8) Near-term milestones

The next milestone should deepen the repo where it is already strong.

### Milestone A — route-specific read expansion

Build read-first support for:

- `stats`
- `dashboard`
- richer account aggregation
- route-specific governance-side reads where they are actually observed

### Milestone B — remaining `/trade` management semantics

Prove, don’t assume:

- add margin
- reduce
- leverage-adjust edge behavior
- how those paths relate to the already-verified explicit close path

### Milestone C — dedicated `/mintv2` close semantics on a fresh position

Only after repay readiness exists again on a new live position:

- re-check the dedicated `/mintv2` close execution story
- keep it separate from the already-verified `/trade` terminal close story
- preserve the distinction between partial repay, terminal close, and zero-state shell NFT semantics

## 9) Non-goals for the current repo stage

Not current goals:

- production-safe transaction execution
- broad multi-route automation
- governance-first product framing
- pretending blank or ambiguous routes are supported just because the codebase hints at them

## 10) Bottom line

SigmaCLI already has a real public-repo story:

- it is evidence-first
- it is read-first
- it has verified live route truth where it matters
- it distinguishes partial close from terminal close
- it keeps claims tighter than the average crypto operator tool

That is enough to be useful publicly — as long as the repo keeps choosing **truth over breadth**.
