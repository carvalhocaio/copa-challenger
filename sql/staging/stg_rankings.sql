-- stg.rankings — snapshots de ranking FIFA em formato longo (long format).
-- Só o snapshot de 2022 alinha com uma edição em escopo; NÃO há ranking de 2018.
-- O de 2026 entra como dimensão de contexto (storytelling), nunca como escopo.

CREATE OR REPLACE VIEW stg.rankings AS
SELECT
    DATE '2022-10-06'    AS snapshot_date,
    2022                 AS cycle,
    team,
    team_code,
    association,
    rank,
    previous_rank,
    points,
    previous_points,
    CAST(NULL AS BIGINT) AS rated_matches
FROM raw.ranking_2022
UNION ALL
SELECT
    DATE '2026-06-08'    AS snapshot_date,
    2026                 AS cycle,
    team,
    team_code,
    association,
    rank,
    previous_rank,
    points,
    previous_points,
    rated_matches
FROM raw.ranking_2026;
