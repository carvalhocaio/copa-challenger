-- mart.team_strength_inputs — grão: uma linha por seleção, pooling 2018+2022.
-- Insumo do modelo preditivo (Missão 04): soma bruta (não médias por edição)
-- porque, com amostras deste tamanho, mais jogos agregados dão estimativa
-- mais estável do que separar por ano. O shrinkage/normalização por
-- volume de jogos acontece em Python (predict/features.py).

CREATE OR REPLACE VIEW mart.team_strength_inputs AS
SELECT
    team,
    sum(matches)       AS matches,
    sum(goals_for)      AS goals_for,
    sum(goals_against)  AS goals_against,
    sum(xg_for)          AS xg_for,
    sum(xg_against)      AS xg_against
FROM mart.team_performance
GROUP BY team;
