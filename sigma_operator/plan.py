from __future__ import annotations

from typing import Any

from .abi import route_hints, route_operation_details
from .operations import build_operation_plan


def build_plan(operation: str, forwarded_args: list[str]) -> dict[str, Any]:
    payload = build_operation_plan(operation, forwarded_args)
    operation_model = payload.get("operationModel") or route_operation_details(operation)
    if operation_model:
        payload["operationModel"] = operation_model
    payload["operatorMode"] = "plan-only"
    payload["executionReady"] = False
    payload["routingHints"] = route_hints(operation)

    next_steps: list[str] = []
    if operation_model:
        entrypoint = operation_model.get("entrypoint") or {}
        if entrypoint.get("kind") == "archived-app":
            next_steps.append("Treat this as an archived/legacy Sigma flow until a current wallet preview or tx capture proves the route still exists.")
        elif entrypoint.get("kind") == "docs-only":
            next_steps.append("Treat this as docs-only guidance for now; do not claim a live app route until a real capture proves it.")
        elif operation_model.get("docsStatus") == "current-docs-disabled-upgrade":
            next_steps.append("Check the current /earn UI first because the docs still say Stability Pool deposits are disabled during an ongoing upgrade.")
    next_steps.extend([
        "Capture a real wallet preview or calldata sample before treating medium-confidence routing as executable truth.",
        "Verify target contract address against the Sigma ABI manifest.",
        "Use sigma decode on any captured calldata and compare it against this plan.",
    ])
    payload["nextSteps"] = next_steps
    payload.setdefault("warnings", [])
    if operation_model:
        entrypoint = operation_model.get("entrypoint") or {}
        if entrypoint.get("kind") == "archived-app":
            payload["warnings"].append("This operation is modeled from archived Sigma docs and is not claimed as a current live route.")
        elif entrypoint.get("kind") == "docs-only":
            payload["warnings"].append("This operation is docs-described only; exact live entrypoint and routing remain ambiguous.")
        elif operation_model.get("docsStatus") == "current-docs-disabled-upgrade":
            payload["warnings"].append("Sigma docs currently mark this flow as disabled during an ongoing upgrade even though ABI surfaces exist.")
    payload["warnings"].append("This plan intentionally stops before calldata generation or wallet execution.")
    return payload
