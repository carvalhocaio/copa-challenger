select
    year, round, stage_type,
    home_team, away_team,
    home_score, away_score, total_goals,
    home_xg, away_xg, (home_xg + away_xg) as xg_total,
    decided_on_pens, winner
from mart.int_match_stages
order by year, stage_order
