# SigmaCLI (`sigma-operator`)

Evidence-first operator CLI for **Sigma on BNB Chain / BSC**.

SigmaCLI is strongest today on **capture, decode, planning, ABI inspection, and read-only account evidence**. It is **not** a generalized execution bot, and it does **not** pretend every visible Sigma route is fully mapped or execution-ready.

## What is verified right now

The repo can now say these things plainly and honestly:

- the surfaced `/trade` **Close** path is real and distinct from `Adjust Leverage`
- tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` is a verified **partial repay / partial close**
- tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092` is a verified **terminal `/trade` close**
- the verified terminal close paid out **USDT**: `6.792825626759770802`
- after full economic close, position/NFT `#158` remained wallet-owned as a **zero-state shell** with `rawColls = 0` and `rawDebts = 0`
- SigmaCLI is currently **more trustworthy on read/evidence than on broad execution semantics**

## Repo posture

This repo follows a simple rule:

> **Read first. Decode first. Verify first. Execute later, if at all.**

That means:

- prefer read-only RPC, decoded receipts, and app/no-auth evidence over speculation
- separate **verified**, **alpha/read-first**, **scaffold**, and **planned** surfaces
- avoid claiming that a route is supported just because the frontend bundle or app shell hints at it
- treat wallet-required flows as a higher bar than read-only flows

See also:

- [`STATUS.md`](STATUS.md) — compact current snapshot
- [`SPEC.md`](SPEC.md) — public repo spec and operating model
- [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md) — command/surface maturity labels
- [`SIGMA_RUN_LEDGER.md`](SIGMA_RUN_LEDGER.md) — chronological verification ledger
- [`SIGMA_STATUS_AND_PUBLIC_REPO_PATH.md`](SIGMA_STATUS_AND_PUBLIC_REPO_PATH.md) — maintainer trajectory memo

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

Explorer mode still exists, but it is **secondary / optional** on BNB Chain.

## Quick start

### 1) Inspect command groups

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

### 4) Model mint-close readiness without submitting anything

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

### 6) Start a capture workspace

```bash
./sigma capture start first-pass --target PoolManager --target BNBUSD
./sigma capture browser-helper captures/<session>
```

## Command groups

- `capture` — capture-session scaffolding and import helpers
- `decode` — calldata / tx / receipt / log decoding, including live tx-hash fetch via read-only RPC
- `plan` — plan-only operation modeling with explicit warnings and disambiguation notes
- `account` — read-only owner, position, stability-pool, and mint-close-readiness views
- `abi` — inspect or refresh the Sigma ABI cache
- `config` — persist operator-side approval-policy preferences
- `governance` — **truthful scaffold only**; structural CLI umbrella, not deep route support

For the exact maturity of each command family, read [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md).

## Project layout

- `sigma` — launcher script
- `sigma_operator/cli.py` — CLI entrypoint and command wiring
- `sigma_operator/account.py` — read-only account, pool, trace, and readiness logic
- `sigma_operator/decode.py` — tx/receipt/log ingest and decode helpers
- `sigma_operator/operations.py` — named operation models and routing hints
- `sigma_operator/surface_truth.py` — route-truth registry and governance surface metadata
- `STATUS.md` / `SIGMA_RUN_LEDGER.md` / `MINT_CLOSE_CONTRACT_MAP_2026-03-16.md` — repo truth and evidence docs

## Current verified route truth

### `/trade`

- live route and management surface are real
- explicit `Close` is verified distinct from `Adjust Leverage`
- full terminal close is verified onchain
- add-margin / reduce semantics still need more evidence before being presented as broadly supported

### `/earn`

- bounded deposit and delayed-withdraw semantics were observed live
- the repo can distinguish wallet-held balance, deposited shares, pending delayed redeem, and claimable-after-unlock state
- current repo value here is primarily read/evidence and operator interpretation

### `/mintv2`

- BNB -> bnbUSD mint open is verified live
- mint-close read-side semantics are useful and implemented
- partial repay / partial close is verified and distinct from terminal `/trade` close
- the repo should not overstate `/mintv2` as a fully generalized write surface

### Governance-related routes

Governance is **not** the center of repo truth right now.

- `/governance` remains the broken / non-rendered umbrella route in observed current state
- route-specific children like `/xsigma`, `/vote`, `/incentivize`, `/dashboard`, and `/statistics` are useful next-phase targets
- current `governance` CLI commands are honest scaffolds, not deep live integrations

## Limits

- no signing or production execution tooling
- no promise of broad route coverage just because a route renders or a bundle hints at it
- no stable governance execution support yet
- no committed secrets, wallet addresses, or private RPC endpoints
- live examples assume the operator supplies their own RPC endpoint and wallet context

## Contributor path

If you are new here, read in this order:

1. `README.md`
2. [`STATUS.md`](STATUS.md)
3. [`SPEC.md`](SPEC.md)
4. [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md)
5. [`SIGMA_RUN_LEDGER.md`](SIGMA_RUN_LEDGER.md)
6. [`MINT_CLOSE_CONTRACT_MAP_2026-03-16.md`](MINT_CLOSE_CONTRACT_MAP_2026-03-16.md) if you are touching mint-close logic

Then read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a PR.
