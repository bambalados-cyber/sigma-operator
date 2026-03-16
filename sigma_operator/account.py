from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, getcontext
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from .abi import decode_arguments, normalize_address, selector_for_signature, user_facing_views
from .config import (
    MAX_UINT256,
    approval_policy_desired_allowance_raw,
    approval_policy_to_dict,
    format_token_amount_from_raw,
    get_settings,
    parse_token_amount_to_raw,
    resolve_approval_policy,
)
from .fetch import FetchError, fetch_transaction_bundle
from .operations import RELATED_CONTRACTS

DEFAULT_SIGMA_APP_BASE_URL = "https://sigma.money"
DEFAULT_OBSERVED_SIGMA_ROUTER_ADDRESS = "0xae2658f23176f843af11d2209dbd04cffc0ff87b"
DISCOVERED_LIVE_POOL_ADDRESSES = [
    "0x31c464Cfe506d44CEaA86C05CDBB94b5c94f70fb",
    "0x6C83261d45a394475bc1f4E2C6355b8d9c621855",
    "0x7a97B5Fad34Ca48158B79245149A0fCf664aed91",
]
DEFAULT_STABILITY_POOL_ADDRESSES = [
    "0xde1bdd429692e12e60796ae02208b14fd5eacea7",
    "0x16d39a7a489dcbeb1ec6da383f1d95a7b1754c94",
    "0x2b9C1F069Ddcd873275B3363986081bDA94A3aA3",
]
STABILITY_POOL_METADATA = {
    normalize_address("0xde1bdd429692e12e60796ae02208b14fd5eacea7"): {
        "label": "bnbUSD/USDT Stability Pool - Lista-Pangolins Vault",
        "source": "2026-03-14/16 current-app devtools + live Rabby spender evidence",
    },
    normalize_address("0x16d39a7a489dcbeb1ec6da383f1d95a7b1754c94"): {
        "label": "bnbUSD/USDT Stability Pool - Lista Vault",
        "source": "2026-03-14 current-app devtools multicall evidence",
    },
    normalize_address("0x2b9C1F069Ddcd873275B3363986081bDA94A3aA3"): {
        "label": "Sigma Stability Pool (docs-published base pool)",
        "source": "docs.sigma.money smart-contract list",
    },
}
_TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
_APPROVAL_TOPIC0 = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
_BROWSERISH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}
getcontext().prec = 80


class AccountFetchError(RuntimeError):
    pass


def fetch_account_status(
    owner: str,
    *,
    rpc_url: str | None = None,
    timeout_seconds: float | None = None,
    pools: list[str] | None = None,
    sigma_app_base_url: str = DEFAULT_SIGMA_APP_BASE_URL,
    include_history: bool = False,
    history_limit: int = 20,
    include_empty_pools: bool = True,
    include_controller_entry_price: bool = False,
    controller_address: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    normalized_owner = normalize_address(owner)
    if normalized_owner is None or not normalized_owner.startswith("0x") or len(normalized_owner) != 42:
        raise AccountFetchError("owner must be a 20-byte 0x-prefixed address")

    resolved_rpc_url = (rpc_url or settings.bnb_rpc_url or "").strip()
    if not resolved_rpc_url:
        raise AccountFetchError(
            "BNB Chain RPC URL is required. Use --bnb-rpc-url (or aliases) or set SIGMA_OPERATOR_BNB_RPC_URL."
        )
    resolved_timeout = float(timeout_seconds or settings.bnb_rpc_timeout_seconds)

    chosen_pools = _resolve_pool_list(pools)
    chain_id_hex = _rpc_call(resolved_rpc_url, "eth_chainId", [], timeout_seconds=resolved_timeout)
    chain_id = _parse_intlike(chain_id_hex)
    if chain_id != 56:
        raise AccountFetchError(f"Expected BNB Chain chainId 56 but RPC returned {chain_id!r}")

    views = _function_views()
    sy_pool_functions = views["SyPool"]
    controller_functions = views["SigmaController"]
    resolved_controller = normalize_address(controller_address or RELATED_CONTRACTS["SigmaController"])

    total_positions = 0
    total_raw_colls = 0
    total_raw_debts = 0
    pool_records: list[dict[str, Any]] = []
    warnings: list[str] = []

    for pool in chosen_pools:
        try:
            balance_value = int(
                _call_view_function(
                    resolved_rpc_url,
                    resolved_timeout,
                    pool,
                    sy_pool_functions["balanceOf"],
                    [normalized_owner],
                )
            )
        except Exception as exc:  # noqa: BLE001 - preserve partial pool evidence
            warnings.append(f"Pool {pool}: balanceOf(owner) failed: {exc}")
            pool_records.append({
                "pool": pool,
                "status": "error",
                "error": str(exc),
            })
            continue

        pool_record: dict[str, Any] = {
            "pool": pool,
            "positionCount": balance_value,
            "positions": [],
        }

        if balance_value == 0 and not include_empty_pools:
            continue

        for index in range(balance_value):
            try:
                token_id = int(
                    _call_view_function(
                        resolved_rpc_url,
                        resolved_timeout,
                        pool,
                        sy_pool_functions["tokenOfOwnerByIndex"],
                        [normalized_owner, index],
                    )
                )
                raw_position = _call_view_function(
                    resolved_rpc_url,
                    resolved_timeout,
                    pool,
                    sy_pool_functions["getPosition"],
                    [token_id],
                )
                position_data = _call_view_function(
                    resolved_rpc_url,
                    resolved_timeout,
                    pool,
                    sy_pool_functions["positionData"],
                    [token_id],
                )
                position_metadata = _call_view_function(
                    resolved_rpc_url,
                    resolved_timeout,
                    pool,
                    sy_pool_functions["positionMetadata"],
                    [token_id],
                )
            except Exception as exc:  # noqa: BLE001 - keep other positions/pools alive
                warnings.append(f"Pool {pool} token index {index}: onchain view read failed: {exc}")
                pool_record["positions"].append({
                    "index": index,
                    "status": "error",
                    "error": str(exc),
                })
                continue

            total_positions += 1
            total_raw_colls += int(raw_position.get("rawColls", 0))
            total_raw_debts += int(raw_position.get("rawDebts", 0))

            position_record: dict[str, Any] = {
                "index": index,
                "tokenId": token_id,
                "rawPosition": raw_position,
                "positionData": position_data,
                "positionMetadata": {
                    "raw": position_metadata,
                    "asUint256": _bytes32_hex_to_int(position_metadata) if isinstance(position_metadata, str) else None,
                },
            }

            try:
                position_record["entryPriceNoAuth"] = _fetch_entry_price_no_auth(
                    sigma_app_base_url,
                    pool,
                    token_id,
                    normalized_owner,
                    timeout_seconds=resolved_timeout,
                )
            except Exception as exc:  # noqa: BLE001 - no-auth enrichment is optional
                warnings.append(f"Pool {pool} token {token_id}: getEntryPrice/no-auth failed: {exc}")

            if include_history:
                try:
                    position_record["historyNoAuth"] = _fetch_long_short_list_no_auth(
                        sigma_app_base_url,
                        pool,
                        token_id,
                        normalized_owner,
                        timeout_seconds=resolved_timeout,
                        limit=history_limit,
                    )
                except Exception as exc:  # noqa: BLE001 - preserve onchain status even if app API fails
                    warnings.append(f"Pool {pool} token {token_id}: long-short-list/no-auth failed: {exc}")

            if include_controller_entry_price and resolved_controller:
                try:
                    controller_result = _call_view_function(
                        resolved_rpc_url,
                        resolved_timeout,
                        resolved_controller,
                        controller_functions["positionIdToEntryPrice"],
                        [pool, token_id],
                    )
                    if any(int(controller_result.get(key, 0)) != 0 for key in ("entryPrice", "positionColl", "positionDebt")):
                        position_record["controllerEntryPriceHint"] = {
                            "controller": resolved_controller,
                            "params": {"pool": pool, "positionId": token_id},
                            "result": controller_result,
                        }
                    else:
                        position_record["controllerEntryPriceHint"] = {
                            "controller": resolved_controller,
                            "params": {"pool": pool, "positionId": token_id},
                            "result": controller_result,
                            "note": "Returned zeroed values; binding remains unproven for this live pool/position pair.",
                        }
                except Exception as exc:  # noqa: BLE001 - experimental hint only
                    warnings.append(f"Pool {pool} token {token_id}: controller entry-price hint failed: {exc}")

            pool_record["positions"].append(position_record)

        pool_records.append(pool_record)

    return {
        "mode": "account-status",
        "owner": normalized_owner,
        "rpc": {
            "url": resolved_rpc_url,
            "chainId": chain_id,
            "timeoutSeconds": resolved_timeout,
            "readOnlyMethods": ["eth_chainId", "eth_call"],
        },
        "poolDiscovery": {
            "source": "2026-03-15 Sigma current-app frontier + explicit overrides",
            "queriedPools": chosen_pools,
            "defaultDiscoveredPools": [normalize_address(pool) for pool in DISCOVERED_LIVE_POOL_ADDRESSES],
        },
        "sigmaApp": {
            "baseUrl": sigma_app_base_url.rstrip("/"),
            "noAuthEntryPriceAttempted": True,
            "noAuthHistoryAttempted": include_history,
        },
        "portfolio": {
            "positionCount": total_positions,
            "totalRawColls": total_raw_colls,
            "totalRawDebts": total_raw_debts,
            "poolsWithPositions": [record["pool"] for record in pool_records if record.get("positionCount", 0) > 0],
        },
        "pools": pool_records,
        "warnings": warnings,
        "notes": [
            "Onchain reads currently assume the live pool addresses expose the SyPool view surface discovered from the Sigma frontier.",
            "No-auth Sigma app helpers need browser-like headers; direct bare urllib/curl requests can 403.",
            "controllerEntryPriceHint is experimental because the verified SigmaController signature binding is not yet proven across the live pool set.",
        ],
    }


def fetch_account_positions(
    owner: str,
    *,
    rpc_url: str | None = None,
    timeout_seconds: float | None = None,
    pools: list[str] | None = None,
    sigma_app_base_url: str = DEFAULT_SIGMA_APP_BASE_URL,
    include_controller_entry_price: bool = False,
    controller_address: str | None = None,
) -> dict[str, Any]:
    status = fetch_account_status(
        owner,
        rpc_url=rpc_url,
        timeout_seconds=timeout_seconds,
        pools=pools,
        sigma_app_base_url=sigma_app_base_url,
        include_history=False,
        include_empty_pools=False,
        include_controller_entry_price=include_controller_entry_price,
        controller_address=controller_address,
    )
    positions: list[dict[str, Any]] = []
    for pool_record in status.get("pools", []):
        pool = pool_record.get("pool")
        for position in pool_record.get("positions", []):
            if position.get("status") == "error":
                continue
            positions.append({
                "pool": pool,
                **position,
            })
    return {
        "mode": "account-positions",
        "owner": status["owner"],
        "rpc": status["rpc"],
        "portfolio": status["portfolio"],
        "positions": positions,
        "warnings": status.get("warnings", []),
        "notes": [
            "This is a flattened projection of account status intended for direct portfolio/position inspection.",
            *status.get("notes", []),
        ],
    }


def fetch_account_history(
    owner: str,
    *,
    rpc_url: str | None = None,
    timeout_seconds: float | None = None,
    pools: list[str] | None = None,
    sigma_app_base_url: str = DEFAULT_SIGMA_APP_BASE_URL,
    history_limit: int = 20,
    position_id: int | None = None,
) -> dict[str, Any]:
    status = fetch_account_status(
        owner,
        rpc_url=rpc_url,
        timeout_seconds=timeout_seconds,
        pools=pools,
        sigma_app_base_url=sigma_app_base_url,
        include_history=True,
        history_limit=history_limit,
        include_empty_pools=False,
        include_controller_entry_price=False,
    )
    items: list[dict[str, Any]] = []
    for pool_record in status.get("pools", []):
        pool = pool_record.get("pool")
        for position in pool_record.get("positions", []):
            token_id = position.get("tokenId")
            if position_id is not None and token_id != position_id:
                continue
            history_items = position.get("historyNoAuth", {}).get("response", {}).get("items", [])
            for item in history_items:
                items.append({
                    "pool": pool,
                    "positionId": token_id,
                    **item,
                })
    items.sort(key=lambda item: str(item.get("timestamp") or item.get("createDate") or ""), reverse=True)
    return {
        "mode": "account-history",
        "owner": status["owner"],
        "rpc": status["rpc"],
        "history": {
            "count": len(items),
            "positionFilter": position_id,
            "items": items,
        },
        "warnings": status.get("warnings", []),
        "notes": [
            "History is sourced from Sigma current-app no-auth endpoints layered on top of pool discovery.",
            "Use this for route/account continuity, not as a canonical audit replacement for raw chain traces.",
        ],
    }


def fetch_mint_close_readiness(
    owner: str,
    *,
    position_id: int,
    pool: str,
    rpc_url: str | None = None,
    timeout_seconds: float | None = None,
    bnbusd_address: str | None = None,
    router_address: str | None = None,
    repay_amount: str | None = None,
    target_ltv: str | None = None,
    withdraw_amount: str | None = None,
    approval_policy_mode: str | None = None,
    approval_amount: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    normalized_owner = normalize_address(owner)
    normalized_pool = normalize_address(pool)
    normalized_bnbusd = normalize_address(bnbusd_address or RELATED_CONTRACTS["BNBUSD"])
    normalized_router = normalize_address(router_address or DEFAULT_OBSERVED_SIGMA_ROUTER_ADDRESS)
    if normalized_owner is None or not normalized_owner.startswith("0x") or len(normalized_owner) != 42:
        raise AccountFetchError("owner must be a 20-byte 0x-prefixed address")
    if normalized_pool is None or not normalized_pool.startswith("0x") or len(normalized_pool) != 42:
        raise AccountFetchError("pool must be a 20-byte 0x-prefixed address")
    if normalized_bnbusd is None or not normalized_bnbusd.startswith("0x") or len(normalized_bnbusd) != 42:
        raise AccountFetchError("bnbusd_address must be a 20-byte 0x-prefixed address")
    if normalized_router is None or not normalized_router.startswith("0x") or len(normalized_router) != 42:
        raise AccountFetchError("router_address must be a 20-byte 0x-prefixed address")

    resolved_rpc_url = (rpc_url or settings.bnb_rpc_url or "").strip()
    if not resolved_rpc_url:
        raise AccountFetchError(
            "BNB Chain RPC URL is required. Use --bnb-rpc-url (or aliases) or set SIGMA_OPERATOR_BNB_RPC_URL."
        )
    resolved_timeout = float(timeout_seconds or settings.bnb_rpc_timeout_seconds)

    chain_id_hex = _rpc_call(resolved_rpc_url, "eth_chainId", [], timeout_seconds=resolved_timeout)
    chain_id = _parse_intlike(chain_id_hex)
    if chain_id != 56:
        raise AccountFetchError(f"Expected BNB Chain chainId 56 but RPC returned {chain_id!r}")

    views = _function_views_for({
        "BNBUSD": {"balanceOf", "allowance"},
        "SyPool": {"ownerOf", "getApproved", "isApprovedForAll", "getPosition", "positionData", "getPositionDebtRatio"},
    })
    bnbusd_functions = views["BNBUSD"]
    sy_pool_functions = views["SyPool"]

    wallet_bnbusd_balance = int(
        _call_view_function(
            resolved_rpc_url,
            resolved_timeout,
            normalized_bnbusd,
            bnbusd_functions["balanceOf"],
            [normalized_owner],
        )
    )
    wallet_bnbusd_allowance = int(
        _call_view_function(
            resolved_rpc_url,
            resolved_timeout,
            normalized_bnbusd,
            bnbusd_functions["allowance"],
            [normalized_owner, normalized_router],
        )
    )
    nft_owner = _call_view_function(
        resolved_rpc_url,
        resolved_timeout,
        normalized_pool,
        sy_pool_functions["ownerOf"],
        [position_id],
    )
    nft_get_approved = _call_view_function(
        resolved_rpc_url,
        resolved_timeout,
        normalized_pool,
        sy_pool_functions["getApproved"],
        [position_id],
    )
    nft_approved_for_all = bool(
        _call_view_function(
            resolved_rpc_url,
            resolved_timeout,
            normalized_pool,
            sy_pool_functions["isApprovedForAll"],
            [normalized_owner, normalized_router],
        )
    )
    raw_position = _call_view_function(
        resolved_rpc_url,
        resolved_timeout,
        normalized_pool,
        sy_pool_functions["getPosition"],
        [position_id],
    )
    position_data = _call_view_function(
        resolved_rpc_url,
        resolved_timeout,
        normalized_pool,
        sy_pool_functions["positionData"],
        [position_id],
    )
    debt_ratio = int(
        _call_view_function(
            resolved_rpc_url,
            resolved_timeout,
            normalized_pool,
            sy_pool_functions["getPositionDebtRatio"],
            [position_id],
        )
    )

    raw_debt = int(raw_position.get("rawDebts", 0))
    raw_coll = int(raw_position.get("rawColls", 0))
    debt_shortfall = max(raw_debt - wallet_bnbusd_balance, 0)
    allowance_shortfall = max(raw_debt - wallet_bnbusd_allowance, 0)
    nft_router_ready = nft_approved_for_all or normalize_address(str(nft_get_approved)) == normalized_router
    wallet_has_full_raw_debt = wallet_bnbusd_balance >= raw_debt
    wallet_has_full_router_allowance = wallet_bnbusd_allowance >= raw_debt
    observed_ui_blocker_consistent = wallet_bnbusd_balance == 0

    try:
        approval_policy = resolve_approval_policy(
            mode_override=approval_policy_mode,
            amount_override=approval_amount,
        )
    except ValueError as exc:
        raise AccountFetchError(str(exc)) from exc

    partial_close_preview = _build_partial_mint_close_preview(
        repay_amount=repay_amount,
        withdraw_amount=withdraw_amount,
        target_ltv=target_ltv,
        raw_debt=raw_debt,
        raw_coll=raw_coll,
        debt_ratio_wad=debt_ratio,
        wallet_balance_raw=wallet_bnbusd_balance,
        current_allowance_raw=wallet_bnbusd_allowance,
        approval_policy=approval_policy,
    )

    semantic_findings = [
        "The live mint position carries explicit onchain debt in the SyPool position record; it is not just frontend-only accounting.",
        "The wallet currently holds zero spendable bnbUSD, which is consistent with Sigma showing Repay Balance: 0.00 on the close surface." if wallet_bnbusd_balance == 0 else "Wallet-held bnbUSD is present, so the close path can now be modeled as repayable instead of blocked by zero repay balance alone.",
        "The observed router currently has neither bnbUSD allowance nor NFT approval from this wallet/position, so a close path would still need approvals even after funding bnbUSD." if not nft_router_ready or wallet_bnbusd_allowance == 0 else "Observed router allowance / NFT authority is no longer the only blocker; partial close planning can focus on repay amount and LTV constraints.",
        "Because ERC721 approvals clear on transfer, repeated router-mediated position modifications can require fresh NFT approval unless approval-for-all is set.",
        "Current close semantics now treat partial repay / partial close as supported: the debt token is bnbUSD, max withdraw depends on repay amount, and LTV/health remains the governing constraint.",
        "The partial-close preview is a specified read-side math model grounded in current debt ratio / LTV, not a final contract-validated close quote.",
    ]

    notes = [
        "The observed router address comes from live write-path evidence, not from the docs-published contract list.",
        "rawDebts is the safest debt-side number for readiness checks because it matches the initial minted bnbUSD amount in the captured open transaction bundle.",
        "Use sigma account bnbusd-trace to classify wallet-held vs deposited vs pending/claimable repay sources before assuming the debt token simply disappeared.",
        "Use sigma account stability-pools to distinguish delayed redeem vs claimable-after-unlock directly from redeemRequests(address) chain state.",
        "Exact full-close execution still needs a live preview/tx capture before hardcoding spender, min-coll, or fee math into write commands.",
        "The 2026-03-16 current frontend bundle includes an exact-approval branch for mint-close (approve 0, then approve the repay amount) when Unlimited Approval is OFF, but the live Rabby popup still surfaced max approval, so the unresolved blocker is now the UI-state / popup-path mismatch rather than absence of a finite-approval branch in code.",
    ]

    return {
        "mode": "account-mint-close-readiness",
        "owner": normalized_owner,
        "pool": normalized_pool,
        "positionId": position_id,
        "rpc": {
            "url": resolved_rpc_url,
            "chainId": chain_id,
            "timeoutSeconds": resolved_timeout,
            "readOnlyMethods": ["eth_chainId", "eth_call"],
        },
        "observedWriteTarget": {
            "routerAddress": normalized_router,
            "source": "2026-03-15/16 live Sigma mint write-path captures",
            "note": "Observed live write target from Rabby/Sigma captures; not a docs-published contract.",
        },
        "approvalPolicy": {
            **approval_policy_to_dict(approval_policy),
            "writePathStatus": "modeled-but-not-fully-proven",
            "evidenceNote": "Current live close evidence still showed Rabby requesting max approval even when Sigma Unlimited Approval was visually OFF, but the 2026-03-16 frontend bundle also exposes a finite-approval branch for the OFF state.",
        },
        "assets": {
            "bnbusd": {
                "tokenAddress": normalized_bnbusd,
                "walletBalanceRaw": wallet_bnbusd_balance,
                "walletBalance": _format_18(wallet_bnbusd_balance),
                "allowanceToObservedRouterRaw": wallet_bnbusd_allowance,
                "allowanceToObservedRouter": _format_18(wallet_bnbusd_allowance),
            },
            "position": {
                "rawColls": raw_coll,
                "rawCollsFormatted": _format_18(raw_coll),
                "rawDebts": raw_debt,
                "rawDebtsFormatted": _format_18(raw_debt),
                "positionData": position_data,
                "positionDataFormatted": {
                    "colls": _format_18(int(position_data.get("colls", 0))),
                    "debts": _format_18(int(position_data.get("debts", 0))),
                },
                "debtRatioWad": debt_ratio,
                "debtRatioRatio": str(Decimal(debt_ratio) / Decimal(10**18)),
                "debtRatioPercent": _format_percent_from_wad(debt_ratio),
            },
        },
        "nftControl": {
            "ownerOf": nft_owner,
            "getApproved": nft_get_approved,
            "isApprovedForAllToObservedRouter": nft_approved_for_all,
            "observedRouterCanMovePositionNow": nft_router_ready,
        },
        "closureReadiness": {
            "walletHasFullRawDebt": wallet_has_full_raw_debt,
            "walletHasFullAllowanceToObservedRouter": wallet_has_full_router_allowance,
            "observedRouterCanMovePositionNow": nft_router_ready,
            "rawDebtShortfall": debt_shortfall,
            "rawDebtShortfallFormatted": _format_18(debt_shortfall),
            "allowanceShortfall": allowance_shortfall,
            "allowanceShortfallFormatted": _format_18(allowance_shortfall),
            "observedUiCloseBlockerConsistentWithWalletState": observed_ui_blocker_consistent,
            "supportsPartialRepay": True,
            "supportsPartialClose": True,
            "walletHeldRepayRequired": True,
            "maxWithdrawDependsOnRepayAmount": True,
            "governingConstraint": "LTV / health",
        },
        "partialClosePreview": partial_close_preview,
        "semanticFindings": semantic_findings,
        "notes": notes,
    }

def fetch_stability_pool_status(
    owner: str,
    *,
    rpc_url: str | None = None,
    timeout_seconds: float | None = None,
    pools: list[str] | None = None,
    bnbusd_address: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    normalized_owner = normalize_address(owner)
    normalized_bnbusd = normalize_address(bnbusd_address or RELATED_CONTRACTS["BNBUSD"])
    if normalized_owner is None or not normalized_owner.startswith("0x") or len(normalized_owner) != 42:
        raise AccountFetchError("owner must be a 20-byte 0x-prefixed address")
    if normalized_bnbusd is None or not normalized_bnbusd.startswith("0x") or len(normalized_bnbusd) != 42:
        raise AccountFetchError("bnbusd_address must be a 20-byte 0x-prefixed address")

    resolved_rpc_url = (rpc_url or settings.bnb_rpc_url or "").strip()
    if not resolved_rpc_url:
        raise AccountFetchError(
            "BNB Chain RPC URL is required. Use --bnb-rpc-url (or aliases) or set SIGMA_OPERATOR_BNB_RPC_URL."
        )
    resolved_timeout = float(timeout_seconds or settings.bnb_rpc_timeout_seconds)

    chain_id_hex = _rpc_call(resolved_rpc_url, "eth_chainId", [], timeout_seconds=resolved_timeout)
    chain_id = _parse_intlike(chain_id_hex)
    if chain_id != 56:
        raise AccountFetchError(f"Expected BNB Chain chainId 56 but RPC returned {chain_id!r}")

    chosen_pools = _resolve_contract_list(pools or DEFAULT_STABILITY_POOL_ADDRESSES)
    views = _function_views_for({
        "BNBUSDBasePool": {
            "balanceOf",
            "redeemRequests",
            "previewRedeem",
            "redeemCoolDownPeriod",
            "stableToken",
            "yieldToken",
            "name",
            "symbol",
            "decimals",
        },
    })
    pool_functions = views["BNBUSDBasePool"]
    now_ts = int(datetime.now(tz=UTC).timestamp())

    pool_records: list[dict[str, Any]] = []
    warnings: list[str] = []
    total_share_balance_raw = 0
    total_pending_redeem_shares_raw = 0
    total_available_shares_raw = 0
    total_estimated_bnbusd_in_available_shares_raw = 0
    total_estimated_bnbusd_pending_redeem_raw = 0
    total_estimated_bnbusd_claimable_raw = 0

    for stability_pool in chosen_pools:
        metadata = STABILITY_POOL_METADATA.get(stability_pool, {})
        record: dict[str, Any] = {
            "pool": stability_pool,
            "label": metadata.get("label"),
            "source": metadata.get("source"),
        }
        try:
            name = _call_view_function(resolved_rpc_url, resolved_timeout, stability_pool, pool_functions["name"], [])
            symbol = _call_view_function(resolved_rpc_url, resolved_timeout, stability_pool, pool_functions["symbol"], [])
            decimals = int(_call_view_function(resolved_rpc_url, resolved_timeout, stability_pool, pool_functions["decimals"], []))
            stable_token = _call_view_function(resolved_rpc_url, resolved_timeout, stability_pool, pool_functions["stableToken"], [])
            yield_token = _call_view_function(resolved_rpc_url, resolved_timeout, stability_pool, pool_functions["yieldToken"], [])
            cooldown = int(_call_view_function(resolved_rpc_url, resolved_timeout, stability_pool, pool_functions["redeemCoolDownPeriod"], []))
            share_balance_raw = int(_call_view_function(resolved_rpc_url, resolved_timeout, stability_pool, pool_functions["balanceOf"], [normalized_owner]))
            redeem_request = _call_view_function(resolved_rpc_url, resolved_timeout, stability_pool, pool_functions["redeemRequests"], [normalized_owner])
        except Exception as exc:  # noqa: BLE001 - preserve partial pool evidence
            warnings.append(f"Stability pool {stability_pool}: read failed: {exc}")
            pool_records.append({
                **record,
                "status": "error",
                "error": str(exc),
            })
            continue

        pending_redeem_raw = int(redeem_request.get("amount", 0)) if isinstance(redeem_request, dict) else 0
        unlock_at = int(redeem_request.get("unlockAt", 0)) if isinstance(redeem_request, dict) else 0
        available_shares_raw = max(share_balance_raw - pending_redeem_raw, 0)
        claimable_now = pending_redeem_raw > 0 and unlock_at <= now_ts

        record.update({
            "status": "ok",
            "name": name,
            "symbol": symbol,
            "decimals": decimals,
            "tokens": {
                "yieldToken": yield_token,
                "yieldTokenIsBnbUsd": normalize_address(str(yield_token)) == normalized_bnbusd,
                "stableToken": stable_token,
            },
            "balances": {
                "shareBalanceRaw": share_balance_raw,
                "shareBalance": _format_units(share_balance_raw, decimals),
                "pendingRedeemSharesRaw": pending_redeem_raw,
                "pendingRedeemShares": _format_units(pending_redeem_raw, decimals),
                "availableSharesRaw": available_shares_raw,
                "availableShares": _format_units(available_shares_raw, decimals),
            },
            "timing": {
                "coolDownSeconds": cooldown,
                "pendingUnlockAt": unlock_at,
                "pendingUnlockAtUtc": _unix_timestamp_to_utc(unlock_at),
                "pendingRedeemClaimableNow": claimable_now,
                "secondsUntilUnlock": max(unlock_at - now_ts, 0) if pending_redeem_raw > 0 else 0,
                "observedAtUtc": _unix_timestamp_to_utc(now_ts),
            },
        })

        available_preview = None
        pending_preview = None
        estimated_available_bnbusd_raw = 0
        estimated_pending_bnbusd_raw = 0

        if available_shares_raw > 0:
            try:
                preview = _call_view_function(
                    resolved_rpc_url,
                    resolved_timeout,
                    stability_pool,
                    pool_functions["previewRedeem"],
                    [available_shares_raw],
                )
                available_preview = _format_redeem_preview(preview)
                if normalize_address(str(yield_token)) == normalized_bnbusd:
                    estimated_available_bnbusd_raw = int(preview.get("amountYieldOut", 0))
            except Exception as exc:  # noqa: BLE001 - keep other signals intact
                warnings.append(f"Stability pool {stability_pool}: previewRedeem(availableShares) failed: {exc}")

        if pending_redeem_raw > 0:
            try:
                preview = _call_view_function(
                    resolved_rpc_url,
                    resolved_timeout,
                    stability_pool,
                    pool_functions["previewRedeem"],
                    [pending_redeem_raw],
                )
                pending_preview = _format_redeem_preview(preview)
                if normalize_address(str(yield_token)) == normalized_bnbusd:
                    estimated_pending_bnbusd_raw = int(preview.get("amountYieldOut", 0))
            except Exception as exc:  # noqa: BLE001 - keep other signals intact
                warnings.append(f"Stability pool {stability_pool}: previewRedeem(pendingRedeem) failed: {exc}")

        if available_preview is not None:
            record["availableRedeemPreview"] = available_preview
        if pending_preview is not None:
            record["pendingRedeemPreview"] = pending_preview

        record["classification"] = {
            "hasShareBalance": share_balance_raw > 0,
            "hasPendingRedeem": pending_redeem_raw > 0,
            "pendingRedeemClaimableNow": claimable_now,
            "estimatedBnbUsdInAvailableSharesRaw": estimated_available_bnbusd_raw,
            "estimatedBnbUsdInAvailableShares": _format_18(estimated_available_bnbusd_raw),
            "estimatedBnbUsdInPendingRedeemRaw": estimated_pending_bnbusd_raw,
            "estimatedBnbUsdInPendingRedeem": _format_18(estimated_pending_bnbusd_raw),
        }

        total_share_balance_raw += share_balance_raw
        total_pending_redeem_shares_raw += pending_redeem_raw
        total_available_shares_raw += available_shares_raw
        total_estimated_bnbusd_in_available_shares_raw += estimated_available_bnbusd_raw
        if claimable_now:
            total_estimated_bnbusd_claimable_raw += estimated_pending_bnbusd_raw
        else:
            total_estimated_bnbusd_pending_redeem_raw += estimated_pending_bnbusd_raw
        pool_records.append(record)

    return {
        "mode": "account-stability-pools",
        "owner": normalized_owner,
        "rpc": {
            "url": resolved_rpc_url,
            "chainId": chain_id,
            "timeoutSeconds": resolved_timeout,
            "readOnlyMethods": ["eth_chainId", "eth_call"],
        },
        "poolDiscovery": {
            "queriedPools": chosen_pools,
            "defaultDiscoveredPools": [normalize_address(pool) for pool in DEFAULT_STABILITY_POOL_ADDRESSES],
            "source": "2026-03-14/16 current-app earn bundle + docs base-pool references",
        },
        "summary": {
            "poolCount": len(pool_records),
            "poolsWithShareBalance": [record["pool"] for record in pool_records if record.get("balances", {}).get("shareBalanceRaw", 0) > 0],
            "poolsWithPendingRedeem": [record["pool"] for record in pool_records if record.get("balances", {}).get("pendingRedeemSharesRaw", 0) > 0],
            "totalShareBalanceRaw": total_share_balance_raw,
            "totalPendingRedeemSharesRaw": total_pending_redeem_shares_raw,
            "totalAvailableSharesRaw": total_available_shares_raw,
            "estimatedBnbUsdInAvailableSharesRaw": total_estimated_bnbusd_in_available_shares_raw,
            "estimatedBnbUsdInAvailableShares": _format_18(total_estimated_bnbusd_in_available_shares_raw),
            "estimatedBnbUsdPendingDelayedWithdrawRaw": total_estimated_bnbusd_pending_redeem_raw,
            "estimatedBnbUsdPendingDelayedWithdraw": _format_18(total_estimated_bnbusd_pending_redeem_raw),
            "estimatedBnbUsdClaimableAfterUnlockRaw": total_estimated_bnbusd_claimable_raw,
            "estimatedBnbUsdClaimableAfterUnlock": _format_18(total_estimated_bnbusd_claimable_raw),
        },
        "pools": pool_records,
        "warnings": warnings,
        "notes": [
            "redeemRequests(address) is an onchain pending-withdraw register, so delayed withdraw vs claimable-after-unlock can be distinguished directly without browser automation.",
            "previewRedeem(...) outputs are estimates from the current pool math, not a claim that redeem() has already been executed.",
            "Available share estimates use balanceOf(owner) minus pending redeem shares so pending and still-deposited buckets do not double-count the same share amount.",
        ],
    }


def fetch_bnbusd_trace(
    owner: str,
    *,
    position_id: int,
    pool: str,
    rpc_url: str | None = None,
    timeout_seconds: float | None = None,
    sigma_app_base_url: str = DEFAULT_SIGMA_APP_BASE_URL,
    history_limit: int = 20,
    bnbusd_address: str | None = None,
    router_address: str | None = None,
    stability_pools: list[str] | None = None,
    tx_hashes: list[str] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    resolved_rpc_url = (rpc_url or settings.bnb_rpc_url or "").strip()
    if not resolved_rpc_url:
        raise AccountFetchError(
            "BNB Chain RPC URL is required. Use --bnb-rpc-url (or aliases) or set SIGMA_OPERATOR_BNB_RPC_URL."
        )
    resolved_timeout = float(timeout_seconds or settings.bnb_rpc_timeout_seconds)

    readiness = fetch_mint_close_readiness(
        owner,
        position_id=position_id,
        pool=pool,
        rpc_url=resolved_rpc_url,
        timeout_seconds=resolved_timeout,
        bnbusd_address=bnbusd_address,
        router_address=router_address,
    )
    normalized_owner = readiness["owner"]
    normalized_pool = readiness["pool"]
    normalized_bnbusd = readiness["assets"]["bnbusd"]["tokenAddress"]
    normalized_router = readiness["observedWriteTarget"]["routerAddress"]

    stability_status = fetch_stability_pool_status(
        normalized_owner,
        rpc_url=resolved_rpc_url,
        timeout_seconds=resolved_timeout,
        pools=stability_pools,
        bnbusd_address=normalized_bnbusd,
    )
    spender_addresses = _resolve_contract_list([
        normalized_router,
        *(record.get("pool") for record in stability_status.get("pools", []) if record.get("pool")),
    ])
    known_allowances = _fetch_known_allowances(
        resolved_rpc_url,
        resolved_timeout,
        normalized_bnbusd,
        normalized_owner,
        spender_addresses,
    )

    history = fetch_account_history(
        normalized_owner,
        rpc_url=resolved_rpc_url,
        timeout_seconds=resolved_timeout,
        pools=[normalized_pool],
        sigma_app_base_url=sigma_app_base_url,
        history_limit=history_limit,
        position_id=position_id,
    )
    discovered_history_hashes = _history_tx_hashes(history.get("history", {}).get("items", []))
    requested_hashes = _resolve_tx_hashes(tx_hashes or discovered_history_hashes)

    tx_analyses: list[dict[str, Any]] = []
    warnings = [*readiness.get("warnings", []), *stability_status.get("warnings", []), *history.get("warnings", [])]
    for tx_hash in requested_hashes:
        try:
            bundle, _metadata = fetch_transaction_bundle(
                tx_hash,
                rpc_url=resolved_rpc_url,
                timeout_seconds=resolved_timeout,
                fetch_source="rpc",
            )
            tx_analyses.append(
                _analyze_bnbusd_transaction_bundle(
                    bundle,
                    owner=normalized_owner,
                    bnbusd_address=normalized_bnbusd,
                    observed_router=normalized_router,
                )
            )
        except FetchError as exc:
            warnings.append(f"tx {tx_hash}: fetch failed: {exc}")
            tx_analyses.append({
                "txHash": tx_hash,
                "status": "error",
                "error": str(exc),
            })

    origin_mint = next((item for item in tx_analyses if item.get("mintedTotalRaw", 0) > 0), None)
    wallet_balance_raw = readiness["assets"]["bnbusd"]["walletBalanceRaw"]
    approved_but_unspent_max_raw = max(
        (min(wallet_balance_raw, item.get("allowanceRaw", 0)) for item in known_allowances),
        default=0,
    )
    deposited_elsewhere_raw = int(stability_status.get("summary", {}).get("estimatedBnbUsdInAvailableSharesRaw", 0))
    pending_delayed_withdraw_raw = int(stability_status.get("summary", {}).get("estimatedBnbUsdPendingDelayedWithdrawRaw", 0))
    claimable_after_unlock_raw = int(stability_status.get("summary", {}).get("estimatedBnbUsdClaimableAfterUnlockRaw", 0))
    visible_repay_sources_raw = wallet_balance_raw + deposited_elsewhere_raw + pending_delayed_withdraw_raw + claimable_after_unlock_raw
    raw_debt = readiness["assets"]["position"]["rawDebts"]
    unknown_repay_gap_raw = max(raw_debt - visible_repay_sources_raw, 0)

    return {
        "mode": "account-bnbusd-trace",
        "owner": normalized_owner,
        "pool": normalized_pool,
        "positionId": position_id,
        "rpc": readiness["rpc"],
        "referencePosition": readiness["assets"]["position"],
        "mintCloseReadiness": readiness["closureReadiness"],
        "currentWalletState": {
            "bnbusd": readiness["assets"]["bnbusd"],
            "knownAllowances": known_allowances,
            "approvedButUnspentMaxRaw": approved_but_unspent_max_raw,
            "approvedButUnspentMax": _format_18(approved_but_unspent_max_raw),
        },
        "approvalPolicy": readiness.get("approvalPolicy"),
        "currentRepaySourceBuckets": {
            "walletHeldRaw": wallet_balance_raw,
            "walletHeld": _format_18(wallet_balance_raw),
            "approvedButUnspentRaw": approved_but_unspent_max_raw,
            "approvedButUnspent": _format_18(approved_but_unspent_max_raw),
            "depositedElsewhereEstimatedRaw": deposited_elsewhere_raw,
            "depositedElsewhereEstimated": _format_18(deposited_elsewhere_raw),
            "pendingDelayedWithdrawRaw": pending_delayed_withdraw_raw,
            "pendingDelayedWithdraw": _format_18(pending_delayed_withdraw_raw),
            "claimableAfterUnlockRaw": claimable_after_unlock_raw,
            "claimableAfterUnlock": _format_18(claimable_after_unlock_raw),
            "unknownNotDirectlyVisibleRaw": unknown_repay_gap_raw,
            "unknownNotDirectlyVisible": _format_18(unknown_repay_gap_raw),
        },
        "stabilityPools": stability_status,
        "historyEvidence": {
            "items": history.get("history", {}).get("items", []),
            "usedTxHashes": requested_hashes,
            "discoveredTxHashes": discovered_history_hashes,
        },
        "mintOriginTrace": {
            "referenceMintTx": origin_mint,
            "txAnalyses": tx_analyses,
            "semanticSummary": _summarize_origin_trace(origin_mint),
        },
        "warnings": warnings,
        "notes": [
            "currentRepaySourceBuckets are a direct repay-source model, not a cryptographic proof that the exact same bnbUSD units from the original mint tx still exist in each bucket.",
            "mintOriginTrace focuses on what the observed mint tx did in the same receipt/log bundle; currentRepaySourceBuckets focus on what is visible and potentially usable now.",
            "delayed withdraw vs claimable-after-unlock comes from live onchain redeemRequests(address) + previewRedeem(...) reads, so it stays in the direct-CLI/contract lane.",
            "approvalPolicy reflects the currently resolved CLI/operator preference, but live 2026-03-16 close evidence still showed a max-approval request even with Sigma Unlimited Approval visually OFF.",
        ],
    }


def _resolve_contract_list(candidates: list[str] | None) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for candidate in candidates or []:
        normalized = normalize_address(candidate)
        if normalized is None or not normalized.startswith("0x") or len(normalized) != 42:
            continue
        if normalized in seen:
            continue
        ordered.append(normalized)
        seen.add(normalized)
    return ordered


def _fetch_known_allowances(
    rpc_url: str,
    timeout_seconds: float,
    token_address: str,
    owner: str,
    spenders: list[str],
) -> list[dict[str, Any]]:
    views = _function_views_for({"BNBUSD": {"allowance"}})
    token_functions = views["BNBUSD"]
    results: list[dict[str, Any]] = []
    for spender in _resolve_contract_list(spenders):
        allowance_raw = int(
            _call_view_function(
                rpc_url,
                timeout_seconds,
                token_address,
                token_functions["allowance"],
                [owner, spender],
            )
        )
        pool_metadata = STABILITY_POOL_METADATA.get(spender, {})
        results.append({
            "spender": spender,
            "label": pool_metadata.get("label") or ("Observed Sigma router" if spender == normalize_address(DEFAULT_OBSERVED_SIGMA_ROUTER_ADDRESS) else None),
            "allowanceRaw": allowance_raw,
            "allowance": _format_18(allowance_raw),
        })
    return results


def _history_tx_hashes(items: list[dict[str, Any]]) -> list[str]:
    ranked: list[tuple[int, str, str]] = []
    for item in items:
        tx_hash = normalize_address(item.get("txHash"))
        if tx_hash is None or not tx_hash.startswith("0x") or len(tx_hash) != 66:
            continue
        timestamp_rank = _parse_intlike(item.get("timestamp"))
        create_date = str(item.get("createDate") or "")
        ranked.append((timestamp_rank if timestamp_rank is not None else 0, create_date, tx_hash))
    ranked.sort()
    ordered: list[str] = []
    seen: set[str] = set()
    for _timestamp_rank, _create_date, tx_hash in ranked:
        if tx_hash in seen:
            continue
        ordered.append(tx_hash)
        seen.add(tx_hash)
    return ordered


def _resolve_tx_hashes(candidates: list[str] | None) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for candidate in candidates or []:
        if not isinstance(candidate, str):
            continue
        normalized = candidate.strip().lower()
        if not normalized.startswith("0x") or len(normalized) != 66:
            continue
        if normalized in seen:
            continue
        ordered.append(normalized)
        seen.add(normalized)
    return ordered


def _analyze_bnbusd_transaction_bundle(
    bundle: dict[str, Any],
    *,
    owner: str,
    bnbusd_address: str,
    observed_router: str,
) -> dict[str, Any]:
    tx = bundle.get("transaction") or {}
    receipt = bundle.get("receipt") or {}
    normalized_owner = normalize_address(owner)
    normalized_bnbusd = normalize_address(bnbusd_address)
    normalized_router = normalize_address(observed_router)

    transfers: list[dict[str, Any]] = []
    approvals: list[dict[str, Any]] = []
    minted_total_raw = 0
    minted_to_wallet_raw = 0
    minted_to_router_raw = 0
    wallet_outflow_raw = 0
    router_outflow_raw = 0

    for log in receipt.get("logs", []):
        if normalize_address(log.get("address")) != normalized_bnbusd:
            continue
        topics = [str(topic).lower() for topic in (log.get("topics") or []) if topic]
        if not topics:
            continue
        if topics[0] == _TRANSFER_TOPIC0 and len(topics) >= 3:
            from_address = _topic_address(topics[1])
            to_address = _topic_address(topics[2])
            amount_raw = int(str(log.get("data") or "0x0"), 16)
            classification = _classify_transfer_edge(from_address, to_address, normalized_owner, normalized_router)
            transfers.append({
                "logIndex": _parse_intlike(log.get("logIndex")),
                "from": from_address,
                "to": to_address,
                "amountRaw": amount_raw,
                "amount": _format_18(amount_raw),
                "classification": classification,
            })
            if from_address == "0x0000000000000000000000000000000000000000":
                minted_total_raw += amount_raw
                if to_address == normalized_owner:
                    minted_to_wallet_raw += amount_raw
                if to_address == normalized_router:
                    minted_to_router_raw += amount_raw
            if from_address == normalized_owner:
                wallet_outflow_raw += amount_raw
            if from_address == normalized_router:
                router_outflow_raw += amount_raw
        elif topics[0] == _APPROVAL_TOPIC0 and len(topics) >= 3:
            approval_owner = _topic_address(topics[1])
            approval_spender = _topic_address(topics[2])
            allowance_raw = int(str(log.get("data") or "0x0"), 16)
            approvals.append({
                "logIndex": _parse_intlike(log.get("logIndex")),
                "owner": approval_owner,
                "spender": approval_spender,
                "allowanceRaw": allowance_raw,
                "allowance": _format_18(allowance_raw),
            })

    return {
        "txHash": tx.get("hash") or receipt.get("transactionHash"),
        "status": "ok",
        "to": tx.get("to"),
        "from": tx.get("from"),
        "inputSelector": (tx.get("input") or "")[:10],
        "mintedTotalRaw": minted_total_raw,
        "mintedTotal": _format_18(minted_total_raw),
        "mintedToWalletRaw": minted_to_wallet_raw,
        "mintedToWallet": _format_18(minted_to_wallet_raw),
        "mintedToObservedRouterRaw": minted_to_router_raw,
        "mintedToObservedRouter": _format_18(minted_to_router_raw),
        "sameTxWalletOutflowRaw": wallet_outflow_raw,
        "sameTxWalletOutflow": _format_18(wallet_outflow_raw),
        "sameTxObservedRouterOutflowRaw": router_outflow_raw,
        "sameTxObservedRouterOutflow": _format_18(router_outflow_raw),
        "semanticBucket": _classify_origin_trace_bucket(minted_total_raw, minted_to_wallet_raw, router_outflow_raw, wallet_outflow_raw),
        "transferFlow": transfers,
        "approvalFlow": approvals,
    }


def _summarize_origin_trace(origin_mint: dict[str, Any] | None) -> list[str]:
    if not origin_mint:
        return [
            "No origin tx with an observed bnbUSD mint was found in the provided position-history tx set.",
        ]
    bucket = origin_mint.get("semanticBucket")
    if bucket == "spent-routed-onward":
        return [
            "The earliest observed mint tx minted bnbUSD inside the receipt bundle, but none of that mint landed directly in the owner wallet.",
            "The same tx then forwarded the minted amount onward from the observed Sigma router, so the origin flow is best described as spent/routed onward rather than wallet-held.",
        ]
    if bucket == "wallet-held":
        return [
            "The observed mint tx delivered bnbUSD directly into the owner wallet without a same-tx outflow from the owner or observed router.",
        ]
    if bucket == "wallet-received-then-routed":
        return [
            "The observed mint tx delivered bnbUSD to the owner wallet, but the same tx also routed some of it back out.",
        ]
    if bucket == "no-bnbusd-mint-observed":
        return [
            "This tx did not emit a bnbUSD mint event in the decoded receipt logs.",
        ]
    return [
        "The origin tx needs manual review; the observed bnbUSD flow was not cleanly classifiable from same-tx transfer edges alone.",
    ]


def _classify_origin_trace_bucket(
    minted_total_raw: int,
    minted_to_wallet_raw: int,
    router_outflow_raw: int,
    wallet_outflow_raw: int,
) -> str:
    if minted_total_raw == 0:
        return "no-bnbusd-mint-observed"
    if minted_to_wallet_raw > 0 and wallet_outflow_raw == 0 and router_outflow_raw == 0:
        return "wallet-held"
    if minted_to_wallet_raw == 0 and router_outflow_raw > 0:
        return "spent-routed-onward"
    if minted_to_wallet_raw > 0 and wallet_outflow_raw > 0:
        return "wallet-received-then-routed"
    return "unknown"


def _classify_transfer_edge(from_address: str, to_address: str, owner: str | None, observed_router: str | None) -> str:
    zero = "0x0000000000000000000000000000000000000000"
    if from_address == zero:
        if to_address == owner:
            return "mint-to-wallet"
        if to_address == observed_router:
            return "mint-to-observed-router"
        return "mint-to-other"
    if from_address == owner:
        return "wallet-outflow"
    if to_address == owner:
        return "wallet-inflow"
    if from_address == observed_router:
        return "observed-router-outflow"
    if to_address == observed_router:
        return "observed-router-inflow"
    return "other-transfer"


def _topic_address(topic_hex: str) -> str:
    normalized = topic_hex[2:] if topic_hex.startswith("0x") else topic_hex
    return normalize_address("0x" + normalized[-40:]) or "0x0000000000000000000000000000000000000000"


def _format_redeem_preview(preview: Any) -> dict[str, Any]:
    if not isinstance(preview, dict):
        return {
            "raw": preview,
        }
    amount_yield_out = int(preview.get("amountYieldOut", 0))
    amount_stable_out = int(preview.get("amountStableOut", 0))
    return {
        "amountYieldOutRaw": amount_yield_out,
        "amountYieldOut": _format_18(amount_yield_out),
        "amountStableOutRaw": amount_stable_out,
        "amountStableOut": _format_18(amount_stable_out),
    }


def _format_units(value: int, decimals: int) -> str:
    scaled = Decimal(value) / (Decimal(10) ** Decimal(decimals))
    text = format(scaled, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _unix_timestamp_to_utc(value: int | None) -> str | None:
    if value is None or value <= 0:
        return None
    return datetime.fromtimestamp(value, UTC).isoformat().replace("+00:00", "Z")


def _resolve_pool_list(explicit_pools: list[str] | None) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for candidate in [*(explicit_pools or []), *DISCOVERED_LIVE_POOL_ADDRESSES]:
        normalized = normalize_address(candidate)
        if normalized is None or not normalized.startswith("0x") or len(normalized) != 42:
            continue
        if normalized in seen:
            continue
        ordered.append(normalized)
        seen.add(normalized)
    return ordered


def _function_views() -> dict[str, dict[str, dict[str, Any]]]:
    return _function_views_for({
        "SyPool": {
            "balanceOf",
            "tokenOfOwnerByIndex",
            "getPosition",
            "positionData",
            "positionMetadata",
        },
        "SigmaController": {"positionIdToEntryPrice"},
    })


def _function_views_for(required_functions: dict[str, set[str]]) -> dict[str, dict[str, dict[str, Any]]]:
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for view in user_facing_views():
        docs_name = view["docsName"]
        if docs_name not in required_functions:
            continue
        functions = {
            item["name"]: item
            for item in view["abi"]
            if item.get("type") == "function"
        }
        out[docs_name] = functions
    missing = {
        (group, name)
        for group, names in required_functions.items()
        for name in names
    } - {(group, name) for group, items in out.items() for name in items}
    if missing:
        formatted = ", ".join(f"{group}.{name}" for group, name in sorted(missing))
        raise AccountFetchError(f"Required ABI entries are missing from the cache: {formatted}")
    return out


def _call_view_function(
    rpc_url: str,
    timeout_seconds: float,
    contract_address: str,
    function_abi: dict[str, Any],
    args: list[Any],
) -> Any:
    signature = _signature_from_abi(function_abi)
    calldata = _encode_call(function_abi, args)
    result = _rpc_call(
        rpc_url,
        "eth_call",
        [{"to": contract_address, "data": calldata}, "latest"],
        timeout_seconds=timeout_seconds,
    )
    if not isinstance(result, str) or not result.startswith("0x"):
        raise AccountFetchError(f"eth_call returned a non-hex result for {signature}: {result!r}")
    output_bytes = bytes.fromhex(result[2:]) if len(result) > 2 else b""
    decoded = decode_arguments(function_abi.get("outputs", []), output_bytes)
    return _simplify_decoded_output(decoded)


def _signature_from_abi(function_abi: dict[str, Any]) -> str:
    inputs = function_abi.get("inputs", [])
    return f"{function_abi['name']}({','.join(param['type'] for param in inputs)})"


def _encode_call(function_abi: dict[str, Any], args: list[Any]) -> str:
    inputs = function_abi.get("inputs", [])
    if len(inputs) != len(args):
        raise AccountFetchError(
            f"{function_abi['name']} expected {len(inputs)} argument(s) but got {len(args)}"
        )
    selector = selector_for_signature(_signature_from_abi(function_abi))[2:]
    return "0x" + selector + "".join(_encode_abi_word(param["type"], value) for param, value in zip(inputs, args, strict=False))


def _encode_abi_word(solidity_type: str, value: Any) -> str:
    if solidity_type == "address":
        normalized = normalize_address(str(value))
        if normalized is None or not normalized.startswith("0x") or len(normalized) != 42:
            raise AccountFetchError(f"Invalid address argument: {value!r}")
        return "0" * 24 + normalized[2:]
    if solidity_type == "bool":
        return (1 if bool(value) else 0).to_bytes(32, "big").hex()
    if solidity_type.startswith("uint"):
        integer = int(value)
        if integer < 0:
            raise AccountFetchError(f"Unsigned integer cannot be negative: {value!r}")
        return integer.to_bytes(32, "big").hex()
    if solidity_type.startswith("int"):
        integer = int(value)
        if integer < 0:
            integer = (1 << 256) + integer
        return integer.to_bytes(32, "big").hex()
    if solidity_type == "bytes32":
        raw = str(value)
        if raw.startswith("0x"):
            raw = raw[2:]
        if len(raw) != 64:
            raise AccountFetchError(f"bytes32 argument must be exactly 32 bytes: {value!r}")
        return raw.lower()
    raise AccountFetchError(f"Unsupported ABI input type for account fetch slice: {solidity_type}")


def _simplify_decoded_output(values: list[dict[str, Any]]) -> Any:
    if not values:
        return None
    if len(values) == 1:
        return values[0]["value"]
    names = [item.get("name") or "" for item in values]
    if all(name and name != "(unnamed)" for name in names) and len(set(names)) == len(names):
        return {item["name"]: item["value"] for item in values}
    return values


def _bytes32_hex_to_int(value: str) -> int | None:
    if not isinstance(value, str):
        return None
    raw = value[2:] if value.startswith("0x") else value
    if len(raw) != 64:
        return None
    try:
        return int(raw, 16)
    except ValueError:
        return None


def _fetch_entry_price_no_auth(
    sigma_app_base_url: str,
    pool: str,
    position_id: int,
    owner: str,
    *,
    timeout_seconds: float,
) -> dict[str, Any]:
    response = _sigma_api_get_json(
        sigma_app_base_url,
        "/api/position/getEntryPrice/no-auth",
        {
            "pool": pool,
            "positionId": str(position_id),
            "owner": owner,
        },
        timeout_seconds=timeout_seconds,
        referer_path="/mintv2",
    )
    data = response.get("data")
    return {
        "request": {
            "pool": pool,
            "positionId": position_id,
            "owner": owner,
        },
        "response": {
            "code": response.get("code"),
            "success": response.get("success"),
            "data": data,
            "timestamp": response.get("timestamp"),
        },
    }


def _fetch_long_short_list_no_auth(
    sigma_app_base_url: str,
    pool: str,
    position_id: int,
    owner: str,
    *,
    timeout_seconds: float,
    limit: int,
) -> dict[str, Any]:
    response = _sigma_api_get_json(
        sigma_app_base_url,
        "/api/user-event/long-short-list/no-auth",
        {
            "offset": "0",
            "limit": str(limit),
            "position": str(position_id),
            "pool": pool,
            "owner": owner,
        },
        timeout_seconds=timeout_seconds,
        referer_path="/mintv2",
    )
    items, count = _extract_history_payload(response)
    return {
        "request": {
            "pool": pool,
            "position": position_id,
            "owner": owner,
            "offset": 0,
            "limit": limit,
        },
        "response": {
            "code": response.get("code"),
            "success": response.get("success"),
            "items": items,
            "count": count,
            "timestamp": response.get("timestamp"),
        },
    }


def _extract_history_payload(response: dict[str, Any]) -> tuple[list[Any], int | None]:
    if isinstance(response.get("items"), list):
        return response["items"], _parse_intlike(response.get("count"))

    payload = response.get("data")
    if isinstance(payload, list):
        if len(payload) == 2 and isinstance(payload[0], list):
            return payload[0], _parse_intlike(payload[1])
        if all(isinstance(item, dict) for item in payload):
            return payload, len(payload)
    return [], None


def _sigma_api_get_json(
    sigma_app_base_url: str,
    path: str,
    params: dict[str, str],
    *,
    timeout_seconds: float,
    referer_path: str,
) -> dict[str, Any]:
    base = sigma_app_base_url.rstrip("/") + "/"
    request_url = urljoin(base, path.lstrip("/"))
    if params:
        request_url += "?" + urlencode(params)
    headers = dict(_BROWSERISH_HEADERS)
    headers["Referer"] = urljoin(base, referer_path.lstrip("/"))
    headers["Origin"] = base.rstrip("/")
    request = Request(request_url, headers=headers)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise AccountFetchError(f"Sigma app API HTTP error {exc.code}: {detail}") from exc
    except URLError as exc:
        raise AccountFetchError(f"Sigma app API connectivity error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AccountFetchError(f"Sigma app API returned non-JSON content for {request_url}") from exc


def _rpc_call(rpc_url: str, method: str, params: list[Any], *, timeout_seconds: float) -> Any:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    request = Request(
        rpc_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise AccountFetchError(f"RPC HTTP error for {method}: {exc.code} {detail}") from exc
    except URLError as exc:
        raise AccountFetchError(f"RPC connectivity error for {method}: {exc}") from exc

    if "error" in body:
        raise AccountFetchError(f"RPC error for {method}: {body['error']}")
    return body.get("result")


def _format_percent_from_wad(wad_value: int) -> str:
    ratio = Decimal(wad_value) / Decimal(10**18)
    return format(ratio * Decimal(100), ".4f").rstrip("0").rstrip(".")


def _parse_ratio_input(value: str) -> Decimal:
    stripped = value.strip()
    if not stripped:
        raise AccountFetchError("target_ltv cannot be empty")
    try:
        parsed = Decimal(stripped.rstrip("%"))
    except Exception as exc:  # noqa: BLE001
        raise AccountFetchError(f"Invalid target_ltv value: {value!r}") from exc
    if stripped.endswith("%") or parsed > 1:
        parsed = parsed / Decimal(100)
    if parsed <= 0 or parsed >= 1:
        raise AccountFetchError("target_ltv must resolve to a ratio between 0 and 1 (exclusive)")
    return parsed


def _build_partial_mint_close_preview(
    *,
    repay_amount: str | None,
    withdraw_amount: str | None,
    target_ltv: str | None,
    raw_debt: int,
    raw_coll: int,
    debt_ratio_wad: int,
    wallet_balance_raw: int,
    current_allowance_raw: int,
    approval_policy: Any,
) -> dict[str, Any]:
    current_ltv_ratio = Decimal(debt_ratio_wad) / Decimal(10**18) if debt_ratio_wad > 0 else Decimal(0)
    preview: dict[str, Any] = {
        "supportsPartialRepay": True,
        "supportsPartialClose": True,
        "mathModel": {
            "name": "constant-price target-ltv bound",
            "fullyContractValidated": False,
            "validationNote": "Uses current onchain debt ratio / LTV as the default guardrail. Final close-path rounding, min-debt floors, and contract-specific constraints are not fully proven.",
        },
        "currentPosition": {
            "rawDebt": raw_debt,
            "rawDebtFormatted": _format_18(raw_debt),
            "rawCollateral": raw_coll,
            "rawCollateralFormatted": _format_18(raw_coll),
            "currentLtvRatio": format(current_ltv_ratio, "f"),
            "currentLtvPercent": _format_percent_from_wad(debt_ratio_wad) if debt_ratio_wad > 0 else None,
        },
        "approvalPolicy": approval_policy_to_dict(approval_policy),
        "notes": [
            "Repay amount and withdraw amount are modeled against the current debt ratio / LTV, which matches the currently observed UI LTV order of magnitude.",
            "If you omit --target-ltv, the preview preserves the current onchain LTV as the guardrail for max withdraw calculations.",
            "Health / rebalancing thresholds still govern the real route, but the exact contract-enforced close preview is not yet captured here.",
        ],
    }
    if repay_amount is None or not repay_amount.strip():
        preview["status"] = "available-without-scenario"
        preview["notes"].append("Pass --repay-amount to model a partial close scenario.")
        return preview

    try:
        repay_raw = parse_token_amount_to_raw(repay_amount, decimals=18)
    except ValueError as exc:
        raise AccountFetchError(str(exc)) from exc
    if repay_raw > raw_debt:
        raise AccountFetchError("repay_amount cannot exceed the current raw debt")

    target_ltv_ratio = _parse_ratio_input(target_ltv) if target_ltv else current_ltv_ratio
    if target_ltv_ratio <= 0:
        raise AccountFetchError("current debt ratio is zero; partial close preview requires a positive LTV baseline")

    collateral_raw_decimal = Decimal(raw_coll)
    debt_raw_decimal = Decimal(raw_debt)
    current_collateral_value_raw = debt_raw_decimal / current_ltv_ratio if current_ltv_ratio > 0 else Decimal(0)
    price_raw_per_coll = current_collateral_value_raw / collateral_raw_decimal if collateral_raw_decimal > 0 else Decimal(0)
    remaining_debt_raw = raw_debt - repay_raw
    remaining_debt_raw_decimal = Decimal(remaining_debt_raw)
    min_remaining_collateral_value_raw = Decimal(0)
    if remaining_debt_raw > 0 and target_ltv_ratio > 0:
        min_remaining_collateral_value_raw = remaining_debt_raw_decimal / target_ltv_ratio
    max_withdrawable_value_raw = max(current_collateral_value_raw - min_remaining_collateral_value_raw, Decimal(0))
    if price_raw_per_coll > 0:
        max_withdrawable_coll_raw_decimal = max_withdrawable_value_raw / price_raw_per_coll
    else:
        max_withdrawable_coll_raw_decimal = Decimal(0)
    max_withdrawable_coll_raw = int(min(max_withdrawable_coll_raw_decimal, collateral_raw_decimal).to_integral_value())

    desired_allowance_raw = approval_policy_desired_allowance_raw(
        approval_policy,
        requested_amount=repay_amount,
        decimals=18,
    )
    desired_allowance = None
    if desired_allowance_raw is not None:
        desired_allowance = "max-uint256" if desired_allowance_raw == MAX_UINT256 else format_token_amount_from_raw(desired_allowance_raw, decimals=18)

    scenario: dict[str, Any] = {
        "status": "scenario-modeled",
        "requestedRepayAmountRaw": repay_raw,
        "requestedRepayAmount": _format_18(repay_raw),
        "remainingDebtRaw": remaining_debt_raw,
        "remainingDebt": _format_18(remaining_debt_raw),
        "targetLtvRatio": format(target_ltv_ratio, "f"),
        "targetLtvPercent": format(target_ltv_ratio * Decimal(100), ".4f").rstrip("0").rstrip("."),
        "maxWithdrawableCollateralRaw": max_withdrawable_coll_raw,
        "maxWithdrawableCollateral": _format_18(max_withdrawable_coll_raw),
        "maxWithdrawableCollateralModeledAt": "target-ltv-bound",
        "resultingLtvIfWithdrawingMax": format(target_ltv_ratio, "f"),
        "resultingLtvIfWithdrawingMaxPercent": format(target_ltv_ratio * Decimal(100), ".4f").rstrip("0").rstrip("."),
        "walletHasRequestedRepayNow": wallet_balance_raw >= repay_raw,
        "allowanceAlreadyCoversRequestedRepay": current_allowance_raw >= repay_raw,
        "approval": {
            "policy": approval_policy_to_dict(approval_policy),
            "desiredAllowanceRaw": str(desired_allowance_raw) if desired_allowance_raw is not None else None,
            "desiredAllowance": desired_allowance,
            "currentAllowanceRaw": current_allowance_raw,
            "currentAllowance": _format_18(current_allowance_raw),
            "currentAllowanceSatisfiesPolicy": (current_allowance_raw >= desired_allowance_raw) if desired_allowance_raw not in (None, MAX_UINT256) else (current_allowance_raw == MAX_UINT256 if desired_allowance_raw == MAX_UINT256 else None),
            "finitePolicyWritePathProven": False,
            "writePathEvidenceNote": "Live 2026-03-16 close flow still surfaced a max approval request in Rabby despite Sigma Unlimited Approval being visually OFF.",
        },
    }

    if withdraw_amount is not None and withdraw_amount.strip():
        try:
            requested_withdraw_raw = parse_token_amount_to_raw(withdraw_amount, decimals=18)
        except ValueError as exc:
            raise AccountFetchError(str(exc)) from exc
        if requested_withdraw_raw > raw_coll:
            raise AccountFetchError("withdraw_amount cannot exceed the current collateral")
        remaining_coll_raw = raw_coll - requested_withdraw_raw
        resulting_ltv_ratio = None
        if remaining_coll_raw > 0 and price_raw_per_coll > 0 and remaining_debt_raw >= 0:
            remaining_collateral_value_raw = Decimal(remaining_coll_raw) * price_raw_per_coll
            if remaining_collateral_value_raw > 0:
                resulting_ltv_ratio = remaining_debt_raw_decimal / remaining_collateral_value_raw
        scenario["requestedWithdrawAmountRaw"] = requested_withdraw_raw
        scenario["requestedWithdrawAmount"] = _format_18(requested_withdraw_raw)
        scenario["requestedWithdrawWithinModeledMax"] = requested_withdraw_raw <= max_withdrawable_coll_raw
        scenario["resultingLtvAfterRequestedWithdraw"] = format(resulting_ltv_ratio, "f") if resulting_ltv_ratio is not None else None
        scenario["resultingLtvAfterRequestedWithdrawPercent"] = (
            format(resulting_ltv_ratio * Decimal(100), ".4f").rstrip("0").rstrip(".")
            if resulting_ltv_ratio is not None
            else None
        )

    preview["scenario"] = scenario
    return preview


def _format_18(value: int) -> str:
    scaled = Decimal(value) / Decimal(10**18)
    text = format(scaled, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _parse_intlike(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            if stripped.startswith(("0x", "0X")):
                return int(stripped, 16)
            return int(stripped)
        except ValueError:
            return None
    return None
