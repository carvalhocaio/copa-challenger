# ⚽ World Cup Intelligence Desk — Copa Challenger (Dados por Todos)

Mesa de inteligência sobre as Copas do Mundo de 2018 e 2022, com um modelo preditivo para a Copa de 2026 — construída para o desafio [Copa Challenger — Dados por Todos](https://www.kaggle.com/competitions/copa-challenger-dados-por-todos) no Kaggle.

O projeto percorre as 4 missões do desafio como camadas de um mesmo pipeline: **SQL** (modelagem em DuckDB) → **EDA** (notebook reativo) → **Dashboard** (storytelling) → **IA** (agente de chat + modelo preditivo). Roda 100% local — DuckDB embarcado, sem infraestrutura externa além da API do Kaggle (para baixar os dados) e da API do Gemini (opcional, só para o chat).

## Mapa das 4 missões

| Missão | Entregável | Onde está | Como rodar |
|---|---|---|---|
| **1 — SQL** | Camada `staging`/`marts` (views estilo dbt) + 5 perguntas de negócio | [`sql/staging/`](sql/staging), [`sql/marts/`](sql/marts), [`analytics/report.py`](src/copa_challenger/analytics/report.py) | `uv run copa build && uv run copa report` |
| **2 — EDA** | Notebook reativo (marimo + Altair + Polars), consome os marts da Missão 1 | [`notebooks/02_eda.py`](notebooks/02_eda.py) | `uv run marimo edit notebooks/02_eda.py` |
| **3 — Dashboard** | Storytelling em 3 páginas (Evidence.dev) | [`dashboard/pages/`](dashboard/pages) | `uv run copa sync-dashboard` → `cd dashboard && npm install && npm run sources && npm run dev` |
| **4 — IA** | (a) agente de chat sobre dados históricos; (b) pipeline preditivo para 2026 | [`agent/`](src/copa_challenger/agent), [`predict/`](src/copa_challenger/predict) | `uv run copa chat` · `uv run copa predict` · `uv run copa backtest` |

> A Missão 4 tem duas metades hoje **desconectadas**: o agente de chat (4a) só enxerga o schema histórico `mart` e não sabe nada das previsões de 2026 geradas pelo pipeline preditivo (4b). É uma lacuna conhecida — ver issue de integração no roadmap abaixo.

## Requisitos

- **Python ≥ 3.12** + [`uv`](https://docs.astral.sh/uv/) para gerenciar dependências e o ambiente virtual.
- **Node ≥ 18 / npm ≥ 7** — só para a Missão 3 (dashboard Evidence.dev).
- **Credenciais do Kaggle** (`~/.kaggle/kaggle.json` ou `KAGGLE_USERNAME`/`KAGGLE_KEY`) — só para `copa download`.
- **`GEMINI_API_KEY`** — só para `copa chat`.
- Copie `.env.example` para `.env` (`cp .env.example .env`) e preencha as chaves acima — `copa chat`/`copa download` carregam esse `.env` automaticamente.
- O projeto usa `dependency-groups` no `pyproject.toml` (`dev`, `eda`, `agent`); nenhum grupo default cobre tudo. Use `uv sync --all-groups` para instalar todas as etapas de uma vez.

## Quickstart

```bash
uv sync --all-groups           # ou por grupo: --group dev / eda / agent

uv run copa download           # baixa data/raw/*.csv (Kaggle API)
uv run copa ingest             # CSVs -> DuckDB, camada raw
uv run copa build              # staging + marts (sql/)
uv run copa report             # Missão 1 — 5 perguntas de negócio

uv run marimo edit notebooks/02_eda.py     # Missão 2 — EDA reativa

uv run copa sync-dashboard     # copia o DuckDB para dashboard/sources/copa/
cd dashboard && npm install && npm run sources && npm run dev   # Missão 3

uv run copa predict            # Missão 4b — gera submissions/predictions_2026.csv
uv run copa backtest           # Missão 4b — valida o modelo contra 2022
uv run copa chat               # Missão 4a — chat Streamlit (requer GEMINI_API_KEY)
```

Se `data/raw/` e `data/copa.duckdb` já existem localmente, `download`/`ingest` podem ser pulados — útil para quem só quer reproduzir a parte de modelagem/previsão.

## Estrutura de pastas

```
sql/staging/, sql/marts/, sql/seeds/   -> Missão 1 (modelos SQL, estilo dbt)
src/copa_challenger/analytics/         -> Missão 1 (CLI `report`) + Missão 2 (queries usadas pelo notebook)
notebooks/02_eda.py                    -> Missão 2 (EDA reativa)
dashboard/                             -> Missão 3 (projeto Evidence.dev)
src/copa_challenger/agent/             -> Missão 4a (agente de chat + guardrail de SQL)
src/copa_challenger/predict/           -> Missão 4b (features, modelo, backtest, geração de previsões)
src/copa_challenger/data/              -> download, ingestão e build do pipeline (raw -> stg -> mart)
tests/                                 -> 30 testes (guardrail de SQL + núcleo matemático do modelo)
submissions/predictions_2026.csv       -> saída da Missão 4 (gitignored; gerado via `copa predict`)
```

## Principais resultados

**Missão 1 — SQL** (`uv run copa report`): Rússia 2018 (64 jogos, 169 gols, público médio 47.371, campeão **França**, artilheiro Harry Kane — 6 gols) vs. Catar 2022 (64 jogos, 172 gols, público médio 53.191, campeão **Argentina**, artilheiro Mbappé — 8 gols). O favorito do ranking FIFA venceu **68,4%** dos jogos decididos na fase de grupos e **81,3%** no mata-mata (2022). Mais eficientes na finalização (`attack_vs_xg`): Rússia 2018 (+6,0) e Holanda 2022 (+5,3). Melhores defesas vs. xG: Croácia 2022 (+4,0) e Dinamarca 2018 (+3,9).

**Missão 3 — Dashboard**: [As duas Copas](dashboard/pages/edicoes.md) compara eficiência ofensiva/defensiva entre edições; [O paradoxo do favorito](dashboard/pages/favorito.md) explica por que o ranking acerta a partida isolada (81% no mata-mata) mas quase nunca o campeão — vencer 7 jogos seguidos a 81% cada dá só ≈23% de chance (0,81⁷).

**Missão 4b — pipeline preditivo** (`uv run copa backtest`, treino só em 2018, teste nos 64 jogos reais de 2022):

| | accuracy | log-loss |
|---|---|---|
| Modelo (Poisson ataque/defesa) | 54,7% | 1,036 |
| Baseline: frequência ingênua (2018) | 45,3% | 1,075 |
| Baseline: favorito do ranking | 56,2% | n/a (não-probabilístico) |

O modelo bate a baseline ingênua, mas fica levemente abaixo do baseline trivial "aposte sempre no favorito do ranking" em acurácia — resultado honesto, não escondido (ver limitações abaixo e a issue de sweep no roadmap). `uv run copa predict` gera as 72 partidas de fase de grupos de 2026 em `submissions/predictions_2026.csv`, com a soma das probabilidades W/D/L sempre ≈ 1,0000.

## Limitações e decisões de design conhecidas

- Os 72 jogos de 2026 são tratados como **neutros** (sem vantagem de mando) — o dataset de calendário não traz coluna de sede/estádio.
- O modelo de Poisson é calculado à mão (sem scipy/sklearn/PyTorch), de propósito: 128 partidas históricas não justificam um framework de ML.
- `SHRINKAGE_K = 3.0` e o blend 50/50 entre gol real e xG são heurísticas escolhidas por julgamento, ainda não validadas por um sweep contra o próprio backtest.
- O backtest é um único fold (64 jogos, sem ranking FIFA de 2018 para fazer k-fold) — leia os números como indício, não validação estatística robusta.
- O agente de chat (Missão 4a) não conhece o pipeline preditivo (Missão 4b) — perguntas sobre 2026 ainda não têm resposta pelo chat.

## Testes e qualidade

```bash
uv run pytest        # 30 testes: guardrail de SQL + núcleo matemático do modelo preditivo
uv run ruff check .  # lint
```

## Roadmap

O backlog de melhorias conscientes (não bugs escondidos) está nas [issues do repositório](https://github.com/carvalhocaio/copa-challenger/issues) — cobre desde a integração entre o agente de chat e o pipeline preditivo até validação empírica das constantes do modelo, CI e pequenos cleanups.

## Licença e créditos

Código sob licença [MIT](LICENSE). Dados: [FIFA World Cup dataset](https://www.kaggle.com/datasets/piterfm/fifa-football-world-cup) (Kaggle, por `piterfm`).
