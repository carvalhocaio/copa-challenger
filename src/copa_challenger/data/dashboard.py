"""Sincroniza o DuckDB de trabalho para o projeto Evidence (dashboard).

Copia data/copa.duckdb -> dashboard/sources/copa/copa.duckdb. Isso evita que
o Evidence abra o banco de trabalho (e o lock de leitura/escrita do DuckDB).
O arquivo copiado é um artefato de build, regenerável a qualquer momento com:
    uv run copa build && uv run copa sync-dashboard
"""

import shutil

from copa_challenger.config import DASHBOARD_SOURCE_DIR, DUCKDB_PATH


def sync_dashboard_db() -> None:
    """Copia o DuckDB para dentro do source do Evidence."""
    if not DUCKDB_PATH.exists():
        raise FileNotFoundError(f"{DUCKDB_PATH} não existe. Rode `uv run copa build` antes.")

    DASHBOARD_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    dest = DASHBOARD_SOURCE_DIR / "copa.duckdb"
    shutil.copy2(DUCKDB_PATH, dest)

    size_mb = dest.stat().st_size / 1_048_576
    print(f"ok - copiado -> {dest} ({size_mb:.1f} MB)")
