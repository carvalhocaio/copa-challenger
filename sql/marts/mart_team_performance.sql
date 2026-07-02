-- mart.team_performance - grão: uma linha por (seleção, edição).
-- KPIs ofensivos/defensivos e o eixo central do desk:
--  attack_vs_xg > 0 => marcou mais que o esperado (eficiência/sorte na finalização)
--  defense_vs_xg > 0 => sofreu menos gols que o xG concedido (defesa/goleiro/sorte)

CREATE OR REPLACE VIEW mart.team_performance AS
SELECT
    team,
    year,
    count(*) AS matches,
    count(*) FILTER (WHERE result = 'win') AS wins_reg,
    count(*) FILTER (WHERE result = 'draw') AS draws,
    count(*) FILTER (WHERE result = 'loss') AS losses_reg,
    count(*) FILTER (WHERE won_match) AS advanced_or_won,
    sum(goals_for) AS goals_for,
    sum(goals_against) AS goals_against,
    sum(goals_for) - sum(goals_against) AS goals_diff,
    round(sum(xg_for), 2) AS xg_for,
    round(sum(xg_against), 2) AS xg_against,
    round(sum(goals_for) - sum(xg_for), 2) AS attack_vs_xg,
    round(sum(xg_against) - sum(goals_against), 2) AS defense_vs_xg
FROM mart.int_team_matches
GROUP BY team, year;
