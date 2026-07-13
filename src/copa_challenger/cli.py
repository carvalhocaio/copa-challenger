"""CLI do World Cup Intelligence Desk."""

import typer

app = typer.Typer(help="World Cup Intelligence Desk — Copa Challenger")


@app.callback()
def main() -> None:
    """World Cup Intelligence Desk — Copa Challenger."""
    # Carrega variáveis do .env (ex.: GEMINI_API_KEY, KAGGLE_USERNAME/KAGGLE_KEY)
    # para todos os comandos, antes que o kaggle valide credenciais no import.
    from dotenv import load_dotenv

    load_dotenv()


@app.command()
def download(
    force: bool = typer.Option(
        False, "--force", help="Baixa novamente mesmo se os dados já existirem."
    ),
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
    """Copia o DuckDB para o projeto Evidence (dashboard/sources/copa/)."""
    from copa_challenger.data.dashboard import sync_dashboard_db

    sync_dashboard_db()


@app.command()
def predict() -> None:
    """Gera probabilidades W/D/L e gols esperados para os 72 jogos de 2026 (Missão 04)."""
    from copa_challenger.predict.predict import generate_predictions

    generate_predictions()


@app.command()
def pipeline(
    skip_download: bool = typer.Option(
        False,
        "--skip-download",
        help="Pula o download e usa os CSVs já presentes em data/raw/.",
    ),
) -> None:
    """Roda o pipeline completo de ponta a ponta: download → ingest → build → predict."""
    from copa_challenger.data.build import build_all
    from copa_challenger.data.download import download_dataset
    from copa_challenger.data.ingest import ingest_raw
    from copa_challenger.predict.predict import generate_predictions

    if skip_download:
        print("[1/4] download: pulado (--skip-download)")
    else:
        print("[1/4] download...")
        download_dataset()

    print("[2/4] ingest...")
    ingest_raw()

    print("[3/4] build...")
    build_all()

    print("[4/4] predict...")
    generate_predictions()

    print("Pipeline concluído: submissions/predictions_2026.csv gerado.")


@app.command()
def backtest(
    sweep: bool = typer.Option(
        False,
        "--sweep",
        help="Varre a grade (k, blend gol/xG) e imprime uma tabela ordenada por log-loss.",
    ),
) -> None:
    """Valida o modelo preditivo contra os 64 jogos reais de 2022 (Missão 04)."""
    from copa_challenger.predict.evaluate import run_backtest, run_sweep

    if sweep:
        run_sweep()
    else:
        run_backtest()


@app.command()
def chat() -> None:
    """Sobe a interface de chat do agente (Streamlit)."""
    import subprocess
    import sys
    from pathlib import Path

    app_path = Path(__file__).parent / "agent" / "app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], check=True)


if __name__ == "__main__":
    app()
