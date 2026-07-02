-- stg.world_cup — resumo por edição, restrito ao escopo 2018/2022.
-- Nota: "TopScorrer" preserva o typo da origem; "Runner-Up" precisa de aspas.

CREATE OR REPLACE VIEW stg.world_cup AS
SELECT
    Year AS year,
    Host AS host,
    Teams AS n_teams,
    Champion AS champion,
    "Runner-Up" AS runner_up,
    TopScorrer AS top_scorer,
    Attendance AS attendance_total,
    AttendanceAvg AS attendance_avg,
    Matches AS n_matches
FROM raw.world_cup
WHERE Year IN (2018, 2022);
