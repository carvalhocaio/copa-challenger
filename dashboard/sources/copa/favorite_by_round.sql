select
    round,
    case round
        when 'Group stage'       then 1
        when 'Round of 16'       then 2
        when 'Quarter-finals'    then 3
        when 'Semi-finals'       then 4
        when 'Third-place match' then 5
        when 'Final'             then 6
    end as stage_order,
    count(*) filter (where favorite_won is not null)  as decided,
    count(*) filter (where favorite_won)              as favorite_wins,
    round(100.0 * count(*) filter (where favorite_won)
          / nullif(count(*) filter (where favorite_won is not null), 0), 1)
                                                      as favorite_win_pct
from mart.ranking_vs_result
group by round
having count(*) filter (where favorite_won is not null) > 0
order by stage_order
