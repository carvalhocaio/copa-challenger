-- mart.knockout_analysys - dinâmica de mata-mata por edição.
-- Responde: os jogos ficam mais travados (menos gols, mais pênaltis)
-- conforme o torneio avança?

CREATE OR REPLACE VIEW mart.knockout_analysys AS
SELECT
    year,
    round,
    any_value(stage_order) AS stage_order,
    count(*) AS n_matches,
    round(avg(total_goals), 2) AS goals_per_match,
    round(avg(home_xg + away_xg), 2) AS xg_per_match,
    count(*) FILTER (WHERE decided_on_pens) AS pen_shootouts
FROM mart.int_match_stages
WHERE stage_type = 'knockout'
GROUP BY year, round
ORDER BY year, stage_order;
