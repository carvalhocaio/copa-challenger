-- stg.matches — partidas das Copas de 2018 e 2022 (escopo da competição).
-- A camada raw preserva 1930–2022; o recorte do desafio é aplicado AQUI,
-- de forma explícita e auditável (boa prática: regra de negócio na staging).

CREATE OR REPLACE VIEW stg.matches AS
WITH base AS (
    SELECT
        Year AS year,
        Date AS match_date,
        Host AS host,
        Round AS round,
        Venue AS venue,
        Attendance AS attendance,
        home_team,
        away_team,
        home_score,
        away_score,
        home_xg,
        away_xg,
        home_penalty AS home_pens,   -- gols na disputa por pênaltis (shootout)
        away_penalty AS away_pens,
        home_manager,
        away_manager,
        home_captain,
        away_captain,
        Referee AS referee,
        Notes AS notes
    FROM raw.matches
    WHERE Year IN (2018, 2022)
)
SELECT
    *,
    home_score + away_score AS total_goals,
    home_score - away_score AS home_goal_diff,
    -- defensivo contra 0 vs NULL: soma dos gols de shootout > 0
    (COALESCE(home_pens, 0) + COALESCE(away_pens, 0)) > 0 AS decided_on_pens,
    CASE
        WHEN home_score > away_score THEN 'home_win'
        WHEN home_score < away_score THEN 'away_win'
        ELSE 'draw'
    END AS result_regulation,
    -- vencedor considerando pênaltis; NULL = empate real (fase de grupos)
    CASE
        WHEN home_score > away_score THEN home_team
        WHEN away_score > home_score THEN away_team
        WHEN COALESCE(home_pens, 0) > COALESCE(away_pens, 0) THEN home_team
        WHEN COALESCE(away_pens, 0) > COALESCE(home_pens, 0) THEN away_team
        ELSE NULL
    END                                                  AS winner,
    -- performance ofensiva vs. esperado (só onde há xG)
    CASE
        WHEN home_xg IS NOT NULL AND away_xg IS NOT NULL
        THEN round((home_score + away_score) - (home_xg + away_xg), 2)
    END AS goals_minus_xg
FROM base;
