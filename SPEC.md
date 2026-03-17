# SigmaCLI repo spec

_Last updated: 2026-03-17_

## 1) Purpose

SigmaCLI (`sigma-operator`) is a wallet-aware operator CLI for **Sigma on BNB Chain / BSC**.

Its long-term job is to let an operator or agent:

- inspect Sigma state directly
- connect to a wallet/signing backend
- plan route-specific actions before signing
- execute guarded protocol/app interactions through direct adapters
- verify post-state after execution

Its current shipped job is narrower and already useful:

- capture evidence
- decode calldata, txs, receipts, and logs
- inspect account and position state
- model route semantics in read-first form

## 2) Core architecture rule

SigmaCLI is now built around this rule:

> **wallet connectivity and direct route interaction are the product architecture; browser automation is not.**

Browser/UI work may still help with:

- route discovery
- reverse-engineering
- validation
- evidence capture

But it is not the runtime contract the repo should optimize around.

## 3) Trust model

SigmaCLI follows a **read / plan / execute / verify** trust model.

### Read

Use chain reads, Sigma APIs, and decoded evidence to understand actual current state.

### Plan

Create an explicit action plan before signing. That plan should state:

- route
- inputs
- required assets
- required backend capabilities
- approval behavior
- expected post-state

### Execute

Only execute when:

- the route adapter exists
- the backend supports the required capabilities
- policy checks pass
- the route maturity is honest enough for bounded execution

### Verify

Re-read state after submission.

A tx hash alone is not a success condition. SigmaCLI should verify:

- receipt state
- balance or debt deltas
- position changes
- payout asset where relevant
- shell-position semantics where relevant

## 4) Current verified truths to preserve

These remain part of the public repo truth:

- explicit `/trade` **Close** is distinct from `Adjust Leverage`
- tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` is verified **partial repay / partial close**
- tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092` is verified **terminal `/trade` close**
- the terminal close paid out verified **USDT**
- a fully closed economic position can still remain as a wallet-owned **zero-state shell NFT** with zero collateral and zero debt

These truths matter because the future execution layer must preserve them in both planning and verification.

## 5) Product shape

SigmaCLI should be thought of as five layers.

### Layer 1 — evidence and route truth

- capture
- decode
- ABI inspection
- route-truth registry

### Layer 2 — read-side account state

- account status
- positions
- history
- repay readiness
- stability-pool state
- asset tracing

### Layer 3 — wallet backend and policy

- backend selection
- auth/session state
- approval policy
- slippage policy
- route enablement policy

### Layer 4 — route-specific adapters

Examples:

- `trade.close`
- `mint.repay`
- `earn.deposit`
- `earn.claim`

Each route adapter should be explicit and independently matured.

### Layer 5 — verification

- tx receipt verification
- post-state verification
- discrepancy classification
- saved artifacts for operator review

## 6) Backend model

SigmaCLI should support a small set of backend types.

### `readonly`

- no signing
- no tx submission
- default lowest-risk mode

### `external-session`

- externally managed wallet/signing session
- may be backed by a wallet like Rabby
- SigmaCLI treats it as a signer/session provider, not a browser UI target

### `local-key-env`

- explicit env-var key loading for dev/test or tightly controlled automation
- secondary path, not the default public recommendation

### Optional later session backends

- walletconnect-style session backends
- other signer bridges

See [`WALLET_ARCHITECTURE.md`](WALLET_ARCHITECTURE.md) for the detailed backend model.

## 7) Command model

The next stable command spine should be:

- `auth`
- `status`
- `doctor`
- `plan`
- `execute`
- `verify`

Current shipped families such as `capture`, `decode`, `account`, `abi`, and `config` remain important. They become supporting layers around that spine.

## 8) Route capability model

Every route should have an explicit capability record.

That record should say:

- whether read support exists
- whether plan support exists
- whether execute support exists
- whether verify support exists
- which backends are allowed
- what approval behavior is expected
- what post-state checks define success
- what maturity label applies

This keeps SigmaCLI from drifting into fake generic support.

## 9) Current repo stage

Today the repo is best described as:

- **shipped and credible on read-side operator work**
- **architecturally pivoting toward wallet-backed direct execution**
- **not yet a broad production execution CLI**

That is an honest and useful public position.

## 10) Current focus and non-focus

### Current focus

- wallet backend abstraction
- execution policy
- plan / execute / verify flow
- direct route adapters
- post-state verification

### Not the current focus

- governance-first expansion
- broad route marketing
- browser automation as runtime architecture
- pretending support exists where only UI visibility exists

## 11) Milestone direction

The next milestone is not “add more random surfaces.”

It is:

1. build the wallet foundation first
2. define the command spine clearly
3. add route capability and policy gating
4. land the first direct route adapters in the strongest verified areas

See [`MILESTONE_NEXT.md`](MILESTONE_NEXT.md) and [`SIGMA_CLI_COMMAND_SPEC_NEXT.md`](SIGMA_CLI_COMMAND_SPEC_NEXT.md).

## 12) Bottom line

SigmaCLI should become a **wallet-connected operator shell** for Sigma:

- direct where possible
- guarded by policy
- explicit about maturity
- verified after every action

That is the product story the repo should now optimize for.