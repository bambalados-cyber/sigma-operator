# Next milestone: wallet foundation + first direct route adapters

_Last updated: 2026-03-17_

## Objective

Build the wallet layer first.

The next public milestone is no longer framed as "more browser-observed read coverage."

It is:

1. define and ship the wallet/signing backend abstraction
2. make execution policy explicit
3. establish a real `plan -> execute -> verify` flow
4. add direct route adapters where SigmaCLI already has the strongest evidence
5. keep browser/UI work as validation and research only

## Why this is the right next milestone

The repo already knows enough to make the product direction clear:

- SigmaCLI should connect to wallets, not browsers
- route execution should come from direct adapters, not accessibility or click automation
- read-first tooling is still crucial, but now as the safety substrate for execution
- the current strongest truths are route semantics and post-state evidence, not UI automation

So the next milestone should build the missing execution foundation instead of widening the read-only surface first.

## Preserved truths

This milestone keeps these existing truths intact:

- explicit `/trade` **Close** is distinct from `Adjust Leverage`
- terminal `/trade` close is verified onchain
- verified terminal close paid out **USDT**
- partial repay / partial close remains distinct from terminal close
- a closed economic position may persist as a wallet-owned **zero-state shell NFT**

Those are inputs to the new architecture, not facts to re-litigate.

## In scope

### 1) Wallet backend abstraction

Define and implement the common backend model for:

- `readonly`
- `external-session`
- `local-key-env`

Minimum requirements:

- explicit backend kind
- chain id and address visibility
- capability flags for read / sign / send / wait
- named profile selection

### 2) Policy and config model

Extend the operator config so it governs:

- default profile
- approval policy (`exact`, `unlimited`, `custom`)
- route enablement
- verification requirement
- slippage defaults and caps

### 3) Command spine

Define and begin landing the next command spine:

- `auth`
- `status`
- `doctor`
- `plan`
- `execute`
- `verify`

Minimum expectations for this milestone:

- `auth` can describe/connect backends
- `status` can summarize backend and route state
- `doctor` can run real preflight checks
- `plan` produces an explicit artifact
- `execute` is policy-gated
- `verify` checks post-state, not just receipts

### 4) Route capability registry

Create the adapter/capability layer that marks each route with:

- read support
- plan support
- execute support
- verify support
- required backend types
- approval behavior
- post-state checks
- maturity label

### 5) First direct route adapters

Prioritize route adapters in the strongest-evidence order:

1. `trade.close`
2. `mint.repay`
3. `earn.deposit`
4. `earn.claim`

Important rule:

- route adapters must stay route-specific
- no generic "execute Sigma action" abstraction as the first implementation

## Out of scope

Not part of this milestone:

- browser automation as runtime architecture
- accessibility-driven wallet interaction
- governance-first expansion
- pretending all Sigma routes are execution-ready
- broad route coverage just because UI pages render
- overpromising unsupported writes

## Success criteria

This milestone is successful when all of the following are true:

### Architecture

- the public docs clearly center on wallet backends and direct route interaction
- browser/UI work is explicitly described as non-core validation only
- the command spine is documented and internally consistent

### Foundation

- backend profiles exist
- policy/config is explicit
- route capability records exist
- `plan` and `verify` share a stable artifact model

### Execution readiness

- `doctor` can reject bad backend/policy/route states before execution
- `execute` is wired through route adapters rather than hand-wavy generic calls
- post-state verification is defined as part of success, not an optional afterthought

### Honesty

- the repo still does not claim broad execution support if only the foundation exists
- route maturity stays explicit
- current verified truths remain visible in README/spec/status docs

## Suggested implementation order

### Phase 1

- `WALLET_ARCHITECTURE.md`
- command spec rewrite
- config/policy extension
- backend interface and profiles

### Phase 2

- `auth`
- `status`
- `doctor`
- route capability registry

### Phase 3

- stable plan artifact
- stable verify artifact
- shared execution result persistence

### Phase 4

- first direct route adapter: `trade.close`
- then `mint.repay`
- then selected `/earn` flows

## Verification plan for this milestone

- validate backend selection and profile resolution without sending txs
- validate doctor output against real route/account state
- validate plan artifacts against known verified Sigma semantics
- validate verify output against known historic tx truths
- only then start bounded live execution for the first route adapter(s)

## Bottom line

The next SigmaCLI milestone is:

> **wallet layer first, direct route adapters second, execution only through policy-gated plan/verify flow.**

That is the cleanest path from a strong read/evidence CLI to a trustworthy execution-capable SigmaCLI.