select year, round, stage_order, home_team, away_team,
       home_score, away_score, winner
from mart.int_match_stages
where decided_on_pens
order by year, stage_order
