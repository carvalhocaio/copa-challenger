-- seed.team_crosswalk — reconcilia nomes de seleção entre fontes.
-- `match_name` = como aparece em stg.matches/raw.schedule_2026;
-- `ranking_name` = como aparece em stg.rankings/raw.ranking_2026.
-- Reaproveitada pelos ciclos 2022 (mart.ranking_vs_result) e 2026
-- (mart preditivo): sem coluna de ciclo porque, hoje, nenhum match_name
-- diverge de forma diferente entre os dois ciclos. Se isso mudar, resolver
-- fica ambíguo — revisar então.

CREATE OR REPLACE TABLE seed.team_crosswalk (
    match_name    VARCHAR,
    ranking_name  VARCHAR
);

INSERT INTO seed.team_crosswalk VALUES
    ('United States', 'USA'),
    ('Bosnia-Herzegovina', 'Bosnia and Herzegovina'),
    ('Cape Verde', 'Cabo Verde');
