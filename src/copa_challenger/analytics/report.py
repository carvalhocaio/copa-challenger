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
