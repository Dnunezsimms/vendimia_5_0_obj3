from __future__ import annotations

from pathlib import Path


DASHBOARD_DIR = Path(__file__).resolve().parents[1]


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or DASHBOARD_DIR).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "docs" / "objetivo_3_vendimia_5_0.md").exists():
            return candidate
        if (candidate / ".git").exists():
            return candidate
    return DASHBOARD_DIR.parents[1]


REPO_ROOT = find_repo_root()
CLIMATE_COVERAGE_DIR = REPO_ROOT / "data" / "metadata" / "climate_coverage"
CLIMATE_MASTER_PATH = CLIMATE_COVERAGE_DIR / "tabla_maestra_clima_obj3_2025_2026.csv"
CLIMATE_HOURLY_DATAVID = REPO_ROOT / "data" / "raw" / "climate" / "hourly" / "datavid"
CLIMATE_HOURLY_INIA = REPO_ROOT / "data" / "raw" / "climate" / "hourly" / "inia_agromet"
CLIMATE_HOURLY_ZENTRA = REPO_ROOT / "data" / "raw" / "climate" / "hourly" / "zentra"
GDD_DIR = REPO_ROOT / "models" / "indicador_biologico" / "outputs_multisite_gdd"
LUIS_DASHBOARD_DIR = REPO_ROOT / "models" / "dashboard_luis" / "0_0_0_0_Predicciones_Diego_SprintMayo"
MATURITY_RAW_DIR = REPO_ROOT / "data" / "raw" / "maturity"
PHENOLOGY_RAW_DIR = REPO_ROOT / "data" / "raw" / "phenology"
PHENOLOGY_PREPARED_DIR = REPO_ROOT / "data" / "processed" / "phenology_climate"
LOG_DIR = DASHBOARD_DIR / "logs"

HOST = "127.0.0.1"
PORT = 7862
