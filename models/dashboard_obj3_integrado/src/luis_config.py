from __future__ import annotations

import logging
import os
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[1]


def get_project_root(start: Path | None = None) -> Path:
    """Return the git/project root when available, otherwise this dashboard dir."""
    current = (start or DASHBOARD_DIR).resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
        if (candidate / "models").exists() and (candidate / "README.md").exists():
            return candidate
    return DASHBOARD_DIR


def _looks_like_artifacts_dir(path: Path) -> bool:
    return (
        (path / "outputs").exists()
        or (path / "data" / "prepared").exists()
        or (path / "config" / "experiment_config.json").exists()
        or (path / "monitoring").exists()
    )


def resolve_artifacts_dir() -> Path:
    """Resolve the dashboard artifact directory without relying on Luis' host paths."""
    env_value = os.environ.get("CYT_ARTIFACTS_DIR") or os.environ.get("CYT_PROJECT_DIR")
    candidates: list[Path] = []
    if env_value:
        candidates.append(Path(env_value).expanduser())

    repo_root = get_project_root()
    candidates.extend(
        [
            DASHBOARD_DIR,
            repo_root
            / "models"
            / "dashboard_luis"
            / "0_0_0_0_Predicciones_Diego_SprintMayo",
            Path.cwd() / "models" / "dashboard_luis" / "0_0_0_0_Predicciones_Diego_SprintMayo",
        ]
    )

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists() and _looks_like_artifacts_dir(resolved):
            return resolved

    fallback = candidates[0].resolve() if candidates else DASHBOARD_DIR
    logging.warning("No artifact directory found; falling back to %s", fallback)
    return fallback


BASE_DIR = resolve_artifacts_dir()

OUTPUTS_DIR = BASE_DIR / "outputs"
MONITORING_DIR = BASE_DIR / "monitoring"
DATA_DIR = BASE_DIR / "data" / "prepared"
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "demo_results" / "cache" / "dashboard_v2"

HOST = "0.0.0.0"
PORT = 7860

VALIDATION_OPTIONS = ["cv5_mixed", "lofo_mixed"]

DEFAULT_TARGETS = ["antocianinas_mg_baya", "taninos_mg_baya"]

BASE_COMBO_LABEL = "GDA + VPD + IFTT"


COMBO_ORDER_HUMAN = [
    "GDA",
    "VPD",
    "GDA + VPD",
    "GDA + VPD + IFTT",
    "GDA + VPD + IFN",
    "GDA + VPD + IFs",
    "GDA + VPD + IFTT + azucar",
    "GDA + VPD + IFN + azucar",
    "GDA + VPD + IFs + azucar",
    "GDA + VPD + IFTT + peso",
    "GDA + VPD + IFN + peso",
    "GDA + VPD + IFs + peso",
    "GDA + VPD + IFTT + rendimiento",
    "GDA + VPD + IFN + rendimiento",
    "GDA + VPD + IFs + rendimiento",
    "GDA + VPD + IFTT + azucar + peso",
    "GDA + VPD + IFN + azucar + peso",
    "GDA + VPD + IFs + azucar + peso",
    "GDA + VPD + IFTT + azucar + rendimiento",
    "GDA + VPD + IFN + azucar + rendimiento",
    "GDA + VPD + IFs + azucar + rendimiento",
    "GDA + VPD + IFTT + peso + rendimiento",
    "GDA + VPD + IFN + peso + rendimiento",
    "GDA + VPD + IFs + peso + rendimiento",
]
