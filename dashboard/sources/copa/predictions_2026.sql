select
    round,
    date,
    home_team,
    away_team,
    expected_home_goals,
    expected_away_goals,
    prob_home_win,
    prob_draw,
    prob_away_win
from predict.predictions_2026
order by date, home_team
