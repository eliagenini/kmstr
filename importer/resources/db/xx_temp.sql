create table if not exists vehicles
(
    vin         text not null
        constraint vehicles_pk
            primary key,
    model       text,
    nickname    text,
    image       text,
    online      boolean,
    last_update timestamp default CURRENT_TIMESTAMP,
    last_change timestamp default CURRENT_TIMESTAMP
);

alter table vehicles
    owner to kmstr_appl;

grant select on vehicles to anon;

grant insert, select, update on vehicles to data_producer;

create table if not exists ranges
(
    id                     serial
        constraint ranges_pk
            primary key,
    vin                    text                                not null
        constraint ranges_fk_vehicle
            references vehicles,
    total_range_km         integer                             not null,
    primary_current_pct    integer,
    primary_remaining_km   integer,
    secondary_current_pct  integer,
    secondary_remaining_km integer,
    captured_timestamp     timestamp default CURRENT_TIMESTAMP not null
);

alter table ranges
    owner to kmstr_appl;

grant select, usage on sequence ranges_id_seq to data_producer;

grant select on ranges to anon;

grant insert, select, update on ranges to data_producer;

create table if not exists mileages
(
    id                 serial
        constraint mileages_pk
            primary key,
    vin                text                                not null
        constraint mileages_fk_vehicle
            references vehicles,
    mileage_km         integer                             not null,
    captured_timestamp timestamp default CURRENT_TIMESTAMP not null
);

alter table mileages
    owner to kmstr_appl;

grant select, usage on sequence mileages_id_seq to data_producer;

grant select on mileages to anon;

grant insert, select, update on mileages to data_producer;

create table if not exists locations
(
    osm_id         bigint not null
        constraint locations_pk
            primary key,
    osm_type       text,
    latitude       numeric,
    longitude      numeric,
    display_name   text,
    name           text,
    amenity        text,
    house_number   text,
    road           text,
    neighbourhood  text,
    city           text,
    postcode       text,
    county         text,
    country        text,
    state          text,
    state_district text,
    raw            text
);

alter table locations
    owner to kmstr_appl;

create table if not exists trips
(
    id                       serial
        constraint trips_pk
            primary key,
    vin                      text                                not null
        constraint trips_fk_vehicle
            references vehicles,
    start_date               timestamp default CURRENT_TIMESTAMP not null,
    end_date                 timestamp,
    start_position_latitude  double precision                    not null,
    start_position_longitude double precision                    not null,
    start_location_id        bigint
        constraint trips_start_fk_location
            references locations,
    end_position_latitude    double precision,
    end_position_longitude   double precision,
    end_location_id          bigint
        constraint trips_end_fk_location
            references locations,
    start_mileage            integer                             not null,
    end_mileage              integer,
    last_modified            timestamp default CURRENT_TIMESTAMP not null
);

alter table trips
    owner to kmstr_appl;

grant select, usage on sequence trips_id_seq to data_producer;

grant select on trips to anon;

grant insert, select, update on trips to data_producer;

create table if not exists geofences
(
    id          serial
        constraint geofences_pk
            primary key,
    location_id integer
        constraint geofences_fk_location
            references locations,
    name        text    not null,
    latitude    numeric not null,
    longitude   numeric not null,
    radius      numeric not null
);

alter table geofences
    owner to kmstr_appl;

grant select, usage on sequence geofences_id_seq to data_producer;

grant select on geofences to anon;

grant insert, select, update on geofences to data_producer;

grant select on locations to anon;

grant insert, select, update on locations to data_producer;

create table if not exists refuels
(
    id          serial
        constraint refuels_pk
            primary key,
    location_id integer
        constraint refuels_fk_location
            references locations,
    date        timestamp,
    mileage_km  integer,
    start_pct   integer,
    end_pct     integer,
    latitude    numeric,
    longitude   numeric,
    vin         text not null
);

alter table refuels
    owner to kmstr_appl;

grant select, usage on sequence refuels_id_seq to data_producer;

grant select on refuels to anon;

grant insert, select, update on refuels to data_producer;

create table if not exists pictures
(
    id                 serial
        constraint pictures_pk
            primary key,
    vin                text                                not null
        constraint pictures_fk_vehicle
            references vehicles,
    name               text                                not null,
    image              bytea                               not null,
    captured_timestamp timestamp default CURRENT_TIMESTAMP not null
);

alter table pictures
    owner to kmstr_appl;

grant select, usage on sequence pictures_id_seq to data_producer;

grant select on pictures to anon;

grant insert, select, update on pictures to data_producer;

create table if not exists parkings
(
    id                 serial
        constraint parkings_pk
            primary key,
    vin                text                                not null
        constraint parkings_fk_vehicle
            references vehicles,
    location_id        bigint
        constraint parkings_fk_location
            references locations,
    latitude           numeric,
    longitude          numeric,
    captured_timestamp timestamp default CURRENT_TIMESTAMP not null
);

alter table parkings
    owner to kmstr_appl;

grant select, usage on sequence parkings_id_seq to data_producer;

grant select on parkings to anon;

grant insert, select, update on parkings to data_producer;

create or replace view daily_mileage(id, vin, mileage_km, date) as
WITH ranked_mileage AS (SELECT mileages.id,
                               mileages.vin,
                               mileages.mileage_km,
                               date_trunc('day'::text, mileages.captured_timestamp)                                                                               AS date,
                               mileages.captured_timestamp,
                               row_number()
                               OVER (PARTITION BY mileages.vin, (date_trunc('day'::text, mileages.captured_timestamp)) ORDER BY mileages.captured_timestamp DESC) AS rn
                        FROM kmstr.mileages)
SELECT id,
       vin,
       mileage_km,
       date
FROM ranked_mileage
WHERE rn = 1
ORDER BY date DESC, vin;

alter table daily_mileage
    owner to kmstr_appl;

grant select on daily_mileage to anon;

grant insert, select, update on daily_mileage to data_producer;

create or replace view daily_fuel_level(id, vin, primary_current_pct, date) as
WITH ranked_fuel_level AS (SELECT ranges.id,
                                  ranges.vin,
                                  ranges.primary_current_pct,
                                  date_trunc('day'::text, ranges.captured_timestamp)                                                                           AS date,
                                  ranges.captured_timestamp,
                                  row_number()
                                  OVER (PARTITION BY ranges.vin, (date_trunc('day'::text, ranges.captured_timestamp)) ORDER BY ranges.captured_timestamp DESC) AS rn
                           FROM kmstr.ranges)
SELECT id,
       vin,
       primary_current_pct,
       date
FROM ranked_fuel_level
WHERE rn = 1
ORDER BY date DESC, vin;

alter table daily_fuel_level
    owner to kmstr_appl;

grant select on daily_fuel_level to anon;

grant insert, select, update on daily_fuel_level to data_producer;

create or replace view daily_ranges(id, vin, total_range_km, date) as
WITH ranked_ranges AS (SELECT ranges.id,
                              ranges.vin,
                              ranges.total_range_km,
                              date_trunc('day'::text, ranges.captured_timestamp)                                                                           AS date,
                              ranges.captured_timestamp,
                              row_number()
                              OVER (PARTITION BY ranges.vin, (date_trunc('day'::text, ranges.captured_timestamp)) ORDER BY ranges.captured_timestamp DESC) AS rn
                       FROM kmstr.ranges)
SELECT id,
       vin,
       total_range_km,
       date
FROM ranked_ranges
WHERE rn = 1
ORDER BY date DESC, vin;

alter table daily_ranges
    owner to kmstr_appl;

grant select on daily_ranges to anon;

grant insert, select, update on daily_ranges to data_producer;

create or replace view current_mileage(id, vin, mileage_km, captured_timestamp) as
WITH ranked_mileage AS (SELECT mileages.id,
                               mileages.vin,
                               mileages.mileage_km,
                               mileages.captured_timestamp,
                               row_number()
                               OVER (PARTITION BY mileages.vin ORDER BY mileages.captured_timestamp DESC) AS rn
                        FROM kmstr.mileages)
SELECT id,
       vin,
       mileage_km,
       captured_timestamp
FROM ranked_mileage
WHERE rn = 1;

alter table current_mileage
    owner to kmstr_appl;

grant select on current_mileage to anon;

grant insert, select, update on current_mileage to data_producer;

create or replace view current_fuel_level(id, vin, primary_current_pct, captured_timestamp) as
WITH ranked_fuel_level AS (SELECT ranges.id,
                                  ranges.vin,
                                  ranges.primary_current_pct,
                                  ranges.captured_timestamp,
                                  row_number()
                                  OVER (PARTITION BY ranges.vin ORDER BY ranges.captured_timestamp DESC) AS rn
                           FROM kmstr.ranges)
SELECT id,
       vin,
       primary_current_pct,
       captured_timestamp
FROM ranked_fuel_level
WHERE rn = 1;

alter table current_fuel_level
    owner to kmstr_appl;

grant select on current_fuel_level to anon;

grant insert, select, update on current_fuel_level to data_producer;

create or replace view current_ranges(id, vin, total_range_km, captured_timestamp) as
WITH ranked_ranges AS (SELECT ranges.id,
                              ranges.vin,
                              ranges.total_range_km,
                              ranges.captured_timestamp,
                              row_number() OVER (PARTITION BY ranges.vin ORDER BY ranges.captured_timestamp DESC) AS rn
                       FROM kmstr.ranges)
SELECT id,
       vin,
       total_range_km,
       captured_timestamp
FROM ranked_ranges
WHERE rn = 1;

alter table current_ranges
    owner to kmstr_appl;

grant select on current_ranges to anon;

grant insert, select, update on current_ranges to data_producer;

create or replace view mileage_changes(vin, date, mileage_changed, mileage_difference) as
WITH daily_mileage AS (SELECT mileages.vin,
                              date_trunc('day'::text, mileages.captured_timestamp)                                                                               AS date,
                              mileages.mileage_km,
                              row_number()
                              OVER (PARTITION BY mileages.vin, (date_trunc('day'::text, mileages.captured_timestamp)) ORDER BY mileages.captured_timestamp DESC) AS rn
                       FROM kmstr.mileages),
     latest_mileage AS (SELECT daily_mileage.vin,
                               daily_mileage.date,
                               daily_mileage.mileage_km
                        FROM daily_mileage
                        WHERE daily_mileage.rn = 1),
     previous_day AS (SELECT latest_mileage.vin,
                             latest_mileage.date,
                             latest_mileage.mileage_km,
                             lag(latest_mileage.mileage_km)
                             OVER (PARTITION BY latest_mileage.vin ORDER BY latest_mileage.date) AS prev_day_mileage
                      FROM latest_mileage)
SELECT vin,
       date,
       CASE
           WHEN prev_day_mileage IS NULL THEN false
           ELSE mileage_km <> prev_day_mileage
           END AS mileage_changed,
       CASE
           WHEN prev_day_mileage IS NULL THEN NULL::integer
           ELSE mileage_km - prev_day_mileage
           END AS mileage_difference
FROM previous_day;

alter table mileage_changes
    owner to kmstr_appl;

grant select on mileage_changes to anon;

grant insert, select, update on mileage_changes to data_producer;

create or replace view current_parking(id, vin, osm_id, latitude, longitude, captured_timestamp) as
WITH ranked_parkings AS (SELECT pa.id,
                                pa.vin,
                                lo.osm_id,
                                pa.latitude,
                                pa.longitude,
                                pa.captured_timestamp,
                                row_number() OVER (PARTITION BY pa.vin ORDER BY pa.captured_timestamp DESC) AS rn
                         FROM kmstr.parkings pa
                                  LEFT JOIN kmstr.locations lo ON lo.osm_id = pa.location_id)
SELECT id,
       vin,
       osm_id,
       latitude,
       longitude,
       captured_timestamp
FROM ranked_parkings
WHERE rn = 1;

alter table current_parking
    owner to kmstr_appl;

grant select on current_parking to anon;

grant insert, select, update on current_parking to data_producer;

