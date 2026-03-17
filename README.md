# SigmaCLI (`sigma-operator`)

Wallet-aware, evidence-first operator CLI for **Sigma on BNB Chain / BSC**.

SigmaCLI is moving toward a clear product shape:

> **connect to a wallet backend, talk to Sigma routes directly, plan actions, execute guarded calls, then verify post-state.**

That does **not** mean browser automation is the architecture.

Browser capture and UI research may still be useful for reverse-engineering or validation, but the core product direction is now:

- wallet connectivity
- signer/backend abstraction
- execution policy
- direct route adapters
- plan / execute / verify flow
- post-state verification

## What is verified right now

These truths remain core and should not be lost in the architecture rewrite:

- explicit `/trade` **Close** is real and distinct from `Adjust Leverage`
- tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` is a verified **partial repay / partial close**
- tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092` is a verified **terminal `/trade` close**
- the verified terminal close paid out **USDT**: `6.792825626759770802`
- after full economic close, position/NFT `#158` remained wallet-owned as a **zero-state shell** with `rawColls = 0` and `rawDebts = 0`

## Where the repo is today

Today the shipped repo is strongest on:

- capture
- decode
- plan-only modeling
- ABI inspection
- read-only account and position inspection
- repay-readiness and asset-trace analysis

So the honest current positioning is:

- **strong today:** read, plan, decode, verify
- **next build focus:** wallet layer first
- **not the product architecture:** browser or accessibility-driven automation

## Read this first

- [`WALLET_ARCHITECTURE.md`](WALLET_ARCHITECTURE.md) — target wallet/signing backend architecture and command spine
- [`SPEC.md`](SPEC.md) — public repo spec and operating model
- [`MILESTONE_NEXT.md`](MILESTONE_NEXT.md) — next milestone: wallet foundation + first direct route adapters
- [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md) — current shipped vs planned command maturity
- [`STATUS.md`](STATUS.md) — compact current snapshot
- [`SIGMA_CLI_COMMAND_SPEC_NEXT.md`](SIGMA_CLI_COMMAND_SPEC_NEXT.md) — exact next command surface
- [`SIGMA_RUN_LEDGER.md`](SIGMA_RUN_LEDGER.md) — verification ledger

## Repo posture

SigmaCLI now follows this rule:

> **Read first. Plan first. Verify first. Then execute only through explicit wallet backends and route adapters.**

That means:

- prefer read-only RPC, decoded receipts, and direct protocol/app evidence over speculation
- keep wallet-backed execution separate from read-only inspection
- make approval policy, slippage, and route maturity explicit
- verify post-state after execution instead of trusting tx submission alone
- treat browser/UI work as research and validation only

## Current command groups

Shipped today:

- `capture` — evidence collection helpers
- `decode` — calldata / tx / receipt / log decoding
- `plan` — plan-only modeling with warnings and disambiguation notes
- `account` — read-only owner, position, stability-pool, and repay-readiness views
- `abi` — inspect or refresh Sigma ABI cache
- `config` — operator-side approval-policy persistence
- `governance` — truthful scaffolds only, not deep live integration

Planned next command spine:

- `auth`
- `status`
- `doctor`
- `plan`
- `execute`
- `verify`

See [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md) for which parts are shipped versus planned.

## Install

From the repo root:

```bash
python3 -m pip install -e .
```

Or use the launcher directly:

```bash
./sigma --help
python3 -m sigma_operator.cli --help
```

## BNB RPC setup

Live read-only fetches should use a **BNB Chain RPC endpoint**.

```bash
export SIGMA_OPERATOR_BNB_RPC_URL="https://bsc-mainnet.nodereal.io/v1/YOUR_API_KEY"
export SIGMA_OPERATOR_BNB_RPC_TIMEOUT="20"
```

## Quick start

### 1) Inspect current shipped command groups

```bash
./sigma --help
./sigma account --help
./sigma decode --help
```

### 2) Decode a live tx hash over read-only BNB RPC

```bash
./sigma decode \
  --tx-hash 0xf1419c52735a27c0ca7ad8d25c8a6197076f5a134d4859e4ef03b05277ee7ddf \
  --fetch-source rpc \
  --bnb-rpc-url "$SIGMA_OPERATOR_BNB_RPC_URL"
```

### 3) Inspect a wallet's current Sigma positions

```bash
./sigma account status \
  --owner <owner-address> \
  --bnb-rpc-url "$SIGMA_OPERATOR_BNB_RPC_URL" \
  --include-history
```

### 4) Model mint repay / close readiness without submitting anything

```bash
./sigma account mint-close-readiness \
  --owner <owner-address> \
  --position-id 158 \
  --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb \
  --bnb-rpc-url "$SIGMA_OPERATOR_BNB_RPC_URL" \
  --repay-amount 0.79
```

### 5) Build a plan-only payload for an operation

```bash
./sigma plan open-long --asset BNB --amount 1 --leverage 3 --slippage-bps 50
./sigma plan mint-close -- --repay-amount 0.79
```

### 6) Review the target execution architecture

Read:

- [`WALLET_ARCHITECTURE.md`](WALLET_ARCHITECTURE.md)
- [`SIGMA_CLI_COMMAND_SPEC_NEXT.md`](SIGMA_CLI_COMMAND_SPEC_NEXT.md)
- [`MILESTONE_NEXT.md`](MILESTONE_NEXT.md)

## Current route truth

### `/trade`

- explicit `Close` is verified distinct from `Adjust Leverage`
- terminal close is verified onchain
- add-margin / reduce / full route coverage should not be overstated yet

### `/mintv2`

- BNB -> bnbUSD mint open is verified live
- partial repay / partial close semantics are verified and important
- dedicated mint-side execution should still be described carefully until direct route adapters are built

### `/earn`

- deposit and delayed-withdraw semantics were observed live
- current repo value here is strongest on read/evidence and state classification

### Governance-related routes

Governance is **not** the current center of the repo.

- `/governance` remains the broken / non-rendered umbrella route in observed current state
- route-specific children like `/xsigma`, `/vote`, `/incentivize`, `/dashboard`, and `/statistics` are real surfaces, but they are not the current architecture focus

## Limits

Today the repo does **not** claim:

- broad production execution support
- browser automation as a supported product core
- stable governance execution support
- full route coverage just because a frontend surface exists

## Contributor path

If you are new here, read in this order:

1. `README.md`
2. [`WALLET_ARCHITECTURE.md`](WALLET_ARCHITECTURE.md)
3. [`STATUS.md`](STATUS.md)
4. [`SPEC.md`](SPEC.md)
5. [`MILESTONE_NEXT.md`](MILESTONE_NEXT.md)
6. [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md)
7. [`SIGMA_RUN_LEDGER.md`](SIGMA_RUN_LEDGER.md)

Then read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a PR.