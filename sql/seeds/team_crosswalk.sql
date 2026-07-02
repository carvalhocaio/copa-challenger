-- seed.team_crosswalk — reconcilia nomes de seleção entre fontes.
-- `match_name` = como aparece em stg.matches; `ranking_name` = em stg.rankings.
-- Diagnóstico mostrou só 1 divergência (United States) no escopo 2022;
-- estrutura permite crescer sem tocar nos modelos.

CREATE OR REPLACE TABLE seed.team_crosswalk (
    match_name    VARCHAR,
    ranking_name  VARCHAR
);

INSERT INTO seed.team_crosswalk VALUES
    ('United States', 'USA');
    -- confirme o valor real com o comando de sanity antes de assumir 'USA'.
