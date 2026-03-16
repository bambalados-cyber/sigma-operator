# Mint close contract map — 2026-03-16

Purpose: reduce the mint close question from UI guesswork to direct contract/state evidence.

## Bottom line

Best current reading:
- **mint close expects wallet-held repay asset, not hidden internal auto-netting**
- the repay asset is **`bnbUSD`**
- that repay dependency is now proven in two stages:
  1. delayed `/earn` claim created wallet-held `bnbUSD`
  2. a fresh bounded `/mintv2` close replay successfully consumed `0.79 bnbUSD`
- the fresh exact-approval replay is now also proven live end to end:
  - `revoke approval -> exact token approval -> NFT approval -> execution confirm`
- the same replay is now proven by direct decode to be a **partial repay / partial close**, not a terminal full close:
  - `deltaColls = 0`
  - `deltaDebts = -0.79 bnbUSD`
  - same position NFT `#158` remained live after the tx
- current post-replay wallet/control state is:
  - **`bnbUSD balance = 0.005238383559755168`**
  - **`bnbUSD allowance to observed router = 0`**
  - **`NFT approval to observed router = 0 / false`**

Confidence:
- **high** that close needs spendable wallet-held `bnbUSD` for repay
- **high** that exact approval can be honored on the fresh replay path when re-driven from a clean state
- **high** that the successful replay reduced debt without withdrawing raw collateral
- **medium** on the exact final write path / spender / min-coll / fee math for a true full close, because the verified tx was a partial repay on the still-live position

---

## Direct current chain state

Read-only command now available:

```bash
./sigma account mint-close-readiness \
  --owner 0xOWNER_ADDRESS \
  --position-id 158 \
  --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb \
  --bnb-rpc-url https://bsc-dataseed.binance.org/
```

Observed result for the live mint position after the successful fresh replay:
- pool: `0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb`
- position id: `158`
- owner: `0xOWNER_ADDRESS`
- `rawColls`: `0.014954999999999998 BNB`
- `rawDebts`: `3.220571150970316111 bnbUSD`
- current `bnbUSD` wallet balance: `0.005238383559755168`
- current `bnbUSD` allowance to observed live router `0xae2658f23176f843af11d2209dbd04cffc0ff87b`: `0`
- current NFT `ownerOf(158)`: wallet owner
- current NFT `getApproved(158)`: zero address
- current NFT `isApprovedForAll(owner, router)`: `false`

Practical implication:
- the wallet can no longer be described as “zero-repay-balance blocked”; it already consumed `0.79 bnbUSD` successfully on the replayed close path
- the current remaining state is a **smaller live position** with approvals cleared again
- a true full repay / final exit would still need more `bnbUSD` and fresh approval(s)

---

## Contract surface relevant to mint close

### SyPool / SigmaLongPool (`0xe8a1...` proxy, live pool `0x31c4...`)
Verified user-facing/write-relevant functions:
- `getPosition(uint256)` -> `(rawColls, rawDebts)`
- `positionData(uint256)` -> `(tick, nodeId, colls, debts)`
- `getPositionDebtRatio(uint256)`
- `ownerOf(uint256)`
- `getApproved(uint256)`
- `isApprovedForAll(address,address)`
- `operate(uint256,int256,int256,address)`
- `redeem(uint256)`
- `reduceDebt(uint256)`
- `reduceCollateral(uint256)`

### PoolManager (`0x0a43...` proxy)
Verified lifecycle/write-relevant functions:
- `operate(address,uint256,int256,int256)`
- `operate(address,uint256,int256,int256,bool)`
- `repay(address,address,uint256)`
- `redeem(address,uint256,uint256)`
- `reduceDebt(address,uint256)`

### SigmaController (`0xaB98...` proxy)
Verified archived-mint-style surface:
- `deposit((pool,positionId),(collToken,collAmount),(debtToken,debtAmount),(receiver),bytes)`
- `redeemInstant((pool,positionId),(collToken,collAmount),(debtToken,debtAmount),(receiver))`

Important semantic clue from `redeemInstant(...)`:
- the close-side surface takes an explicit **`debtToken` + `debtAmount`** tuple
- that strongly supports a **user-supplied repay asset** model rather than “Sigma internally settles debt without the wallet holding repay asset”

---

## What the captured mint txs prove

### 1) Initial mint/open tx created explicit debt and the position NFT

Primary tx:
- `0x3ef4072cf992dd2a3cf89e1e807ece7b571f3eda738c5239765fe13feafbd097`
- destination: observed live router `0xae2658f23176f843af11d2209dbd04cffc0ff87b`

Relevant decoded effects from logs:
- `PoolManager.Operate`
  - pool: `0x31c464...70fb`
  - position: `158`
  - `deltaColls = 0.008973 BNB`
  - `deltaDebts = 4.010571150970316112 bnbUSD`
- `SyPool` minted NFT `#158`
  - first to router
  - then router transferred it to the wallet owner
- `BNBUSD` minted `4.010571150970316112`
  - to the router
  - then the router routed/swapped it onward through downstream contracts
  - it did **not** remain in the wallet as spendable `bnbUSD`

Meaning:
- the position debt is explicit and real
- the protocol did not leave the minted `bnbUSD` sitting in the user wallet automatically

### 2) Later txs only added collateral; they did not repay debt

Add-collateral txs:
- `0x53611ccbb51aab2a1fca9073b400c0fe17f64ca2cfb20084b4e14496553a94a2`
- `0xd79307353d5cda0f7064d0f70a5221209d9d318b5bd88619ca54723472c10313`

Relevant decoded effects from logs:
- wallet NFT `#158` transferred to router, then returned to wallet
- `WBNB` approved from router to `PoolManager`
- `PoolManager.Operate`
  - `deltaColls = 0.002991 BNB`
  - `deltaDebts = 0`
- no new debt created
- no repay performed

Meaning:
- these txs are position-management / add-collateral actions
- repeating tiny BNB adds does **not** populate the repay balance
- they do not create spendable wallet `bnbUSD`

### 3) Router-mediated position management uses the NFT, and approval can clear again

The add-collateral txs show:
- wallet NFT `#158` -> router
- router performs the management action
- router returns NFT `#158` -> wallet

Because ERC721 approvals clear on transfer, the observed zero `getApproved(158)` state after the txs is expected.

Practical implication:
- repeated modify/close flows through the observed router can require a fresh NFT approval each time unless `setApprovalForAll` is used

---

## Exact semantic findings

### Mint open
Best current contract-level map:
1. user funds BNB/WBNB into observed router path
2. router forwards collateral into `PoolManager.operate(...)`
3. `PoolManager` creates / updates the SyPool position
4. position NFT is minted/transferred
5. debt in `bnbUSD` is created explicitly
6. the minted `bnbUSD` can be routed onward rather than left in the wallet

### Mint add collateral
Best current contract-level map:
1. position NFT is handed to the router temporarily
2. router receives/uses WBNB collateral
3. `PoolManager.operate(...)` runs with positive `deltaColls` and `deltaDebts = 0`
4. NFT returns to wallet owner

### Mint close / repay
Best current contract-level map:
1. close is debt-first, not “just unlock collateral”
2. the debt token is `bnbUSD`
3. the wallet must hold repayable `bnbUSD` balance for the amount being closed
4. the close path will also need approval(s) for the repay asset and likely renewed NFT authority for the router-mediated path
5. exact full-close preview math still needs a captured close tx or preview call before hardcoding spender/min-coll behavior

---

## What this means for the CLI

### Implemented now
- `sigma account status`
- `sigma account mint-close-readiness`
  - now includes optional partial-close preview inputs:
    - `--repay-amount`
    - `--target-ltv`
    - `--withdraw-amount`
  - now reports the resolved CLI approval policy
- `sigma plan mint-close`
  - now reports partial repay / partial close semantics
  - now reports the resolved approval policy (`unlimited`, `exact`, `custom`)
- `sigma config show`
- `sigma config init --approval-policy ...`
- `sigma config set-approval-policy --approval-policy ...`

### Truthful CLI guidance now
- use `account mint-close-readiness` before treating mint close as actionable
- use `account mint-close-readiness --repay-amount <amount>` when you want the CLI to model:
  - remaining debt after partial repay
  - max modeled withdrawable collateral under the current/target LTV guardrail
  - resulting LTV after the modeled partial close
- do **not** assume “I added/support bnbUSD in Rabby” is enough
- do **not** assume “I added more BNB collateral” is enough
- do **not** assume max approval is inherently required just because one live close attempt surfaced a max allowance popup
- current honest requirement is closer to:
  - acquire / hold repayable `bnbUSD`
  - choose an approval policy (`unlimited`, `exact`, `custom`) and persist it if desired
  - approve the observed close-path spender
  - refresh NFT approval / authority as needed
  - then capture the actual close preview/write path

---

## Remaining gap

Still not fully proven:
- the exact close transaction calldata / selector on the live observed router path
- whether full close uses the observed router directly, `SigmaController.redeemInstant(...)`, a controller helper, or a router wrapper around that controller surface
- exact minimum repay / min-coll / fee rounding for the final close submit

So the repo should now treat the question this way:
- **resolved:** close is wallet-repay-asset dependent
- **not yet fully resolved:** exact write-path implementation details for direct execution

---

## Live update — 2026-03-16 delayed claim matured and close path reactivated

New capture root:
- `projects/sigma-operator/captures/20260316T164411Z-earn-unlock-claim-mint-close`

### What was proven live

1. The delayed `/earn` redeem did mature into real repay asset
- claim popup showed:
  - `-0.9900 sigmaSP1`
  - `+0.7952 bnbUSD`
  - `+0.2008 USDT`
- after claim, Sigma `/earn` reflected wallet balances:
  - `0.80 bnbUSD`
  - `49.19 USDT`

2. `/mintv2` close immediately became live-repayable once that asset existed
- close form no longer showed the old practical dead-end
- visible live state became:
  - `Repay Balance: 0.80`
  - range `0.00 ~ 3.03`
- manual bounded repay input `0.79` was accepted
- CTA `Approve & Close` became enabled

This materially strengthens the semantic map:
- the close path is indeed wallet-repay-asset dependent
- the delayed earn claim can be one concrete source of that repay asset

### New blocker captured exactly

When `Approve & Close` was triggered with:
- repay `0.79 bnbUSD`
- Sigma `Unlimited Approval` toggle visually OFF

Rabby still requested:
- `Token Approval`
- approve token display `115,792,089,237,316...`
- chain `BNB Chain`
- my balance `0.7952 bnbUSD`
- approve to `0xae2658f23176f843af11d2209dbd04cffc0ff87b`
- protocol `Sigma.Money`

Meaning:
- the live close path currently surfaces a **max / unlimited allowance request** even when the Sigma UI toggle is OFF
- this pass did **not** prove whether the router truly requires max approval or whether the finite-approval path is just not being surfaced/edited correctly in the popup
- because the bounded-approval preference remained in force, the approval was not signed

### Updated practical conclusion

Resolved further:
- missing wallet-held `bnbUSD` was a real blocker
- that blocker can be removed by the matured earn claim path
- once removed, the close UI becomes truly actionable

Still unresolved:
- how to submit close with a finite `bnbUSD` approval amount
- whether the observed router `0xae2658f23176f843af11d2209dbd04cffc0ff87b` only exposes a max allowance path in Rabby
- whether a different route / direct calldata path can avoid this allowance shape

Practical CLI stance after this pass:
- exact/custom approval is now a first-class operator preference in the CLI config and plan/readiness output
- but the repo still does **not** claim that the current live `mint-close` write path already honors finite approval end-to-end
- the partial-close preview math should be read as a contract-aligned planning aid, not as proof that the live router will quote or execute the same numbers byte-for-byte


### Update — 2026-03-16 bundle-level approval truth

This repo can now state something materially tighter than the prior live-popup-only conclusion:

- the current frontend bundle contains close variants that initialize `Unlimited Approval` as ON by default
- in the ON branch, the approval amount is set to `ks` / max uint
- in the OFF branch, the bundle performs a bounded approval sequence (`approve(0)` then `approve(repayAmount)`)

Meaning:
- the repo should **not** describe Sigma mint-close as inherently max-approval-only
- the remaining blocker is narrower:
  - prior live Rabby evidence still showed a max approval popup with the Sigma toggle appearing OFF
  - so the unresolved question is now whether the live session was desynced / stale / on a different close variant, or whether the wallet popup path is not faithfully reflecting the UI state

Updated practical conclusion:
- finite approval is present in current close code paths
- finite approval is still **not** proven live end to end
- next proof step is a fresh repayable close replay that captures the first approval popup amount under a deliberately toggled OFF state

### Update — 2026-03-16 successful replay + verification pack

The next proof step has now been completed and independently verified.

Fresh live replay result (`20260316T112241Z-fresh-mint-close-replay`):
- Sigma `Unlimited Approval` was toggled OFF on the close surface
- fresh Rabby sequence completed as:
  1. `Revoke Token Approval` for `bnbUSD`
  2. finite `Token Approval` for exact `0.7900 bnbUSD`
  3. `NFT Approval` for `#158`
  4. execution popup / final confirm

Fresh read-only verification result (`20260316T114949Z-post-close-verification-pack`):
- replay tx hash: `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d`
- decoded contract effect:
  - `PoolManager.Operate`
    - `deltaColls = 0`
    - `deltaDebts = -0.79 bnbUSD`
- `0.79 bnbUSD` moved wallet -> observed router -> burn
- NFT `#158` moved wallet -> router -> wallet in the same tx
- current post-replay onchain state is:
  - `rawColls = 0.014954999999999998 BNB`
  - `rawDebts = 3.220571150970316111 bnbUSD`

What this resolves:
- finite approval is now **proven live end to end** for the bounded replay path
- the successful replay was a **partial debt reduction / partial close** on the same position NFT
- the replay did **not** withdraw raw collateral and did **not** fully extinguish the position

New practical conclusion:
- the close path can honor exact approval when re-driven from a fresh state
- a Sigma UI action labeled `Close` can still resolve into a partial repay on the same position rather than a terminal close
- exact write-path implementation details are clearer now, but full-close / collateral-withdraw semantics still need their own explicit capture before being documented as proven
