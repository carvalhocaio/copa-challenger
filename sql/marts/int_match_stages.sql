-- mart.int_match_stages — enriquece cada partida com metadados de fase.
-- stage_type: 'group' vs 'knockout'; stage_order p/ ordenação cronológica
-- do chaveamento. Base p/ análises de mata-mata (pênaltis, xG por fase).

CREATE OR REPLACE VIEW mart.int_match_stages AS
SELECT
    *,
    CASE WHEN round = 'Group stage' THEN 'group' ELSE 'knockout' END AS stage_type,
    CASE round
        WHEN 'Group stage'       THEN 1
        WHEN 'Round of 16'       THEN 2
        WHEN 'Quarter-finals'    THEN 3
        WHEN 'Semi-finals'       THEN 4
        WHEN 'Third-place match' THEN 5
        WHEN 'Final'             THEN 6
    END AS stage_order
FROM stg.matches;
