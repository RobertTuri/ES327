"""Load the assumptions register (configs/base.yaml) and apply scenario overrides.

Each leaf parameter is a dict {value, unit, source, status}. `flatten` turns the tree into
dotted keys ("economics.discount_rate") so the model code reads plain numbers while the
provenance stays in the YAML.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs"
LEAF_KEYS = {"value", "unit", "source", "status"}


# Statuses that are allowed to run but must be flagged on every output.
UNVERIFIED_STATUSES = ("mock", "placeholder")


class PlaceholderError(RuntimeError):
    """Raised in strict mode when a placeholder assumption would reach a reported result."""


def _is_leaf(node: Any) -> bool:
    return isinstance(node, dict) and "value" in node and set(node) <= LEAF_KEYS


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and not _is_leaf(v) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def flatten(tree: dict, prefix: str = "") -> dict[str, dict]:
    flat: dict[str, dict] = {}
    for k, v in tree.items():
        key = f"{prefix}{k}"
        if _is_leaf(v):
            flat[key] = v
        elif isinstance(v, dict):
            flat.update(flatten(v, key + "."))
    return flat


def load_config(scenario: str | None = None, strict: bool = False,
                config_dir: Path = CONFIG_DIR) -> dict[str, dict]:
    """Return flat {dotted_key: {value, unit, source, status}} for base + scenario."""
    tree = yaml.safe_load((config_dir / "base.yaml").read_text())
    if scenario:
        scen = yaml.safe_load((config_dir / "scenarios" / f"{scenario}.yaml").read_text())
        tree = _merge(tree, scen.get("overrides") or {})
    flat = flatten(tree)
    if strict:
        missing = [k for k, p in flat.items() if p.get("status") == "placeholder"]
        if missing:
            raise PlaceholderError("Placeholder assumptions still in use: " + ", ".join(missing))
    return flat


def values(flat: dict[str, dict]) -> dict[str, Any]:
    """Strip provenance: {dotted_key: value}."""
    return {k: p["value"] for k, p in flat.items()}


def unverified(flat: dict[str, dict]) -> dict[str, list[str]]:
    """Which loaded parameters are mock or placeholder: {status: [dotted keys]}.

    This flags everything that was LOADED, not only what a given result used, so it can
    over-warn but never under-warn.
    """
    return {
        status: [k for k, p in flat.items() if p.get("status") == status]
        for status in UNVERIFIED_STATUSES
        if any(p.get("status") == status for p in flat.values())
    }


def provenance_note(flat: dict[str, dict]) -> str:
    """One line to put on every output (plot title, CSV header, KPI table)."""
    flags = unverified(flat)
    if not flags:
        return "All inputs verified."
    counts = ", ".join(f"{len(keys)} {status}" for status, keys in flags.items())
    return f"UNVERIFIED INPUTS ({counts}): not for reporting."

