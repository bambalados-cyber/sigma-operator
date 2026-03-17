# Next milestone: read-model expansion + remaining `/trade` semantics

_Last updated: 2026-03-17_

## Objective

Make SigmaCLI materially stronger at the things it is already credible at:

1. **public/read-first protocol visibility**
2. **owner/account aggregation and portfolio interpretation**
3. **evidence-backed clarification of the next unresolved `/trade` management semantics**

This milestone is intentionally **not** about generalized write automation.

## Why this is the next milestone

The repo already has a clear public truth:

- `/trade` explicit `Close` is verified live and distinct from `Adjust Leverage`
- terminal `/trade` close is verified onchain
- SigmaCLI is strongest today on **read, decode, evidence, and operator interpretation**
- route-render-observed surfaces like `/statistics` and `/dashboard` are better next targets than broad execution claims

So the next step should deepen the repo where trust is already high:

- expand read support for `stats`
- add practical `dashboard` read models
- improve cross-surface account aggregation
- then prove the next unresolved `/trade` management semantics before claiming more execution coverage

## In scope

### 1) `stats` read support

Add a dedicated read-only `stats` family for the observed `/statistics` surface.

Target outcomes:

- normalized protocol overview output
- explicit source visibility
- pool / TVL style datasets where currently observable
- raw dataset passthrough for operator inspection when schemas drift

### 2) `dashboard` read models

Add owner-centric reads for the observed `/dashboard` surface.

Target outcomes:

- summary view
- rewards view
- points / account-side score view if surfaced reliably
- unwrap-related preview/read model only if it can be done honestly without implying execution support

### 3) deeper account aggregation / portfolio visibility

Extend `account` so it becomes the operator’s best cross-surface wallet summary.

Target outcomes:

- clearer aggregation across `/trade`, `/earn`, `/mintv2`, and dashboard-side reads
- rewards and exposure summaries where they can be computed honestly
- explicit distinction between:
  - active economic positions
  - pending/redeemable stability-pool states
  - wallet-held balances
  - wallet-owned **zero-state shell NFTs** (`rawColls = 0`, `rawDebts = 0`)

### 4) prove the next unresolved `/trade` semantics

Before expanding write claims, gather route- and tx-level truth for:

- **add margin**
- **reduce**
- **leverage-adjust edge behavior**

This is a proof milestone first, not a “ship every management action” milestone.

## Out of scope

Not part of this milestone:

- generalized write automation
- broad wallet-execution support across Sigma routes
- governance-first repo framing
- treating `/governance` as the center of repo truth
- relitigating the already-resolved `#158` close story except as established truth
- claiming support for new assets or new mint lanes without fresh evidence
- promising production-safe execution flows

## Proposed command additions and changes

### New command family: `stats`

Proposed first commands:

- `sigma stats overview`
- `sigma stats tvl`
- `sigma stats pools`
- `sigma stats sources`
- `sigma stats raw --dataset <name>`

Rules:

- keep `stats` read-only
- preserve raw/source visibility so operators can inspect drift rather than trust silent normalization

### New command family: `dashboard`

Proposed first commands:

- `sigma dashboard summary --owner <address>`
- `sigma dashboard rewards --owner <address>`
- `sigma dashboard points --owner <address>`
- `sigma dashboard unwrap-preview --owner <address>` only if it remains an honest read/preview surface

Rules:

- no claim/unwrap execution in this milestone
- if a dashboard field cannot be sourced stably, surface that uncertainty directly

### `account` expansion

Keep `account status` as the anchor, then extend with:

- `sigma account rewards --owner <address>`
- `sigma account exposure --owner <address>`

Also strengthen existing output so `account status` / `account positions` can better represent:

- live vs zero-state positions
- dashboard-linked rewards context
- `/earn` deposited vs pending vs claimable states
- clearer owner-level portfolio totals where they are evidence-backed

### `/trade` semantics handling in this milestone

No generalized write command expansion is required to call this milestone successful.

Instead:

- keep current `/trade` verified `Close` truth intact
- collect new evidence for add-margin / reduce / leverage-adjust behavior
- only promote command/help/docs language after those paths are actually verified

If useful, route-semantics work may first land as:

- richer `decode` interpretation
- stronger `plan` warnings/disambiguation
- updated route-truth and maturity docs

## Success criteria

This milestone is successful when all of the following are true:

### Read-side delivery

- `stats` exists as a real, useful read-only command family
- `dashboard` has at least a credible summary/rewards read surface
- `account` gives a stronger owner-level portfolio view than today

### Truth quality

- docs continue to describe SigmaCLI as **read-first** and **evidence-first**
- new command/help text does not imply generalized execution support
- zero-state shell handling remains explicit and operator-safe

### `/trade` semantic proof

- repo evidence clearly classifies add margin, reduce, and leverage-adjust edge behavior
- docs distinguish verified behavior from still-unresolved behavior
- no new trade-management claim is upgraded to “supported” without evidence

## Verification plan

### For `stats`

- capture live `/statistics` payloads and route-render state
- record source provenance for each surfaced dataset
- compare normalized CLI output against raw payloads
- keep a raw escape hatch when schemas or source fields drift

### For `dashboard`

- capture live `/dashboard` render state and backing payloads
- verify owner-level summaries against visible UI/account state
- only expose points/rewards fields that can be matched consistently

### For `account`

- cross-check aggregated output against existing `account status`, `account positions`, `account history`, and `account stability-pools`
- verify shell-position classification on known closed state patterns
- ensure aggregation does not double-count wallet, deposited, pending, and claimable balances

### For `/trade` semantics

- capture the surfaced route states for add margin / reduce / leverage adjust
- decode any associated txs/receipts before making support claims
- document edge cases separately from the already-verified explicit `Close` path
- keep route-truth, command-truth, and public wording aligned

## Risks

- current-app helper / API schemas may drift
- dashboard/statistics data may be useful but not stable enough for over-normalized contracts
- owner aggregation can become misleading if balances are double-counted across wallet and protocol states
- `/trade` management surfaces may render more clearly than they decode; proof still has to come from evidence, not UI labels alone

## Non-goals and guardrails

- Do not turn this into a generic trading bot milestone.
- Do not present governance as “done” because some child routes render.
- Do not muddy the verified close story with speculative new close narratives.
- Do not hide uncertainty: when a source is partial or inferred, say so.

## Bottom line

The next public milestone should make SigmaCLI better at **seeing**, **explaining**, and **classifying** Sigma state before it tries to automate more of Sigma. That means: `stats`, `dashboard`, richer `account` aggregation, and evidence-backed proof of the remaining `/trade` management semantics — while keeping execution claims intentionally narrow.
