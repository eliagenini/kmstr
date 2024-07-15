-- Daily

BEGIN;

SET client_encoding = 'UTF_8';

-- Daily mileage
CREATE OR REPLACE VIEW kmstr.daily_mileage AS
WITH ranked_mileage AS (SELECT id,
                               vehicle,
                               mileage,
                               DATE_TRUNC('day', last_modified)                                                          AS date,
                               last_modified,
                               ROW_NUMBER()
                               OVER (PARTITION BY vehicle, DATE_TRUNC('day', last_modified) ORDER BY last_modified DESC) AS rn
                        FROM kmstr.mileage)
SELECT id,
       vehicle,
       mileage,
       date
FROM ranked_mileage
WHERE rn = 1
ORDER BY date desc, vehicle asc;

CREATE OR REPLACE VIEW kmstr.daily_mileage AS
WITH ranked_mileage AS (SELECT id,
                               vehicle,
                               mileage,
                               DATE_TRUNC('day', last_modified)                                                          AS date,
                               last_modified,
                               ROW_NUMBER()
                               OVER (PARTITION BY vehicle, DATE_TRUNC('day', last_modified) ORDER BY last_modified DESC) AS rn
                        FROM kmstr.mileage)
SELECT id,
       vehicle,
       mileage,
       date
FROM ranked_mileage
WHERE rn = 1
ORDER BY date desc, vehicle asc;

-- Daily fuel level
CREATE OR REPLACE VIEW kmstr.daily_fuel_level AS
WITH ranked_fuel_level AS (SELECT id,
                                  vehicle,
                                  level,
                                  DATE_TRUNC('day', last_modified)                                                          AS date,
                                  last_modified,
                                  ROW_NUMBER()
                                  OVER (PARTITION BY vehicle, DATE_TRUNC('day', last_modified) ORDER BY last_modified DESC) AS rn
                           FROM kmstr.fuel_level)
SELECT id,
       vehicle,
       level,
       date
FROM ranked_fuel_level
WHERE rn = 1
ORDER BY date desc, vehicle asc;

-- Daily total range
CREATE OR REPLACE VIEW kmstr.daily_total_range AS
WITH ranked_total_range AS (SELECT id,
                                   vehicle,
                                   range,
                                   DATE_TRUNC('day', last_modified)                                                          AS date,
                                   last_modified,
                                   ROW_NUMBER()
                                   OVER (PARTITION BY vehicle, DATE_TRUNC('day', last_modified) ORDER BY last_modified DESC) AS rn
                            FROM kmstr.total_range)
SELECT id,
       vehicle,
       range,
       date
FROM ranked_total_range
WHERE rn = 1
ORDER BY date desc, vehicle asc;

COMMIT;

-- Current
BEGIN;

SET client_encoding = 'UTF_8';

-- Current mileage
CREATE OR REPLACE VIEW kmstr.current_mileage AS
WITH ranked_mileage AS (SELECT id,
                               vehicle,
                               mileage,
                               last_modified,
                               ROW_NUMBER() OVER (PARTITION BY vehicle ORDER BY last_modified DESC) AS rn
                        FROM kmstr.mileage)
SELECT id,
       vehicle,
       mileage,
       last_modified
FROM ranked_mileage
WHERE rn = 1;

-- Daily fuel level
CREATE OR REPLACE VIEW kmstr.current_fuel_level AS
WITH ranked_fuel_level AS (SELECT id,
                                  vehicle,
                                  level,
                                  last_modified,
                                  ROW_NUMBER() OVER (PARTITION BY vehicle ORDER BY last_modified DESC) AS rn
                           FROM kmstr.fuel_level)
SELECT id,
       vehicle,
       level,
       last_modified
FROM ranked_fuel_level
WHERE rn = 1;

-- Daily total range
CREATE OR REPLACE VIEW kmstr.current_total_range AS
WITH ranked_total_range AS (SELECT id,
                                   vehicle,
                                   range,
                                   last_modified,
                                   ROW_NUMBER() OVER (PARTITION BY vehicle ORDER BY last_modified DESC) AS rn
                            FROM kmstr.total_range)
SELECT id,
       vehicle,
       range,
       last_modified
FROM ranked_total_range
WHERE rn = 1;

COMMIT;

BEGIN;

CREATE OR REPLACE VIEW kmstr.mileage_changes AS
WITH daily_mileage AS (
    SELECT
        vehicle,
        DATE_TRUNC('day', last_modified) AS date,
        mileage,
        ROW_NUMBER() OVER (PARTITION BY vehicle, DATE_TRUNC('day', last_modified) ORDER BY last_modified DESC) AS rn
    FROM
        kmstr.mileage
), latest_mileage AS (
    SELECT
        vehicle,
        date,
        mileage
    FROM
        daily_mileage
    WHERE
        rn = 1
), previous_day AS (
    SELECT
        vehicle,
        date,
        mileage,
        LAG(mileage) OVER (PARTITION BY vehicle ORDER BY date) AS prev_day_mileage
    FROM
        latest_mileage
)
SELECT
    vehicle,
    date,
    CASE
        WHEN prev_day_mileage IS NULL THEN false -- Nessun giorno precedente disponibile
        ELSE (mileage != prev_day_mileage)
        END AS mileage_changed,
    CASE
        WHEN prev_day_mileage IS NULL THEN NULL -- Nessun giorno precedente disponibile
        ELSE (mileage - prev_day_mileage)
        END AS mileage_difference
FROM
    previous_day;

COMMIT;