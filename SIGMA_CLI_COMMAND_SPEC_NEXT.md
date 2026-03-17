# SigmaCLI command spec — next phase

_Last updated: 2026-03-17_

## Purpose

Define the next concrete command surface for SigmaCLI after the architectural correction:

- SigmaCLI should connect to wallets, not browsers
- execution should come from direct route adapters, not UI automation
- read / plan / verify remains core, but now as the safety substrate for guarded execution

This document is a **target command spec** for the next build phase. It does **not** claim that the full surface below is already shipped.

See also:

- [`WALLET_ARCHITECTURE.md`](WALLET_ARCHITECTURE.md)
- [`MILESTONE_NEXT.md`](MILESTONE_NEXT.md)
- [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md)

## Command spine

The next stable command spine should be:

- `auth`
- `status`
- `doctor`
- `plan`
- `execute`
- `verify`

Existing families such as `decode`, `account`, `capture`, `abi`, and `config` remain useful supporting layers.

## 1) `auth`

Purpose:

- discover backends
- connect a profile
- inspect wallet/session state
- switch active profile
- disconnect cleanly

Exact target shape:

```bash
sigma auth backends
sigma auth connect --backend readonly --rpc-url "$SIGMA_OPERATOR_BNB_RPC_URL"
sigma auth connect --backend external-session --wallet rabby --session default
sigma auth connect --backend local-key-env --env-var SIGMA_PRIVATE_KEY --label dev
sigma auth status
sigma auth use default
sigma auth disconnect --profile default
```

Expected output fields:

- backend kind
- selected profile
- address
- chain id
- capability flags (`read`, `sign_tx`, `send_tx`, `wait_receipt`)
- approval policy summary

## 2) `status`

Purpose:

- summarize the current wallet/route/operator state
- provide an execution-aware top-line summary

Exact target shape:

```bash
sigma status summary
sigma status wallet
sigma status routes
sigma status balances --owner 0x...
sigma status position --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb
```

Expected output fields:

- active profile
- route capability summary
- balances and repay asset availability
- position classification
- shell-position classification where relevant

## 3) `doctor`

Purpose:

- run preflight checks before execution
- fail early on backend, policy, chain, allowance, or route problems

Exact target shape:

```bash
sigma doctor auth
sigma doctor config
sigma doctor route trade.close --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb
sigma doctor route mint.repay --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79
sigma doctor route earn.claim --pool <pool-id>
```

Doctor should explicitly classify:

- backend ready / not ready
- chain match / mismatch
- policy satisfied / blocked
- balance sufficient / insufficient
- route supported / planned / unsupported
- verification path available / incomplete

## 4) `plan`

Purpose:

- build an execution artifact without sending anything
- convert route intent into concrete steps and expected post-state

Exact target shape:

```bash
sigma plan trade close --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79
sigma plan mint repay --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79 --target-ltv 0.65
sigma plan earn deposit --pool <pool-id> --asset USDT --amount 1
sigma plan earn claim --pool <pool-id>
```

Plan artifacts should include:

- route key
- maturity label
- backend requirements
- approval mode implied by policy
- expected tx count / steps
- expected post-state checks
- route-specific notes and warnings

## 5) `execute`

Purpose:

- execute only through a route adapter
- prefer execution from an explicit plan
- persist tx artifacts automatically

Exact target shape:

```bash
sigma execute --plan plan.json
sigma execute trade close --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79
sigma execute mint repay --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79 --from-plan plan.json
```

Execution rules:

- refuse when backend capabilities are missing
- refuse when route maturity is insufficient under current policy
- refuse when approval/slippage policy is violated
- persist plan, tx hash, receipt, and verification handoff data

## 6) `verify`

Purpose:

- verify actual post-state after planning or execution
- classify success, partial success, mismatch, or uncertainty

Exact target shape:

```bash
sigma verify tx --tx-hash 0x...
sigma verify plan --plan plan.json
sigma verify route trade.close --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb
sigma verify position --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb
```

Verification should check things like:

- debt delta
- collateral delta
- payout asset
- remaining position state
- zero-state shell NFT classification

## Backend model used by the command spine

The command spine assumes these backend types:

- `readonly`
- `external-session`
- `local-key-env`

Important note:

- an external wallet like Rabby may back `external-session`
- SigmaCLI still treats it as a signer/session provider, **not** as a browser-automation target

## Route adapter priority order

The first route adapters should be built in this order:

1. `trade.close`
2. `mint.repay`
3. `earn.deposit`
4. `earn.claim`

Why:

- they follow the strongest existing evidence
- they preserve the already-proven semantic distinctions
- they keep the first execution phase narrow and honest

## Policy model assumptions

The command surface assumes explicit policy controls for:

- approval mode: `exact`, `unlimited`, `custom`
- verification requirement
- route enablement
- slippage defaults and caps
- whether unverified routes are allowed at all

## Existing supporting families that remain important

Even after the new command spine lands, these remain core support layers:

- `decode` for evidence and tx interpretation
- `account` for deep owner/position state reads
- `config` for persisted operator policy
- `capture` for reverse-engineering and validation artifacts
- `abi` for ABI inspection and refresh

## Explicit non-goals for this command phase

This command spec does **not** imply:

- browser automation as the runtime contract
- full governance execution support
- full route coverage across Sigma
- production-safe support for every visible surface

## Bottom line

The next SigmaCLI command surface should feel like this:

> **authenticate a backend, inspect status, doctor the route, plan the action, execute through a direct adapter, then verify post-state.**

That is the command shape the repo should now optimize around.