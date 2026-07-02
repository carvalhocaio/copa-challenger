-- mart.int_team_matches - grão: uma linha por (partida, seleção).
-- Desnormaliza stg.matches em perspectiva "do time", habilitando
-- agregações por seleção. Reutilizado no dashboard e no agente.

CREATE OR REPLACE VIEW mart.int_team_matches AS
SELECT
    year, match_date, round, host,
    home_team AS team,
    away_team AS opponent,
    TRUE AS is_home,
    home_score AS goals_for,
    away_score AS goals_against,
    home_xg AS xg_for,
    away_xg AS xg_against,
    home_pens AS pens_for,
    away_pens AS pens_against,
    decided_on_pens,
    CASE
        WHEN home_score > away_score THEN 'win'
        WHEN home_score < away_score THEN 'loss'
        ELSE 'draw'
    END AS result,
    (winner = home_team) AS won_match -- inclui decisão por pênaltis
FROM stg.matches
UNION ALL
SELECT
    year, match_date, round, host,
    away_team AS team,
    home_team AS opponent,
    FALSE AS is_home,
    away_score AS goals_for,
    home_score AS goals_against,
    away_xg AS xg_for,
    home_xg AS xg_against,
    away_pens AS pens_for,
    home_pens AS pens_against,
    decided_on_pens,
    CASE
        WHEN away_score > home_score THEN 'win'
        WHEN away_score < home_score THEN 'loss'
        ELSE 'draw'
    END AS result,
    (winner = away_team) AS won_match
FROM stg.matches;
