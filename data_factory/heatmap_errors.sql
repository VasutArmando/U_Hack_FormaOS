-- Harta de Căldură a Erorilor sub Presiune
-- Descriere: Identifică unde pierde mingea adversarul (sub presiune adversă)
-- pe parcursul ultimelor 5 meciuri, generând o rețea spațială (grid) de vulnerabilitate.

WITH Last5Matches AS (
    -- Găsim ultimele 5 meciuri ale echipei adverse
    SELECT DISTINCT match_id, match_date
    FROM `forma-os.analytics.match_metadata`
    WHERE team_id = @opponent_team_id
    ORDER BY match_date DESC
    LIMIT 5
),
ErrorEvents AS (
    -- Filtrăm doar evenimentele unificate unde se pierde mingea sub presiune
    SELECT 
        match_id,
        x,
        y,
        event_type
    FROM `forma-os.analytics.unified_events`
    WHERE 
        team_id = @opponent_team_id
        AND match_id IN (SELECT match_id FROM Last5Matches)
        AND is_under_pressure = TRUE
        AND event_type IN ('Dispossessed', 'Miscontrol', 'Pass')
        -- Dacă este Pasă, ne interesează doar pasele interceptate/greșite
        -- Presupunem că JSON-ul din BQ a fost parsat și are un field pass_outcome
        AND (event_type != 'Pass' OR JSON_EXTRACT_SCALAR(tracking_360, '$.pass_outcome') = 'Incomplete')
)
SELECT 
    -- Împărțim terenul (ex. 120m x 80m) într-un Grid de 10x10 metri
    CAST(FLOOR(x / 10) * 10 AS INT64) AS grid_x_start,
    CAST(FLOOR(y / 10) * 10 AS INT64) AS grid_y_start,
    COUNT(*) AS error_density_score
FROM 
    ErrorEvents
GROUP BY 
    grid_x_start, grid_y_start
HAVING 
    error_density_score > 2 -- Eliminăm zgomotul (doar grid-urile cu erori recurente)
ORDER BY 
    error_density_score DESC;
