from __future__ import annotations

import json
import re
from shutil import copy2
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .abi import user_facing_views
from .config import get_settings
from .decode import decode_payload

_CAPTURED_RPC_METHODS = [
    "eth_sendTransaction",
    "eth_call",
    "eth_signTransaction",
    "wallet_sendCalls",
    "eth_sendRawTransaction",
]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "capture"


def capture_docs() -> dict[str, Any]:
    return {
        "mode": "operator-first capture",
        "steps": [
            "Record what the user is trying to do before touching calldata.",
            "Capture the named Sigma operation (for example open-long, stability-pool-redeem-normal, mint-open, or bnbusd-redeem), plus whether docs treat it as current, archived, or docs-only.",
            "Capture the target route surface (trade / earn / mint / docs-only), target contract if known, and wallet preview screenshots or text.",
            "Save raw transaction input or exported request payloads under raw/.",
            "Optionally run sigma capture import <session> <export.har|export.json> to normalize HAR/devtools exports into raw/imported/.",
            "Optionally run sigma capture browser-helper <session> to generate a browser-side JSON-RPC interceptor snippet.",
            "Run sigma decode on the captured calldata before treating any route as executable truth.",
            "If routing confidence is not high, keep the output in plan-only mode and do not generate execution calldata.",
        ],
        "expectedArtifacts": [
            "raw/*.json",
            "raw/imported/*.json",
            "decoded/*.json",
            "plans/*.json",
            "helpers/*",
            "notes.md",
        ],
        "warning": "Capture is for evidence collection and uncertainty reduction. It is not an execute command.",
    }


def capture_start(label: str, targets: list[str] | None = None) -> dict[str, Any]:
    settings = get_settings()
    settings.captures_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    session_name = f"{timestamp}-{_slugify(label)}"
    session_dir = settings.captures_dir / session_name
    raw_dir = session_dir / "raw"
    decoded_dir = session_dir / "decoded"
    plans_dir = session_dir / "plans"
    helpers_dir = session_dir / "helpers"
    raw_dir.mkdir(parents=True, exist_ok=False)
    decoded_dir.mkdir()
    plans_dir.mkdir()
    helpers_dir.mkdir()

    target_map = {view["docsName"].lower(): view for view in user_facing_views()}
    resolved_targets = []
    for target in targets or []:
        view = target_map.get(target.lower())
        if view:
            resolved_targets.append(
                {
                    "docsName": view["docsName"],
                    "callAddress": view["callAddress"],
                    "abiAddress": view["abiAddress"],
                }
            )
        else:
            resolved_targets.append({"query": target, "matched": False})

    intake = {
        "session": session_name,
        "label": label,
        "createdAtUtc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "protocol": "Sigma.Money",
        "network": {"name": "BNB Chain", "chainId": 56},
        "targets": resolved_targets,
        "status": "capture-started",
        "operatorMode": True,
        "executionReady": False,
        "notes": [
            "Add raw tx input or exported wallet payloads under raw/.",
            "Decode before trusting any medium-confidence route.",
            "Use helpers/ for browser-side interceptors or import aids.",
        ],
    }
    (session_dir / "intake.json").write_text(
        json.dumps(intake, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (session_dir / "capture-template.json").write_text(
        json.dumps(
            {
                "source": "wallet-preview | browser-export | manual-paste",
                "operation": "open-long | stability-pool-redeem-normal | mint-open | bnbusd-redeem",
                "route": "trade | earn | mint | docs-only",
                "routeStatus": "current | current-docs-disabled | archived | ambiguous",
                "to": "0x...",
                "input": "0x...",
                "txHash": None,
                "operatorNotes": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (session_dir / "notes.md").write_text(
        "# Notes\n\n- Objective:\n- Risk / ambiguity:\n- What still needs proof:\n",
        encoding="utf-8",
    )
    (session_dir / "README.md").write_text(
        "# Capture Session\n\n"
        f"- session: `{session_name}`\n"
        f"- label: `{label}`\n\n"
        "## What to put here\n\n"
        "- `raw/` — raw tx JSON, copied calldata, browser exports\n"
        "- `decoded/` — `sigma decode` outputs\n"
        "- `plans/` — `sigma plan` outputs\n"
        "- `helpers/` — browser capture snippets / import helpers\n"
        "- `notes.md` — operator observations and unresolved ambiguity\n\n"
        "## Safe workflow\n\n"
        "1. capture first\n"
        "2. optionally install the browser helper into the active Sigma tab\n"
        "3. decode second\n"
        "4. plan with confidence labels\n"
        "5. only then decide whether execution tooling is warranted\n",
        encoding="utf-8",
    )
    for directory in (raw_dir, decoded_dir, plans_dir, helpers_dir):
        (directory / ".gitkeep").write_text("", encoding="utf-8")

    return {
        "session": session_name,
        "path": str(session_dir),
        "created": [
            str(session_dir / "README.md"),
            str(session_dir / "intake.json"),
            str(session_dir / "capture-template.json"),
            str(session_dir / "notes.md"),
            str(raw_dir),
            str(decoded_dir),
            str(plans_dir),
            str(helpers_dir),
        ],
        "targets": resolved_targets,
        "nextSteps": [
            f"Drop raw tx material into {raw_dir}",
            f"Optionally run sigma capture import {session_dir} ./export.har",
            f"Optionally run sigma capture browser-helper {session_dir}",
            "Run sigma decode against the captured input",
            "Run sigma plan for the intended action and compare confidence vs evidence",
        ],
    }


def capture_browser_helper(session_ref: str, *, print_snippet: bool = False) -> dict[str, Any]:
    session_dir = _resolve_capture_session(session_ref)
    helpers_dir = session_dir / "helpers"
    helpers_dir.mkdir(parents=True, exist_ok=True)

    session_name = session_dir.name
    snippet = _browser_capture_snippet(session_name)
    script_path = helpers_dir / "sigma_browser_capture.js"
    guide_path = helpers_dir / "README-browser-capture.md"
    script_path.write_text(snippet, encoding="utf-8")
    guide_path.write_text(_browser_capture_guide(session_name), encoding="utf-8")

    payload: dict[str, Any] = {
        "session": session_name,
        "path": str(session_dir),
        "created": [str(script_path), str(guide_path)],
        "capturedRpcMethods": _CAPTURED_RPC_METHODS,
        "workflow": [
            f"Open the Sigma tab you want to inspect, then paste {script_path} into the page DevTools console.",
            "Reproduce the Sigma action until the wallet/request flow appears.",
            "Run window.__sigmaCapture.download() in that same page context to export a JSON artifact.",
            f"Move the downloaded JSON into {session_dir / 'raw'} and run sigma decode on it.",
        ],
        "limitations": [
            "The helper hooks fetch/XHR inside the page context; it cannot see extension-internal wallet traffic that never touches page JS.",
            "OpenClaw Browser Relay support is indirect: inject this snippet via the attached tab's console/evaluate path, then download/export from the browser.",
            "Responses are captured best-effort; binary bodies and cross-origin restrictions may limit what the page can read.",
        ],
    }
    if print_snippet:
        payload["script"] = snippet
    return payload


def capture_import(session_ref: str, artifact_path: str, *, prefix: str | None = None) -> dict[str, Any]:
    session_dir = _resolve_capture_session(session_ref)
    raw_dir = session_dir / "raw"
    helpers_dir = session_dir / "helpers"
    raw_dir.mkdir(parents=True, exist_ok=True)
    helpers_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(artifact_path).expanduser().resolve()
    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(source_path)

    payload = json.loads(source_path.read_text(encoding="utf-8"))
    detected_shape, entries = _extract_import_entries(payload)

    import_stem = _slugify(prefix or source_path.stem)
    raw_import_dir = raw_dir / "imported"
    raw_import_dir.mkdir(parents=True, exist_ok=True)
    helper_import_dir = helpers_dir / "imports"
    helper_import_dir.mkdir(parents=True, exist_ok=True)

    source_copy = helper_import_dir / f"{import_stem}.source{source_path.suffix.lower() or '.json'}"
    copy2(source_path, source_copy)

    guide_path = helpers_dir / "README-import.md"
    guide_path.write_text(_import_capture_guide(session_dir.name), encoding="utf-8")

    created = [str(source_copy), str(guide_path)]
    imported_entries: list[dict[str, Any]] = []
    skipped_entries: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        normalized = _normalize_import_entry(
            entry,
            source_path=source_path,
            import_kind=detected_shape,
            entry_index=index,
        )
        probe = decode_payload(normalized, source_name=f"{source_path.name}#{index}")
        signal_count = probe.get("transactionCount", 0) + probe.get("receiptCount", 0) + probe.get("logCount", 0)
        summary_entry = {
            "entryIndex": index,
            "requestUrl": normalized.get("import", {}).get("requestUrl"),
            "requestMethod": normalized.get("import", {}).get("requestMethod"),
            "responseStatus": normalized.get("import", {}).get("responseStatus"),
            "transactionCount": probe.get("transactionCount", 0),
            "receiptCount": probe.get("receiptCount", 0),
            "logCount": probe.get("logCount", 0),
        }
        if signal_count <= 0:
            skipped_entries.append(summary_entry)
            continue

        output_path = raw_import_dir / f"{import_stem}__entry-{index:03d}.json"
        output_path.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        created.append(str(output_path))
        imported_entries.append({**summary_entry, "outputPath": str(output_path)})

    payload_summary = {
        "session": session_dir.name,
        "path": str(session_dir),
        "sourceArtifact": str(source_path),
        "sourceCopy": str(source_copy),
        "detectedShape": detected_shape,
        "entryCount": len(entries),
        "importedEntryCount": len(imported_entries),
        "skippedEntryCount": len(skipped_entries),
        "importedEntries": imported_entries,
        "skippedEntries": skipped_entries,
        "created": created,
        "workflow": [
            f"Run sigma decode {session_dir}",
            f"Or batch only the normalized imports with sigma decode --capture-dir {raw_import_dir}",
            "Use --route-operation on decode if you want a route-evidence comparison against known Sigma hints.",
        ],
    }
    summary_path = helper_import_dir / f"{import_stem}__import-summary.json"
    summary_path.write_text(json.dumps(payload_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload_summary["created"].append(str(summary_path))
    return payload_summary


def _import_capture_guide(session_name: str) -> str:
    return (
        "# Import Helper\n\n"
        f"- session: `{session_name}`\n\n"
        "## Accepted source shapes\n\n"
        "- HAR exports with `log.entries[].request.postData.text` and optional `response.content.text`\n"
        "- DevTools/network exports with top-level `entries[]`\n"
        "- Single request/response bundles with `request`, `response`, `requestBody`, or `responseBody` fields\n\n"
        "## Workflow\n\n"
        "1. Save the browser export as `.har` or `.json`.\n"
        f"2. Run `sigma capture import {session_name} ./export.har`.\n"
        "3. Review the normalized files under `raw/imported/`.\n"
        f"4. Run `sigma decode {session_name}` or `sigma decode --capture-dir captures/{session_name}/raw/imported`.\n"
    )


def _extract_import_entries(payload: Any) -> tuple[str, list[dict[str, Any]]]:
    if isinstance(payload, dict):
        har_log = payload.get("log")
        if isinstance(har_log, dict) and isinstance(har_log.get("entries"), list):
            return "har", [item for item in har_log["entries"] if isinstance(item, dict)]

        entries = payload.get("entries")
        if isinstance(entries, list):
            return "devtools-entries", [item for item in entries if isinstance(item, dict)]

        return "single-export", [payload]

    if isinstance(payload, list):
        dict_entries = [item for item in payload if isinstance(item, dict)]
        if dict_entries:
            return "devtools-list", dict_entries

    raise ValueError("Import helper expects a JSON object or array exported from HAR/devtools.")


def _normalize_import_entry(
    entry: dict[str, Any],
    *,
    source_path: Path,
    import_kind: str,
    entry_index: int,
) -> dict[str, Any]:
    request_block = _select_request_block(entry)
    response_block = _select_response_block(entry)
    normalized: dict[str, Any] = {
        "import": {
            "kind": import_kind,
            "entryIndex": entry_index,
            "sourceArtifact": str(source_path),
            "sourceName": source_path.name,
            "requestUrl": (request_block or {}).get("url"),
            "requestMethod": (request_block or {}).get("method"),
            "responseStatus": (response_block or {}).get("status"),
            "startedDateTime": entry.get("startedDateTime") or entry.get("capturedAt"),
        }
    }
    if request_block is not None:
        normalized["request"] = request_block
    if response_block is not None:
        normalized["response"] = response_block

    request_body = _extract_body_text(request_block)
    response_body = _extract_body_text(response_block)
    if request_body is not None and request_block is None:
        normalized["requestBody"] = request_body
    if response_body is not None and response_block is None:
        normalized["responseBody"] = response_body
    return normalized


def _select_request_block(entry: dict[str, Any]) -> dict[str, Any] | None:
    request = entry.get("request")
    if isinstance(request, dict):
        return request

    request_like = {
        key: entry.get(key)
        for key in ("url", "method", "postData", "requestBody", "body", "headers")
        if entry.get(key) is not None
    }
    return request_like or None


def _select_response_block(entry: dict[str, Any]) -> dict[str, Any] | None:
    response = entry.get("response")
    if isinstance(response, dict):
        return response

    response_like = {
        key: entry.get(key)
        for key in ("status", "content", "responseBody", "body", "headers")
        if entry.get(key) is not None
    }
    return response_like or None


def _extract_body_text(payload: Any) -> str | None:
    if payload is None:
        return None
    if isinstance(payload, str):
        stripped = payload.strip()
        return stripped or None
    if isinstance(payload, dict):
        for key in ("text", "body", "requestBody", "responseBody"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        for key in ("postData", "content", "payload"):
            nested = payload.get(key)
            text = _extract_body_text(nested)
            if text is not None:
                return text
    return None


def _resolve_capture_session(session_ref: str) -> Path:
    settings = get_settings()
    direct = Path(session_ref).expanduser()
    candidates = []
    if direct.exists() and direct.is_dir():
        candidates.append(direct.resolve())
    named = settings.captures_dir / session_ref
    if named.exists() and named.is_dir():
        candidates.append(named.resolve())
    if not candidates:
        raise FileNotFoundError(
            f"Capture session not found: {session_ref}. Use an absolute path or a directory name under {settings.captures_dir}."
        )
    return candidates[0]


def _browser_capture_snippet(session_name: str) -> str:
    safe_session = session_name.replace("\\", "\\\\").replace("`", "\\`")
    methods_json = json.dumps(_CAPTURED_RPC_METHODS)
    return f"""(() => {{
  const SESSION = `{safe_session}`;
  const RPC_METHODS = {methods_json};
  if (window.__sigmaCapture && window.__sigmaCapture.installed) {{
    console.info(`[sigma-capture] already installed for ${{window.__sigmaCapture.session}}`);
    return window.__sigmaCapture;
  }}

  const state = {{
    installed: true,
    session: SESSION,
    installedAt: new Date().toISOString(),
    entries: [],
    rpcMethods: RPC_METHODS.slice(),
    version: 1,
  }};

  const parseMaybeJson = (value) => {{
    if (typeof value !== 'string') return value ?? null;
    const trimmed = value.trim();
    if (!trimmed) return null;
    try {{
      return JSON.parse(trimmed);
    }} catch (_error) {{
      return value;
    }}
  }};

  const payloadHasInterestingMethod = (payload) => {{
    if (!payload) return false;
    const items = Array.isArray(payload) ? payload : [payload];
    return items.some((item) => item && typeof item === 'object' && RPC_METHODS.includes(item.method));
  }};

  const sanitizeBody = (value) => parseMaybeJson(typeof value === 'string' ? value : value ?? null);

  const record = (entry) => {{
    const requestPayload = sanitizeBody(entry.requestBody);
    const responsePayload = sanitizeBody(entry.responseBody);
    if (!payloadHasInterestingMethod(requestPayload) && !payloadHasInterestingMethod(responsePayload)) {{
      return null;
    }}
    const captured = {{
      capturedAt: new Date().toISOString(),
      session: SESSION,
      transport: entry.transport,
      url: entry.url || location.href,
      method: entry.method || 'UNKNOWN',
      request: {{ body: requestPayload }},
      response: {{ status: entry.status ?? null, body: responsePayload }},
      page: {{ href: location.href, title: document.title }},
      userAgent: navigator.userAgent,
    }};
    state.entries.push(captured);
    console.info('[sigma-capture] captured RPC payload', captured);
    return captured;
  }};

  window.__sigmaCapture = Object.assign(state, {{
    clear() {{
      state.entries.length = 0;
      console.info(`[sigma-capture] cleared entries for ${{SESSION}}`);
    }},
    summary() {{
      return {{ session: SESSION, entryCount: state.entries.length, lastEntry: state.entries[state.entries.length - 1] || null }};
    }},
    toJSONBundle() {{
      return {{
        session: SESSION,
        exportedAt: new Date().toISOString(),
        location: location.href,
        entries: state.entries.slice(),
      }};
    }},
    download(filename) {{
      const bundle = JSON.stringify(this.toJSONBundle(), null, 2);
      const blob = new Blob([bundle], {{ type: 'application/json' }});
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = filename || `sigma-browser-capture-${{SESSION}}-${{new Date().toISOString().replace(/[:.]/g, '-')}}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
      console.info(`[sigma-capture] downloaded ${{state.entries.length}} entries`);
      return state.entries.length;
    }},
  }});

  const originalFetch = window.fetch.bind(window);
  window.fetch = async function(input, init) {{
    const requestUrl = typeof input === 'string' ? input : input?.url;
    const requestMethod = init?.method || (typeof input !== 'string' ? input?.method : undefined) || 'GET';
    const requestBody = init?.body;
    const response = await originalFetch(input, init);
    try {{
      const responseText = await response.clone().text();
      record({{ transport: 'fetch', url: requestUrl, method: requestMethod, requestBody, responseBody: responseText, status: response.status }});
    }} catch (error) {{
      console.warn('[sigma-capture] fetch response capture failed', error);
    }}
    return response;
  }};

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(method, url) {{
    this.__sigmaCaptureMeta = {{ method, url }};
    return originalOpen.apply(this, arguments);
  }};
  XMLHttpRequest.prototype.send = function(body) {{
    const meta = this.__sigmaCaptureMeta || {{}};
    this.addEventListener('loadend', () => {{
      try {{
        record({{ transport: 'xhr', url: meta.url, method: meta.method, requestBody: body, responseBody: this.responseText, status: this.status }});
      }} catch (error) {{
        console.warn('[sigma-capture] xhr response capture failed', error);
      }}
    }}, {{ once: true }});
    return originalSend.apply(this, arguments);
  }};

  console.info(`[sigma-capture] installed for session ${{SESSION}}. Reproduce the Sigma action, then run window.__sigmaCapture.download().`);
  return window.__sigmaCapture;
}})();
"""


def _browser_capture_guide(session_name: str) -> str:
    return (
        "# Browser Capture Helper\n\n"
        f"Session: `{session_name}`\n\n"
        "## Standard browser workflow\n\n"
        "1. Open the Sigma page you want to inspect.\n"
        "2. Open DevTools on that page.\n"
        "3. Paste the contents of `sigma_browser_capture.js` into the page console and press Enter.\n"
        "4. Reproduce the Sigma action until the wallet / RPC flow fires.\n"
        "5. Run `window.__sigmaCapture.download()` in the same page context.\n"
        "6. Move the downloaded JSON into `raw/` and run `sigma decode --tx-json <file>`.\n\n"
        "## OpenClaw Browser Relay workflow (indirect)\n\n"
        "1. Attach the target tab with Browser Relay.\n"
        "2. Inject the helper through the attached page's console/evaluate path.\n"
        "3. Reproduce the action in-browser.\n"
        "4. Call `window.__sigmaCapture.download()` (or inspect `window.__sigmaCapture.summary()`) from that same attached page context.\n"
        "5. Import the downloaded JSON into this capture session's `raw/` directory.\n\n"
        "## What it captures\n\n"
        f"- JSON-RPC methods: {', '.join(_CAPTURED_RPC_METHODS)}\n"
        "- fetch/XHR request bodies and best-effort JSON responses visible from the page context\n"
        "- page URL/title for operator evidence\n\n"
        "## Limitations\n\n"
        "- It does not magically see extension-only traffic that bypasses page JS hooks.\n"
        "- If the wallet signs via a privileged browser extension path, capture the wallet preview manually too.\n"
        "- Some responses may be unreadable if the browser blocks page access to them.\n"
    )
