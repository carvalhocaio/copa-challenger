-- mart.edition_kpis - grão: uma linha por edição (Rússia 2018 x Catar 2022).
-- KPIs de alto nível do torneio, base do comparativo entre ciclos.

CREATE OR REPLACE VIEW mart.edition_kpis AS
SELECT
    m.year,
    any_value(m.host) AS host,
    count(*) AS n_matches,
    sum(m.total_goals) AS total_goals,
    round(avg(m.total_goals), 2) AS goals_per_match,
    round(avg(m.home_xg + m.away_xg), 2) AS xg_per_match,
    round(avg(m.total_goals) - avg(m.home_xg + m.away_xg), 2) AS goals_minus_xg,
    count(*) FILTER (WHERE m.decided_on_pens) AS pen_shootouts,
    round(avg(m.attendance)) AS avg_attendance,
    any_value(w.champion) AS champion,
    any_value(w.runner_up) AS runner_up,
    any_value(w.top_scorer) AS top_scorer
FROM stg.matches m
LEFT JOIN stg.world_cup w USING (year)
GROUP BY m.year
ORDER BY m.year;
