from __future__ import annotations

import argparse
from decimal import Decimal
from typing import Any

from .config import (
    MAX_UINT256,
    approval_policy_desired_allowance_raw,
    approval_policy_to_dict,
    format_token_amount_from_raw,
    resolve_approval_policy,
)

LEVERAGE_MIN = 1.1
LEVERAGE_MAX = 7.0
CHAIN = {"name": "BNB Chain", "chainId": 56, "note": "chainId inferred from public deployment context"}

RELATED_CONTRACTS = {
    "BNBUSD": "0x5519a479Da8Ce3Af7f373c16f14870BbeaFDa265",
    "BNBUSDBasePool": "0x2b9C1F069Ddcd873275B3363986081bDA94A3aA3",
    "PegKeeper": "0xEE3f89a14dDD6f77dEE050AA4f9d3a52947373F6",
    "PoolManager": "0x0a43ca87954ED1799b7b072F6E9D51d88Cca600E",
    "SigmaController": "0xaB98D10CA647B90564feB4D7C4489b09B701188b",
    "BNBPriceOracle": "0x45dCDFcE8C0D163708Eaa47ab5e72280AF3eFa3E",
}

BASE_SOURCES = {
    "trade-open": [
        "https://docs.sigma.money/getting-started/opening-a-leverage-position",
        "https://docs.sigma.money/risk-management/risk-parameters",
        "https://docs.sigma.money/sigma-money-mechanism/fee-structure",
        "https://docs.sigma.money/other/resources/smart-contracts",
    ],
    "trade-close": [
        "https://docs.sigma.money/getting-started/closing-a-leverage-position",
        "https://docs.sigma.money/getting-started/add-or-reduce-your-position",
        "https://docs.sigma.money/risk-management/risk-parameters",
        "https://docs.sigma.money/sigma-money-mechanism/fee-structure",
        "https://docs.sigma.money/other/resources/smart-contracts",
    ],
    "earn": [
        "https://docs.sigma.money/getting-started/using-the-stability-pool",
        "https://docs.sigma.money/sigma-money-mechanism/stability-pool",
        "https://docs.sigma.money/sigma-money-mechanism/fee-structure",
        "https://docs.sigma.money/other/resources/smart-contracts",
    ],
    "mint-open": [
        "https://sigma.money/mint",
        "https://docs.sigma.money/archives/mint-bnbusd",
        "https://docs.sigma.money/archives/minting-bnbusd-open-position",
        "https://docs.sigma.money/other/resources/smart-contracts",
    ],
    "mint-close": [
        "https://sigma.money/close",
        "https://docs.sigma.money/archives/returning-bnbusd-close-position",
        "https://docs.sigma.money/archives/position-rebalancing-for-mint-xposition-bnbusd",
        "https://docs.sigma.money/other/resources/smart-contracts",
    ],
    "redemption": [
        "https://docs.sigma.money/risk-management/peg-protection",
        "https://docs.sigma.money/risk-management/risk-parameters",
        "https://docs.sigma.money/sigma-money-mechanism/fee-structure",
        "https://docs.sigma.money/other/resources/smart-contracts",
    ],
}

OPERATION_SPECS: dict[str, dict[str, Any]] = {
    "open-long": {
        "label": "Trade open long",
        "category": "trade",
        "route": "https://sigma.money/trade",
        "routeKind": "app",
        "docsStatus": "current",
        "operatorSupport": "plan-plus-partial-routing",
        "summary": "Current /trade long-position flow.",
        "requiresLeverage": True,
        "approvalMode": "asset",
        "contracts": ["BNBUSD", "PoolManager", "SigmaController", "BNBPriceOracle"],
        "sources": BASE_SOURCES["trade-open"],
        "disambiguation": [
            "This is the current trade flow, not the archived /mint flow.",
            "Trade opens may mint bnbUSD internally, but that does not make them the same as peg redemption or Stability Pool redeem paths.",
        ],
        "hints": [
            {"docsName": "BNBUSD", "confidence": "high", "contains": ("approve(", "permit("), "reason": "collateral / token approval surface"},
            {"docsName": "PoolManager", "confidence": "medium-high", "contains": ("operate(", "borrow(", "repay(", "redeem(", "rebalance("), "reason": "trade lifecycle surface most likely used by /trade"},
            {"docsName": "SigmaController", "confidence": "low-medium", "contains": ("deposit(",), "reason": "verified controller surface exists, but exact frontend hop is not yet proven"},
        ],
    },
    "open-short": {
        "label": "Trade open short",
        "category": "trade",
        "route": "https://sigma.money/trade",
        "routeKind": "app",
        "docsStatus": "current",
        "operatorSupport": "plan-plus-partial-routing",
        "summary": "Current /trade short-position flow.",
        "requiresLeverage": True,
        "approvalMode": "asset",
        "contracts": ["BNBUSD", "PoolManager", "SigmaController", "BNBPriceOracle"],
        "sources": BASE_SOURCES["trade-open"],
        "disambiguation": [
            "This is the current trade flow, not the archived /mint flow.",
            "Short opens use bnbUSD-related debt/collateral semantics, but are distinct from peg redemption and Stability Pool redeem paths.",
        ],
        "hints": [
            {"docsName": "BNBUSD", "confidence": "high", "contains": ("approve(", "permit("), "reason": "short flow uses bnbUSD-related approval / allowance surfaces"},
            {"docsName": "PoolManager", "confidence": "medium-high", "contains": ("operate(", "borrow(", "repay(", "redeem(", "rebalance("), "reason": "trade lifecycle surface most likely used by /trade"},
            {"docsName": "SigmaController", "confidence": "low-medium", "contains": ("deposit(",), "reason": "verified controller surface exists, but exact frontend hop is not yet proven"},
        ],
    },
    "add-position": {
        "label": "Trade add position",
        "category": "trade",
        "route": "https://sigma.money/trade",
        "routeKind": "app",
        "docsStatus": "current",
        "operatorSupport": "plan-plus-partial-routing",
        "summary": "Current /trade add-position flow.",
        "requiresLeverage": True,
        "approvalMode": "asset",
        "contracts": ["BNBUSD", "PoolManager", "SigmaController", "BNBPriceOracle"],
        "sources": BASE_SOURCES["trade-open"],
        "disambiguation": [
            "This is a trade-position action, not Stability Pool or peg redemption.",
        ],
        "hints": [
            {"docsName": "PoolManager", "confidence": "medium-high", "contains": ("operate(", "borrow(", "repay(", "rebalance("), "reason": "position management surface"},
        ],
    },
    "reduce-position": {
        "label": "Trade reduce position",
        "category": "trade",
        "route": "https://sigma.money/trade",
        "routeKind": "app",
        "docsStatus": "current",
        "operatorSupport": "plan-plus-partial-routing",
        "summary": "Current /trade partial-close / reduction flow.",
        "requiresLeverage": False,
        "approvalMode": "none",
        "contracts": ["BNBUSD", "PoolManager", "SigmaController", "BNBPriceOracle"],
        "sources": BASE_SOURCES["trade-close"],
        "disambiguation": [
            "This is not Stability Pool redeem on /earn.",
            "This is not docs-described bnbUSD peg redemption.",
        ],
        "hints": [
            {"docsName": "PoolManager", "confidence": "medium-high", "contains": ("operate(", "repay(", "redeem("), "reason": "position reduction surface"},
        ],
    },
    "close-position": {
        "label": "Trade close position",
        "category": "trade",
        "route": "https://sigma.money/trade",
        "routeKind": "app",
        "docsStatus": "current",
        "operatorSupport": "plan-plus-partial-routing",
        "summary": "Current /trade close-position flow.",
        "requiresLeverage": False,
        "approvalMode": "none",
        "contracts": ["BNBUSD", "PoolManager", "SigmaController", "BNBPriceOracle"],
        "sources": BASE_SOURCES["trade-close"],
        "disambiguation": [
            "This is not Stability Pool redeem on /earn.",
            "This is not docs-described bnbUSD peg redemption.",
            "This is not the archived mint-close flow.",
        ],
        "hints": [
            {"docsName": "PoolManager", "confidence": "medium-high", "contains": ("operate(", "repay(", "redeem("), "reason": "position close surface"},
        ],
    },
    "adjust-leverage": {
        "label": "Trade adjust leverage",
        "category": "trade",
        "route": "https://sigma.money/trade",
        "routeKind": "app",
        "docsStatus": "current",
        "operatorSupport": "plan-plus-partial-routing",
        "summary": "Current /trade leverage-adjustment flow.",
        "requiresLeverage": True,
        "approvalMode": "none",
        "contracts": ["BNBUSD", "PoolManager", "SigmaController", "BNBPriceOracle"],
        "sources": BASE_SOURCES["trade-open"],
        "disambiguation": [
            "This is a trade-position action, not Stability Pool or peg redemption.",
        ],
        "hints": [
            {"docsName": "PoolManager", "confidence": "medium-high", "contains": ("operate(", "rebalance("), "reason": "leverage adjustment likely routes through PoolManager"},
        ],
    },
    "stability-pool-deposit": {
        "label": "Stability Pool deposit",
        "category": "earn",
        "route": "https://sigma.money/earn",
        "routeKind": "app",
        "docsStatus": "current-docs-disabled-upgrade",
        "operatorSupport": "plan-plus-high-confidence-routing",
        "summary": "Docs describe /earn deposits, but the same docs currently say deposits are disabled during an ongoing upgrade.",
        "requiresLeverage": False,
        "approvalMode": "asset",
        "contracts": ["BNBUSD", "BNBUSDBasePool", "PegKeeper", "PoolManager"],
        "sources": BASE_SOURCES["earn"],
        "disambiguation": [
            "This is an /earn deposit path, not any redeem path.",
        ],
        "hints": [
            {"docsName": "BNBUSD", "confidence": "high", "contains": ("approve(", "permit("), "reason": "deposit approval surface"},
            {"docsName": "BNBUSDBasePool", "confidence": "high", "contains": ("deposit(", "previewDeposit("), "reason": "ABI-backed Stability Pool deposit surface"},
        ],
    },
    "stability-pool-withdraw": {
        "label": "Stability Pool withdraw (umbrella)",
        "category": "earn",
        "route": "https://sigma.money/earn",
        "routeKind": "app",
        "docsStatus": "current",
        "operatorSupport": "plan-plus-high-confidence-routing",
        "summary": "Umbrella /earn withdrawal model covering both cooldown redeem and immediate redeem modes.",
        "requiresLeverage": False,
        "approvalMode": "none",
        "contracts": ["BNBUSD", "BNBUSDBasePool", "PegKeeper", "PoolManager"],
        "sources": BASE_SOURCES["earn"],
        "disambiguation": [
            "Use stability-pool-redeem-normal or stability-pool-redeem-instant when the exact withdrawal mode matters.",
            "This is not docs-described bnbUSD peg redemption.",
            "This is not /trade close-position.",
        ],
        "hints": [
            {"docsName": "BNBUSDBasePool", "confidence": "high", "contains": ("requestRedeem(", "redeem(", "previewRedeem(", "instantRedeem("), "reason": "ABI-backed Stability Pool withdrawal surface"},
        ],
    },
    "stability-pool-redeem-normal": {
        "label": "Stability Pool redeem (cooldown)",
        "category": "earn",
        "route": "https://sigma.money/earn",
        "routeKind": "app",
        "docsStatus": "current",
        "operatorSupport": "plan-plus-high-confidence-routing",
        "summary": "Current /earn normal withdrawal path with cooldown before redeem completion.",
        "requiresLeverage": False,
        "approvalMode": "none",
        "contracts": ["BNBUSD", "BNBUSDBasePool", "PegKeeper", "PoolManager"],
        "sources": BASE_SOURCES["earn"],
        "disambiguation": [
            "This is not the 1% immediate redeem path.",
            "This is not docs-described bnbUSD peg redemption.",
            "This is not /trade close-position.",
        ],
        "hints": [
            {"docsName": "BNBUSDBasePool", "confidence": "high", "contains": ("requestRedeem(", "redeem(", "previewRedeem(", "redeemCoolDownPeriod("), "reason": "ABI-backed Stability Pool cooldown redeem surface"},
        ],
    },
    "stability-pool-redeem-instant": {
        "label": "Stability Pool redeem (instant)",
        "category": "earn",
        "route": "https://sigma.money/earn",
        "routeKind": "app",
        "docsStatus": "current",
        "operatorSupport": "plan-plus-high-confidence-routing",
        "summary": "Current /earn immediate withdrawal path with the docs-described 1% early-exit fee.",
        "requiresLeverage": False,
        "approvalMode": "none",
        "contracts": ["BNBUSD", "BNBUSDBasePool", "PegKeeper", "PoolManager"],
        "sources": BASE_SOURCES["earn"],
        "disambiguation": [
            "This is not the cooldown redeem path.",
            "This is not docs-described bnbUSD peg redemption.",
            "This is not /trade close-position.",
        ],
        "hints": [
            {"docsName": "BNBUSDBasePool", "confidence": "high", "contains": ("instantRedeem(", "instantRedeemFeeRatio("), "reason": "ABI-backed Stability Pool instant redeem surface"},
        ],
    },
    "mint-open": {
        "label": "Mint open (archived)",
        "category": "mint",
        "route": "https://sigma.money/mint",
        "routeKind": "archived-app",
        "docsStatus": "archived",
        "operatorSupport": "plan-plus-partial-routing",
        "summary": "Archived/legacy mint-xPOSITION flow documented separately from current /trade positions.",
        "requiresLeverage": False,
        "approvalMode": "asset",
        "contracts": ["BNBUSD", "SigmaController", "BNBPriceOracle"],
        "sources": BASE_SOURCES["mint-open"],
        "disambiguation": [
            "This is not the current /trade open flow.",
            "Treat any live routing or availability as unproven until captured from the current app.",
        ],
        "hints": [
            {"docsName": "SigmaController", "confidence": "low-medium", "contains": ("deposit(",), "reason": "mint-related controller surface is verified but still needs capture to confirm exact binding"},
            {"docsName": "BNBUSD", "confidence": "high", "contains": ("approve(", "permit("), "reason": "approval / allowance surface for collateral or bnbUSD-related steps"},
        ],
    },
    "mint-close": {
        "label": "Mint close (archived)",
        "category": "mint",
        "route": "https://sigma.money/close",
        "routeKind": "archived-app",
        "docsStatus": "archived",
        "operatorSupport": "plan-plus-partial-routing",
        "summary": "Archived/legacy close path for returning bnbUSD against the mint flow.",
        "requiresLeverage": False,
        "approvalMode": "bnbusd",
        "contracts": ["BNBUSD", "SigmaController", "BNBPriceOracle"],
        "sources": BASE_SOURCES["mint-close"],
        "disambiguation": [
            "This is not Stability Pool redeem on /earn.",
            "This is not /trade close-position.",
            "Treat any live routing or availability as unproven until captured from the current app.",
        ],
        "hints": [
            {"docsName": "SigmaController", "confidence": "low-medium", "contains": ("redeemInstant(",), "reason": "controller instant redeem surface exists but exact archived flow mapping is not proven"},
            {"docsName": "BNBUSD", "confidence": "high", "contains": ("approve(", "permit("), "reason": "approval / allowance surface for bnbUSD repay path"},
        ],
    },
    "bnbusd-redeem": {
        "label": "bnbUSD redemption (peg docs)",
        "category": "redemption",
        "route": "https://docs.sigma.money/risk-management/peg-protection",
        "routeKind": "docs-only",
        "docsStatus": "docs-described-routing-ambiguous",
        "operatorSupport": "plan-plus-low-confidence-routing",
        "summary": "Docs describe redeeming bnbUSD for $1 worth of collateral, but the live public app entrypoint and exact routing are still ambiguous.",
        "requiresLeverage": False,
        "approvalMode": "unknown",
        "contracts": ["BNBUSD", "PegKeeper", "PoolManager", "SigmaController", "BNBPriceOracle"],
        "sources": BASE_SOURCES["redemption"],
        "disambiguation": [
            "This is not Stability Pool redeem on /earn.",
            "This is not /trade close-position.",
            "Current support is docs plus low-confidence ABI hints, not execution routing.",
        ],
        "hints": [
            {"docsName": "PegKeeper", "confidence": "low-medium", "contains": ("isRedeemAllowed(",), "reason": "peg-protection docs imply redeem gating and stabilization logic around PegKeeper"},
            {"docsName": "PoolManager", "confidence": "low-medium", "contains": ("redeem(",), "reason": "verified redeem surface exists, but it overlaps with trade lifecycle semantics and is not safely bound to a public redemption button yet"},
        ],
    },
}


def route_operations() -> list[str]:
    return sorted(OPERATION_SPECS)


def route_operation_hints(operation: str) -> list[dict[str, Any]]:
    return list(OPERATION_SPECS.get(operation, {}).get("hints", []))


def route_operation_details(operation: str) -> dict[str, Any] | None:
    spec = OPERATION_SPECS.get(operation)
    if not spec:
        return None
    return {
        "name": operation,
        "label": spec["label"],
        "category": spec["category"],
        "entrypoint": {
            "url": spec["route"],
            "kind": spec["routeKind"],
        },
        "docsStatus": spec["docsStatus"],
        "operatorSupport": spec["operatorSupport"],
        "summary": spec["summary"],
        "disambiguation": list(spec["disambiguation"]),
    }


def _operation_contracts(operation: str) -> dict[str, str]:
    return {name: RELATED_CONTRACTS[name] for name in OPERATION_SPECS[operation]["contracts"]}


def _approval_token(operation: str, asset: str | None) -> str | None:
    mode = OPERATION_SPECS[operation]["approvalMode"]
    if mode == "none":
        return None
    if mode == "bnbusd":
        return "bnbUSD"
    if mode == "unknown":
        return None
    return asset or "wallet-selected asset"


def _approval_policy_payload(
    operation: str,
    approval_token: str | None,
    repay_amount: str | None,
    approval_policy: Any,
) -> dict[str, Any]:
    desired_raw = approval_policy_desired_allowance_raw(
        approval_policy,
        requested_amount=repay_amount,
        decimals=18,
    )
    desired_allowance = None
    if desired_raw is not None:
        desired_allowance = "max-uint256" if desired_raw == MAX_UINT256 else format_token_amount_from_raw(desired_raw, decimals=18)

    notes: list[str] = []
    if approval_token is None:
        notes.append("This operation model does not currently require a standalone ERC20 approval token in the preflight planner.")
    elif approval_policy.mode == "exact":
        notes.append("Exact approval means the intended allowance should match the planned transaction amount for the approval token.")
    elif approval_policy.mode == "custom":
        notes.append("Custom approval means the intended allowance should be capped at the configured finite amount rather than max uint256.")
    else:
        notes.append("Unlimited approval means the intended allowance target is effectively max uint256 for the approval token.")

    if operation == "mint-close":
        notes.extend(
            [
                "Mint close now has live evidence for partial repay / partial close semantics; the repay amount does not need to equal full raw debt.",
                "Current live close evidence still showed Rabby requesting max approval even when Sigma's Unlimited Approval toggle was OFF, so exact/custom approval policy is modeled here but not yet proven end-to-end on the write path.",
            ]
        )

    return {
        "token": approval_token,
        "policy": approval_policy_to_dict(approval_policy),
        "desiredAllowance": desired_allowance,
        "desiredAllowanceRaw": str(desired_raw) if desired_raw is not None else None,
        "desiredAllowanceSource": "repay-amount" if approval_policy.mode == "exact" and repay_amount else ("custom-policy-amount" if approval_policy.mode == "custom" else approval_policy.mode),
        "notes": notes,
    }


def _close_semantics_payload(operation: str, repay_amount: str | None) -> dict[str, Any] | None:
    if operation != "mint-close":
        return None
    requested_repay = None
    if repay_amount is not None and repay_amount.strip():
        try:
            requested_repay = format(Decimal(repay_amount.strip()), "f")
        except Exception:  # noqa: BLE001 - keep the planner resilient to non-numeric drafts
            requested_repay = repay_amount.strip()
    return {
        "supportsPartialRepay": True,
        "supportsPartialClose": True,
        "repayAsset": "bnbUSD",
        "walletHeldRepayRequired": True,
        "maxWithdrawDependsOnRepayAmount": True,
        "governingConstraint": "LTV / health constraints remain binding after any partial repay / withdraw.",
        "mathValidationStatus": "specified-read-side-model; exact final write-path math still needs a live preview or captured close tx",
        "requestedRepayAmount": requested_repay,
        "notes": [
            "Use sigma account mint-close-readiness --repay-amount <amount> to preview remaining debt, max modeled withdraw, and resulting LTV under the current onchain state.",
            "The read-side preview uses current debt ratio / LTV as the default guardrail unless a tighter target LTV is supplied.",
            "The repo now treats max approval as a policy choice, not as an inherent mint-close requirement.",
        ],
    }


def build_operation_plan(operation: str, forwarded_args: list[str]) -> dict[str, Any]:
    if operation not in OPERATION_SPECS:
        expected = ", ".join(route_operations())
        raise SystemExit(f"Unsupported Sigma operation: {operation!r}. Expected one of: {expected}")

    parser = argparse.ArgumentParser(prog=f"sigma plan {operation}")
    parser.add_argument("--asset", help="Collateral / deposit asset symbol, e.g. BNB, WBNB, USDT, bnbUSD")
    parser.add_argument("--amount", help="Primary input amount, as a human-readable string")
    parser.add_argument("--leverage", type=float, help="Desired leverage for open/add operations")
    parser.add_argument("--slippage-bps", type=int, default=50, help="UI slippage budget in bps")
    parser.add_argument("--position-percent", type=float, help="Percent of position to close/reduce")
    parser.add_argument("--repay-amount", help="bnbUSD repay amount for mint-close flows")
    parser.add_argument(
        "--approval-policy",
        choices=["unlimited", "exact", "custom"],
        help="override the persisted approval policy for this plan (unlimited, exact per tx, or custom finite amount)",
    )
    parser.add_argument(
        "--approval-amount",
        help="custom finite approval amount in token units when --approval-policy custom is used",
    )
    parser.add_argument("--immediate", action="store_true", help="Use fast withdrawal mode where applicable")
    args = parser.parse_args(forwarded_args)

    spec = OPERATION_SPECS[operation]
    try:
        approval_policy = resolve_approval_policy(
            mode_override=args.approval_policy,
            amount_override=args.approval_amount,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if spec["requiresLeverage"]:
        if args.leverage is None:
            raise SystemExit("--leverage is required for this operation")
        if not (LEVERAGE_MIN <= args.leverage <= LEVERAGE_MAX):
            raise SystemExit(f"leverage must be between {LEVERAGE_MIN} and {LEVERAGE_MAX}")

    warnings = [
        "This output is a preflight plan from public docs plus cached ABI routing hints, not calldata.",
        "Public docs and verified ABIs do not prove exact current frontend routing for every Sigma action.",
    ]
    assumptions = [
        "Network is BNB Chain.",
        "Leverage range in docs is 1.1x to 7x.",
        "Wallet confirmation and live app preview override prose docs if they differ.",
    ]
    checks = [
        "Verify the connected wallet is on BNB Chain.",
        "Check app preview or docs page for execution price, fees, and post-action state.",
        "Verify token approval scope before signing.",
    ]
    fees: list[str] = []

    if spec["routeKind"] == "archived-app":
        warnings.append("This operation comes from archived/legacy Sigma docs. Do not assume the current app still routes it the same way.")
        assumptions.append("Archived mint pages are modeled separately from current trade flows.")
    if spec["routeKind"] == "docs-only":
        warnings.append("No live public app route is claimed here. This is docs-described behavior with ambiguous current routing.")
        checks.append("Get a current wallet preview or tx capture before treating this as a live executable route.")
    if spec["docsStatus"] == "current-docs-disabled-upgrade":
        warnings.append("Sigma docs currently say the Stability Pool deposit function is disabled during an ongoing upgrade.")
        assumptions.append("If the UI still blocks deposit, treat the docs warning as authoritative.")

    if operation == "stability-pool-deposit":
        checks.append("Confirm whether the live /earn UI still blocks new deposits before assuming availability.")
    if operation == "stability-pool-withdraw":
        if args.immediate:
            fees.append("Immediate Stability Pool withdrawal carries a 1% early-exit fee.")
        else:
            checks.append("Normal Stability Pool withdrawal implies about a 60-minute cooldown.")
    if operation == "stability-pool-redeem-normal":
        checks.append("Normal Stability Pool redeem implies about a 60-minute cooldown.")
    if operation == "stability-pool-redeem-instant":
        fees.append("Immediate Stability Pool withdrawal carries a 1% early-exit fee.")
    if operation in {"open-long", "open-short", "add-position"}:
        fees.extend(["Opening fee: 0.3%", f"User-configured slippage budget: {args.slippage_bps} bps"])
    if operation in {"close-position", "reduce-position", "mint-close"}:
        fees.append("Closing fee: 0.1% applies to current trade close paths; archived mint-close should be confirmed from its own preview/docs.")
    if operation == "mint-open":
        assumptions.append("Archived docs describe mint-xPOSITION as a separate mint flow from trade positions.")
    if operation == "open-short" and args.asset and args.asset.lower() != "bnbusd":
        warnings.append("Mechanism docs describe sPOSITION collateral as bnbUSD, while getting-started trade docs mention a broader approved-asset selector.")
    if operation in {"open-long", "open-short", "add-position", "adjust-leverage"}:
        checks.append("Verify leverage is still within docs range: 1.1x-7x.")
    if operation in {"close-position", "reduce-position"} and args.position_percent is not None:
        checks.append(f"Confirm close size: {args.position_percent}% of current position.")
    if operation == "mint-close" and args.repay_amount:
        checks.append(f"Confirm bnbUSD repay amount: {args.repay_amount}.")
    if operation == "mint-close":
        checks.append("Confirm this is the archived mint-close flow, not /trade close-position or Stability Pool redeem.")
        checks.append("Run sigma account mint-close-readiness or sigma account bnbusd-trace first; current evidence points to wallet-held bnbUSD repay semantics rather than hidden internal netting.")
        checks.append("Distinguish delayed Stability Pool redeem from instant redeem; a pending unlock/claim banner does not satisfy wallet-held repay readiness yet.")
    if operation == "bnbusd-redeem":
        fees.append("Docs list a redemption fee of 0.5% for the peg/redemption path.")
        assumptions.append("Docs cap redemption at 20% of a position at a time, but exact live enforcement should be verified from current UI/tx evidence.")
        checks.append("Confirm whether the current UI exposes a redemption route or whether this remains a docs-only mechanism description.")
        checks.append("Disambiguate this from Stability Pool redeem and from /trade close-position before acting.")
    if operation.startswith("stability-pool-redeem") or operation == "stability-pool-withdraw":
        checks.append("Disambiguate Stability Pool redeem from docs-described bnbUSD peg redemption and from /trade close-position.")
    if operation in {"close-position", "reduce-position"}:
        checks.append("Disambiguate /trade close from Stability Pool redeem and bnbUSD peg redemption in operator notes.")
    if operation.startswith("mint"):
        checks.append("Capture a fresh preview because mint flows are archived/legacy in the consulted Sigma docs.")

    approval_token = _approval_token(operation, args.asset)
    approval_policy_payload = _approval_policy_payload(
        operation,
        approval_token,
        args.repay_amount or args.amount,
        approval_policy,
    )
    if approval_token:
        checks.append(f"Active approval policy: {approval_policy.mode}.")
        if approval_policy.mode == "unlimited":
            warnings.append(f"Active approval policy is unlimited for {approval_token}; confirm that you actually want a max allowance before signing.")
        elif approval_policy.mode == "custom":
            checks.append(f"Configured finite approval cap for {approval_token}: {approval_policy.amount}.")
        elif approval_policy.mode == "exact":
            checks.append(f"Exact approval policy expects the allowance to match the intended {approval_token} spend for this transaction.")
    if operation == "mint-close":
        warnings.append("Partial mint close is modeled as supported, but the exact close write path still is not proven enough for direct execution tooling.")
        warnings.append("Live 2026-03-16 evidence showed Rabby requesting max bnbUSD approval for close even with Sigma Unlimited Approval visually OFF.")

    return {
        "protocol": "Sigma.Money",
        "operation": operation,
        "operationModel": route_operation_details(operation),
        "route": spec["route"],
        "routeKind": spec["routeKind"],
        "network": CHAIN,
        "inputs": {
            "asset": args.asset,
            "amount": args.amount,
            "leverage": args.leverage,
            "slippageBps": args.slippage_bps,
            "positionPercent": args.position_percent,
            "repayAmount": args.repay_amount,
            "immediate": args.immediate,
        },
        "requiredApprovalToken": approval_token,
        "approvalPolicy": approval_policy_payload,
        "closeSemantics": _close_semantics_payload(operation, args.repay_amount),
        "relatedContracts": _operation_contracts(operation),
        "semanticNotes": list(spec["disambiguation"]),
        "docsBackedAssumptions": assumptions,
        "preflightChecks": checks,
        "feesAndConstraints": fees,
        "warnings": warnings,
        "sources": list(spec["sources"]),
    }
