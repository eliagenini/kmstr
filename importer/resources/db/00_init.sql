BEGIN;

SET client_encoding = 'UTF_8';

CREATE SCHEMA IF NOT EXISTS kmstr;

CREATE ROLE authenticator LOGIN NOINHERIT NOCREATEDB NOCREATEROLE NOSUPERUSER;
ALTER USER authenticator PASSWORD 'great-password';

CREATE ROLE anon nologin;
GRANT anon TO authenticator;

GRANT USAGE ON SCHEMA kmstr TO anon;
ALTER DEFAULT PRIVILEGES IN SCHEMA kmstr GRANT SELECT ON TABLES TO anon;

CREATE ROLE data_producer nologin;
GRANT data_producer TO authenticator;

GRANT USAGE ON SCHEMA kmstr TO data_producer;
ALTER DEFAULT PRIVILEGES IN SCHEMA kmstr GRANT SELECT, INSERT, UPDATE ON TABLES TO data_producer;
ALTER DEFAULT PRIVILEGES IN SCHEMA kmstr GRANT USAGE, SELECT ON SEQUENCES TO data_producer;

CREATE TABLE IF NOT EXISTS kmstr.vehicles
(
    vin         text      NOT NULL,
    model       text,
    nickname    text,
    image       text,
    online      boolean,
    last_update timestamp DEFAULT CURRENT_TIMESTAMP,
    last_change timestamp DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kmstr.ranges
(
    id                     serial    NOT NULL,
    vin                    text      NOT NULL,
    total_range_km         integer   NOT NULL,
    primary_current_pct    integer,
    primary_remaining_km   integer,
    secondary_current_pct  integer,
    secondary_remaining_km integer,
    captured_timestamp     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kmstr.trips
(
    id                       serial    NOT NULL,
    vin                      text      NOT NULL,
    start_date               timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date                 timestamp,
    start_position_latitude  float     NOT NULL,
    start_position_longitude float     NOT NULL,
    start_location_id bigint,
    end_position_latitude    float,
    end_position_longitude   float,
    end_location_id bigint,
    start_mileage            integer   NOT NULL,
    end_mileage              integer,
    last_modified            timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kmstr.mileages
(
    id            serial    NOT NULL,
    vin           text      NOT NULL,
    mileage_km       integer   NOT NULL,
    captured_timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CREATE TABLE IF NOT EXISTS kmstr.parking
-- (
--     id            serial    NOT NULL,
--     vin           text      NOT NULL,
--     latitude      numeric   NOT NULL,
--     longitude     numeric   NOT NULL,
--     last_modified timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
-- );
--

CREATE TABLE IF NOT EXISTS kmstr.geofences
(
    id  serial NOT NULL,
    location_id integer,
    name text NOT NULL,
    latitude numeric NOT NULL,
    longitude numeric NOT NULL,
    radius numeric NOT NULL
);

CREATE TABLE IF NOT EXISTS kmstr.locations
(
    osm_id bigint NOT NULL,
    osm_type text,
    latitude numeric,
    longitude numeric,
    display_name text,
    name text,
    amenity text,
    house_number text,
    road text,
    neighbourhood text,
    city text,
    postcode text,
    county text,
    country text,
    state text,
    state_district text,
    raw text
);

CREATE TABLE IF NOT EXISTS kmstr.refuels
(
    id  serial NOT NULL,
    location_id integer,
    date timestamp,
    mileage_km integer,
    start_pct integer,
    end_pct integer,
    latitude numeric,
    longitude numeric
);

ALTER TABLE ONLY kmstr.vehicles
    ADD CONSTRAINT vehicles_pk PRIMARY KEY (vin);
ALTER TABLE ONLY kmstr.ranges
    ADD CONSTRAINT ranges_pk PRIMARY KEY (id),
    ADD CONSTRAINT ranges_fk_vehicle FOREIGN KEY (vin) REFERENCES kmstr.vehicles (vin);
ALTER TABLE ONLY kmstr.mileages
    ADD CONSTRAINT mileages_pk PRIMARY KEY (id),
    ADD CONSTRAINT mileages_fk_vehicle FOREIGN KEY (vin) REFERENCES kmstr.vehicles (vin);
-- ALTER TABLE ONLY kmstr.parking
--     ADD CONSTRAINT parking_pk PRIMARY KEY (id),
--     ADD CONSTRAINT parking_fk_vehicle FOREIGN KEY (vin) REFERENCES kmstr.vehicles (vin);
ALTER TABLE ONLY kmstr.locations
    ADD CONSTRAINT locations_pk PRIMARY KEY (osm_id);
ALTER TABLE ONLY kmstr.geofences
    ADD CONSTRAINT geofences_pk PRIMARY KEY (id),
    ADD CONSTRAINT geofences_fk_location FOREIGN KEY (location_id) REFERENCES kmstr.locations (osm_id);
ALTER TABLE ONLY kmstr.trips
    ADD CONSTRAINT trips_pk PRIMARY KEY (id),
    ADD CONSTRAINT trips_fk_vehicle FOREIGN KEY (vin) REFERENCES kmstr.vehicles (vin),
    ADD CONSTRAINT trips_start_fk_location FOREIGN KEY (start_location_id) REFERENCES kmstr.locations (osm_id),
    ADD CONSTRAINT trips_end_fk_location FOREIGN KEY (end_location_id) REFERENCES kmstr.locations (osm_id);
ALTER TABLE ONLY kmstr.refuels
    ADD CONSTRAINT refuels_pk PRIMARY KEY (id),
    ADD CONSTRAINT refuels_fk_location FOREIGN KEY (location_id) REFERENCES kmstr.locations (osm_id);

COMMIT;

NOTIFY pgrst, 'reload schema';