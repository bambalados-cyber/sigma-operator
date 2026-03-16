# Sigma CLI status and public-repo path

_Last updated: 2026-03-16_

Purpose: give maintainers and future contributors one stable repo-quality memo for where `sigma-operator` started, what the Part 2 frontier achieved, what changed, what is still unresolved, and what this repo needs before it is comfortable as a public contributor-facing project.

This is a **status + trajectory** document, not a replacement for the run ledger.
For attempt-by-attempt history, use `SIGMA_RUN_LEDGER.md`.
For the current compact dashboard, use `STATUS.md`.

---

## Current snapshot

Best current reading:
- `sigma-operator` has crossed from vague exploration into **evidence-backed, controlled CLI/operator testing**.
- The repo is already useful as an **operator-first, read-heavy, evidence-first** Sigma CLI.
- The repo is **not** yet ready to promise broad execution coverage, generic governance coverage, or stable support for every visible Sigma route.

In plain terms:
- the core capture/decode/plan/read-only account foundation is real
- important live BNB-chain route truth now exists for `/trade`, `/earn`, and `/mintv2`
- several earlier assumptions were corrected by evidence
- the next phase is narrower and more contributor-friendly than the original frontier, but it still has unresolved execution-path questions

---

## Initial intent

The project started as an operator CLI for Sigma on **BNB Chain / BSC** with a deliberately honest scope:
- capture app/network evidence
- decode calldata, txs, receipts, and logs
- inspect Sigma ABIs and cached contract surfaces
- generate operator planning output for named Sigma operations
- add read-only account/portfolio visibility without pretending to be an execution bot

The repo has consistently aimed to be:
- **evidence-first** rather than speculative
- **BNB-native** in naming and backend guidance
- explicit about **what is verified**, **what is inferred**, and **what is still blocked**

---

## Initial plan

The first major execution frame was **Part 2**.
Its purpose was not “build everything,” but to answer a narrower question:

> Is there enough live verification to stop broad exploration and start disciplined CLI-based testing?

Part 2 focused on:
- restoring reproducible connected Sigma state on BNB Chain
- understanding the hidden Rabby boundary behind Sigma `TRANSACTION... 5/6`
- classifying Long and Short truthfully
- resolving `/earn` with evidence instead of guesses
- resolving `/mintv2` with evidence instead of guesses
- syncing repo files so the truth lived in Git, not in chat memory

That plan largely succeeded, and the repo frontier moved from discovery work into tighter route-truth and position-management work.

---

## What was achieved

### Core CLI foundation
Implemented and documented:
- runnable CLI launcher: `./sigma`
- capture workspace scaffolding
- browser-helper capture support
- HAR / devtools import flow
- raw calldata / tx / receipt / log decode
- batch decode over capture directories
- partial `routeEvidence` comparison against named Sigma operations
- plan surfaces for trade, mint, and redeem-related operations
- ABI inspect / refresh bridge into the upstream Sigma skill cache

### Backend and live read path hardening
Landed and verified:
- shift from explorer-first assumptions to **BNB RPC / MegaNode / NodeReal-compatible** live guidance
- real read-only BNB RPC validation on chain `56`
- `decode --tx-hash` over live RPC
- BNB-native env and flag naming

### Read-only account/position coverage
Landed and verified:
- `sigma account status`
- current pool discovery across the observed live pool set
- no-auth current-app enrichments for entry price and history where available
- `sigma account mint-close-readiness`
  - now includes an explicit partial-close preview model (`--repay-amount`, optional `--target-ltv`, optional `--withdraw-amount`)
  - now carries the resolved CLI approval-policy context
- `sigma account stability-pools`
- `sigma account bnbusd-trace`
  - now carries approval-policy context alongside repay-source buckets
- persisted CLI approval-policy support via:
  - `sigma config show`
  - `sigma config init --approval-policy ...`
  - `sigma config set-approval-policy --approval-policy ...`

### Live route truth achieved
Evidence now supports the following statements:
- `/trade`
  - a live Long position was opened and later observed back in Sigma
  - the old `TRANSACTION... 5/6` mystery is no longer a mystery; it is tied to real Rabby sign/approval flow(s)
  - in the later live-open state, Sigma exposed **position management**, not a fresh concurrent Short entry form
- `/earn`
  - a bounded `1 USDT` deposit path completed through a real Rabby popup chain
  - the deposit resulted in an unstaked receipt balance around `0.99 SigmaSP1`
  - a later unwind created a **timed withdraw/redeem process**, not immediate wallet return
- `/mintv2`
  - bounded mint open is live and repeatable on the BNB -> bnbUSD lane
  - close is a real visible surface
  - earlier `Repay Balance: 0.00` was a real wallet-state blocker
  - after the delayed `/earn` claim produced wallet-held `bnbUSD`, the frontier shifted from repay-balance absence to approval-shape / allowance control
- `/governance`
  - route exists, but current observed behavior remains **blank / non-rendered**

### Repo-truth improvements
The repo now contains a much stronger documentary trail:
- plan/gate/checklist files for Part 2
- a concrete run ledger
- handoff and next-phase notes
- mint-close contract/state mapping
- corrected next-phase CLI command map

---

## What changed from the original assumptions

This is the most important contributor-facing section. Several material assumptions changed once live evidence existed.

### 1) Explorer-first was the wrong default
Earlier mental model:
- explorer/proxy APIs could be treated as the default live fetch path

Current truth:
- on BNB Chain, **RPC is the canonical live path**
- explorer access is secondary, optional, and provider-limited

### 2) `/governance` should not be treated as a working top-level app surface
Earlier temptation:
- use generic governance language as if the visible route were healthy

Current truth:
- `https://sigma.money/governance` is currently observed as **BLANK_ROUTE / NON_RENDERED**
- a CLI `governance` namespace is acceptable only as a **structural umbrella** over route-specific targets such as `xsigma`, `vote`, and `incentivize`
- it is **not** proof that the app-level `/governance` page works

### 3) Mint close is not just a UI mystery
Earlier uncertainty:
- maybe close would work once the token was visible in Rabby, or after more collateral adds

Current truth:
- chain-state evidence now strongly supports **wallet-held `bnbUSD` repay semantics**
- the CLI can now classify repay sources more precisely than a bare `Repay Balance: 0.00` screenshot:
  - wallet-held `bnbUSD`
  - allowance / approved-but-unspent ceiling
  - residual `bnbUSD` still represented by stability-pool shares
  - pending delayed redeem vs claimable-after-unlock via `redeemRequests(address)`
- adding collateral did not itself satisfy repay requirements, and delayed earn exits must be distinguished from immediate wallet-held repay balance

### 4) `/earn` was more real than the earlier stall suggested
Earlier uncertainty:
- the `TRANSACTION... 1/3` state might be a frontend stall

Current truth:
- the earlier stall was a **hidden wallet boundary chain**
- deposit completed
- the resulting position is more nuanced than “user staked”; the observed post-deposit state was an unstaked receipt balance, and a later withdraw produced a timed process rather than instant wallet assets

### 5) Trade management is less symmetric than expected
Earlier temptation:
- assume open, add-margin, reduce, and close would surface cleanly once one path was proven

Current truth:
- the collapsed current management surface still starts at **Adjust Leverage**, but the expanded live long card now truthfully exposes a distinct **Close** tab
- the explicit close panel is not an adjust-to-zero alias: `Adjust Leverage` bottoms at `1.00x`, while the close panel has its own `Approve & Close` path and payout selector

---

## Current truthful frontier

### Verified now

#### Repo / CLI level
- the CLI foundation is runnable and useful
- read-only decode and account surfaces are real
- route-truth documentation is much stronger than it was at the start

#### Live route level
- `/trade`
  - Long: verified live
  - Short: truthfully classified in the later live-open state as **not currently exposed for fresh concurrent entry**
  - current truthful management path: collapsed `Adjust` + expandable explicit `Close`
  - explicit `Close` is now verified end to end onchain via tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092`
  - verified terminal-close semantics:
    - payout asset = `USDT`
    - payout amount = `6.792825626759770802 USDT`
    - position / NFT `#158` remains wallet-owned only as a zero-state shell (`rawColls = 0`, `rawDebts = 0`)
- `/earn`
  - bounded deposit completed
  - unstaked receipt state observed (`~0.99 SigmaSP1`)
  - withdraw/redeem timing semantics observed
- `/mintv2`
  - BNB -> bnbUSD mint open verified live
  - close-side semantics are now documented more precisely:
    - earlier `Repay Balance: 0.00` observations were real
    - tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` is verified as partial repay / partial close only
    - mint-close readiness remains a useful read-side CLI/account problem, but it is no longer the repo’s main unresolved execution story for position `#158`
- `/governance`
  - route exists but remains blank / non-rendered in observed current state

### Still inferred or incomplete

These are **not** settled enough to present as finished support:
- exact write-path calldata/selector/spender/min-output details for mint close as a dedicated `/mintv2` close path
- whether matured `/earn` withdrawal will produce wallet-held `bnbUSD` in the way needed for future mint-close workflows
- deeper add-margin / reduce truth beyond the now-verified explicit `/trade` close path
- live execution truth for `xsigma`, `vote`, `incentivize`, and `dashboard`
- stable public API/schema contracts for every analytics/statistics dataset

---

## What is still open

The repo is no longer blocked by basic viability. It is blocked by narrower, better-defined questions.

### Product/route questions still open
1. **Mint close final path**
   - exact `/mintv2` close write path is still not fully captured as its own standalone execution story
   - repay-asset dependency is understood, but the dedicated mint-close execution shape is still not fully mapped

2. **Trade position-management depth**
   - explicit `/trade` `Close` is now proven with wallet-confirmed onchain completion
   - explicit add-margin / reduce truth still need evidence before they should appear as real supported flows

3. **Route-specific governance/dashboard truth**
   - `xsigma`, `vote`, `incentivize`, `dashboard`, and `stats` are the right next conceptual surfaces
   - but only parts of that surface map are currently proven deeply enough to present as more than planned/read-first work

4. **Post-timed `/earn` unwind consequences**
   - the repo has strong evidence for delayed withdraw semantics
   - the next important truth question is what assets actually become wallet-held after maturity and whether that changes future mint-close readiness

### Repo/package questions still open
- contributor onboarding is still spread across multiple docs rather than one simple contributor path
- command stability is documented informally, not yet as a public-facing stability policy
- automated test expectations for read-only vs live/manual verification are not yet fully packaged for outside contributors

---

## Recommended next steps

### Immediate technical next steps
1. **Re-check the matured `/earn` withdraw state before doing more mint-close speculation**
   - confirm what assets are actually claimable / received
   - then re-run `sigma account mint-close-readiness` for any future live position that needs it

2. **Capture the exact mint-close preview/write path only after repay readiness exists again**
   - avoid further blind UI looping when no repay-ready position is live

3. **Package the verified explicit trade-close path cleanly for contributors**
   - keep the distinction explicit between:
     - partial repay / partial close
     - terminal `/trade` close
     - zero-state shell NFT post-close semantics

4. **Keep expanding read-only value first**
   - `stats`
   - richer `account` views
   - route-specific read models for `dashboard` and governance-side surfaces

### Documentation / maintenance next steps
1. keep `STATUS.md` compact
2. keep `SIGMA_RUN_LEDGER.md` as the attempt-by-attempt log
3. use this document as the stable maintainer/contributor orientation note
4. avoid documenting unverified routes/assets as supported just because the app or bundle hints they may exist

---

## Public-repo / contributor-readiness guidance

If this repo is going to become a public contribution target, it should lean into what it already does well: **truthful operator tooling with explicit evidence boundaries**.

### What the repo is ready to say publicly now
Reasonable public framing today:
- operator-focused Sigma CLI for BNB Chain
- strong capture/decode/plan/read-only account foundation
- evidence-backed route notes for `/trade`, `/earn`, and `/mintv2`
- verified distinction between:
  - partial repay / partial close
  - terminal explicit `/trade` close
  - zero-state shell NFT post-close state
- explicit distinction between verified live support, visible-but-blocked paths, docs-only surfaces, and blank routes

### What the repo should not promise yet
Not yet safe to promise publicly:
- broad “full Sigma CLI” execution coverage
- stable governance execution support
- broad asset coverage beyond the verified BNB-centric frontier
- automatic or production-safe transaction execution

### Recommended public-repo evolution

#### 1) Docs structure
Before wider contributor onboarding, add or tighten:
- `CONTRIBUTING.md`
- `TESTING.md` or `docs/testing.md`
- a short `ARCHITECTURE.md` describing capture / decode / route-truth / account modules
- a stable “source of truth” section in README explaining the role of:
  - `STATUS.md`
  - `SIGMA_RUN_LEDGER.md`
  - this document
  - the Part 2 pack

#### 2) Command stability policy
Classify commands explicitly, for example:
- **stable read-only**
- **experimental read-only**
- **planned**
- **wallet-required / not yet verified**

That avoids accidental overclaiming in help text and future PRs.

#### 3) Route-truth registry
The repo should keep a canonical machine-readable or code-level truth layer for route status, such as:
- `verified_live`
- `visible_but_blocked`
- `blank_route`
- `docs_only`
- `archived`
- `planned`

This would make contributor changes safer and keep docs/help text aligned.

#### 4) Safety notes for live work
A public repo should preserve the existing live-testing discipline:
- no secrets committed
- no real API keys in artifacts
- no MAX by default
- Unlimited Approval OFF by default in documented live tests
- bounded-value examples only
- explicit redaction guidance for wallet prompts, RPC endpoints, and personal addresses where appropriate

#### 5) Testing expectations
Split tests into clear layers:
- **unit/fixture tests** for decode, ABI, parsers, and account helpers
- **read-only integration tests** for RPC/API-backed code where feasible
- **manual/live verification notes** for wallet-bound routes

Contributors should not have to guess whether a command is expected to be CI-safe, mock-backed, or manual-only.

---

## Suggested contributor reading order

If you are new to the repo, read in this order:
1. `README.md`
2. `STATUS.md`
3. this document
4. `SIGMA_RUN_LEDGER.md`
5. `SIGMA_CLI_COMMAND_SPEC_NEXT.md`
6. `MINT_CLOSE_CONTRACT_MAP_2026-03-16.md` if you are touching mint-close logic

If you are continuing live-verification work, also read:
- `PART2_PLAN.md`
- `PART2_CLI_TESTING_GATE.md`
- `NEXT_PHASE_POSITION_MANAGEMENT_2026-03-15.md`

---

## Bottom line

`sigma-operator` is no longer just a rough exploration repo.
It now has a real operator CLI core, real live-route evidence, and a much clearer map of where Sigma truth ends and speculation begins.

That makes it a plausible future public repo — but only if it keeps the same discipline that got it here:
- document the frontier honestly
- separate verified support from planned support
- prefer read-first value before broad execution claims
- treat every live wallet boundary as something to classify, not hand-wave


## Update — 2026-03-16 remaining-blockers closure pass

Material truth tightened in this pass:
- `/dashboard` and `/statistics` are no longer just abstract route targets; they were observed rendering live content in the attached Chrome session
- `/xsigma`, `/vote`, and `/incentivize` also rendered live child-route product surfaces
- `/governance` should still be treated as the broken umbrella route, not the source of governance truth
- mint-close should no longer be documented as inherently max-approval-only:
  - current frontend bundle evidence includes a finite-approval branch when Unlimited Approval is OFF
  - the remaining blocker is the live UI / wallet-popup mismatch, which still needs an end-to-end replay

## Update — 2026-03-16 post-close verification pack

Material truth tightened further in this pass:
- the end-to-end exact-approval replay was not only captured live, it was also verified afterward from direct CLI/no-auth/read-only evidence
- Sigma no-auth history now records replay tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` as `CLOSED`
- but current account state still shows the same live position NFT `#158` with:
  - `rawColls = 0.014954999999999998 BNB`
  - `rawDebts = 3.220571150970316111 bnbUSD`
- decode of the replay tx proves the action was:
  - `0.79 bnbUSD` repay
  - `deltaColls = 0`
  - `deltaDebts = -0.79`
  - same NFT returned to the wallet

Contributor-facing meaning:
- the repo can now say something more precise than “mint close works”:
  - a bounded close-side action succeeded on the exact-approval path
  - the verified effect was a **partial repay / partial close**, not a terminal full close
- the repo should also document a current Sigma-history caveat:
  - `CLOSED` in the no-auth history feed is not reliable as proof that the position no longer exists
  - current state must still be cross-checked against live position/account reads

Trajectory impact:
- this strengthens the repo’s “evidence-first, read-verified” posture materially
- it also suggests a clean next packaging distinction for contributors:
  - `verified partial close / repay`
  - `not yet verified full close / collateral exit`


## Update — 2026-03-17 bounded Priority A/B pass

What newly became true:
- `/trade` is no longer honestly described as `Adjust`-only
- the live long card can be expanded into a real `Open` / `Close` widget
- `Adjust Leverage` still exists, but bottoms at `1.00x`, which means full close is not just an adjust-to-zero variant
- the live close payout selector was observed with `BNB`, `USDT`, `WBNB`, and `bnbUSD` options
- a bounded full-close setup reached a live-ready state (`0.014954999999999998` xPOSITION, projected `6.807260 USDT`, `Unlimited Approval` OFF) and Sigma advanced to in-app `TRANSACTION... 2/6` after `Approve & Close`

What is still missing:
- wallet-confirmed continuation of the Rabby popup boundary
- tx hash / receipt / post-close state proof
- any claim that Priority A or Priority B completed

Maintainer implication:
- trade close should now be documented as a **real surfaced UI path blocked at wallet-popup control**, not as a merely hypothetical or hidden path

## Update — 2026-03-17 post-manual-sign verification pass

What newly became true:
- the previously blocked bounded trade-close submission was manually signed through Rabby and then re-verified from fresh live state
- Priority A is now verified complete onchain via tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092`
- the prior Long was economically fully closed:
  - position/NFT `#158` is still wallet-owned as a shell
  - but `rawColls = 0`
  - and `rawDebts = 0`
- the close outcome is now exact rather than preview-only:
  - received asset = `USDT`
  - received amount = `6.792825626759770802 USDT`
  - full collateral removed = `0.014954999999999998 BNB`
  - full debt burned = `3.2205711509703163 bnbUSD`

What this changes for contributor-facing truth:
- the repo should no longer frame the situation as “partial close still pending a real full close proof”
- it should distinguish the two verified events explicitly:
  - `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` = verified partial repay
  - `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092` = verified terminal trade close
- Priority B is no longer an open execution goal, because no mint debt/collateral remains on the verified closed position

Maintainer implication:
- this materially improves the project’s public credibility story: the repo now holds not only bounded close-side evidence, but a full onchain-verified terminal close result with exact post-state and exact received asset amount
