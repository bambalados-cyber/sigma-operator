# STATUS

_Last updated: 2026-03-17_

## Snapshot

SigmaCLI is now a **public-shareable, evidence-first operator CLI** with real value on the read side.

Current honest headline:

- **strong today:** capture, decode, plan, ABI inspection, and read-only account / route evidence
- **verified live highlight:** explicit `/trade` close is real, distinct from `Adjust Leverage`, and verified onchain
- **not the current story:** generic governance coverage or broad write automation

## Most important verified truths

- tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d`
  - verified **partial repay / partial close**
  - reduced debt by `0.79 bnbUSD`
  - did **not** remove raw collateral
- tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092`
  - verified **terminal explicit `/trade` close**
  - burned full remaining debt: `3.2205711509703163 bnbUSD`
  - removed full remaining collateral: `0.014954999999999998 BNB`
  - paid out **`6.792825626759770802 USDT`**
- position / NFT `#158` remained wallet-owned after full economic close, but only as a **zero-state shell**:
  - `rawColls = 0`
  - `rawDebts = 0`
- mint-close semantics remain important, but the repo should now distinguish clearly between:
  - partial mint-side repay / partial close evidence
  - terminal `/trade` close evidence
  - shell-NFT post-close semantics

## Shipped command surface

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

See [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md) for the maturity labels.

## Current route truth

### Verified and useful now

- `/trade`
  - explicit `Close` path is verified distinct from `Adjust Leverage`
  - full terminal close is verified onchain
- `/earn`
  - deposit and delayed withdraw semantics were observed live
  - repo read-side classification here is useful and real
- `/mintv2`
  - BNB -> bnbUSD mint open is verified live
  - partial repay / partial close semantics are real and modeled read-first in the CLI

### Not yet safe to overclaim

- generalized write execution support
- add-margin / reduce semantics across all trade management paths
- full dedicated `/mintv2` close execution story independent of the verified `/trade` close result
- deep governance execution support

### Governance note

- `/governance` remains **blank / non-rendered** in observed current state
- route-specific children such as `/xsigma`, `/vote`, `/incentivize`, `/dashboard`, and `/statistics` are better next-phase read targets than governance-first framing

## Near-term milestone direction

Best next milestone after this repo-polish pass:

1. **expand route-specific read models before more execution claims**, especially:
   - `stats`
   - `dashboard`
   - richer account aggregation
2. **prove remaining `/trade` management semantics** beyond the now-verified explicit close path:
   - add margin
   - reduce
   - leverage-adjust edge cases
3. **only revisit dedicated `/mintv2` close execution capture on a new repay-ready live position**, not by muddying the already-verified terminal close story

## Source-of-truth reading order

- [`README.md`](README.md)
- [`SPEC.md`](SPEC.md)
- [`COMMAND_MATURITY.md`](COMMAND_MATURITY.md)
- [`SIGMA_RUN_LEDGER.md`](SIGMA_RUN_LEDGER.md)
- [`SIGMA_STATUS_AND_PUBLIC_REPO_PATH.md`](SIGMA_STATUS_AND_PUBLIC_REPO_PATH.md)

Historical execution-pack docs remain useful, but they are no longer the easiest public entrypoint.
