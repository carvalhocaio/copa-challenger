"""Configurações e paths do projeto."""

from pathlib import Path

# raiz do projeto (assume execução via `uv run` a partir da raiz)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DUCKDB_PATH = DATA_DIR / "copa.duckdb"

KAGGLE_DATASET = "piterfm/fifa-football-world-cup"

SQL_DIR = PROJECT_ROOT / "sql"

# Dashboard (Evidence.dev)
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
DASHBOARD_SOURCE_DIR = DASHBOARD_DIR / "sources" / "copa"

# Saída do pipeline preditivo (Missão 04)
SUBMISSIONS_DIR = PROJECT_ROOT / "submissions"
