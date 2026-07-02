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


if __name__ == "__main__":
    app()
