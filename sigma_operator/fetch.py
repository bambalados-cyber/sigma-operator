from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .abi import normalize_address
from .config import get_settings
from .decode import decode_payload


class FetchError(RuntimeError):
    pass


_FETCH_SOURCES = {"rpc", "explorer"}


def fetch_decode_by_hash(
    tx_hash: str,
    *,
    rpc_url: str | None = None,
    timeout_seconds: float | None = None,
    target_address: str | None = None,
    save_json: str | Path | None = None,
    fetch_source: str = "rpc",
    explorer_api_url: str | None = None,
    explorer_api_key: str | None = None,
    explorer_chain_id: int | None = None,
    route_operations: list[str] | None = None,
) -> dict[str, Any]:
    bundle, metadata = fetch_transaction_bundle(
        tx_hash,
        rpc_url=rpc_url,
        timeout_seconds=timeout_seconds,
        fetch_source=fetch_source,
        explorer_api_url=explorer_api_url,
        explorer_api_key=explorer_api_key,
        explorer_chain_id=explorer_chain_id,
    )

    saved_path = None
    if save_json is not None:
        output_path = Path(save_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        saved_path = str(output_path)

    result = decode_payload(
        bundle,
        source_name=f"tx-hash:{metadata['transactionHash']}",
        target_address=target_address,
        route_operations=route_operations,
    )
    result["mode"] = "tx-hash"
    result["fetch"] = metadata
    if saved_path is not None:
        result["savedFetchJson"] = saved_path
        backend_label = metadata.get("backendLabel", metadata["source"])
        result["summary"].append(f"Fetched {backend_label} bundle was written to {saved_path}.")
    if bundle.get("receipt") is None:
        result.setdefault("warnings", []).append(
            "Transaction was fetched successfully, but no receipt is available yet (likely pending or dropped)."
        )
    return result


def fetch_transaction_bundle(
    tx_hash: str,
    *,
    rpc_url: str | None = None,
    timeout_seconds: float | None = None,
    fetch_source: str = "rpc",
    explorer_api_url: str | None = None,
    explorer_api_key: str | None = None,
    explorer_chain_id: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved_source = _normalize_fetch_source(fetch_source)
    if resolved_source == "rpc":
        return _fetch_transaction_bundle_from_rpc(
            tx_hash,
            rpc_url=rpc_url,
            timeout_seconds=timeout_seconds,
        )
    return _fetch_transaction_bundle_from_explorer(
        tx_hash,
        timeout_seconds=timeout_seconds,
        explorer_api_url=explorer_api_url,
        explorer_api_key=explorer_api_key,
        explorer_chain_id=explorer_chain_id,
    )


def _fetch_transaction_bundle_from_rpc(
    tx_hash: str,
    *,
    rpc_url: str | None = None,
    timeout_seconds: float | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    settings = get_settings()
    resolved_hash = _normalize_hash(tx_hash)
    if resolved_hash is None or len(resolved_hash) != 66:
        raise FetchError("tx hash must be a 32-byte 0x-prefixed hex value")

    resolved_rpc_url = (rpc_url or settings.bnb_rpc_url or "").strip()
    if not resolved_rpc_url:
        raise FetchError(
            "BNB Chain RPC URL is required. Use --bnb-rpc-url (or --meganode-rpc-url / --nodereal-rpc-url / --rpc-url) "
            "or set SIGMA_OPERATOR_BNB_RPC_URL."
        )

    resolved_timeout = float(timeout_seconds or settings.bnb_rpc_timeout_seconds)
    chain_id = _rpc_call(resolved_rpc_url, "eth_chainId", [], timeout_seconds=resolved_timeout)
    transaction = _rpc_call(
        resolved_rpc_url,
        "eth_getTransactionByHash",
        [resolved_hash],
        timeout_seconds=resolved_timeout,
    )
    if transaction is None:
        raise FetchError(f"Transaction {resolved_hash} was not found via {resolved_rpc_url}")

    receipt = _rpc_call(
        resolved_rpc_url,
        "eth_getTransactionReceipt",
        [resolved_hash],
        timeout_seconds=resolved_timeout,
    )

    normalized_tx = _normalize_transaction(transaction, chain_id=chain_id, source_label="rpc")
    normalized_receipt = _normalize_receipt(receipt, source_label="rpc") if receipt is not None else None
    fetched_at = _utc_now()
    bundle: dict[str, Any] = {
        "fetch": {
            "source": "rpc",
            "backendLabel": "BNB Chain RPC (MegaNode / NodeReal compatible)",
            "rpcUrl": resolved_rpc_url,
            "fetchedAtUtc": fetched_at,
            "transactionHash": resolved_hash,
            "chainId": _parse_intlike(chain_id),
        },
        "transaction": normalized_tx,
    }
    if normalized_receipt is not None:
        bundle["receipt"] = normalized_receipt

    metadata = {
        "source": "rpc",
        "backendLabel": "BNB Chain RPC (MegaNode / NodeReal compatible)",
        "rpcUrl": resolved_rpc_url,
        "timeoutSeconds": resolved_timeout,
        "chainId": _parse_intlike(chain_id),
        "transactionHash": resolved_hash,
        "receiptAvailable": normalized_receipt is not None,
        "fetchedAtUtc": fetched_at,
        "readOnlyMethods": [
            "eth_chainId",
            "eth_getTransactionByHash",
            "eth_getTransactionReceipt",
        ],
    }
    return bundle, metadata


def _fetch_transaction_bundle_from_explorer(
    tx_hash: str,
    *,
    timeout_seconds: float | None = None,
    explorer_api_url: str | None = None,
    explorer_api_key: str | None = None,
    explorer_chain_id: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    settings = get_settings()
    resolved_hash = _normalize_hash(tx_hash)
    if resolved_hash is None or len(resolved_hash) != 66:
        raise FetchError("tx hash must be a 32-byte 0x-prefixed hex value")

    resolved_api_url = (explorer_api_url or settings.bsctrace_api_url or "").strip()
    if not resolved_api_url:
        raise FetchError(
            "Explorer mode is optional and no longer defaults to Etherscan. Use --bsctrace-api-url (or --explorer-api-url) "
            "or set SIGMA_OPERATOR_BSCTRACE_API_URL / SIGMA_OPERATOR_EXPLORER_API_URL."
        )
    resolved_api_key = (explorer_api_key or settings.bsctrace_api_key or "").strip() or None
    resolved_chain_id = int(explorer_chain_id or settings.bsctrace_chain_id)
    resolved_timeout = float(timeout_seconds or settings.bsctrace_timeout_seconds)

    transaction = _explorer_proxy_call(
        resolved_api_url,
        "eth_getTransactionByHash",
        tx_hash=resolved_hash,
        chain_id=resolved_chain_id,
        api_key=resolved_api_key,
        timeout_seconds=resolved_timeout,
    )
    if transaction is None:
        raise FetchError(f"Transaction {resolved_hash} was not found via explorer {resolved_api_url}")

    receipt = _explorer_proxy_call(
        resolved_api_url,
        "eth_getTransactionReceipt",
        tx_hash=resolved_hash,
        chain_id=resolved_chain_id,
        api_key=resolved_api_key,
        timeout_seconds=resolved_timeout,
    )

    normalized_tx = _normalize_transaction(
        transaction,
        chain_id=transaction.get("chainId") or hex(resolved_chain_id),
        source_label="explorer",
    )
    normalized_receipt = _normalize_receipt(receipt, source_label="explorer") if receipt is not None else None
    fetched_at = _utc_now()
    bundle: dict[str, Any] = {
        "fetch": {
            "source": "explorer",
            "backendLabel": "Explorer API (secondary / optional)",
            "explorerApiUrl": resolved_api_url,
            "explorerChainId": resolved_chain_id,
            "fetchedAtUtc": fetched_at,
            "transactionHash": resolved_hash,
            "chainId": _parse_intlike(transaction.get("chainId")) or resolved_chain_id,
        },
        "transaction": normalized_tx,
    }
    if normalized_receipt is not None:
        bundle["receipt"] = normalized_receipt

    metadata = {
        "source": "explorer",
        "backendLabel": "Explorer API (secondary / optional)",
        "explorerApiUrl": resolved_api_url,
        "explorerChainId": resolved_chain_id,
        "apiKeyConfigured": resolved_api_key is not None,
        "timeoutSeconds": resolved_timeout,
        "chainId": _parse_intlike(transaction.get("chainId")) or resolved_chain_id,
        "transactionHash": resolved_hash,
        "receiptAvailable": normalized_receipt is not None,
        "fetchedAtUtc": fetched_at,
        "readOnlyMethods": [
            "proxy.eth_getTransactionByHash",
            "proxy.eth_getTransactionReceipt",
        ],
    }
    return bundle, metadata


def _normalize_fetch_source(value: str | None) -> str:
    resolved = (value or "rpc").strip().lower()
    if resolved not in _FETCH_SOURCES:
        expected = ", ".join(sorted(_FETCH_SOURCES))
        raise FetchError(f"Unsupported fetch source: {value!r}. Expected one of: {expected}.")
    return resolved


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
    except HTTPError as exc:  # pragma: no cover - network surfaces vary
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise FetchError(f"RPC HTTP error for {method}: {exc.code} {detail}") from exc
    except URLError as exc:  # pragma: no cover - network surfaces vary
        raise FetchError(f"RPC connectivity error for {method}: {exc}") from exc

    if "error" in body:
        raise FetchError(f"RPC error for {method}: {body['error']}")
    return body.get("result")


def _explorer_proxy_call(
    base_url: str,
    action: str,
    *,
    tx_hash: str,
    chain_id: int,
    api_key: str | None,
    timeout_seconds: float,
) -> Any:
    query = {
        "chainid": str(chain_id),
        "module": "proxy",
        "action": action,
        "txhash": tx_hash,
    }
    if api_key:
        query["apikey"] = api_key

    request_url = _with_query(base_url, query)
    request = Request(
        request_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "sigma-operator/0.1",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:  # pragma: no cover - network surfaces vary
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise FetchError(f"Explorer HTTP error for {action}: {exc.code} {detail}") from exc
    except URLError as exc:  # pragma: no cover - network surfaces vary
        raise FetchError(f"Explorer connectivity error for {action}: {exc}") from exc

    if not isinstance(body, dict):
        raise FetchError(f"Explorer response for {action} was not a JSON object")
    if "error" in body:
        raise FetchError(f"Explorer error for {action}: {body['error']}")

    status = str(body.get("status", "")).strip()
    result = body.get("result")
    if status == "0":
        message = str(result or body.get("message") or f"Explorer request failed for {action}")
        raise FetchError(_decorate_explorer_error(action, message))
    return result


def _decorate_explorer_error(action: str, message: str) -> str:
    detail = f"Explorer error for {action}: {message}"
    lowered = message.lower()
    if "deprecated v1 endpoint" in lowered:
        return detail + " BscScan's classic proxy API is deprecated; explorer mode is secondary now, so prefer read-only BNB RPC unless you have a modern compatible explorer endpoint."
    if "free api access is not supported for this chain" in lowered:
        return detail + " BNB Chain explorer fetch currently needs a paid Etherscan V2 plan or another compatible explorer endpoint/key. Practical fallback: use --fetch-source rpc with a MegaNode / NodeReal / BSCTrace-compatible BNB RPC URL."
    if "missing or unsupported chainid" in lowered:
        return detail + " Sigma defaults to BNB Chain chainId 56; override with --bsctrace-chain-id or --explorer-chain-id if needed."
    return detail


def _with_query(base_url: str, query: dict[str, str]) -> str:
    separator = "&" if "?" in base_url else "?"
    if base_url.endswith(("?", "&")):
        separator = ""
    return f"{base_url}{separator}{urlencode(query)}"


def _normalize_transaction(payload: dict[str, Any], *, chain_id: str | None, source_label: str) -> dict[str, Any]:
    return {
        "hash": _normalize_hash(payload.get("hash") or payload.get("transactionHash")),
        "from": normalize_address(payload.get("from")),
        "to": normalize_address(payload.get("to")),
        "input": _normalize_hex(payload.get("input") or payload.get("data")),
        "value": payload.get("value"),
        "valueDecimal": _parse_intlike(payload.get("value")),
        "chainId": _parse_intlike(payload.get("chainId") or chain_id),
        "nonce": _parse_intlike(payload.get("nonce")),
        "gas": _parse_intlike(payload.get("gas")),
        "gasPrice": _parse_intlike(payload.get("gasPrice")),
        "maxFeePerGas": _parse_intlike(payload.get("maxFeePerGas")),
        "maxPriorityFeePerGas": _parse_intlike(payload.get("maxPriorityFeePerGas")),
        "blockHash": _normalize_hash(payload.get("blockHash")),
        "blockNumber": _parse_intlike(payload.get("blockNumber")),
        "transactionIndex": _parse_intlike(payload.get("transactionIndex")),
        "type": _parse_intlike(payload.get("type")),
        "accessList": payload.get("accessList") if isinstance(payload.get("accessList"), list) else None,
        "origin": f"{source_label}.eth_getTransactionByHash",
    }


def _normalize_receipt(payload: dict[str, Any], *, source_label: str) -> dict[str, Any]:
    logs = []
    for item in payload.get("logs", []):
        normalized = _normalize_log(item)
        if normalized is not None:
            logs.append(normalized)
    return {
        "transactionHash": _normalize_hash(payload.get("transactionHash")),
        "transactionIndex": _parse_intlike(payload.get("transactionIndex")),
        "blockHash": _normalize_hash(payload.get("blockHash")),
        "blockNumber": _parse_intlike(payload.get("blockNumber")),
        "from": normalize_address(payload.get("from")),
        "to": normalize_address(payload.get("to")),
        "contractAddress": normalize_address(payload.get("contractAddress")),
        "status": _parse_intlike(payload.get("status")),
        "gasUsed": _parse_intlike(payload.get("gasUsed")),
        "cumulativeGasUsed": _parse_intlike(payload.get("cumulativeGasUsed")),
        "effectiveGasPrice": _parse_intlike(payload.get("effectiveGasPrice")),
        "type": _parse_intlike(payload.get("type")),
        "logs": logs,
        "origin": f"{source_label}.eth_getTransactionReceipt",
    }


def _normalize_log(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    topics = payload.get("topics")
    if not isinstance(topics, list) or not topics:
        return None
    return {
        "address": normalize_address(payload.get("address") or payload.get("to")),
        "topics": [_normalize_hex(topic) for topic in topics],
        "data": _normalize_hex(payload.get("data")) or "0x",
        "logIndex": _parse_intlike(payload.get("logIndex") or payload.get("index")),
        "transactionHash": _normalize_hash(payload.get("transactionHash") or payload.get("txHash")),
        "blockNumber": _parse_intlike(payload.get("blockNumber")),
    }


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_hash(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    stripped = value.strip()
    if not stripped:
        return None
    if stripped.startswith(("0x", "0X")):
        stripped = stripped[2:]
    return "0x" + stripped.lower()


def _normalize_hex(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    stripped = value.strip()
    if not stripped:
        return None
    if stripped.startswith(("0x", "0X")):
        return "0x" + stripped[2:]
    return stripped


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
