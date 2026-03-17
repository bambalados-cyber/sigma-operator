# STATUS

_Last updated: 2026-03-17_

## Snapshot

SigmaCLI is in an architectural transition.

Current honest headline:

- **shipped today:** evidence-first, read-heavy operator tooling
- **next build focus:** wallet backend/signing abstraction and direct route execution architecture
- **not the product architecture:** browser automation or accessibility-driven control

## Most important verified truths

These remain the core repo truths:

- tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d`
  - verified **partial repay / partial close**
  - reduced debt by `0.79 bnbUSD`
  - did **not** remove raw collateral
- tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092`
  - verified **terminal explicit `/trade` close**
  - burned full remaining debt: `3.2205711509703163 bnbUSD`
  - removed full remaining collateral: `0.014954999999999998 BNB`
  - paid out **`6.792825626759770802 USDT`**
- explicit `/trade` `Close` is distinct from `Adjust Leverage`
- position / NFT `#158` remained wallet-owned after full economic close, but only as a **zero-state shell**:
  - `rawColls = 0`
  - `rawDebts = 0`

## Current shipped surface

Implemented now:

- `capture`
- `decode`
- `plan`
- `abi inspect` / `abi refresh`
- `account status`
- `account positions`
- `account history`
- `account mint-close-readiness`
- `account stability-pools`
- `account bnbusd-trace`
- `config`
- `governance ...` scaffolds

This is real shipped value, but it is still primarily a read/evidence stack.

## What changed in the public framing

The repo is now explicitly centered on:

- wallet connectivity
- signer/backend abstraction
- execution policy
- direct route adapters
- `plan -> execute -> verify`
- post-state verification

The repo is explicitly **not** centered on:

- browser interaction as the core execution model
- accessibility/UI automation as the product contract
- governance as the current top-level focus

## Current route truth

### Strongest verified areas

- `/trade`
  - explicit `Close` path is verified distinct from `Adjust Leverage`
  - terminal close is verified onchain
- `/mintv2`
  - BNB -> bnbUSD mint open is verified live
  - partial repay / partial close semantics are real and modeled read-first in the CLI
- `/earn`
  - deposit and delayed withdraw semantics were observed live
  - read-side classification here is useful and real

### Important caution

The repo should still avoid overclaiming:

- broad wallet execution support
- full route coverage
- governance execution support
- browser-driven automation as a supported core path

## Near-term milestone direction

See [`MILESTONE_NEXT.md`](MILESTONE_NEXT.md) and [`WALLET_ARCHITECTURE.md`](WALLET_ARCHITECTURE.md).

The next milestone is:

1. build the wallet foundation first
2. make policy/config explicit
3. define the command spine around `auth`, `status`, `doctor`, `plan`, `execute`, and `verify`
4. add first direct route adapters in the strongest-evidence areas

## Best reader path from here

- [`README.md`](README.md)
- [`WALLET_ARCHITECTURE.md`](WALLET_ARCHITECTURE.md)
- [`SPEC.md`](SPEC.md)
- [`MILESTONE_NEXT.md`](MILESTONE_NEXT.md)
- [`SIGMA_CLI_COMMAND_SPEC_NEXT.md`](SIGMA_CLI_COMMAND_SPEC_NEXT.md)
- [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md)

## Bottom line

SigmaCLI already has a credible public story.

That story is now:

> **a wallet-aware operator CLI that is strong on evidence today and is being rebuilt around direct wallet-backed route execution, not browser automation.**