-- mart.ranking_vs_result — o ranking FIFA previu os resultados em 2022?
-- SÓ 2022 (não há ranking de 2018). Para cada partida, compara o rank das
-- duas seleções e verifica se a mais bem ranqueada venceu.
-- Usa o crosswalk p/ reconciliar nomes (ex.: United States -> USA).

CREATE OR REPLACE VIEW mart.ranking_vs_result AS
WITH r AS (
    SELECT team, rank FROM stg.rankings WHERE cycle = 2022
),
-- aplica crosswalk: resolve o nome do ranking a partir do nome da partida
resolved AS (
    SELECT
        m.year, m.round, m.home_team, m.away_team, m.winner,
        m.decided_on_pens,
        rh.rank AS home_rank,
        ra.rank AS away_rank
    FROM stg.matches m
    LEFT JOIN seed.team_crosswalk ch ON ch.match_name = m.home_team
    LEFT JOIN seed.team_crosswalk ca ON ca.match_name = m.away_team
    LEFT JOIN r rh ON rh.team = COALESCE(ch.ranking_name, m.home_team)
    LEFT JOIN r ra ON ra.team = COALESCE(ca.ranking_name, m.away_team)
    WHERE m.year = 2022
)
SELECT
    round,
    home_team, away_team,
    home_rank, away_rank,
    winner,
    -- seleção mais bem ranqueada (rank menor = melhor)
    CASE WHEN home_rank < away_rank THEN home_team ELSE away_team END AS higher_ranked,
    -- a favorita (por ranking) venceu? NULL em empate real de grupos
    CASE
        WHEN winner IS NULL THEN NULL
        WHEN (home_rank < away_rank AND winner = home_team)
          OR (away_rank < home_rank AND winner = away_team) THEN TRUE
        ELSE FALSE
    END                                                              AS favorite_won
FROM resolved;
