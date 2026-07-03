"""CLI do World Cup Intelligence Desk."""

import typer

app = typer.Typer(help="World Cup Intelligence Desk — Copa Challenger")


@app.callback()
def main() -> None:
    """World Cup Intelligence Desk — Copa Challenger."""
    pass


@app.command()
def download(
    force: bool = typer.Option(False, "--force", help="Rebaixa mesmo se os dados já existirem."),
) -> None:
    """Baixa o dataset oficial da competição para data/raw/."""
    from copa_challenger.data.download import download_dataset

    download_dataset(force=force)


@app.command()
def ingest() -> None:
    """Carrega os CSVs brutos para o DuckDB (camada raw) e imprime o catálogo."""
    from copa_challenger.data.ingest import ingest_raw

    ingest_raw()


@app.command()
def build() -> None:
    """Constrói a camada de staging (views stg.*) a partir dos modelos SQL."""
    from copa_challenger.data.build import build_all

    build_all()


@app.command()
def report() -> None:
    """Responde as perguntas de negócio do desk (Missão 01)."""
    from copa_challenger.analytics.report import run_report

    run_report()


@app.command(name="sync-dashboard")
def sync_dashboard() -> None:
    """Copia o DuckDB para o proejto Evidence (dashboard/sources/copa/)."""
    from copa_challenger.data.dashboard import sync_dashboard_db

    sync_dashboard_db()


if __name__ == "__main__":
    app()
