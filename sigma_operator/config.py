from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

APPROVAL_POLICY_MODES = ("unlimited", "exact", "custom")
DEFAULT_APPROVAL_POLICY_MODE = "exact"
MAX_UINT256 = (1 << 256) - 1


@dataclass(frozen=True)
class Settings:
    project_root: Path
    workspace_root: Path
    skill_root: Path
    abi_dir: Path
    script_dir: Path
    captures_dir: Path
    config_path: Path
    bnb_rpc_url: str | None
    bnb_rpc_timeout_seconds: float
    bsctrace_api_url: str | None
    bsctrace_api_key: str | None
    bsctrace_chain_id: int
    bsctrace_timeout_seconds: float
    rpc_url: str | None
    rpc_timeout_seconds: float
    explorer_api_url: str | None
    explorer_api_key: str | None
    explorer_chain_id: int
    explorer_timeout_seconds: float
    default_approval_policy_mode: str
    default_approval_policy_amount: str | None


@dataclass(frozen=True)
class ApprovalPolicy:
    mode: str
    amount: str | None = None
    source: str = "default"


@dataclass(frozen=True)
class OperatorConfig:
    path: Path
    exists: bool
    approval_policy: ApprovalPolicy
    raw: dict[str, Any]


def _parse_env_int(value: str, fallback: int) -> int:
    try:
        return int(value, 0)
    except ValueError:
        return fallback


def _first_env_value(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value is None:
            continue
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def _parse_env_float(value: str | None, fallback: float) -> float:
    if value is None:
        return fallback
    try:
        return float(value)
    except ValueError:
        return fallback


def _parse_decimal_amount(value: str) -> Decimal:
    try:
        amount = Decimal(value.strip())
    except (AttributeError, InvalidOperation) as exc:
        raise ValueError(f"Invalid approval amount: {value!r}") from exc
    if amount <= 0:
        raise ValueError("approval amount must be greater than zero")
    return amount


def normalize_approval_policy(mode: str | None, amount: str | None = None, *, source: str = "default") -> ApprovalPolicy:
    normalized_mode = (mode or DEFAULT_APPROVAL_POLICY_MODE).strip().lower()
    if normalized_mode not in APPROVAL_POLICY_MODES:
        expected = ", ".join(APPROVAL_POLICY_MODES)
        raise ValueError(f"Unsupported approval policy mode: {mode!r}. Expected one of: {expected}")

    normalized_amount: str | None = None
    if normalized_mode == "custom":
        if amount is None or not str(amount).strip():
            raise ValueError("approval amount is required when approval policy mode is 'custom'")
        normalized_amount = format(_parse_decimal_amount(str(amount)), "f")
    elif amount is not None and str(amount).strip():
        raise ValueError("approval amount is only valid when approval policy mode is 'custom'")

    return ApprovalPolicy(mode=normalized_mode, amount=normalized_amount, source=source)


def approval_policy_to_dict(policy: ApprovalPolicy) -> dict[str, Any]:
    return {
        "mode": policy.mode,
        "amount": policy.amount,
        "source": policy.source,
        "supportedModes": list(APPROVAL_POLICY_MODES),
    }


def parse_token_amount_to_raw(amount: str, *, decimals: int = 18) -> int:
    scaled = _parse_decimal_amount(amount) * (Decimal(10) ** decimals)
    return int(scaled.to_integral_value())


def format_token_amount_from_raw(raw: int, *, decimals: int = 18) -> str:
    scaled = Decimal(raw) / (Decimal(10) ** decimals)
    text = format(scaled, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def approval_policy_desired_allowance_raw(
    policy: ApprovalPolicy,
    *,
    requested_amount: str | None,
    decimals: int = 18,
) -> int | None:
    if policy.mode == "unlimited":
        return MAX_UINT256
    if policy.mode == "custom":
        if policy.amount is None:
            return None
        return parse_token_amount_to_raw(policy.amount, decimals=decimals)
    if policy.mode == "exact":
        if requested_amount is None or not str(requested_amount).strip():
            return None
        return parse_token_amount_to_raw(str(requested_amount), decimals=decimals)
    return None


def _default_approval_policy_from_settings(settings: Settings) -> ApprovalPolicy:
    return normalize_approval_policy(
        settings.default_approval_policy_mode,
        settings.default_approval_policy_amount,
        source="env-default" if settings.default_approval_policy_mode != DEFAULT_APPROVAL_POLICY_MODE or settings.default_approval_policy_amount else "default",
    )


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[1]
    workspace_root = Path(__file__).resolve().parents[3]
    skill_root = Path(
        os.environ.get("SIGMA_SKILL_ROOT", str(workspace_root / "skills" / "sigma-money"))
    ).expanduser().resolve()
    abi_dir = Path(
        os.environ.get("SIGMA_OPERATOR_ABI_DIR", str(skill_root / "references" / "abi"))
    ).expanduser().resolve()
    script_dir = skill_root / "scripts"
    captures_dir = project_root / "captures"
    config_path = Path(
        os.environ.get("SIGMA_OPERATOR_CONFIG_PATH", "~/.config/sigma-operator/config.json")
    ).expanduser().resolve()

    bnb_rpc_url = _first_env_value(
        "SIGMA_OPERATOR_BNB_RPC_URL",
        "SIGMA_OPERATOR_BSC_RPC_URL",
        "SIGMA_OPERATOR_MEGANODE_RPC_URL",
        "SIGMA_OPERATOR_NODEREAL_RPC_URL",
        "SIGMA_OPERATOR_RPC_URL",
    )
    bnb_rpc_timeout_seconds = _parse_env_float(
        _first_env_value(
            "SIGMA_OPERATOR_BNB_RPC_TIMEOUT",
            "SIGMA_OPERATOR_BSC_RPC_TIMEOUT",
            "SIGMA_OPERATOR_MEGANODE_RPC_TIMEOUT",
            "SIGMA_OPERATOR_NODEREAL_RPC_TIMEOUT",
            "SIGMA_OPERATOR_RPC_TIMEOUT",
        ),
        20.0,
    )

    bsctrace_api_url = _first_env_value(
        "SIGMA_OPERATOR_BSCTRACE_API_URL",
        "SIGMA_OPERATOR_EXPLORER_API_URL",
    )
    bsctrace_api_key = _first_env_value(
        "SIGMA_OPERATOR_BSCTRACE_API_KEY",
        "SIGMA_OPERATOR_EXPLORER_API_KEY",
    )
    bsctrace_chain_id = _parse_env_int(
        _first_env_value(
            "SIGMA_OPERATOR_BSCTRACE_CHAIN_ID",
            "SIGMA_OPERATOR_EXPLORER_CHAIN_ID",
        )
        or "56",
        56,
    )
    bsctrace_timeout_seconds = _parse_env_float(
        _first_env_value(
            "SIGMA_OPERATOR_BSCTRACE_TIMEOUT",
            "SIGMA_OPERATOR_EXPLORER_TIMEOUT",
        ),
        bnb_rpc_timeout_seconds,
    )

    default_approval_policy_mode = (
        _first_env_value("SIGMA_OPERATOR_APPROVAL_POLICY") or DEFAULT_APPROVAL_POLICY_MODE
    )
    default_approval_policy_amount = _first_env_value("SIGMA_OPERATOR_APPROVAL_AMOUNT")

    return Settings(
        project_root=project_root,
        workspace_root=workspace_root,
        skill_root=skill_root,
        abi_dir=abi_dir,
        script_dir=script_dir,
        captures_dir=captures_dir,
        config_path=config_path,
        bnb_rpc_url=bnb_rpc_url,
        bnb_rpc_timeout_seconds=bnb_rpc_timeout_seconds,
        bsctrace_api_url=bsctrace_api_url,
        bsctrace_api_key=bsctrace_api_key,
        bsctrace_chain_id=bsctrace_chain_id,
        bsctrace_timeout_seconds=bsctrace_timeout_seconds,
        rpc_url=bnb_rpc_url,
        rpc_timeout_seconds=bnb_rpc_timeout_seconds,
        explorer_api_url=bsctrace_api_url,
        explorer_api_key=bsctrace_api_key,
        explorer_chain_id=bsctrace_chain_id,
        explorer_timeout_seconds=bsctrace_timeout_seconds,
        default_approval_policy_mode=default_approval_policy_mode,
        default_approval_policy_amount=default_approval_policy_amount,
    )


def load_operator_config(*, config_path: str | Path | None = None) -> OperatorConfig:
    settings = get_settings()
    path = Path(config_path).expanduser().resolve() if config_path is not None else settings.config_path
    default_policy = _default_approval_policy_from_settings(settings)
    if not path.exists():
        return OperatorConfig(
            path=path,
            exists=False,
            approval_policy=default_policy,
            raw={},
        )

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Operator config is not valid JSON: {path}") from exc

    approval_blob = raw.get("approvalPolicy") if isinstance(raw, dict) else None
    if not isinstance(approval_blob, dict):
        approval_blob = {}

    policy = normalize_approval_policy(
        approval_blob.get("mode") or default_policy.mode,
        approval_blob.get("amount") or default_policy.amount,
        source="config-file",
    )
    return OperatorConfig(
        path=path,
        exists=True,
        approval_policy=policy,
        raw=raw if isinstance(raw, dict) else {},
    )


def resolve_approval_policy(
    *,
    mode_override: str | None = None,
    amount_override: str | None = None,
    config_path: str | Path | None = None,
) -> ApprovalPolicy:
    if mode_override is not None or amount_override is not None:
        policy = normalize_approval_policy(mode_override, amount_override, source="cli-override")
        if policy.mode == "exact" and amount_override:
            raise ValueError("--approval-amount is only valid when --approval-policy custom")
        return policy
    return load_operator_config(config_path=config_path).approval_policy


def save_operator_config(
    *,
    approval_policy: ApprovalPolicy,
    config_path: str | Path | None = None,
    merge_existing: bool = True,
) -> OperatorConfig:
    current = load_operator_config(config_path=config_path)
    path = current.path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = dict(current.raw) if merge_existing else {}
    payload.update(
        {
            "schemaVersion": 1,
            "updatedAt": datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
            "approvalPolicy": {
                "mode": approval_policy.mode,
                "amount": approval_policy.amount,
            },
        }
    )
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return OperatorConfig(
        path=path,
        exists=True,
        approval_policy=ApprovalPolicy(
            mode=approval_policy.mode,
            amount=approval_policy.amount,
            source="config-file",
        ),
        raw=payload,
    )


def initialize_operator_config(
    *,
    mode: str | None = None,
    amount: str | None = None,
    config_path: str | Path | None = None,
) -> OperatorConfig:
    policy = normalize_approval_policy(mode, amount, source="cli-init")
    return save_operator_config(approval_policy=policy, config_path=config_path, merge_existing=False)


def ensure_paths(settings: Settings) -> None:
    missing = []
    for label, path in {
        "skill_root": settings.skill_root,
        "abi_dir": settings.abi_dir,
        "script_dir": settings.script_dir,
    }.items():
        if not path.exists():
            missing.append(f"{label}={path}")
    if missing:
        raise FileNotFoundError(
            "Missing Sigma skill assets. Checked: " + ", ".join(missing)
        )
