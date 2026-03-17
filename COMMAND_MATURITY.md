# Command maturity

_Last updated: 2026-03-17_

This file is the public command-truth map for SigmaCLI.

It answers two different questions:

1. **What is shipped in the repo today?**
2. **What is the next wallet/execution command spine, and what is its maturity?**

## Maturity labels

### Verified

- shipped in the CLI
- exercised against real repo evidence
- safe to present as current repo capability

### Alpha / read-first

- shipped and useful
- still dependent on evolving route, RPC, or app-helper assumptions
- should be described carefully

### Scaffold

- command exists
- output is intentionally limited and structural
- useful for orientation, not deep execution support

### Planned

- documented as part of the next architecture
- not shipped yet, or not shipped in its full intended form

## Current shipped command families

| Command family | Maturity | Notes |
| --- | --- | --- |
| `capture docs`, `capture start`, `capture browser-helper`, `capture import` | Verified | Evidence collection tooling. Useful, but not the core product architecture. |
| `decode` raw calldata / tx JSON / capture-dir | Verified | Core decode path. Strong current repo value. |
| `decode --tx-hash --fetch-source rpc` | Verified | Canonical live read path on BNB Chain. Requires user-supplied RPC. |
| `decode --tx-hash --fetch-source explorer` | Alpha / read-first | Implemented, but secondary and provider-dependent on BNB Chain. |
| `plan` | Verified | Plan-only output with warnings and disambiguation. Not wallet execution yet. |
| `abi inspect` | Verified | Stable cache inspection utility. |
| `abi refresh` | Alpha / read-first | Useful, but depends on the upstream helper bridge / external context. |
| `account status` | Verified | Strong read-only owner/position entrypoint. |
| `account positions` | Verified | Flattened projection of current positions. |
| `account history` | Alpha / read-first | Useful, but depends partly on Sigma no-auth helper behavior. |
| `account mint-close-readiness` | Verified | One of the repo’s strongest current read-side features. |
| `account stability-pools` | Verified | Strong classification for deposited vs pending vs claimable states. |
| `account bnbusd-trace` | Alpha / read-first | Valuable operator analysis; still interpretive rather than perfect lineage proof. |
| `config` | Verified | Operator-side approval-policy persistence is real and shipped. |
| `governance overview` and `governance xsigma|vote|incentivize ...` | Scaffold | Structural truth commands only. Not the current architecture focus. |

## Next command spine

These are the target command families for the wallet-backed architecture described in [`WALLET_ARCHITECTURE.md`](WALLET_ARCHITECTURE.md).

| Command family | Maturity | Notes |
| --- | --- | --- |
| `auth` | Planned | Backend discovery, profile connection, wallet/session state. |
| `status` | Planned | Execution-aware operator summary across backend, routes, balances, and positions. |
| `doctor` | Planned | Preflight route/backend/policy checks before execution. |
| `plan` execution artifact mode | Planned | Current `plan` exists, but the wallet-backed plan artifact format is still next-phase work. |
| `execute` | Planned | Policy-gated route execution through direct adapters. |
| `verify` | Planned | Post-state verification separate from tx submission. |

## Route capability status

These labels matter because SigmaCLI should never imply that route visibility equals route support.

| Surface / route area | Status | Notes |
| --- | --- | --- |
| `/trade` | Verified live semantics | Explicit `Close` is proven distinct from `Adjust Leverage`; terminal close is verified onchain. |
| `/mintv2` | Verified live, bounded | BNB -> bnbUSD mint open is verified; partial repay / partial close is verified; direct wallet architecture still needs to be built. |
| `/earn` | Verified live, read-first strongest | Deposit and delayed redeem semantics were observed; direct route adapters are still next-phase work. |
| `/dashboard` | Route-render-observed | Real surface, but not the current architecture focus. |
| `/statistics` | Route-render-observed | Real surface, but not the current architecture focus. |
| `/xsigma` | Route-render-observed | Not the current focus. |
| `/vote` | Route-render-observed | Not the current focus. |
| `/incentivize` | Route-render-observed | Not the current focus. |
| `/governance` | Blank / non-rendered | Broken umbrella route; do not center public messaging on it. |

## Preserved semantic distinctions

These truths remain part of repo maturity:

- **partial repay / partial close** is not the same as **terminal close**
- explicit `/trade` `Close` is not the same as `Adjust Leverage`
- a wallet-owned NFT with `rawColls = 0` and `rawDebts = 0` is a **zero-state shell**, not an active economic position
- SigmaCLI is currently stronger on **read/evidence** than on **generalized execution**
- browser capture may remain useful, but it is **not** the core architecture

## Safe public wording

Safe wording today:

- "wallet-aware evidence-first operator CLI"
- "read-first today, execution foundation next"
- "direct wallet/backend architecture"
- "verified trade close evidence"
- "mint repay/readiness tooling"
- "post-state verification"

Unsafe wording today:

- "full Sigma CLI"
- "browser automation product"
- "production execution support across Sigma"
- "all visible routes are integrated"
- "governance fully supported"

## Bottom line

Current repo truth:

- SigmaCLI already ships meaningful read-side operator tooling.
- The next command spine is now clearly wallet/backend centered.
- Planned execution support should be described as planned until the backend, policy, execute, and verify layers really land.