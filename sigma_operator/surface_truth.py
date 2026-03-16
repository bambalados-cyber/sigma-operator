from __future__ import annotations

from typing import Any

GOVERNANCE_NAMESPACE_NOTE = (
    "The CLI may expose a governance umbrella namespace for structure, but that does not imply "
    "the /governance app route itself is rendered or operator-ready."
)

SURFACE_TRUTH: dict[str, Any] = {
    "appRouteTruth": {
        "/governance": {
            "status": "blank-non-rendered",
            "cliNamespaceRole": "umbrella-only",
            "note": "Use route-specific children such as /xsigma, /vote, and /incentivize for product truth.",
        },
        "/xsigma": {
            "status": "route-render-observed",
            "mode": "mixed-read-write",
            "summary": "xSIGMA staking / convert / exit surface.",
        },
        "/vote": {
            "status": "route-render-observed",
            "mode": "mixed-read-write",
            "summary": "emissions voting / gauge allocation surface.",
        },
        "/incentivize": {
            "status": "route-render-observed",
            "mode": "mixed-read-write",
            "summary": "gauge incentive / bribing surface.",
        },
        "/dashboard": {
            "status": "route-render-observed",
            "mode": "mixed-read-write",
            "summary": "wallet/account rewards, points, and unwrap surface.",
        },
        "/statistics": {
            "status": "route-render-observed",
            "mode": "read-only",
            "summary": "public protocol analytics surface.",
        },
    },
    "verifiedAssets": {
        "leverage": ["BNB"],
        "mint": ["BNB -> bnbUSD"],
    },
    "governance": {
        "namespace": "governance",
        "note": GOVERNANCE_NAMESPACE_NOTE,
        "sections": {
            "xsigma": {
                "route": "https://sigma.money/xsigma",
                "status": "route-render-observed",
                "verificationStatus": "rendered-2026-03-16",
                "readOnlyCommands": [
                    "sigma governance xsigma overview",
                    "sigma governance xsigma position --owner <address>",
                    "sigma governance xsigma claimable --owner <address>",
                    "sigma governance xsigma convert-preview --amount <amount>",
                ],
                "writeCommandsDeferred": [
                    "sigma governance xsigma convert",
                    "sigma governance xsigma exit",
                    "sigma governance xsigma claim",
                ],
            },
            "vote": {
                "route": "https://sigma.money/vote",
                "status": "route-render-observed",
                "verificationStatus": "rendered-2026-03-16",
                "readOnlyCommands": [
                    "sigma governance vote gauges",
                    "sigma governance vote epoch",
                    "sigma governance vote allocations --owner <address>",
                    "sigma governance vote preview --owner <address>",
                ],
                "writeCommandsDeferred": [
                    "sigma governance vote cast",
                    "sigma governance vote clear",
                ],
            },
            "incentivize": {
                "route": "https://sigma.money/incentivize",
                "status": "route-render-observed",
                "verificationStatus": "rendered-2026-03-16",
                "readOnlyCommands": [
                    "sigma governance incentivize gauges",
                    "sigma governance incentivize campaigns",
                    "sigma governance incentivize positions --owner <address>",
                    "sigma governance incentivize preview --owner <address>",
                ],
                "writeCommandsDeferred": [
                    "sigma governance incentivize create",
                    "sigma governance incentivize topup",
                    "sigma governance incentivize claim",
                ],
            },
        },
    },
}


def governance_namespace_snapshot() -> dict[str, Any]:
    return SURFACE_TRUTH["governance"]


def governance_section_snapshot(section: str) -> dict[str, Any]:
    normalized = section.strip().lower()
    sections = SURFACE_TRUTH["governance"]["sections"]
    if normalized not in sections:
        expected = ", ".join(sorted(sections))
        raise ValueError(f"Unsupported governance section: {section!r}. Expected one of: {expected}")
    payload = dict(sections[normalized])
    payload["section"] = normalized
    payload["namespace"] = SURFACE_TRUTH["governance"]["namespace"]
    payload["namespaceNote"] = SURFACE_TRUTH["governance"]["note"]
    return payload
