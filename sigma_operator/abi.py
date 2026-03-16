from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import get_settings, ensure_paths
from .operations import route_operation_details as _route_operation_details
from .operations import route_operation_hints as _route_operation_hints
from .operations import route_operations as _route_operations

MASK64 = (1 << 64) - 1
ROTATION_OFFSETS = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]
ROUND_CONSTANTS = [
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
]


@dataclass(frozen=True)
class TypeDesc:
    name: str
    base: str
    array_dims: tuple[int | None, ...]
    components: tuple["TypeDesc", ...] = ()


class DecodeError(ValueError):
    pass


def normalize_address(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if value.startswith("0x") and len(value) == 42:
        return value.lower()
    return value.lower()


def get_abi_dir(abi_dir: str | Path | None = None) -> Path:
    if abi_dir is not None:
        return Path(abi_dir).expanduser().resolve()
    settings = get_settings()
    ensure_paths(settings)
    return settings.abi_dir


def load_manifest(abi_dir: str | Path | None = None) -> dict[str, Any]:
    path = get_abi_dir(abi_dir) / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_entries(abi_dir: str | Path | None = None) -> list[dict[str, Any]]:
    base = get_abi_dir(abi_dir)
    manifest = load_manifest(base)
    entries = []
    for file_info in manifest.get("files", []):
        path = base / file_info["file"]
        entries.append(json.loads(path.read_text(encoding="utf-8")))
    return entries


def _format_type(param: dict[str, Any]) -> str:
    typ = param.get("type", "")
    if typ.startswith("tuple"):
        suffix = typ[len("tuple"):]
        inner = ",".join(_format_type(component) for component in param.get("components", []))
        return f"({inner}){suffix}"
    return typ


def signature_for_abi_item(item: dict[str, Any]) -> str | None:
    if item.get("type") != "function":
        return None
    args = ",".join(_format_type(param) for param in item.get("inputs", []))
    return f"{item.get('name', '')}({args})"


def event_signature_for_abi_item(item: dict[str, Any]) -> str | None:
    if item.get("type") != "event":
        return None
    args = ",".join(_format_type(param) for param in item.get("inputs", []))
    return f"{item.get('name', '')}({args})"


def _rotl64(value: int, shift: int) -> int:
    shift %= 64
    return ((value << shift) | (value >> (64 - shift))) & MASK64


def keccak256(data: bytes) -> bytes:
    rate = 136
    state = [0] * 25
    padded = bytearray(data)
    padded.append(0x01)
    while len(padded) % rate != rate - 1:
        padded.append(0)
    padded.append(0x80)

    for start in range(0, len(padded), rate):
        block = padded[start:start + rate]
        for lane_index in range(rate // 8):
            lane = int.from_bytes(block[lane_index * 8:(lane_index + 1) * 8], "little")
            state[lane_index] ^= lane
        _keccak_f1600(state)

    out = bytearray()
    while len(out) < 32:
        for lane_index in range(rate // 8):
            out.extend(state[lane_index].to_bytes(8, "little"))
        if len(out) >= 32:
            break
        _keccak_f1600(state)
    return bytes(out[:32])


def _keccak_f1600(state: list[int]) -> None:
    for rc in ROUND_CONSTANTS:
        c = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rotl64(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= d[x]

        b = [0] * 25
        for x in range(5):
            for y in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rotl64(state[x + 5 * y], ROTATION_OFFSETS[x][y])

        for x in range(5):
            for y in range(5):
                state[x + 5 * y] = b[x + 5 * y] ^ ((~b[(x + 1) % 5 + 5 * y]) & b[(x + 2) % 5 + 5 * y])
                state[x + 5 * y] &= MASK64

        state[0] ^= rc


def selector_for_signature(signature: str) -> str:
    return "0x" + keccak256(signature.encode("utf-8"))[:4].hex()


def topic0_for_signature(signature: str) -> str:
    return "0x" + keccak256(signature.encode("utf-8")).hex()


def manifest_summary(abi_dir: str | Path | None = None) -> dict[str, Any]:
    manifest = load_manifest(abi_dir)
    return {
        "generatedAtUtc": manifest.get("generatedAtUtc"),
        "publishedContracts": len(manifest.get("publishedContracts", [])),
        "implementationContracts": len(manifest.get("implementationContracts", [])),
        "unresolvedPublishedContracts": len(manifest.get("unresolvedPublishedContracts", [])),
        "abiDir": str(get_abi_dir(abi_dir)),
    }


def _index_entries(entries: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(entry["docsName"], entry["role"]): entry for entry in entries}


def user_facing_views(abi_dir: str | Path | None = None) -> list[dict[str, Any]]:
    entries = load_entries(abi_dir)
    index = _index_entries(entries)
    docs_names = sorted({entry["docsName"] for entry in entries})
    views = []
    for docs_name in docs_names:
        published = index.get((docs_name, "published"))
        implementation = index.get((docs_name, "implementation"))
        abi_entry = implementation or published
        if not published or not abi_entry:
            continue
        abi_items = [item for item in abi_entry.get("abi", []) if item.get("type") in {"function", "event"}]
        views.append({
            "docsName": docs_name,
            "callAddress": published["address"],
            "abiAddress": abi_entry["address"],
            "publishedAddress": published["address"],
            "implementationAddress": implementation["address"] if implementation else None,
            "contractName": abi_entry.get("contractName"),
            "isProxy": implementation is not None,
            "verified": abi_entry.get("verified"),
            "sourceKind": abi_entry.get("sourceKind"),
            "abi": abi_items,
            "functionSignatures": [
                signature for signature in (signature_for_abi_item(item) for item in abi_items) if signature
            ],
            "eventSignatures": [
                signature for signature in (event_signature_for_abi_item(item) for item in abi_items) if signature
            ],
        })
    return views


def selector_candidates(abi_dir: str | Path | None = None) -> list[dict[str, Any]]:
    out = []
    for view in user_facing_views(abi_dir):
        for item in view["abi"]:
            if item.get("type") != "function":
                continue
            signature = signature_for_abi_item(item)
            if not signature:
                continue
            out.append({
                "docsName": view["docsName"],
                "callAddress": view["callAddress"],
                "abiAddress": view["abiAddress"],
                "publishedAddress": view["publishedAddress"],
                "implementationAddress": view["implementationAddress"],
                "contractName": view["contractName"],
                "isProxy": view["isProxy"],
                "signature": signature,
                "selector": selector_for_signature(signature),
                "inputs": item.get("inputs", []),
                "stateMutability": item.get("stateMutability"),
            })
    return out


def event_candidates(abi_dir: str | Path | None = None) -> list[dict[str, Any]]:
    out = []
    for view in user_facing_views(abi_dir):
        for item in view["abi"]:
            if item.get("type") != "event":
                continue
            signature = event_signature_for_abi_item(item)
            if not signature:
                continue
            out.append({
                "docsName": view["docsName"],
                "callAddress": view["callAddress"],
                "abiAddress": view["abiAddress"],
                "publishedAddress": view["publishedAddress"],
                "implementationAddress": view["implementationAddress"],
                "contractName": view["contractName"],
                "isProxy": view["isProxy"],
                "eventSignature": signature,
                "eventName": item.get("name"),
                "topic0": topic0_for_signature(signature),
                "inputs": item.get("inputs", []),
                "anonymous": item.get("anonymous", False),
            })
    return out


def inspect_contract(query: str | None, abi_dir: str | Path | None = None) -> dict[str, Any]:
    if not query:
        return manifest_summary(abi_dir)

    entries = load_entries(abi_dir)
    normalized = normalize_address(query)
    matched_docs_name = None
    if normalized and normalized.startswith("0x") and len(normalized) == 42:
        for entry in entries:
            if normalize_address(entry.get("address")) == normalized:
                matched_docs_name = entry["docsName"]
                break
    else:
        for entry in entries:
            if entry["docsName"].lower() == query.lower():
                matched_docs_name = entry["docsName"]
                break

    if matched_docs_name is None:
        return {
            "query": query,
            "found": False,
            "knownDocsNames": sorted({entry["docsName"] for entry in entries}),
        }

    payload: dict[str, Any] = {"query": query, "docsName": matched_docs_name, "found": True}
    for role in ("published", "implementation"):
        current = next((entry for entry in entries if entry["docsName"] == matched_docs_name and entry["role"] == role), None)
        if current:
            payload[role] = {
                "address": current["address"],
                "contractName": current.get("contractName"),
                "verified": current.get("verified"),
                "sourceKind": current.get("sourceKind"),
                "functionSignatures": [
                    sig for sig in (signature_for_abi_item(item) for item in current.get("abi", [])) if sig
                ],
                "eventSignatures": [
                    sig for sig in (event_signature_for_abi_item(item) for item in current.get("abi", [])) if sig
                ],
            }
    return payload


def parse_type(param: dict[str, Any]) -> TypeDesc:
    raw_type = param.get("type", "")
    name = param.get("name", "")
    dims: list[int | None] = []
    while raw_type.endswith("]"):
        start = raw_type.rfind("[")
        dim_text = raw_type[start + 1:-1]
        dims.append(int(dim_text) if dim_text else None)
        raw_type = raw_type[:start]
    components = tuple(parse_type(component) for component in param.get("components", []))
    return TypeDesc(name=name, base=raw_type, array_dims=tuple(dims), components=components)


def is_dynamic(desc: TypeDesc) -> bool:
    if desc.array_dims:
        inner = TypeDesc(name=desc.name, base=desc.base, array_dims=desc.array_dims[1:], components=desc.components)
        return desc.array_dims[0] is None or is_dynamic(inner)
    if desc.base == "bytes":
        return True
    if desc.base == "string":
        return True
    if desc.base == "tuple":
        return any(is_dynamic(component) for component in desc.components)
    return False


def static_size(desc: TypeDesc) -> int:
    if is_dynamic(desc):
        raise DecodeError(f"Type is dynamic: {desc}")
    if desc.array_dims:
        length = desc.array_dims[0]
        assert length is not None
        inner = TypeDesc(name=desc.name, base=desc.base, array_dims=desc.array_dims[1:], components=desc.components)
        return length * static_size(inner)
    if desc.base == "tuple":
        return sum(static_size(component) for component in desc.components)
    return 32


def decode_calldata(calldata_hex: str, target_address: str | None = None, abi_dir: str | Path | None = None) -> dict[str, Any]:
    calldata_hex = calldata_hex.strip()
    if calldata_hex.startswith("0x"):
        calldata_hex = calldata_hex[2:]
    if len(calldata_hex) < 8:
        raise DecodeError("Calldata must include at least a 4-byte selector")
    if len(calldata_hex) % 2 != 0:
        raise DecodeError("Hex string must have an even number of characters")

    raw = bytes.fromhex(calldata_hex)
    selector = "0x" + raw[:4].hex()
    args = raw[4:]
    normalized_target = normalize_address(target_address)

    candidates = [item for item in selector_candidates(abi_dir) if item["selector"] == selector]
    if normalized_target:
        narrowed = []
        for item in candidates:
            addresses = {
                normalize_address(item.get("callAddress")),
                normalize_address(item.get("abiAddress")),
                normalize_address(item.get("publishedAddress")),
                normalize_address(item.get("implementationAddress")),
            }
            if normalized_target in addresses:
                narrowed.append(item)
        candidates = narrowed or candidates

    decoded_matches = []
    for item in candidates:
        try:
            decoded_args = decode_arguments(item.get("inputs", []), args)
            error = None
        except Exception as exc:  # noqa: BLE001 - preserve partial operator evidence instead of aborting all matches
            decoded_args = None
            error = str(exc)
        decoded_matches.append({
            **{
                k: item[k]
                for k in (
                    "docsName",
                    "callAddress",
                    "abiAddress",
                    "publishedAddress",
                    "implementationAddress",
                    "contractName",
                    "isProxy",
                    "signature",
                    "selector",
                    "stateMutability",
                )
            },
            "confidence": _decode_confidence(normalized_target, len(candidates), error is None),
            "decodedArgs": decoded_args,
            "decodeError": error,
            "notes": _decode_notes(item, normalized_target),
        })

    return {
        "input": "0x" + calldata_hex,
        "selector": selector,
        "targetAddress": target_address,
        "matchCount": len(decoded_matches),
        "executionReady": False,
        "matches": decoded_matches,
        "warning": "Decoded calldata is evidence for operator review, not proof of the exact current Sigma frontend routing path.",
    }


def decode_event_log(log: dict[str, Any], target_address: str | None = None, abi_dir: str | Path | None = None) -> dict[str, Any]:
    topics = [topic for topic in (log.get("topics") or []) if topic]
    if not topics:
        raise DecodeError("Event log must include at least topic0")

    topic0 = topics[0].lower()
    data_hex = (log.get("data") or "0x").strip()
    if data_hex.startswith("0x"):
        data_hex = data_hex[2:]
    if len(data_hex) % 2 != 0:
        raise DecodeError("Event log data hex must have an even number of characters")
    data = bytes.fromhex(data_hex) if data_hex else b""

    normalized_target = normalize_address(target_address or log.get("address"))
    candidates = [item for item in event_candidates(abi_dir) if item["topic0"].lower() == topic0]
    if normalized_target:
        narrowed = []
        for item in candidates:
            addresses = {
                normalize_address(item.get("callAddress")),
                normalize_address(item.get("abiAddress")),
                normalize_address(item.get("publishedAddress")),
                normalize_address(item.get("implementationAddress")),
            }
            if normalized_target in addresses:
                narrowed.append(item)
        candidates = narrowed or candidates

    decoded_matches = []
    for item in candidates:
        try:
            decoded_args = _decode_event_inputs(item.get("inputs", []), topics[1:], data)
            error = None
        except Exception as exc:  # noqa: BLE001 - keep other candidate matches alive
            decoded_args = None
            error = str(exc)
        decoded_matches.append({
            **{
                k: item[k]
                for k in (
                    "docsName",
                    "callAddress",
                    "abiAddress",
                    "publishedAddress",
                    "implementationAddress",
                    "contractName",
                    "isProxy",
                    "eventSignature",
                    "eventName",
                    "topic0",
                    "anonymous",
                )
            },
            "confidence": _decode_confidence(normalized_target, len(candidates), error is None),
            "decodedArgs": decoded_args,
            "decodeError": error,
            "notes": _decode_event_notes(item, normalized_target),
        })

    return {
        "address": log.get("address"),
        "topic0": topic0,
        "targetAddress": target_address or log.get("address"),
        "matchCount": len(decoded_matches),
        "matches": decoded_matches,
        "warning": "Event-log decode is first-pass evidence. Indexed dynamic/complex values remain hashes without additional context.",
    }


def _decode_confidence(target_address: str | None, candidate_count: int, success: bool) -> str:
    if not success:
        return "low"
    if target_address and candidate_count == 1:
        return "high"
    if candidate_count == 1:
        return "medium-high"
    if target_address:
        return "medium"
    return "low-medium"


def _decode_notes(item: dict[str, Any], target_address: str | None) -> list[str]:
    notes = []
    if item.get("isProxy"):
        notes.append("User-facing call address is the published proxy; ABI came from the current implementation cache.")
    if not target_address:
        notes.append("No target address was supplied, so selector matching may still be ambiguous across contracts.")
    return notes


def _decode_event_notes(item: dict[str, Any], target_address: str | None) -> list[str]:
    notes = []
    if item.get("isProxy"):
        notes.append("User-facing log address is the published proxy; event ABI came from the current implementation cache.")
    if not target_address:
        notes.append("No emitting contract address was supplied, so topic0 matching may still be ambiguous across contracts.")
    notes.append("Indexed dynamic values are hashed per ABI rules and cannot be reconstructed from topics alone.")
    return notes


def decode_arguments(inputs: list[dict[str, Any]], data: bytes) -> list[dict[str, Any]]:
    descs = [parse_type(item) for item in inputs]
    head_size = sum(32 if is_dynamic(desc) else static_size(desc) for desc in descs)
    if len(data) < head_size:
        raise DecodeError("Calldata shorter than ABI head section")

    out = []
    cursor = 0
    for raw_param, desc in zip(inputs, descs, strict=False):
        if is_dynamic(desc):
            rel = _read_uint(data, cursor)
            value = _decode_value(desc, data, rel)
            cursor += 32
        else:
            value = _decode_value(desc, data, cursor)
            cursor += static_size(desc)
        out.append({
            "name": raw_param.get("name") or "(unnamed)",
            "type": raw_param.get("type"),
            "value": value,
        })
    return out


def _decode_event_inputs(inputs: list[dict[str, Any]], indexed_topics: list[str], data: bytes) -> list[dict[str, Any]]:
    indexed_inputs = [item for item in inputs if item.get("indexed")]
    non_indexed_inputs = [item for item in inputs if not item.get("indexed")]
    if len(indexed_topics) < len(indexed_inputs):
        raise DecodeError("Event log has fewer indexed topics than the ABI expects")

    indexed_values = [_decode_indexed_event_value(item, indexed_topics[index]) for index, item in enumerate(indexed_inputs)]
    non_indexed_values = decode_arguments(non_indexed_inputs, data) if non_indexed_inputs else []

    out = []
    indexed_cursor = 0
    non_indexed_cursor = 0
    for item in inputs:
        if item.get("indexed"):
            current = indexed_values[indexed_cursor]
            indexed_cursor += 1
        else:
            current = non_indexed_values[non_indexed_cursor]
            non_indexed_cursor += 1
        out.append({
            "name": item.get("name") or current.get("name") or "(unnamed)",
            "type": item.get("type"),
            "indexed": bool(item.get("indexed")),
            "value": current.get("value"),
            **({"valueEncoding": current["valueEncoding"]} if "valueEncoding" in current else {}),
        })
    return out


def _decode_indexed_event_value(item: dict[str, Any], topic_hex: str) -> dict[str, Any]:
    normalized = topic_hex.strip()
    if normalized.startswith("0x"):
        normalized = normalized[2:]
    if len(normalized) != 64:
        raise DecodeError("Indexed event topic must be exactly 32 bytes")

    desc = parse_type(item)
    if _indexed_value_is_hashed(desc):
        return {
            "name": item.get("name") or "(unnamed)",
            "value": "0x" + normalized,
            "valueEncoding": "topic-hash",
        }

    raw = bytes.fromhex(normalized)
    return {
        "name": item.get("name") or "(unnamed)",
        "value": _decode_value(desc, raw, 0),
        "valueEncoding": "topic-word",
    }


def _indexed_value_is_hashed(desc: TypeDesc) -> bool:
    if desc.array_dims:
        return True
    if desc.base == "tuple":
        return True
    if is_dynamic(desc):
        return True
    if desc.base.startswith("bytes") and desc.base != "bytes":
        return False
    return static_size(desc) != 32


def _read_word(data: bytes, start: int) -> bytes:
    end = start + 32
    if start < 0 or end > len(data):
        raise DecodeError(f"Out-of-bounds word read at offset {start}")
    return data[start:end]


def _read_uint(data: bytes, start: int) -> int:
    return int.from_bytes(_read_word(data, start), "big")


def _decode_value(desc: TypeDesc, data: bytes, start: int) -> Any:
    if desc.array_dims:
        inner = TypeDesc(name=desc.name, base=desc.base, array_dims=desc.array_dims[1:], components=desc.components)
        length = desc.array_dims[0]
        if length is None:
            count = _read_uint(data, start)
            content_start = start + 32
            if is_dynamic(inner):
                return [
                    _decode_value(inner, data, content_start + _read_uint(data, content_start + i * 32))
                    for i in range(count)
                ]
            step = static_size(inner)
            return [_decode_value(inner, data, content_start + i * step) for i in range(count)]
        if is_dynamic(inner):
            return [
                _decode_value(inner, data, start + _read_uint(data, start + i * 32))
                for i in range(length)
            ]
        step = static_size(inner)
        return [_decode_value(inner, data, start + i * step) for i in range(length)]

    if desc.base == "tuple":
        values = []
        cursor = start
        for component in desc.components:
            if is_dynamic(component):
                rel = _read_uint(data, cursor)
                values.append(_decode_value(component, data, start + rel))
                cursor += 32
            else:
                values.append(_decode_value(component, data, cursor))
                cursor += static_size(component)
        names = [component.name for component in desc.components]
        if all(names) and len(set(names)) == len(names):
            return {name: value for name, value in zip(names, values, strict=False)}
        return values

    word = _read_word(data, start)

    if desc.base == "address":
        return "0x" + word[-20:].hex()
    if desc.base == "bool":
        return bool(int.from_bytes(word, "big"))
    if desc.base.startswith("uint"):
        return int.from_bytes(word, "big")
    if desc.base.startswith("int"):
        value = int.from_bytes(word, "big")
        bits = int(desc.base[3:] or "256")
        if value >= 1 << (bits - 1):
            value -= 1 << bits
        return value
    if desc.base == "string":
        raw = _decode_dynamic_bytes(data, start)
        return raw.decode("utf-8", errors="replace")
    if desc.base == "bytes":
        return "0x" + _decode_dynamic_bytes(data, start).hex()
    if desc.base.startswith("bytes") and desc.base != "bytes":
        size = int(desc.base[5:])
        return "0x" + word[:size].hex()

    raise DecodeError(f"Unsupported Solidity type: {desc.base}")


def _decode_dynamic_bytes(data: bytes, start: int) -> bytes:
    length = _read_uint(data, start)
    data_start = start + 32
    data_end = data_start + length
    if data_end > len(data):
        raise DecodeError(f"Out-of-bounds dynamic bytes read at offset {start}")
    return data[data_start:data_end]


def route_operations() -> list[str]:
    return _route_operations()


def route_operation_details(operation: str) -> dict[str, Any] | None:
    return _route_operation_details(operation)


def route_hints(operation: str, abi_dir: str | Path | None = None) -> list[dict[str, Any]]:
    by_name = {item["docsName"]: item for item in user_facing_views(abi_dir)}
    out = []
    for spec in _route_operation_hints(operation):
        view = by_name.get(spec["docsName"])
        if not view:
            continue
        signatures = [
            sig for sig in view["functionSignatures"]
            if any(token in sig for token in spec.get("contains", ()))
        ]
        out.append({
            "docsName": view["docsName"],
            "callAddress": view["callAddress"],
            "abiAddress": view["abiAddress"],
            "confidence": spec["confidence"],
            "reason": spec["reason"],
            "candidateFunctions": signatures,
        })
    return out
