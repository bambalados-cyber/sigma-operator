from __future__ import annotations

from typing import Any

from .surface_truth import governance_namespace_snapshot, governance_section_snapshot


class GovernanceError(RuntimeError):
    pass


_READ_ACTION_SUMMARIES: dict[tuple[str, str], str] = {
    ("xsigma", "overview"): "Route-truth overview for the xSIGMA staking surface.",
    ("xsigma", "position"): "Owner-scoped xSIGMA position scaffold. Live fetch binding is not implemented yet.",
    ("xsigma", "claimable"): "Owner-scoped xSIGMA claimable scaffold. Live fetch binding is not implemented yet.",
    ("xsigma", "convert-preview"): "Amount-scoped convert preview scaffold. Live pricing/binding is not implemented yet.",
    ("vote", "gauges"): "Gauge list scaffold for emissions voting.",
    ("vote", "epoch"): "Voting epoch scaffold.",
    ("vote", "allocations"): "Owner-scoped vote-allocation scaffold.",
    ("vote", "preview"): "Owner-scoped vote preview scaffold.",
    ("incentivize", "gauges"): "Gauge list scaffold for incentivize.",
    ("incentivize", "campaigns"): "Campaign list scaffold for incentivize.",
    ("incentivize", "positions"): "Owner-scoped incentivize position scaffold.",
    ("incentivize", "preview"): "Owner-scoped incentivize preview scaffold.",
}


def governance_overview() -> dict[str, Any]:
    snapshot = governance_namespace_snapshot()
    return {
        "mode": "governance-overview",
        "namespace": snapshot["namespace"],
        "note": snapshot["note"],
        "sections": snapshot["sections"],
        "notes": [
            "This is a CLI structural namespace, not a claim that the /governance route renders normally in the app.",
            "All currently exposed governance commands are truthful scaffolds until route-specific read bindings are implemented and verified.",
        ],
    }


def governance_read_action(
    section: str,
    action: str,
    *,
    owner: str | None = None,
    amount: str | None = None,
) -> dict[str, Any]:
    try:
        snapshot = governance_section_snapshot(section)
    except ValueError as exc:
        raise GovernanceError(str(exc)) from exc

    normalized_action = action.strip().lower()
    key = (snapshot["section"], normalized_action)
    if key not in _READ_ACTION_SUMMARIES:
        expected = sorted(action for area, action in _READ_ACTION_SUMMARIES if area == snapshot["section"])
        raise GovernanceError(
            f"Unsupported governance action {action!r} for section {section!r}. Expected one of: {', '.join(expected)}"
        )

    payload: dict[str, Any] = {
        "mode": f"governance-{snapshot['section']}-{normalized_action}",
        "section": snapshot["section"],
        "action": normalized_action,
        "namespace": snapshot["namespace"],
        "route": snapshot["route"],
        "status": snapshot["status"],
        "verificationStatus": snapshot["verificationStatus"],
        "summary": _READ_ACTION_SUMMARIES[key],
        "implementedAs": "truthful-scaffold",
        "notes": [
            snapshot["namespaceNote"],
            "This command currently exposes route truth, planned command shape, and required parameters only.",
            "Do not treat this output as live onchain/API governance data until route-specific fetch bindings are implemented.",
        ],
        "recommendedReadOnlyCommands": snapshot["readOnlyCommands"],
        "deferredWriteCommands": snapshot["writeCommandsDeferred"],
    }
    if owner is not None:
        payload["requestedOwner"] = owner
    if amount is not None:
        payload["requestedAmount"] = amount
    return payload
