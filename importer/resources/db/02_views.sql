-- Daily

BEGIN;

SET client_encoding = 'UTF_8';

-- Daily mileage
CREATE OR REPLACE VIEW kmstr.daily_mileage AS
WITH ranked_mileage AS (SELECT id,
                               vin,
                               mileage_km,
                               DATE_TRUNC('day', captured_timestamp)                                                           AS date,
                               captured_timestamp,
                               ROW_NUMBER()
                               OVER (PARTITION BY vin, DATE_TRUNC('day', captured_timestamp) ORDER BY captured_timestamp DESC) AS rn
                        FROM kmstr.mileages)
SELECT id,
       vin,
       mileage_km,
       date
FROM ranked_mileage
WHERE rn = 1
ORDER BY date desc, vin asc;

-- Daily fuel level
CREATE OR REPLACE VIEW kmstr.daily_fuel_level AS
WITH ranked_fuel_level AS (SELECT id,
                                  vin,
                                  primary_current_pct,
                                  DATE_TRUNC('day', captured_timestamp)                                                           AS date,
                                  captured_timestamp,
                                  ROW_NUMBER()
                                  OVER (PARTITION BY vin, DATE_TRUNC('day', captured_timestamp) ORDER BY captured_timestamp DESC) AS rn
                           FROM kmstr.ranges)
SELECT id,
       vin,
       primary_current_pct,
       date
FROM ranked_fuel_level
WHERE rn = 1
ORDER BY date desc, vin asc;

-- Daily total range
CREATE OR REPLACE VIEW kmstr.daily_ranges AS
WITH ranked_ranges AS (SELECT id,
                              vin,
                              total_range_km,
                              DATE_TRUNC('day', captured_timestamp)                                                           AS date,
                              captured_timestamp,
                              ROW_NUMBER()
                              OVER (PARTITION BY vin, DATE_TRUNC('day', captured_timestamp) ORDER BY captured_timestamp DESC) AS rn
                       FROM kmstr.ranges)
SELECT id,
       vin,
       total_range_km,
       date
FROM ranked_ranges
WHERE rn = 1
ORDER BY date desc, vin asc;

COMMIT;

-- Current
BEGIN;

SET client_encoding = 'UTF_8';

-- Current mileage
CREATE OR REPLACE VIEW kmstr.current_mileage AS
WITH ranked_mileage AS (SELECT id,
                               vin,
                               mileage_km,
                               captured_timestamp,
                               ROW_NUMBER() OVER (PARTITION BY vin ORDER BY captured_timestamp DESC) AS rn
                        FROM kmstr.mileages)
SELECT id,
       vin,
       mileage_km,
       captured_timestamp
FROM ranked_mileage
WHERE rn = 1;

-- Daily fuel level
CREATE OR REPLACE VIEW kmstr.current_fuel_level AS
WITH ranked_fuel_level AS (SELECT id,
                                  vin,
                                  primary_current_pct,
                                  captured_timestamp,
                                  ROW_NUMBER() OVER (PARTITION BY vin ORDER BY captured_timestamp DESC) AS rn
                           FROM kmstr.ranges)
SELECT id,
       vin,
       primary_current_pct,
       captured_timestamp
FROM ranked_fuel_level
WHERE rn = 1;

-- Daily total range
CREATE OR REPLACE VIEW kmstr.current_ranges AS
WITH ranked_ranges AS (SELECT id,
                              vin,
                              total_range_km,
                              captured_timestamp,
                              ROW_NUMBER() OVER (PARTITION BY vin ORDER BY captured_timestamp DESC) AS rn
                       FROM kmstr.ranges)
SELECT id,
       vin,
       total_range_km,
       captured_timestamp
FROM ranked_ranges
WHERE rn = 1;

COMMIT;

BEGIN;

CREATE OR REPLACE VIEW kmstr.mileage_changes AS
WITH daily_mileage AS (SELECT vin,
                              DATE_TRUNC('day', captured_timestamp)                                                           AS date,
                              mileage_km,
                              ROW_NUMBER()
                              OVER (PARTITION BY vin, DATE_TRUNC('day', captured_timestamp) ORDER BY captured_timestamp DESC) AS rn
                       FROM kmstr.mileages),
     latest_mileage AS (SELECT vin,
                               date,
                               mileage_km
                        FROM daily_mileage
                        WHERE rn = 1),
     previous_day AS (SELECT vin,
                             date,
                             mileage_km,
                             LAG(mileage_km) OVER (PARTITION BY vin ORDER BY date) AS prev_day_mileage
                      FROM latest_mileage)
SELECT vin,
       date,
       CASE
           WHEN prev_day_mileage IS NULL THEN false -- Nessun giorno precedente disponibile
           ELSE (mileage_km != prev_day_mileage)
           END AS mileage_changed,
       CASE
           WHEN prev_day_mileage IS NULL THEN NULL -- Nessun giorno precedente disponibile
           ELSE (mileage_km - prev_day_mileage)
           END AS mileage_difference
FROM previous_day;

COMMIT;