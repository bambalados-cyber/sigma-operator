from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .abi import decode_calldata, inspect_contract, manifest_summary, route_operations
from .account import (
    AccountFetchError,
    fetch_account_history,
    fetch_account_positions,
    fetch_account_status,
    fetch_bnbusd_trace,
    fetch_mint_close_readiness,
    fetch_stability_pool_status,
)
from .capture import capture_browser_helper, capture_docs, capture_import, capture_start
from .config import (
    approval_policy_to_dict,
    ensure_paths,
    get_settings,
    initialize_operator_config,
    load_operator_config,
    normalize_approval_policy,
    save_operator_config,
)
from .decode import batch_decode_path, decode_json_file
from .fetch import FetchError, fetch_decode_by_hash
from .governance import GovernanceError, governance_overview, governance_read_action
from .plan import build_plan
from .skill_bridge import run_skill_python, script_path


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _read_raw_input_argument(value: str) -> tuple[str, str | None]:
    candidate = Path(value).expanduser()
    if candidate.exists() and candidate.is_file():
        raw_text = candidate.read_text(encoding="utf-8").strip()
        return raw_text, None
    return value, None


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
            continue
        return value
    return None


def _resolve_rpc_override(args: argparse.Namespace) -> str | None:
    return _first_nonempty(
        getattr(args, "bnb_rpc_url", None),
        getattr(args, "bsc_rpc_url", None),
        getattr(args, "meganode_rpc_url", None),
        getattr(args, "nodereal_rpc_url", None),
        getattr(args, "rpc_url", None),
    )


def _resolve_explorer_api_url(args: argparse.Namespace) -> str | None:
    return _first_nonempty(
        getattr(args, "bsctrace_api_url", None),
        getattr(args, "explorer_api_url", None),
    )


def _resolve_explorer_api_key(args: argparse.Namespace) -> str | None:
    return _first_nonempty(
        getattr(args, "bsctrace_api_key", None),
        getattr(args, "explorer_api_key", None),
    )


def _resolve_explorer_chain_id(args: argparse.Namespace) -> int | None:
    return _first_nonempty(
        getattr(args, "bsctrace_chain_id", None),
        getattr(args, "explorer_chain_id", None),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sigma",
        description="MegaNode/NodeReal-first Sigma.Money operator CLI for BNB Chain / BSC capture, decode, plan, and ABI inspection.",
        epilog=(
            "Sigma runs on BNB Chain / BSC. The canonical live fetch path is read-only BNB RPC "
            "(MegaNode / NodeReal compatible); explorer fetch remains secondary and optional."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture", help="capture session helpers")
    capture_sub = capture.add_subparsers(dest="capture_command", required=True)
    capture_docs_parser = capture_sub.add_parser("docs", help="show capture guidance")
    capture_docs_parser.set_defaults(func=cmd_capture_docs)
    capture_start_parser = capture_sub.add_parser("start", help="create a new capture workspace")
    capture_start_parser.add_argument("label", help="human-readable label for this capture session")
    capture_start_parser.add_argument("--target", action="append", default=[], help="known Sigma docsName target(s), e.g. PoolManager")
    capture_start_parser.set_defaults(func=cmd_capture_start)
    capture_browser_helper_parser = capture_sub.add_parser(
        "browser-helper",
        help="write a browser-side fetch/XHR capture helper into a capture session",
    )
    capture_browser_helper_parser.add_argument("session", help="capture session path or directory name under captures/")
    capture_browser_helper_parser.add_argument("--print", dest="print_snippet", action="store_true", help="include the generated JS snippet in stdout JSON")
    capture_browser_helper_parser.set_defaults(func=cmd_capture_browser_helper)

    capture_import_parser = capture_sub.add_parser(
        "import",
        help="import HAR/devtools exports into a capture session as normalized decode-ready artifacts",
    )
    capture_import_parser.add_argument("session", help="capture session path or directory name under captures/")
    capture_import_parser.add_argument("artifact", help="HAR or JSON export to import")
    capture_import_parser.add_argument("--prefix", help="optional filename prefix for normalized imports")
    capture_import_parser.set_defaults(func=cmd_capture_import)

    decode = subparsers.add_parser(
        "decode",
        help="decode calldata, tx JSON, tx hashes, or capture folders using the Sigma ABI cache",
    )
    decode.add_argument("input", nargs="?", help="raw 0x calldata, a JSON/text file, or a capture/raw directory")
    decode.add_argument("--tx-json", help="transaction/request JSON file to ingest")
    decode.add_argument("--capture-dir", help="capture session directory or raw JSON directory to batch decode")
    decode.add_argument("--tx-hash", help="transaction hash to fetch from a read-only BNB Chain source and decode")
    decode.add_argument(
        "--fetch-source",
        choices=["rpc", "explorer"],
        default="rpc",
        help="live source for --tx-hash (rpc is the canonical MegaNode/NodeReal path; explorer is secondary/optional)",
    )
    decode.add_argument(
        "--bnb-rpc-url",
        help="preferred read-only BNB Chain RPC URL for --tx-hash --fetch-source rpc",
    )
    decode.add_argument(
        "--bsc-rpc-url",
        help="alias of --bnb-rpc-url using BSC naming",
    )
    decode.add_argument(
        "--meganode-rpc-url",
        help="alias of --bnb-rpc-url for MegaNode / NodeReal endpoints",
    )
    decode.add_argument(
        "--nodereal-rpc-url",
        help="alias of --bnb-rpc-url for NodeReal dashboard endpoints",
    )
    decode.add_argument(
        "--rpc-url",
        help="legacy alias of --bnb-rpc-url",
    )
    decode.add_argument(
        "--bsctrace-api-url",
        help="optional BSCTrace-compatible explorer API base URL for --fetch-source explorer",
    )
    decode.add_argument(
        "--bsctrace-api-key",
        help="optional BSCTrace-compatible explorer API key for --fetch-source explorer",
    )
    decode.add_argument(
        "--bsctrace-chain-id",
        type=int,
        help="optional explorer chain id override (defaults to 56 for BNB Chain / BSC)",
    )
    decode.add_argument("--explorer-api-url", help="legacy alias of --bsctrace-api-url")
    decode.add_argument("--explorer-api-key", help="legacy alias of --bsctrace-api-key")
    decode.add_argument("--explorer-chain-id", type=int, help="legacy alias of --bsctrace-chain-id")
    decode.add_argument("--save-fetch-json", help="optional path to save the fetched tx+receipt bundle before decode")
    decode.add_argument(
        "--route-operation",
        action="append",
        choices=route_operations(),
        default=[],
        help="compare decoded tx evidence against a named Sigma operation (repeatable), including archived mint and disambiguated redeem variants",
    )
    decode.add_argument("--to", dest="target_address", help="target contract address to narrow ABI matching")
    decode.set_defaults(func=cmd_decode)

    account = subparsers.add_parser(
        "account",
        help="read-only owner/portfolio views from live Sigma pool reads plus current-app no-auth helpers",
    )
    account_sub = account.add_subparsers(dest="account_command", required=True)

    account_status = account_sub.add_parser(
        "status",
        help="enumerate owner positions across the discovered live pool set",
    )
    account_status.add_argument("--owner", required=True, help="owner wallet address to inspect")
    account_status.add_argument(
        "--pool",
        action="append",
        default=[],
        help="explicit pool address to query (repeatable); default frontier pools are still included",
    )
    account_status.add_argument(
        "--bnb-rpc-url",
        help="preferred read-only BNB Chain RPC URL for eth_call reads",
    )
    account_status.add_argument("--bsc-rpc-url", help="alias of --bnb-rpc-url using BSC naming")
    account_status.add_argument("--meganode-rpc-url", help="alias of --bnb-rpc-url for MegaNode endpoints")
    account_status.add_argument("--nodereal-rpc-url", help="alias of --bnb-rpc-url for NodeReal endpoints")
    account_status.add_argument("--rpc-url", help="legacy alias of --bnb-rpc-url")
    account_status.add_argument(
        "--sigma-app-base-url",
        default="https://sigma.money",
        help="Sigma app base URL for no-auth helper enrichment (default: https://sigma.money)",
    )
    account_status.add_argument(
        "--include-history",
        action="store_true",
        help="enrich each discovered position with /api/user-event/long-short-list/no-auth history",
    )
    account_status.add_argument(
        "--history-limit",
        type=int,
        default=20,
        help="max no-auth history rows per position when --include-history is used",
    )
    account_status.add_argument(
        "--exclude-empty-pools",
        action="store_true",
        help="omit pools with zero current positions from the output",
    )
    account_status.add_argument(
        "--include-controller-entry-price",
        action="store_true",
        help="also try SigmaController.positionIdToEntryPrice(pool, positionId) as an experimental hint",
    )
    account_status.add_argument(
        "--controller-address",
        help="override SigmaController address for the experimental entry-price hint",
    )
    account_status.set_defaults(func=cmd_account_status)

    account_positions = account_sub.add_parser(
        "positions",
        help="flatten current discovered positions into a direct portfolio list",
    )
    account_positions.add_argument("--owner", required=True, help="owner wallet address to inspect")
    account_positions.add_argument(
        "--pool",
        action="append",
        default=[],
        help="explicit pool address to query (repeatable); default frontier pools are still included",
    )
    account_positions.add_argument("--bnb-rpc-url", help="preferred read-only BNB Chain RPC URL for eth_call reads")
    account_positions.add_argument("--bsc-rpc-url", help="alias of --bnb-rpc-url using BSC naming")
    account_positions.add_argument("--meganode-rpc-url", help="alias of --bnb-rpc-url for MegaNode endpoints")
    account_positions.add_argument("--nodereal-rpc-url", help="alias of --bnb-rpc-url for NodeReal endpoints")
    account_positions.add_argument("--rpc-url", help="legacy alias of --bnb-rpc-url")
    account_positions.add_argument(
        "--sigma-app-base-url",
        default="https://sigma.money",
        help="Sigma app base URL for no-auth helper enrichment (default: https://sigma.money)",
    )
    account_positions.add_argument(
        "--include-controller-entry-price",
        action="store_true",
        help="also try SigmaController.positionIdToEntryPrice(pool, positionId) as an experimental hint",
    )
    account_positions.add_argument(
        "--controller-address",
        help="override SigmaController address for the experimental entry-price hint",
    )
    account_positions.set_defaults(func=cmd_account_positions)

    account_history = account_sub.add_parser(
        "history",
        help="flatten Sigma no-auth position history across the discovered live pool set",
    )
    account_history.add_argument("--owner", required=True, help="owner wallet address to inspect")
    account_history.add_argument(
        "--pool",
        action="append",
        default=[],
        help="explicit pool address to query (repeatable); default frontier pools are still included",
    )
    account_history.add_argument("--bnb-rpc-url", help="preferred read-only BNB Chain RPC URL for eth_call reads")
    account_history.add_argument("--bsc-rpc-url", help="alias of --bnb-rpc-url using BSC naming")
    account_history.add_argument("--meganode-rpc-url", help="alias of --bnb-rpc-url for MegaNode endpoints")
    account_history.add_argument("--nodereal-rpc-url", help="alias of --bnb-rpc-url for NodeReal endpoints")
    account_history.add_argument("--rpc-url", help="legacy alias of --bnb-rpc-url")
    account_history.add_argument(
        "--sigma-app-base-url",
        default="https://sigma.money",
        help="Sigma app base URL for no-auth helper enrichment (default: https://sigma.money)",
    )
    account_history.add_argument(
        "--history-limit",
        type=int,
        default=20,
        help="max no-auth history rows per position",
    )
    account_history.add_argument(
        "--position-id",
        type=int,
        help="optional position id filter after pool discovery",
    )
    account_history.set_defaults(func=cmd_account_history)

    account_mint_close = account_sub.add_parser(
        "mint-close-readiness",
        help="read-only check for whether the wallet currently has the repay asset and approvals needed for the observed mint close path",
    )
    account_mint_close.add_argument("--owner", required=True, help="owner wallet address to inspect")
    account_mint_close.add_argument("--position-id", required=True, type=int, help="position NFT id to inspect")
    account_mint_close.add_argument("--pool", required=True, help="pool address for the position")
    account_mint_close.add_argument(
        "--bnb-rpc-url",
        help="preferred read-only BNB Chain RPC URL for eth_call reads",
    )
    account_mint_close.add_argument("--bsc-rpc-url", help="alias of --bnb-rpc-url using BSC naming")
    account_mint_close.add_argument("--meganode-rpc-url", help="alias of --bnb-rpc-url for MegaNode endpoints")
    account_mint_close.add_argument("--nodereal-rpc-url", help="alias of --bnb-rpc-url for NodeReal endpoints")
    account_mint_close.add_argument("--rpc-url", help="legacy alias of --bnb-rpc-url")
    account_mint_close.add_argument(
        "--bnbusd-address",
        help="override bnbUSD token address (defaults to the docs-published BNBUSD proxy)",
    )
    account_mint_close.add_argument(
        "--router-address",
        help="override the observed live write-target router address",
    )
    account_mint_close.add_argument(
        "--repay-amount",
        help="optional bnbUSD repay amount to model for partial mint close preview",
    )
    account_mint_close.add_argument(
        "--target-ltv",
        help="optional resulting LTV ratio or percent ceiling for partial close preview (defaults to current onchain LTV)",
    )
    account_mint_close.add_argument(
        "--withdraw-amount",
        help="optional collateral amount to test against the modeled post-repay LTV",
    )
    account_mint_close.add_argument(
        "--approval-policy",
        choices=["unlimited", "exact", "custom"],
        help="override the persisted approval policy for this readiness/preview call",
    )
    account_mint_close.add_argument(
        "--approval-amount",
        help="custom finite approval amount in token units when --approval-policy custom is used",
    )
    account_mint_close.set_defaults(func=cmd_account_mint_close_readiness)

    account_stability_pools = account_sub.add_parser(
        "stability-pools",
        help="read live Sigma stability-pool share balances plus delayed-redeem state directly from chain",
    )
    account_stability_pools.add_argument("--owner", required=True, help="owner wallet address to inspect")
    account_stability_pools.add_argument(
        "--pool",
        action="append",
        default=[],
        help="explicit stability-pool address to query (repeatable); current discovered pools are used by default",
    )
    account_stability_pools.add_argument(
        "--bnb-rpc-url",
        help="preferred read-only BNB Chain RPC URL for eth_call reads",
    )
    account_stability_pools.add_argument("--bsc-rpc-url", help="alias of --bnb-rpc-url using BSC naming")
    account_stability_pools.add_argument("--meganode-rpc-url", help="alias of --bnb-rpc-url for MegaNode endpoints")
    account_stability_pools.add_argument("--nodereal-rpc-url", help="alias of --bnb-rpc-url for NodeReal endpoints")
    account_stability_pools.add_argument("--rpc-url", help="legacy alias of --bnb-rpc-url")
    account_stability_pools.add_argument(
        "--bnbusd-address",
        help="override bnbUSD token address when classifying pool previews",
    )
    account_stability_pools.set_defaults(func=cmd_account_stability_pools)

    account_bnbusd_trace = account_sub.add_parser(
        "bnbusd-trace",
        help="trace observed mint-origin bnbUSD flow and classify current repay-source buckets",
    )
    account_bnbusd_trace.add_argument("--owner", required=True, help="owner wallet address to inspect")
    account_bnbusd_trace.add_argument("--position-id", required=True, type=int, help="position NFT id to inspect")
    account_bnbusd_trace.add_argument("--pool", required=True, help="pool address for the position")
    account_bnbusd_trace.add_argument(
        "--tx-hash",
        action="append",
        default=[],
        help="explicit tx hash to analyze (repeatable); otherwise uses tx hashes discovered from position history",
    )
    account_bnbusd_trace.add_argument(
        "--stability-pool",
        action="append",
        default=[],
        help="explicit stability-pool address to include in current repay-source classification (repeatable)",
    )
    account_bnbusd_trace.add_argument(
        "--history-limit",
        type=int,
        default=20,
        help="max no-auth history rows to inspect when discovering position tx hashes",
    )
    account_bnbusd_trace.add_argument(
        "--bnb-rpc-url",
        help="preferred read-only BNB Chain RPC URL for eth_call / tx receipt reads",
    )
    account_bnbusd_trace.add_argument("--bsc-rpc-url", help="alias of --bnb-rpc-url using BSC naming")
    account_bnbusd_trace.add_argument("--meganode-rpc-url", help="alias of --bnb-rpc-url for MegaNode endpoints")
    account_bnbusd_trace.add_argument("--nodereal-rpc-url", help="alias of --bnb-rpc-url for NodeReal endpoints")
    account_bnbusd_trace.add_argument("--rpc-url", help="legacy alias of --bnb-rpc-url")
    account_bnbusd_trace.add_argument(
        "--sigma-app-base-url",
        default="https://sigma.money",
        help="Sigma app base URL for no-auth history discovery (default: https://sigma.money)",
    )
    account_bnbusd_trace.add_argument(
        "--bnbusd-address",
        help="override bnbUSD token address (defaults to the docs-published BNBUSD proxy)",
    )
    account_bnbusd_trace.add_argument(
        "--router-address",
        help="override the observed live write-target router address",
    )
    account_bnbusd_trace.set_defaults(func=cmd_account_bnbusd_trace)

    config = subparsers.add_parser(
        "config",
        help="persist and inspect operator-side CLI preferences such as approval policy",
    )
    config_sub = config.add_subparsers(dest="config_command", required=True)

    config_show = config_sub.add_parser("show", help="show the resolved operator config and approval policy")
    config_show.set_defaults(func=cmd_config_show)

    config_init = config_sub.add_parser(
        "init",
        help="write a fresh persisted operator config (defaults to exact approval policy)",
    )
    config_init.add_argument(
        "--approval-policy",
        choices=["unlimited", "exact", "custom"],
        default="exact",
        help="approval policy to persist during init",
    )
    config_init.add_argument(
        "--approval-amount",
        help="custom finite approval amount in token units when --approval-policy custom is used",
    )
    config_init.set_defaults(func=cmd_config_init)

    config_set_approval = config_sub.add_parser(
        "set-approval-policy",
        help="update the persisted approval policy without rewriting the rest of the config",
    )
    config_set_approval.add_argument(
        "--approval-policy",
        choices=["unlimited", "exact", "custom"],
        required=True,
        help="approval policy to persist",
    )
    config_set_approval.add_argument(
        "--approval-amount",
        help="custom finite approval amount in token units when --approval-policy custom is used",
    )
    config_set_approval.set_defaults(func=cmd_config_set_approval_policy)

    governance = subparsers.add_parser(
        "governance",
        help="CLI umbrella for the route-specific xsigma / vote / incentivize surfaces",
    )
    governance_sub = governance.add_subparsers(dest="governance_command", required=True)

    governance_overview_parser = governance_sub.add_parser(
        "overview",
        help="show the governance namespace map and route-truth notes",
    )
    governance_overview_parser.set_defaults(func=cmd_governance_overview)

    governance_area = governance_sub.add_parser(
        "xsigma",
        help="xSIGMA governance scaffold commands",
    )
    governance_area_sub = governance_area.add_subparsers(dest="governance_area_command", required=True)
    governance_xsigma_overview = governance_area_sub.add_parser("overview", help="show xSIGMA route truth")
    governance_xsigma_overview.set_defaults(func=cmd_governance_area_read)
    governance_xsigma_position = governance_area_sub.add_parser("position", help="owner-scoped xSIGMA position scaffold")
    governance_xsigma_position.add_argument("--owner", required=True)
    governance_xsigma_position.set_defaults(func=cmd_governance_area_read)
    governance_xsigma_claimable = governance_area_sub.add_parser("claimable", help="owner-scoped xSIGMA claimable scaffold")
    governance_xsigma_claimable.add_argument("--owner", required=True)
    governance_xsigma_claimable.set_defaults(func=cmd_governance_area_read)
    governance_xsigma_preview = governance_area_sub.add_parser("convert-preview", help="amount-scoped xSIGMA convert-preview scaffold")
    governance_xsigma_preview.add_argument("--amount", required=True)
    governance_xsigma_preview.set_defaults(func=cmd_governance_area_read)
    governance_area.set_defaults(governance_area="xsigma")

    governance_area = governance_sub.add_parser(
        "vote",
        help="vote governance scaffold commands",
    )
    governance_area_sub = governance_area.add_subparsers(dest="governance_area_command", required=True)
    governance_vote_gauges = governance_area_sub.add_parser("gauges", help="show vote gauge scaffold")
    governance_vote_gauges.set_defaults(func=cmd_governance_area_read)
    governance_vote_epoch = governance_area_sub.add_parser("epoch", help="show vote epoch scaffold")
    governance_vote_epoch.set_defaults(func=cmd_governance_area_read)
    governance_vote_allocations = governance_area_sub.add_parser("allocations", help="owner-scoped vote allocations scaffold")
    governance_vote_allocations.add_argument("--owner", required=True)
    governance_vote_allocations.set_defaults(func=cmd_governance_area_read)
    governance_vote_preview = governance_area_sub.add_parser("preview", help="owner-scoped vote preview scaffold")
    governance_vote_preview.add_argument("--owner", required=True)
    governance_vote_preview.set_defaults(func=cmd_governance_area_read)
    governance_area.set_defaults(governance_area="vote")

    governance_area = governance_sub.add_parser(
        "incentivize",
        help="incentivize governance scaffold commands",
    )
    governance_area_sub = governance_area.add_subparsers(dest="governance_area_command", required=True)
    governance_incentivize_gauges = governance_area_sub.add_parser("gauges", help="show incentivize gauge scaffold")
    governance_incentivize_gauges.set_defaults(func=cmd_governance_area_read)
    governance_incentivize_campaigns = governance_area_sub.add_parser("campaigns", help="show incentivize campaign scaffold")
    governance_incentivize_campaigns.set_defaults(func=cmd_governance_area_read)
    governance_incentivize_positions = governance_area_sub.add_parser("positions", help="owner-scoped incentivize positions scaffold")
    governance_incentivize_positions.add_argument("--owner", required=True)
    governance_incentivize_positions.set_defaults(func=cmd_governance_area_read)
    governance_incentivize_preview = governance_area_sub.add_parser("preview", help="owner-scoped incentivize preview scaffold")
    governance_incentivize_preview.add_argument("--owner", required=True)
    governance_incentivize_preview.set_defaults(func=cmd_governance_area_read)
    governance_area.set_defaults(governance_area="incentivize")

    plan = subparsers.add_parser(
        "plan",
        help="build a plan-only action payload",
        description=(
            "Build a plan-only Sigma operation payload.\n"
            "Current operations include current trade/earn flows, archived mint flows,\n"
            "and docs-described bnbUSD redemption labeling."
        ),
        epilog=(
            "Examples:\n"
            "  sigma plan open-long --asset BNB --amount 1 --leverage 3\n"
            "  sigma plan stability-pool-redeem-instant --amount 250\n"
            "  sigma plan mint-open --asset BNB --amount 1\n"
            "  sigma plan bnbusd-redeem --amount 250"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    plan.add_argument("operation", choices=route_operations(), help="named Sigma operation to model")
    plan.add_argument("args", nargs=argparse.REMAINDER, help="arguments forwarded to the operator preflight planner")
    plan.set_defaults(func=cmd_plan)

    abi = subparsers.add_parser("abi", help="inspect or refresh Sigma ABI cache")
    abi_sub = abi.add_subparsers(dest="abi_command", required=True)

    abi_inspect = abi_sub.add_parser("inspect", help="inspect cached ABI metadata")
    abi_inspect.add_argument("query", nargs="?", help="docsName or contract address; omit for summary")
    abi_inspect.add_argument("--summary", action="store_true", help="force manifest summary output")
    abi_inspect.set_defaults(func=cmd_abi_inspect)

    abi_refresh = abi_sub.add_parser("refresh", help="refresh ABI cache through the upstream Sigma skill helper")
    abi_refresh.add_argument("--ws-url", help="browser websocket URL from an open BscScan page")
    abi_refresh.add_argument("--output-dir", help="optional override for ABI cache output directory")
    abi_refresh.add_argument("--summary", action="store_true", help="ask upstream helper to print summary JSON")
    abi_refresh.add_argument("--dry-run", action="store_true", help="show what would run without requiring a ws-url")
    abi_refresh.set_defaults(func=cmd_abi_refresh)

    return parser


def cmd_capture_docs(args: argparse.Namespace) -> int:
    print_json(capture_docs())
    return 0


def cmd_capture_start(args: argparse.Namespace) -> int:
    print_json(capture_start(args.label, args.target))
    return 0


def cmd_capture_browser_helper(args: argparse.Namespace) -> int:
    print_json(capture_browser_helper(args.session, print_snippet=args.print_snippet))
    return 0


def cmd_capture_import(args: argparse.Namespace) -> int:
    print_json(capture_import(args.session, args.artifact, prefix=args.prefix))
    return 0


def cmd_decode(args: argparse.Namespace) -> int:
    chosen = [value for value in (args.input, args.tx_json, args.capture_dir, args.tx_hash) if value]
    if not chosen:
        raise SystemExit("decode requires raw calldata, --tx-json, --capture-dir, or --tx-hash")
    if len(chosen) > 1:
        raise SystemExit("Use exactly one of raw calldata/input path, --tx-json, --capture-dir, or --tx-hash")

    if args.tx_hash:
        try:
            payload = fetch_decode_by_hash(
                args.tx_hash,
                rpc_url=_resolve_rpc_override(args),
                target_address=args.target_address,
                save_json=args.save_fetch_json,
                fetch_source=args.fetch_source,
                explorer_api_url=_resolve_explorer_api_url(args),
                explorer_api_key=_resolve_explorer_api_key(args),
                explorer_chain_id=_resolve_explorer_chain_id(args),
                route_operations=args.route_operation,
            )
        except FetchError as exc:
            raise SystemExit(str(exc)) from exc
        print_json(payload)
        return 0

    candidate = Path(args.capture_dir or args.tx_json or args.input).expanduser() if chosen else None
    if args.capture_dir or (candidate and candidate.exists() and candidate.is_dir()):
        payload = batch_decode_path(candidate, target_address=args.target_address, route_operations=args.route_operation)
        print_json(payload)
        return 0

    if args.tx_json or (candidate and candidate.exists() and candidate.is_file() and candidate.suffix.lower() == ".json"):
        payload = decode_json_file(candidate, target_address=args.target_address, route_operations=args.route_operation)
        print_json(payload)
        return 0

    if not args.input:
        raise SystemExit("Raw calldata input is required when not using --tx-json, --capture-dir, or --tx-hash")

    raw_input, target_from_file = _read_raw_input_argument(args.input)
    payload = decode_calldata(raw_input, target_address=args.target_address or target_from_file)
    if args.route_operation:
        payload.setdefault("notes", []).append(
            "route-operation comparison is emitted for tx/receipt evidence modes; bare calldata still needs a transaction context for route evidence."
        )
    print_json(payload)
    return 0


def cmd_account_status(args: argparse.Namespace) -> int:
    try:
        payload = fetch_account_status(
            args.owner,
            rpc_url=_resolve_rpc_override(args),
            pools=args.pool,
            sigma_app_base_url=args.sigma_app_base_url,
            include_history=bool(args.include_history),
            history_limit=args.history_limit,
            include_empty_pools=not bool(args.exclude_empty_pools),
            include_controller_entry_price=bool(args.include_controller_entry_price),
            controller_address=args.controller_address,
        )
    except AccountFetchError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(payload)
    return 0


def cmd_account_positions(args: argparse.Namespace) -> int:
    try:
        payload = fetch_account_positions(
            args.owner,
            rpc_url=_resolve_rpc_override(args),
            pools=args.pool,
            sigma_app_base_url=args.sigma_app_base_url,
            include_controller_entry_price=bool(args.include_controller_entry_price),
            controller_address=args.controller_address,
        )
    except AccountFetchError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(payload)
    return 0


def cmd_account_history(args: argparse.Namespace) -> int:
    try:
        payload = fetch_account_history(
            args.owner,
            rpc_url=_resolve_rpc_override(args),
            pools=args.pool,
            sigma_app_base_url=args.sigma_app_base_url,
            history_limit=args.history_limit,
            position_id=args.position_id,
        )
    except AccountFetchError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(payload)
    return 0


def cmd_account_mint_close_readiness(args: argparse.Namespace) -> int:
    try:
        payload = fetch_mint_close_readiness(
            args.owner,
            position_id=args.position_id,
            pool=args.pool,
            rpc_url=_resolve_rpc_override(args),
            bnbusd_address=args.bnbusd_address,
            router_address=args.router_address,
            repay_amount=args.repay_amount,
            target_ltv=args.target_ltv,
            withdraw_amount=args.withdraw_amount,
            approval_policy_mode=args.approval_policy,
            approval_amount=args.approval_amount,
        )
    except AccountFetchError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(payload)
    return 0


def cmd_account_stability_pools(args: argparse.Namespace) -> int:
    try:
        payload = fetch_stability_pool_status(
            args.owner,
            rpc_url=_resolve_rpc_override(args),
            pools=args.pool,
            bnbusd_address=args.bnbusd_address,
        )
    except AccountFetchError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(payload)
    return 0


def cmd_account_bnbusd_trace(args: argparse.Namespace) -> int:
    try:
        payload = fetch_bnbusd_trace(
            args.owner,
            position_id=args.position_id,
            pool=args.pool,
            rpc_url=_resolve_rpc_override(args),
            sigma_app_base_url=args.sigma_app_base_url,
            history_limit=args.history_limit,
            bnbusd_address=args.bnbusd_address,
            router_address=args.router_address,
            stability_pools=args.stability_pool,
            tx_hashes=args.tx_hash,
        )
    except AccountFetchError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(payload)
    return 0


def cmd_config_show(args: argparse.Namespace) -> int:
    try:
        config = load_operator_config()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(
        {
            "path": str(config.path),
            "exists": config.exists,
            "approvalPolicy": approval_policy_to_dict(config.approval_policy),
            "raw": config.raw,
        }
    )
    return 0


def cmd_config_init(args: argparse.Namespace) -> int:
    try:
        config = initialize_operator_config(
            mode=args.approval_policy,
            amount=args.approval_amount,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(
        {
            "path": str(config.path),
            "written": True,
            "approvalPolicy": approval_policy_to_dict(config.approval_policy),
        }
    )
    return 0


def cmd_config_set_approval_policy(args: argparse.Namespace) -> int:
    try:
        policy = normalize_approval_policy(
            args.approval_policy,
            args.approval_amount,
            source="cli-config-update",
        )
        config = save_operator_config(approval_policy=policy)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(
        {
            "path": str(config.path),
            "written": True,
            "approvalPolicy": approval_policy_to_dict(config.approval_policy),
        }
    )
    return 0


def cmd_governance_overview(args: argparse.Namespace) -> int:
    print_json(governance_overview())
    return 0


def cmd_governance_area_read(args: argparse.Namespace) -> int:
    try:
        payload = governance_read_action(
            args.governance_area,
            args.governance_area_command,
            owner=getattr(args, "owner", None),
            amount=getattr(args, "amount", None),
        )
    except GovernanceError as exc:
        raise SystemExit(str(exc)) from exc
    print_json(payload)
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    forwarded = list(args.args or [])
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]
    payload = build_plan(args.operation, forwarded)
    print_json(payload)
    return 0


def cmd_abi_inspect(args: argparse.Namespace) -> int:
    if args.summary or not args.query:
        print_json(manifest_summary())
    else:
        print_json(inspect_contract(args.query))
    return 0


def cmd_abi_refresh(args: argparse.Namespace) -> int:
    settings = get_settings()
    ensure_paths(settings)
    requested_output = args.output_dir or str(settings.abi_dir)
    command = ["python3", str(script_path("fetch_sigma_abi.py"))]
    if args.ws_url:
        command.extend(["--ws-url", args.ws_url])
    command.extend(["--output-dir", requested_output])
    if args.summary:
        command.append("--summary")

    if args.dry_run:
        print_json({
            "dryRun": True,
            "sourceSkillRoot": str(settings.skill_root),
            "script": str(script_path("fetch_sigma_abi.py")),
            "outputDir": requested_output,
            "wouldRun": command,
        })
        return 0

    if not args.ws_url:
        raise SystemExit("--ws-url is required unless --dry-run is used")

    forwarded = ["--ws-url", args.ws_url, "--output-dir", requested_output]
    if args.summary:
        forwarded.append("--summary")
    completed = run_skill_python("fetch_sigma_abi.py", forwarded, check=True)
    stdout = completed.stdout.strip()
    if stdout:
        try:
            print_json(json.loads(stdout))
        except json.JSONDecodeError:
            print(stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
