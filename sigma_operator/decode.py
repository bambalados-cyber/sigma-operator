from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .abi import decode_calldata, decode_event_log, normalize_address, route_hints, route_operation_details, route_operations

ACCEPTED_INPUT_FORMATS = [
    {
        "name": "direct transaction object",
        "shape": '{"to":"0x...","input|data|calldata":"0x...","value?":...,"chainId?":...}',
    },
    {
        "name": "json-rpc wallet request",
        "shape": '{"method":"eth_sendTransaction"|"eth_call"|"eth_signTransaction","params":[{...tx...}]}',
    },
    {
        "name": "wallet_sendCalls batch",
        "shape": '{"method":"wallet_sendCalls","params":[{"chainId":"0x38","calls":[{"to":"0x...","data":"0x..."}]}]}',
    },
    {
        "name": "browser/devtools request export",
        "shape": '{"request":{"postData":{"text":"{...json-rpc payload...}"}}}'
                 ' or HAR-style {"log":{"entries":[...]}} or DevTools-style {"entries":[...]}',
    },
    {
        "name": "receipt/log bundle",
        "shape": '{"logs":[{"address":"0x...","topics":[...],"data":"0x..."}]}'
                 ' or {"receipt":{"logs":[...]}}',
    },
    {
        "name": "combined tx + receipt evidence bundle",
        "shape": '{"transaction":{...tx...},"receipt":{"transactionHash":"0x...","logs":[...]}}',
    },
]

_RPC_METHODS = {"eth_sendTransaction", "eth_call", "eth_signTransaction"}
_JSON_STRING_KEYS = {
    "body",
    "payload",
    "text",
    "postData",
    "post_data",
    "requestBody",
    "request_body",
    "responseBody",
    "response_body",
    "message",
    "content",
    "raw",
}
_LOG_CONTAINER_KEYS = {"logs", "events"}
_RECEIPT_HINT_KEYS = {
    "status",
    "gasUsed",
    "cumulativeGasUsed",
    "effectiveGasPrice",
    "contractAddress",
    "logs",
}


def decode_json_file(
    path: str | Path,
    target_address: str | None = None,
    route_operations: list[str] | None = None,
) -> dict[str, Any]:
    file_path = Path(path).expanduser().resolve()
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    result = decode_payload(
        payload,
        source_name=str(file_path),
        target_address=target_address,
        route_operations=route_operations,
    )
    result["mode"] = "tx-json"
    result["inputPath"] = str(file_path)
    result["inputKind"] = "har" if _looks_like_har(payload) else "json"
    return result


def batch_decode_path(
    path: str | Path,
    target_address: str | None = None,
    route_operations: list[str] | None = None,
) -> dict[str, Any]:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    if root.is_file():
        return decode_json_file(root, target_address=target_address, route_operations=route_operations)

    source_root = root / "raw" if (root / "raw").is_dir() else root
    artifact_files = sorted(
        candidate for candidate in source_root.rglob("*")
        if candidate.is_file() and candidate.suffix.lower() in {".json", ".har"}
    )
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    artifacts_written: list[str] = []

    decoded_dir: Path | None = None
    if (root / "decoded").is_dir():
        decoded_dir = root / "decoded"
    elif source_root.name == "raw" and source_root.parent.is_dir() and (source_root.parent / "decoded").is_dir():
        decoded_dir = source_root.parent / "decoded"

    for file_path in artifact_files:
        try:
            decoded = decode_json_file(file_path, target_address=target_address, route_operations=route_operations)
            results.append(decoded)
            if decoded_dir is not None:
                relative = file_path.relative_to(source_root)
                output_name = "__".join(relative.with_suffix("").parts) + ".decoded.json"
                output_path = decoded_dir / output_name
                output_path.write_text(json.dumps(decoded, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                artifacts_written.append(str(output_path))
        except Exception as exc:  # noqa: BLE001 - batch mode should preserve per-file failures
            errors.append({"path": str(file_path), "error": str(exc)})

    summary = _batch_summary(root, results, errors, decoded_dir)
    batch_payload = {
        "mode": "batch-decode",
        "inputPath": str(root),
        "fileCount": len(artifact_files),
        "decodedFileCount": len(results),
        "errorCount": len(errors),
        "results": results,
        "errors": errors,
        "artifactsWritten": artifacts_written,
        "summary": summary,
        "acceptedFormats": ACCEPTED_INPUT_FORMATS,
    }
    if decoded_dir is not None:
        summary_path = decoded_dir / "batch-summary.json"
        summary_path.write_text(json.dumps(batch_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifacts_written.append(str(summary_path))
    return batch_payload


def _looks_like_har(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("log"), dict)
        and isinstance(payload["log"].get("entries"), list)
    )




def decode_payload(
    payload: Any,
    source_name: str = "<memory>",
    target_address: str | None = None,
    route_operations: list[str] | None = None,
) -> dict[str, Any]:
    transactions = _collect_transactions(payload)
    receipts = _collect_receipts(payload)
    logs = _collect_logs(payload)

    tx_results = [_decode_transaction(candidate, target_address=target_address) for candidate in transactions]
    receipt_results = [_decode_receipt(candidate, target_address=target_address) for candidate in receipts]
    log_results = [_decode_log(candidate, target_address=target_address) for candidate in logs]

    warnings: list[str] = []
    if not tx_results and not log_results and not receipt_results:
        warnings.append(
            "No supported transaction or log payloads found. See acceptedFormats for the currently supported browser/export shapes."
        )
    if any(item["transaction"].get("methodHint") and not item["transaction"].get("input") for item in tx_results):
        warnings.append(
            "Some payloads exposed method/params hints without raw calldata. Those are reported, but ABI decode remains low-confidence until input/data is present."
        )
    if receipt_results and not tx_results:
        warnings.append(
            "Receipt/log evidence was present without a matching transaction object. Correlation is receipt-first and may miss calldata context."
        )

    evidence_records = _correlate_evidence(tx_results, receipt_results, log_results)
    route_report = _build_route_evidence_report(evidence_records, requested_operations=route_operations)
    summary = _result_summary(source_name, tx_results, receipt_results, log_results, evidence_records, warnings)
    summary.extend(_route_summary(route_report))
    return {
        "source": source_name,
        "transactionCount": len(tx_results),
        "receiptCount": len(receipt_results),
        "logCount": len(log_results),
        "transactions": tx_results,
        "receipts": receipt_results,
        "logs": log_results,
        "evidenceRecords": evidence_records,
        "routeEvidence": route_report,
        "warnings": warnings,
        "summary": summary,
        "acceptedFormats": ACCEPTED_INPUT_FORMATS,
    }


def _decode_transaction(candidate: dict[str, Any], target_address: str | None = None) -> dict[str, Any]:
    tx = candidate["tx"]
    calldata = tx.get("input")
    decoded = None
    warning = None
    if calldata:
        decoded = decode_calldata(calldata, target_address=target_address or tx.get("to"))
    else:
        warning = "No input/data/calldata field was found in this transaction-like payload."

    return {
        "source": candidate["source"],
        "transaction": tx,
        "decode": decoded,
        "warning": warning,
    }


def _decode_receipt(candidate: dict[str, Any], target_address: str | None = None) -> dict[str, Any]:
    receipt = candidate["receipt"]
    decoded_logs = [
        _decode_log(
            {"source": f"{candidate['source']}.logs[{index}]", "log": log},
            target_address=target_address or log.get("address"),
        )
        for index, log in enumerate(receipt.get("logs", []))
    ]
    matched_count = sum(1 for item in decoded_logs if _best_decode_match(item.get("decode")) is not None)
    return {
        "source": candidate["source"],
        "receipt": receipt,
        "statusLabel": _receipt_status_label(receipt.get("status")),
        "decodedLogs": decoded_logs,
        "summary": [
            f"receipt {receipt.get('transactionHash') or '<unknown>'} status {_receipt_status_label(receipt.get('status'))} with {len(decoded_logs)} log(s).",
            f"{matched_count} log(s) had at least one cached Sigma ABI match.",
        ],
    }


def _decode_log(candidate: dict[str, Any], target_address: str | None = None) -> dict[str, Any]:
    log = candidate["log"]
    return {
        "source": candidate["source"],
        "log": log,
        "decode": decode_event_log(log, target_address=target_address or log.get("address")),
    }


def _batch_summary(root: Path, results: list[dict[str, Any]], errors: list[dict[str, Any]], decoded_dir: Path | None) -> list[str]:
    tx_count = sum(item.get("transactionCount", 0) for item in results)
    receipt_count = sum(item.get("receiptCount", 0) for item in results)
    log_count = sum(item.get("logCount", 0) for item in results)
    evidence_count = sum(len(item.get("evidenceRecords", [])) for item in results)
    summary = [
        f"Scanned {len(results) + len(errors)} JSON/HAR file(s) under {root}.",
        f"Decoded {tx_count} transaction candidate(s), {receipt_count} receipt candidate(s), and {log_count} log candidate(s).",
        f"Built {evidence_count} correlated evidence record(s).",
    ]
    if errors:
        summary.append(f"{len(errors)} file(s) failed JSON ingestion or decode and are listed under errors.")
    if decoded_dir is not None:
        summary.append(f"Per-file machine-readable results were written under {decoded_dir}.")
    return summary


def _result_summary(
    source_name: str,
    tx_results: list[dict[str, Any]],
    receipt_results: list[dict[str, Any]],
    log_results: list[dict[str, Any]],
    evidence_records: list[dict[str, Any]],
    warnings: list[str],
) -> list[str]:
    lines = [
        f"Source: {source_name}",
        f"Found {len(tx_results)} transaction candidate(s), {len(receipt_results)} receipt candidate(s), and {len(log_results)} log candidate(s).",
    ]
    for index, item in enumerate(tx_results, start=1):
        tx = item["transaction"]
        best = _best_decode_match(item.get("decode"))
        if best is not None:
            lines.append(
                f"tx[{index}] {best['signature']} via {best['docsName']} @ {best['callAddress']} ({best['confidence']})."
            )
        elif tx.get("input"):
            lines.append(f"tx[{index}] selector {tx['input'][:10]} had no successful ABI-backed decode match.")
        else:
            hint = tx.get("methodHint") or tx.get("rpcMethod") or "unknown method"
            lines.append(f"tx[{index}] exposes {hint} but no raw calldata field was available to decode.")
    for index, item in enumerate(receipt_results, start=1):
        receipt = item["receipt"]
        lines.append(
            f"receipt[{index}] tx {short_hash(receipt.get('transactionHash'))} status {item['statusLabel']} with {len(item.get('decodedLogs', []))} decoded log candidate(s)."
        )
    for index, item in enumerate(log_results, start=1):
        best = _best_decode_match(item.get("decode"), event=True)
        if best is not None:
            lines.append(
                f"log[{index}] {best['eventSignature']} via {best['docsName']} @ {best['callAddress']} ({best['confidence']})."
            )
        else:
            lines.append(f"log[{index}] topic0 {item['decode'].get('topic0')} had no cached Sigma ABI match.")
    for index, record in enumerate(evidence_records, start=1):
        call = record.get("decodedCall")
        call_part = f"; call {call['signature']} via {call['docsName']}" if call else ""
        lines.append(
            f"evidence[{index}] {record['sourceType']} tx {short_hash(record.get('transactionHash'))} status {record['status']}{call_part}; {record['matchedEventCount']}/{record['logCount']} receipt log(s) matched cached ABIs."
        )
    lines.extend(f"warning: {warning}" for warning in warnings)
    return lines


def _collect_transactions(payload: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    _walk_payload(payload, source="root", tx_out=out, log_out=[], seen=seen)
    return out


def _collect_logs(payload: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    _walk_payload(payload, source="root", tx_out=[], log_out=out, seen=seen)
    return out


def _collect_receipts(payload: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    _walk_receipts(payload, source="root", out=out, seen=seen)
    return out


def _walk_payload(
    payload: Any,
    *,
    source: str,
    tx_out: list[dict[str, Any]],
    log_out: list[dict[str, Any]],
    seen: set[str],
    depth: int = 0,
) -> None:
    if depth > 8:
        return

    parsed_from_string = _parse_jsonish_string(payload)
    if parsed_from_string is not None:
        _walk_payload(parsed_from_string, source=f"{source}:json-string", tx_out=tx_out, log_out=log_out, seen=seen, depth=depth + 1)
        return

    if isinstance(payload, list):
        for index, item in enumerate(payload):
            _walk_payload(item, source=f"{source}[{index}]", tx_out=tx_out, log_out=log_out, seen=seen, depth=depth + 1)
        return

    if not isinstance(payload, dict):
        return

    tx_candidate = _normalize_direct_transaction(payload, source)
    if tx_candidate is not None:
        key = json.dumps(tx_candidate, sort_keys=True)
        if key not in seen:
            tx_out.append({"source": source, "tx": tx_candidate})
            seen.add(key)

    for tx_candidate in _extract_rpc_transactions(payload, source):
        key = json.dumps(tx_candidate, sort_keys=True)
        if key not in seen:
            tx_out.append({"source": source, "tx": tx_candidate})
            seen.add(key)

    for log_candidate in _extract_direct_logs(payload):
        key = json.dumps(log_candidate, sort_keys=True)
        if key not in seen:
            log_out.append({"source": source, "log": log_candidate})
            seen.add(key)

    skip_params_recursion = isinstance(payload.get("method"), str) and payload.get("method") in (_RPC_METHODS | {"wallet_sendCalls"})
    for key, value in payload.items():
        if skip_params_recursion and key == "params":
            continue
        next_source = f"{source}.{key}"
        if isinstance(value, (dict, list)):
            _walk_payload(value, source=next_source, tx_out=tx_out, log_out=log_out, seen=seen, depth=depth + 1)
            continue
        if key in _JSON_STRING_KEYS:
            parsed = _parse_jsonish_string(value)
            if parsed is not None:
                _walk_payload(parsed, source=next_source, tx_out=tx_out, log_out=log_out, seen=seen, depth=depth + 1)


def _walk_receipts(
    payload: Any,
    *,
    source: str,
    out: list[dict[str, Any]],
    seen: set[str],
    depth: int = 0,
) -> None:
    if depth > 8:
        return

    parsed_from_string = _parse_jsonish_string(payload)
    if parsed_from_string is not None:
        _walk_receipts(parsed_from_string, source=f"{source}:json-string", out=out, seen=seen, depth=depth + 1)
        return

    if isinstance(payload, list):
        for index, item in enumerate(payload):
            _walk_receipts(item, source=f"{source}[{index}]", out=out, seen=seen, depth=depth + 1)
        return

    if not isinstance(payload, dict):
        return

    receipt_candidate = _normalize_receipt(payload)
    if receipt_candidate is not None:
        key = json.dumps(receipt_candidate, sort_keys=True)
        if key not in seen:
            out.append({"source": source, "receipt": receipt_candidate})
            seen.add(key)

    for key, value in payload.items():
        next_source = f"{source}.{key}"
        if isinstance(value, (dict, list)):
            _walk_receipts(value, source=next_source, out=out, seen=seen, depth=depth + 1)
            continue
        if key in _JSON_STRING_KEYS:
            parsed = _parse_jsonish_string(value)
            if parsed is not None:
                _walk_receipts(parsed, source=next_source, out=out, seen=seen, depth=depth + 1)


def _normalize_direct_transaction(payload: dict[str, Any], source: str) -> dict[str, Any] | None:
    if isinstance(payload.get("topics"), list):
        return None
    if isinstance(payload.get("logs"), list) and any(payload.get(key) is not None for key in ("status", "gasUsed", "cumulativeGasUsed", "effectiveGasPrice", "contractAddress")):
        return None

    to = payload.get("to")
    calldata = payload.get("input") or payload.get("data") or payload.get("calldata")
    method_hint = payload.get("methodName") or payload.get("functionName")

    request_like = payload.get("request")
    if isinstance(request_like, dict):
        nested = request_like.get("to") or request_like.get("input") or request_like.get("data")
        if nested:
            return _normalize_direct_transaction(request_like, f"{source}.request")

    tx_like = payload.get("transaction")
    if isinstance(tx_like, dict):
        nested = tx_like.get("to") or tx_like.get("input") or tx_like.get("data") or tx_like.get("hash")
        if nested:
            return _normalize_direct_transaction(tx_like, f"{source}.transaction")

    rpc_method = payload.get("method") if isinstance(payload.get("method"), str) and payload.get("method", "").startswith("eth_") else None
    tx_hash = payload.get("hash") or payload.get("transactionHash") or payload.get("txHash")
    tx_metadata_present = any(
        payload.get(key) is not None
        for key in (
            "to",
            "from",
            "value",
            "nonce",
            "gas",
            "gasPrice",
            "maxFeePerGas",
            "maxPriorityFeePerGas",
            "blockNumber",
            "transactionIndex",
            "input",
            "data",
            "calldata",
        )
    )
    if not any([calldata, method_hint, rpc_method]) and not (tx_hash and tx_metadata_present):
        return None
    if to is None and calldata is None and method_hint is None and not (tx_hash and tx_metadata_present):
        return None

    return {
        "hash": _normalize_hash(tx_hash),
        "to": normalize_address(str(to)) if to is not None else None,
        "from": normalize_address(payload.get("from")),
        "input": _normalize_hex(calldata),
        "value": payload.get("value"),
        "valueDecimal": _parse_intlike(payload.get("value")),
        "chainId": _parse_intlike(payload.get("chainId") or payload.get("chain_id")),
        "nonce": _parse_intlike(payload.get("nonce")),
        "gas": _parse_intlike(payload.get("gas")),
        "gasPrice": _parse_intlike(payload.get("gasPrice")),
        "maxFeePerGas": _parse_intlike(payload.get("maxFeePerGas")),
        "maxPriorityFeePerGas": _parse_intlike(payload.get("maxPriorityFeePerGas")),
        "blockHash": _normalize_hash(payload.get("blockHash")),
        "blockNumber": _parse_intlike(payload.get("blockNumber")),
        "transactionIndex": _parse_intlike(payload.get("transactionIndex")),
        "type": _parse_intlike(payload.get("type")),
        "methodHint": method_hint,
        "rpcMethod": rpc_method,
        "paramsHint": payload.get("params") if isinstance(payload.get("params"), list) else None,
        "accessList": payload.get("accessList") if isinstance(payload.get("accessList"), list) else None,
        "origin": source,
    }


def _extract_rpc_transactions(payload: dict[str, Any], source: str) -> list[dict[str, Any]]:
    method = payload.get("method")
    params = payload.get("params")
    if not isinstance(method, str) or not isinstance(params, list):
        return []

    out: list[dict[str, Any]] = []
    if method in _RPC_METHODS:
        for index, entry in enumerate(params):
            if isinstance(entry, dict):
                tx = _normalize_direct_transaction({**entry, "method": method}, f"{source}.params[{index}]")
                if tx is not None:
                    out.append(tx)
    elif method == "wallet_sendCalls":
        for index, bundle in enumerate(params):
            if not isinstance(bundle, dict):
                continue
            chain_id = _parse_intlike(bundle.get("chainId"))
            calls = bundle.get("calls")
            if not isinstance(calls, list):
                continue
            for call_index, call in enumerate(calls):
                if not isinstance(call, dict):
                    continue
                tx = _normalize_direct_transaction(
                    {**call, "chainId": chain_id, "method": method},
                    f"{source}.params[{index}].calls[{call_index}]",
                )
                if tx is not None:
                    out.append(tx)
    return out


def _extract_direct_logs(payload: dict[str, Any]) -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    for key in _LOG_CONTAINER_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                normalized = _normalize_log(item)
                if normalized is not None:
                    logs.append(normalized)
    receipt = payload.get("receipt")
    if isinstance(receipt, dict):
        value = receipt.get("logs")
        if isinstance(value, list):
            for item in value:
                normalized = _normalize_log(item)
                if normalized is not None:
                    logs.append(normalized)
    normalized = _normalize_log(payload)
    if normalized is not None:
        logs.append(normalized)
    return logs


def _normalize_receipt(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    receipt_like = payload.get("receipt") if isinstance(payload.get("receipt"), dict) else payload
    if not isinstance(receipt_like, dict):
        return None
    if isinstance(receipt_like.get("topics"), list):
        return None

    logs_value = receipt_like.get("logs")
    has_receipt_shape = any(key in receipt_like for key in _RECEIPT_HINT_KEYS) and isinstance(logs_value, list)
    if not has_receipt_shape:
        return None

    normalized_logs = []
    for item in logs_value:
        normalized = _normalize_log(item)
        if normalized is not None:
            normalized_logs.append(normalized)

    return {
        "transactionHash": _normalize_hash(receipt_like.get("transactionHash") or receipt_like.get("txHash") or payload.get("transactionHash")),
        "to": normalize_address(receipt_like.get("to")),
        "from": normalize_address(receipt_like.get("from")),
        "contractAddress": normalize_address(receipt_like.get("contractAddress")),
        "status": _parse_intlike(receipt_like.get("status")),
        "gasUsed": _parse_intlike(receipt_like.get("gasUsed")),
        "cumulativeGasUsed": _parse_intlike(receipt_like.get("cumulativeGasUsed")),
        "effectiveGasPrice": _parse_intlike(receipt_like.get("effectiveGasPrice")),
        "blockNumber": _parse_intlike(receipt_like.get("blockNumber")),
        "transactionIndex": _parse_intlike(receipt_like.get("transactionIndex")),
        "type": _parse_intlike(receipt_like.get("type")),
        "logs": normalized_logs,
    }


def _normalize_log(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    topics = payload.get("topics")
    if not isinstance(topics, list) or not topics:
        return None
    data = payload.get("data")
    address = payload.get("address") or payload.get("to")
    return {
        "address": normalize_address(str(address)) if address is not None else None,
        "topics": [_normalize_hex(topic) for topic in topics],
        "data": _normalize_hex(data) or "0x",
        "logIndex": _parse_intlike(payload.get("logIndex") or payload.get("index")),
        "transactionHash": _normalize_hash(payload.get("transactionHash") or payload.get("txHash")),
        "blockNumber": _parse_intlike(payload.get("blockNumber")),
    }


def _parse_jsonish_string(value: Any) -> Any | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or stripped[0] not in "[{":
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def _normalize_hex(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.startswith(("0x", "0X")):
            return "0x" + stripped[2:]
        return stripped
    return str(value)


def _normalize_hash(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.startswith(("0x", "0X")):
            stripped = stripped[2:]
        return "0x" + stripped.lower()
    return _normalize_hash(str(value))


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


def _correlate_evidence(
    tx_results: list[dict[str, Any]],
    receipt_results: list[dict[str, Any]],
    log_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    receipt_by_hash = {
        _normalize_hash(item["receipt"].get("transactionHash")): item
        for item in receipt_results
        if _normalize_hash(item["receipt"].get("transactionHash"))
    }
    loose_logs_by_hash: dict[str, list[dict[str, Any]]] = {}
    for item in log_results:
        tx_hash = _normalize_hash(item["log"].get("transactionHash"))
        if tx_hash is None:
            continue
        loose_logs_by_hash.setdefault(tx_hash, []).append(item)

    evidence: list[dict[str, Any]] = []
    matched_receipt_ids: set[int] = set()
    singleton_receipt = receipt_results[0] if len(receipt_results) == 1 else None

    for item in tx_results:
        tx = item["transaction"]
        tx_hash = _normalize_hash(tx.get("hash") or tx.get("transactionHash"))
        receipt_result = receipt_by_hash.get(tx_hash) if tx_hash else None
        fallback_used = False
        if receipt_result is None and singleton_receipt is not None:
            receipt_result = singleton_receipt
            fallback_used = True
        if receipt_result is not None:
            matched_receipt_ids.add(id(receipt_result))

        decoded_logs = receipt_result["decodedLogs"] if receipt_result is not None else loose_logs_by_hash.get(tx_hash or "", [])
        matched_events = [_compact_log_evidence(log) for log in decoded_logs if _best_decode_match(log.get("decode"), event=True) is not None]
        notes: list[str] = []
        if item.get("warning"):
            notes.append(item["warning"])
        if receipt_result is None:
            notes.append("No receipt was available to correlate execution outcome.")
        elif fallback_used:
            notes.append("Used singleton receipt correlation because tx hash matching was unavailable.")

        evidence.append({
            "sourceType": "tx+receipt" if receipt_result is not None else "tx-only",
            "transactionHash": tx_hash or (receipt_result["receipt"].get("transactionHash") if receipt_result else None),
            "from": tx.get("from"),
            "to": tx.get("to") or (receipt_result["receipt"].get("to") if receipt_result else None),
            "blockNumber": (receipt_result["receipt"].get("blockNumber") if receipt_result else None) or tx.get("blockNumber"),
            "chainId": tx.get("chainId"),
            "status": receipt_result["statusLabel"] if receipt_result is not None else "receipt-missing",
            "valueDecimal": tx.get("valueDecimal"),
            "gas": tx.get("gas"),
            "gasPrice": tx.get("gasPrice"),
            "gasUsed": receipt_result["receipt"].get("gasUsed") if receipt_result is not None else None,
            "effectiveGasPrice": receipt_result["receipt"].get("effectiveGasPrice") if receipt_result is not None else None,
            "decodedCall": _compact_call_evidence(item.get("decode")),
            "decodedEvents": matched_events,
            "logCount": len(decoded_logs),
            "matchedEventCount": len(matched_events),
            "notes": notes,
        })

    for receipt_result in receipt_results:
        if id(receipt_result) in matched_receipt_ids:
            continue
        matched_events = [_compact_log_evidence(log) for log in receipt_result["decodedLogs"] if _best_decode_match(log.get("decode"), event=True) is not None]
        evidence.append({
            "sourceType": "receipt-only",
            "transactionHash": receipt_result["receipt"].get("transactionHash"),
            "from": receipt_result["receipt"].get("from"),
            "to": receipt_result["receipt"].get("to"),
            "blockNumber": receipt_result["receipt"].get("blockNumber"),
            "chainId": None,
            "status": receipt_result["statusLabel"],
            "valueDecimal": None,
            "gas": None,
            "gasPrice": None,
            "gasUsed": receipt_result["receipt"].get("gasUsed"),
            "effectiveGasPrice": receipt_result["receipt"].get("effectiveGasPrice"),
            "decodedCall": None,
            "decodedEvents": matched_events,
            "logCount": len(receipt_result["decodedLogs"]),
            "matchedEventCount": len(matched_events),
            "notes": ["Receipt/log evidence exists without a matching transaction payload."],
        })

    return evidence


_ROUTE_CONFIDENCE_WEIGHTS = {
    "high": 3.0,
    "medium-high": 2.5,
    "medium": 2.0,
    "low-medium": 1.5,
    "low": 1.0,
}


def _build_route_evidence_report(
    evidence_records: list[dict[str, Any]],
    *,
    requested_operations: list[str] | None = None,
) -> dict[str, Any] | None:
    requested = [item.strip() for item in (requested_operations or []) if item and item.strip()]

    observed_calls: list[dict[str, Any]] = []
    seen_calls: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for record in evidence_records:
        call = record.get("decodedCall")
        if not isinstance(call, dict) or not call.get("docsName") or not call.get("signature"):
            continue
        observed = {
            "docsName": call.get("docsName"),
            "signature": call.get("signature"),
            "callAddress": call.get("callAddress"),
            "abiDecodeConfidence": call.get("confidence"),
            "notes": call.get("notes") or [],
            "transactionHash": _normalize_hash(record.get("transactionHash")),
            "sourceType": record.get("sourceType"),
            "status": record.get("status"),
        }
        key = _observed_call_key(observed)
        if key in seen_calls:
            continue
        seen_calls.add(key)
        observed_calls.append(observed)

    compared_operations = requested or route_operations()
    if not observed_calls and not requested:
        return None

    matched_keys: set[tuple[str | None, str | None, str | None, str | None]] = set()
    reports: list[dict[str, Any]] = []
    for operation in compared_operations:
        operation_model = route_operation_details(operation)
        hints = route_hints(operation)
        if not operation_model:
            if requested:
                reports.append({
                    "operation": operation,
                    "operationModel": None,
                    "status": "unknown-operation",
                    "hintCount": 0,
                    "matchedHintCount": 0,
                    "docsNameOnlyMatchCount": 0,
                    "coverageRatio": 0.0,
                    "matchedWeight": 0.0,
                    "totalWeight": 0.0,
                    "matchedHints": [],
                    "docsNameOnlyMatches": [],
                    "unmatchedHints": [],
                    "note": "No static route hints are currently defined for this operation.",
                })
            continue
        if not hints:
            reports.append({
                "operation": operation,
                "operationModel": operation_model,
                "status": "defined-without-static-hints",
                "hintCount": 0,
                "matchedHintCount": 0,
                "docsNameOnlyMatchCount": 0,
                "coverageRatio": 0.0,
                "matchedWeight": 0.0,
                "totalWeight": 0.0,
                "matchedHints": [],
                "docsNameOnlyMatches": [],
                "unmatchedHints": [],
                "note": "This Sigma operation is defined explicitly, but no static ABI hints are safe to claim yet.",
            })
            continue

        total_weight = sum(_route_confidence_weight(item.get("confidence")) for item in hints)
        matched_weight = 0.0
        matched_hints: list[dict[str, Any]] = []
        docs_name_only_matches: list[dict[str, Any]] = []
        unmatched_hints: list[dict[str, Any]] = []

        for hint in hints:
            candidate_functions = hint.get("candidateFunctions") or []
            exact_matches = [
                observed for observed in observed_calls
                if observed["docsName"] == hint.get("docsName")
                and (not candidate_functions or observed["signature"] in candidate_functions)
            ]
            docs_name_only = [
                observed for observed in observed_calls
                if observed["docsName"] == hint.get("docsName") and observed not in exact_matches
            ]

            if exact_matches:
                matched_weight += _route_confidence_weight(hint.get("confidence"))
                matched_hints.append({**hint, "observedCalls": exact_matches})
                for observed in exact_matches:
                    matched_keys.add(_observed_call_key(observed))
                continue

            if docs_name_only:
                docs_name_only_matches.append({**hint, "observedCalls": docs_name_only})
            unmatched_hints.append(hint)

        coverage_ratio = matched_weight / total_weight if total_weight else 0.0
        if matched_hints and not unmatched_hints:
            status = "capture-supports-current-hints"
        elif matched_hints:
            status = "partial-overlap"
        elif docs_name_only_matches:
            status = "contract-overlap-only"
        elif observed_calls:
            status = "no-observed-overlap"
        else:
            status = "no-decoded-calls"

        if requested or matched_hints or docs_name_only_matches:
            reports.append({
                "operation": operation,
                "operationModel": operation_model,
                "status": status,
                "hintCount": len(hints),
                "matchedHintCount": len(matched_hints),
                "docsNameOnlyMatchCount": len(docs_name_only_matches),
                "coverageRatio": round(coverage_ratio, 4),
                "matchedWeight": round(matched_weight, 2),
                "totalWeight": round(total_weight, 2),
                "matchedHints": matched_hints,
                "docsNameOnlyMatches": docs_name_only_matches,
                "unmatchedHints": unmatched_hints,
            })

    reports.sort(
        key=lambda item: (
            -item.get("matchedWeight", 0.0),
            -item.get("matchedHintCount", 0),
            -item.get("docsNameOnlyMatchCount", 0),
            item["operation"],
        )
    )
    unmapped_calls = [
        observed for observed in observed_calls
        if _observed_call_key(observed) not in matched_keys
    ]
    return {
        "status": "partial-routing-evidence",
        "basis": "Compares observed ABI-decoded calls against static Sigma route hints from the current ABI cache. It is not a trace or simulation.",
        "requestedOperations": requested or None,
        "requestedOperationModels": [route_operation_details(item) for item in requested] if requested else None,
        "comparedOperationCount": len(compared_operations),
        "observedCallCount": len(observed_calls),
        "observedCalls": observed_calls,
        "operations": reports,
        "unmappedObservedCalls": unmapped_calls,
    }


def _route_summary(route_report: dict[str, Any] | None) -> list[str]:
    if not route_report:
        return []
    lines = [
        f"routeEvidence partial: observed {route_report['observedCallCount']} decoded call(s) against {route_report['comparedOperationCount']} Sigma route-hint operation(s).",
    ]
    for item in route_report.get("operations", [])[:5]:
        coverage_pct = int(round(float(item.get("coverageRatio", 0.0)) * 100))
        label = ((item.get("operationModel") or {}).get("label")) or item["operation"]
        lines.append(
            f"route[{item['operation']}] {label}: {item['status']} with {item['matchedHintCount']}/{item['hintCount']} hinted surface(s) matched ({coverage_pct}% weighted coverage)."
        )
    unmapped = route_report.get("unmappedObservedCalls") or []
    if unmapped:
        lines.append(
            f"route gap: {len(unmapped)} observed decoded call(s) do not match the current route-hint set."
        )
    return lines


def _route_confidence_weight(value: Any) -> float:
    return _ROUTE_CONFIDENCE_WEIGHTS.get(str(value or "").strip().lower(), 1.0)


def _observed_call_key(observed: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None]:
    return (
        _normalize_hash(observed.get("transactionHash")),
        observed.get("sourceType"),
        observed.get("docsName"),
        observed.get("signature"),
    )


def _best_decode_match(decode: dict[str, Any] | None, *, event: bool = False) -> dict[str, Any] | None:
    if not decode or not decode.get("matches"):
        return None
    key = "decodedArgs"
    return next((match for match in decode["matches"] if match.get(key) is not None), decode["matches"][0])


def _compact_call_evidence(decode: dict[str, Any] | None) -> dict[str, Any] | None:
    best = _best_decode_match(decode)
    if best is None:
        return None
    return {
        "docsName": best.get("docsName"),
        "callAddress": best.get("callAddress"),
        "signature": best.get("signature"),
        "confidence": best.get("confidence"),
        "decodedArgs": best.get("decodedArgs"),
        "notes": best.get("notes"),
    }


def _compact_log_evidence(log_result: dict[str, Any]) -> dict[str, Any]:
    best = _best_decode_match(log_result.get("decode"), event=True)
    log = log_result.get("log", {})
    return {
        "address": log.get("address"),
        "transactionHash": log.get("transactionHash"),
        "logIndex": log.get("logIndex"),
        "topic0": log.get("topics", [None])[0],
        "eventSignature": best.get("eventSignature") if best else None,
        "docsName": best.get("docsName") if best else None,
        "callAddress": best.get("callAddress") if best else None,
        "confidence": best.get("confidence") if best else None,
        "decodedArgs": best.get("decodedArgs") if best else None,
    }


def _receipt_status_label(value: Any) -> str:
    parsed = _parse_intlike(value)
    if parsed is None:
        return "unknown"
    if parsed == 1:
        return "success"
    if parsed == 0:
        return "reverted"
    return str(parsed)


def short_hash(value: Any) -> str:
    normalized = _normalize_hash(value)
    if normalized is None:
        return "<unknown>"
    if len(normalized) <= 18:
        return normalized
    return f"{normalized[:10]}…{normalized[-8:]}"
