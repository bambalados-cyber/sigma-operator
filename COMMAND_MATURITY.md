# Command maturity

_Last updated: 2026-03-17_

This file is the public-facing command/surface truth map for SigmaCLI.

Use it to answer two questions:

1. **What exists in the CLI today?**
2. **How hard should I trust it?**

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
- output is structural, truthful, and intentionally limited
- not yet deep live-data support

### Planned

- not implemented yet
- may appear in specs or roadmap notes only

## Command-family status

| Command family | Maturity | Notes |
| --- | --- | --- |
| `capture docs`, `capture start`, `capture browser-helper`, `capture import` | Verified | Core repo workflow tooling. Useful for evidence collection and session setup. |
| `decode` raw calldata / tx JSON / capture-dir | Verified | Core decode path. Good current repo value. |
| `decode --tx-hash --fetch-source rpc` | Verified | Canonical live read path on BNB Chain. Requires user-supplied RPC. |
| `decode --tx-hash --fetch-source explorer` | Alpha / read-first | Implemented, but provider support on BNB Chain is inconsistent / secondary. |
| `plan` | Verified | Plan-only output with warnings and operation disambiguation. Not execution tooling. |
| `abi inspect` | Verified | Stable cache inspection utility. |
| `abi refresh` | Alpha / read-first | Useful, but depends on the upstream helper bridge / external context. |
| `account status` | Verified | Strong read-only owner/position entrypoint. |
| `account positions` | Verified | Flattened projection of current positions. |
| `account history` | Alpha / read-first | Useful, but depends partly on Sigma no-auth helper behavior. |
| `account mint-close-readiness` | Verified | One of the repo’s strongest current read-side features. |
| `account stability-pools` | Verified | Strong read-side classification for deposited vs pending vs claimable states. |
| `account bnbusd-trace` | Alpha / read-first | Valuable operator analysis; still interpretive rather than perfect asset-lineage proof. |
| `config` | Verified | Operator-side approval-policy persistence is real and shipped. |
| `governance overview` and `governance xsigma|vote|incentivize ...` | Scaffold | Honest structural commands only. Not deep live integrations yet. |

## Route-truth status

These are not exactly command labels, but they matter for how the CLI should be described.

| Surface | Status | Notes |
| --- | --- | --- |
| `/trade` | Verified live | Explicit `Close` path is proven distinct from `Adjust Leverage`; terminal close is verified onchain. |
| `/earn` | Verified live, read-first strongest | Deposit and delayed redeem semantics were observed; repo value is strongest on read/evidence. |
| `/mintv2` | Verified live, bounded | BNB -> bnbUSD mint open is verified; partial repay/partial close is verified; do not overstate generalized write support. |
| `/dashboard` | Route-render-observed | Useful next-phase read target, not yet deep CLI support. |
| `/statistics` | Route-render-observed | Good next-phase read target; current CLI family not implemented yet. |
| `/xsigma` | Route-render-observed | Do not market as deep live support yet. |
| `/vote` | Route-render-observed | Same caution as above. |
| `/incentivize` | Route-render-observed | Same caution as above. |
| `/governance` | Blank / non-rendered | Broken umbrella route; do not center public repo messaging on it. |

## Verified semantic distinctions the repo should preserve

These distinctions are part of repo maturity too.

- **partial repay / partial close** is not the same as **terminal close**
- explicit `/trade` `Close` is not the same as `Adjust Leverage`
- a wallet-owned NFT with `rawColls = 0` and `rawDebts = 0` is a **zero-state shell**, not an active economic position
- SigmaCLI should currently be described as **stronger on read/evidence than on generalized execution**

## Planned next additions

Not implemented yet, but good next targets:

- `stats`
- route-specific `dashboard` reads
- richer owner aggregation under `account`
- route-specific governance-side reads beyond scaffolds
- deeper `/trade` management semantics beyond explicit close

## Public wording guardrails

Safe wording today:

- “evidence-first operator CLI”
- “read-first”
- “verified trade close evidence”
- “mint-close readiness tooling”
- “governance scaffolds”

Unsafe wording today:

- “full Sigma CLI”
- “production execution support”
- “governance fully supported”
- “all visible routes are integrated”
