"""Testes do comando `copa pipeline` (orquestração download → ingest → build → predict)."""

from contextlib import ExitStack
from unittest import mock

from typer.testing import CliRunner

from copa_challenger import cli

runner = CliRunner()

# (nome da etapa, caminho da função no módulo de origem) na ordem esperada.
_STEPS = [
    ("download", "copa_challenger.data.download.download_dataset"),
    ("ingest", "copa_challenger.data.ingest.ingest_raw"),
    ("build", "copa_challenger.data.build.build_all"),
    ("predict", "copa_challenger.predict.predict.generate_predictions"),
]


def _run(args: list[str]) -> list[str]:
    """Roda o comando com as 4 etapas substituídas por stubs; devolve a ordem de chamada."""
    calls: list[str] = []
    with ExitStack() as stack:
        for name, target in _STEPS:
            stack.enter_context(
                mock.patch(target, side_effect=lambda *a, _n=name, **k: calls.append(_n))
            )
        result = runner.invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    return calls


def test_pipeline_runs_all_steps_in_order() -> None:
    assert _run(["pipeline"]) == ["download", "ingest", "build", "predict"]


def test_pipeline_skip_download_omits_download() -> None:
    assert _run(["pipeline", "--skip-download"]) == ["ingest", "build", "predict"]
