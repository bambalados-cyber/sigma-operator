# Wallet architecture for SigmaCLI

_Last updated: 2026-03-17_

## Why this document exists

SigmaCLI is no longer framed as a browser-driving Sigma helper.

The product direction is now:

> **connect to a wallet backend, talk to Sigma routes directly, execute guarded actions, then verify post-state.**

Browser research, capture, and UI validation are still useful for discovery and evidence collection, but they are **not** the core runtime architecture.

This document defines the public target architecture for that wallet layer.

---

## 1) Design goals

SigmaCLI should become a wallet-aware operator CLI that can:

1. connect to a signer or wallet session without making browser automation the product core
2. keep read-only and wallet-backed modes explicitly separated
3. plan route-specific actions before any signing or submission happens
4. enforce operator policy before execution
5. use direct route adapters instead of vague generic "click what the UI does" behavior
6. verify post-state after every action
7. preserve evidence artifacts for debugging, auditing, and contributor work

What this means in practice:

- **read / plan / verify** remains core
- **execute** is added on top of that substrate
- execution must stay **route-specific, policy-gated, and evidence-backed**

---

## 2) Current repo truth vs target architecture

### Current repo truth

Today SigmaCLI is strongest on:

- capture
- decode
- plan-only modeling
- ABI inspection
- read-only account and position inspection
- repay-readiness and state tracing

That is real shipped value.

### Target architecture

The next build phase adds a wallet layer so SigmaCLI can eventually do:

- authenticated wallet/session status
- policy-aware transaction planning
- direct route execution
- post-tx verification

Important boundary:

- this document describes the **target architecture for the next build phase**
- it does **not** claim that broad execution support already exists in the repo today

---

## 3) Trust model

SigmaCLI should follow this trust model:

1. **Read state first**
   - use chain reads, Sigma APIs, and decoded evidence to understand current state
2. **Plan before sign**
   - execution starts from an explicit plan object, not from ad hoc wallet prompts
3. **Policy before submit**
   - approval policy, slippage policy, route maturity, and backend safety checks run before any tx is sent
4. **Direct calls, not browser control**
   - SigmaCLI should call route adapters and signing backends directly
   - it should not depend on DOM traversal, accessibility trees, or click automation as its operating model
5. **Verify after execution**
   - a tx hash alone is not enough
   - SigmaCLI must re-read post-state and classify whether the intended state change really happened
6. **Truth over breadth**
   - if a route is only partially understood, the CLI should say so and stop there

---

## 4) Backend model

The wallet layer should revolve around a small backend interface.

Each backend answers the same questions:

- can it read chain state?
- can it identify an address?
- can it sign messages?
- can it sign transactions?
- can it submit transactions?
- can it wait for receipts?
- what chain(s) can it operate on?
- what policy restrictions apply?

### Backend interface

Conceptually, every backend should implement capabilities like:

- `kind`
- `chain_id`
- `address`
- `capabilities.read`
- `capabilities.sign_message`
- `capabilities.sign_tx`
- `capabilities.send_tx`
- `capabilities.wait_receipt`
- `capabilities.simulate` if available
- `policy_hints`

### Backend types

#### 1) `readonly`

Purpose:

- chain reads only
- no signing
- no submission

Use for:

- inspection
- planning
- verification
- contributor work
- CI-safe checks

This should remain the default lowest-risk mode.

#### 2) `external-session`

Purpose:

- use an externally managed wallet/signer session
- the wallet may be a browser extension wallet, desktop wallet, or another signer bridge
- SigmaCLI talks to a signer/session interface, **not** to the wallet UI

Use for:

- real operator execution with user-controlled custody
- wallet-managed signing and submission

Important framing:

- this may be backed by something like Rabby or another injected wallet session
- but SigmaCLI treats it as a **signing/session backend**, not as a browser-automation target

#### 3) `walletconnect-session`

Purpose:

- remote session-based wallet connectivity where available
- still non-custodial from SigmaCLI’s point of view

Use for:

- future session-driven signing flows where the wallet remains the signing authority

This is a valid target backend even if not implemented first.

#### 4) `local-key-env`

Purpose:

- load a key from an explicit environment variable for local dev, testing, or tightly controlled automation

Use for:

- local development
- test wallets
- reproducible execution testing

Restrictions:

- do **not** frame this as the default production backend
- do **not** encourage careless secret handling
- keep it secondary to external-session style backends

### Backend priority order

Public architecture priority should be:

1. `readonly`
2. `external-session`
3. `local-key-env`
4. `walletconnect-session` or equivalent remote-session backends

Rationale:

- keep the safest path first
- support real wallet connectivity without turning browser control into the architecture
- keep local-key signing as a bounded secondary path

---

## 5) Command spine

The wallet architecture should organize the next CLI phase around six command families:

- `auth`
- `status`
- `doctor`
- `plan`
- `execute`
- `verify`

Existing families such as `decode`, `account`, `capture`, and `abi` remain useful. They become supporting layers around the wallet flow rather than the whole story.

### 5.1 `auth`

Purpose:

- enumerate backends
- connect a profile to a backend
- select a default profile
- inspect auth/session state
- disconnect safely

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

Notes:

- `auth connect` should create or refresh a named profile
- `auth status` should show backend kind, address, chain id, signer capabilities, and policy mode
- `readonly` should still be a first-class backend because planning and verification depend on it

### 5.2 `status`

Purpose:

- operator summary for the currently selected profile or owner
- route capability summary
- route/account/position state snapshots

Exact target shape:

```bash
sigma status summary
sigma status wallet
sigma status routes
sigma status position --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb
sigma status balances --owner 0x...
```

Notes:

- `status` is the execution-aware top-line summary layer
- existing `account` commands can remain deeper inspection tools under it

### 5.3 `doctor`

Purpose:

- preflight checks before execution
- backend health checks
- route-specific readiness checks
- allowance / approval / chain / policy mismatch detection

Exact target shape:

```bash
sigma doctor auth
sigma doctor route trade.close --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb
sigma doctor route mint.repay --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79
sigma doctor route earn.claim --pool <pool-id>
sigma doctor config
```

Doctor output should explicitly classify:

- backend available / unavailable
- chain correct / incorrect
- route capability available / planned / blocked
- balances sufficient / insufficient
- allowance policy satisfied / not satisfied
- simulation available / unavailable
- verification path available / incomplete

### 5.4 `plan`

Purpose:

- create an explicit execution plan without sending anything
- resolve route semantics into concrete steps
- encode policy expectations, expected approvals, expected tx count, and expected post-state

Exact target shape:

```bash
sigma plan trade close --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79
sigma plan mint repay --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79 --target-ltv 0.65
sigma plan earn deposit --pool <pool-id> --asset USDT --amount 1
sigma plan earn claim --pool <pool-id>
```

Plan output should include:

- route key
- required backend capabilities
- required assets and balances
- approval requirement
- approval mode implied by policy
- expected tx steps
- slippage / price guard fields if relevant
- post-state invariants to verify
- maturity level for the route adapter

### 5.5 `execute`

Purpose:

- execute from an explicit plan
- refuse to run when policy or route readiness fails
- emit tx artifacts and receipts

Exact target shape:

```bash
sigma execute --plan plan.json
sigma execute trade close --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79
sigma execute mint repay --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb --repay-amount 0.79 --from-plan plan.json
```

Execution rules:

- prefer `--plan` or `--from-plan` over ad hoc execution
- refuse on backend mismatch
- refuse on policy mismatch
- refuse on route marked unsupported
- persist tx hashes and plan artifacts automatically

### 5.6 `verify`

Purpose:

- prove what happened after planning or execution
- compare actual post-state against expected post-state
- keep tx hash and receipt checks separate from economic-state verification

Exact target shape:

```bash
sigma verify tx --tx-hash 0x...
sigma verify plan --plan plan.json
sigma verify route trade.close --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb
sigma verify position --position-id 158 --pool 0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb
```

Verification should classify outcomes such as:

- executed as planned
- submitted but not confirmed
- confirmed but state mismatch
- partial success
- verification blocked by missing read path

---

## 6) Plan object model

A plan should be a stable machine-readable artifact.

Suggested fields:

```json
{
  "route": "trade.close",
  "maturity": "verified|alpha|planned",
  "backend": {
    "required": ["read", "sign_tx", "send_tx", "wait_receipt"],
    "selectedProfile": "default"
  },
  "policy": {
    "approvalMode": "exact",
    "slippageBps": 50,
    "allowUnverifiedRoutes": false,
    "requireVerification": true
  },
  "inputs": {
    "positionId": 158,
    "pool": "0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb",
    "repayAmount": "0.79"
  },
  "steps": [
    {"kind": "approval", "asset": "bnbUSD", "mode": "exact"},
    {"kind": "position-action", "route": "trade.close"}
  ],
  "expectedPostState": {
    "debtDelta": "-0.79",
    "positionStillExists": true
  }
}
```

Important rule:

- plans should describe what SigmaCLI expects to happen
- verification should determine whether reality matched the plan

---

## 7) Policy and config model

The wallet architecture should make policy explicit and persistent.

### Operator config should cover

- default profile
- backend profiles
- default chain / RPC
- approval policy
- slippage policy
- route enablement
- verification requirements
- simulation requirements where available

Suggested config shape:

```json
{
  "defaultProfile": "default",
  "profiles": {
    "default": {
      "backend": "external-session",
      "wallet": "rabby",
      "chainId": 56,
      "address": "0x..."
    }
  },
  "policy": {
    "approval": {
      "mode": "exact",
      "customAmount": null
    },
    "execution": {
      "allowUnverifiedRoutes": false,
      "requirePlanArtifacts": true,
      "requirePostStateVerification": true
    },
    "slippage": {
      "defaultBps": 50,
      "maxBps": 150
    }
  },
  "routes": {
    "trade.close": {"enabled": true},
    "mint.repay": {"enabled": true},
    "earn.deposit": {"enabled": false}
  }
}
```

### Approval policy modes

These should stay explicit:

- `exact`
- `unlimited`
- `custom`

That preserves the already-established repo truth that approval policy is a real operator choice, not hidden UI magic.

---

## 8) Route capability model

Each route adapter should declare its own capability record.

Suggested fields:

- `route_key`
- `category`
- `read_support`
- `plan_support`
- `execute_support`
- `verify_support`
- `required_backends`
- `required_assets`
- `approval_behavior`
- `post_state_checks`
- `maturity`
- `notes`

Example:

```json
{
  "routeKey": "trade.close",
  "category": "trade",
  "supports": {
    "read": true,
    "plan": true,
    "execute": false,
    "verify": true
  },
  "requiredBackends": ["external-session", "local-key-env"],
  "approvalBehavior": "exact-or-custom-policy",
  "postStateChecks": [
    "debt decreased or zeroed",
    "collateral decreased or withdrawn as expected",
    "payout asset observed",
    "shell NFT semantics classified if position zeroes"
  ],
  "maturity": "alpha"
}
```

Why this matters:

- route capability must be explicit per route
- SigmaCLI should not pretend that because one route is executable, another one is too

---

## 9) Preserved verified truths

This architectural rewrite does **not** discard existing verified truths.

These remain important:

- explicit `/trade` **Close** is distinct from `Adjust Leverage`
- tx `0x9b7323079dbb07bf0cd6b9fb89d0f5851d3c36235b9f26592c808934b9d0f50d` is verified **partial repay / partial close**
- tx `0xb873c68cf4785645b17f0100dbe54744f34b797e3c9afa5dd343aa0704c69092` is verified **terminal `/trade` close**
- verified terminal close paid out **USDT**
- a fully closed economic position can still leave a wallet-owned **zero-state shell NFT**

Those truths are exactly why the wallet architecture must keep verification first-class.

---

## 10) Phased implementation order

### Phase 1 — common wallet foundation

Build first:

- backend interface
- profile/config model
- route capability registry
- `auth`
- `status`
- `doctor`

Success condition:

- SigmaCLI can connect to `readonly`
- SigmaCLI can describe what wallet-backed backends are available
- SigmaCLI can run meaningful preflight checks without sending anything

### Phase 2 — plan/verify engine

Build next:

- stable plan artifact format
- route preflight checks
- post-state verification helpers
- common receipt/result persistence

Success condition:

- every future route adapter can reuse one plan/verify substrate

### Phase 3 — first direct route adapters

Prioritize adapters in this order:

1. `trade.close`
2. `mint.repay` / partial-close semantics
3. `earn.deposit`
4. `earn.claim`

Why this order:

- it follows the strongest existing evidence
- it starts from already-proven semantic territory

### Phase 4 — broader account-linked execution surfaces

Only after the wallet core is stable:

- dashboard-linked claims / unwrap
- governance-side reads and later writes
- additional route adapters where evidence is strong enough

---

## 11) Explicit non-goals

Not part of the core SigmaCLI architecture:

- browser automation as the execution engine
- accessibility-tree or DOM-click control as the product contract
- claiming route support just because the frontend renders a button
- generic "do anything on Sigma" execution without route-specific adapters
- governance-first positioning for the current repo phase
- pretending local-key custody is the ideal default for all operators

Browser tools may still help with:

- reverse-engineering
- validation
- capture
- replay debugging

But they are not the architecture.

---

## 12) Bottom line

SigmaCLI should be built as a **wallet-connected operator shell** with:

- explicit backend selection
- explicit policy
- explicit plans
- direct route adapters
- explicit verification

That is the clean path to a real execution-capable SigmaCLI without turning the project into a fragile browser bot.