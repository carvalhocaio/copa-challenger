"""Perguntas de negócio do desk (Missão 01) + diagnósticos de modelagem."""

import duckdb

from copa_challenger.config import DUCKDB_PATH


def run_report() -> None:
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    print("\n == Q1 . Rússia 2018 vs Catar 2022: o torneio mudou? ==")
    con.sql("SELECT * FROM mart.edition_kpis").show()

    print("\n == Q2 . Quem finalizou acima do esperado (attack vs xG)? ==")
    print("(mín. 4 jogos para reduzir ruído de amostra)")
    con.sql("""
        SELECT team, year, matches, goals_for, xg_for, attack_vs_xg
        FROM mart.team_performance
        WHERE matches >= 4
        ORDER BY attack_vs_xg DESC
        LIMIT 8
    """).show()

    print("\n == Q3 . Defesas que renderam mais que o esperado ==")
    con.sql("""
        SELECT team, year, matches, goals_against, xg_against, defense_vs_xg
        FROM mart.team_performance
        WHERE matches >= 4
        ORDER BY defense_vs_xg DESC
        LIMIT 8
    """).show()

    print("\n == Q4 . O mata-mata trava? (gols e pênaltis por fase) ==")
    con.sql("""
        SELECT year, round, n_matches, goals_per_match, xg_per_match, pen_shootouts
        FROM mart.knockout_analysis
        ORDER BY year, stage_order
    """).show()

    print("\n == Q5 . O ranking FIFA previu 2022? (taxa de acerto do favorito) ==")
    con.sql("""
        SELECT
            CASE WHEN round = 'Group stage' THEN 'Fase de grupos'
                    ELSE 'Mata-mata' END                       AS phase,
            count(*) FILTER (WHERE favorite_won IS NOT NULL) AS decided,
            count(*) FILTER (WHERE favorite_won)             AS favorite_won,
            round(100.0 * count(*) FILTER (WHERE favorite_won)
                    / nullif(count(*) FILTER (WHERE favorite_won IS NOT NULL), 0), 1)
                                                                AS favorite_win_pct
        FROM mart.ranking_vs_result
        GROUP BY phase
        ORDER BY phase
    """).show()

    # diagnósticos p/ os próximos passos (não são entregáveis, são bússola)
    print("\n -- diagnóstico: valores distintos de `round` --")
    print("(precisamos deles p/ classificar grupos x mata-mata na próxima etapa)")
    con.sql("""
        SELECT round, count(*) AS n
        FROM stg.matches
        GROUP BY round
        ORDER BY min(match_date)
    """).show()

    print(" -- diagnóstico: seleções de 2022 sem match no ranking --")
    print("(revela necessidade de crosswalk de nomes p/ join com rankings)")
    con.sql("""
        SELECT DISTINCT team FROM mart.int_team_matches WHERE year = 2022
        EXCEPT
        SELECT team FROM stg.rankings WHERE cycle = 2022
        ORDER BY team
    """).show()

    con.close()
