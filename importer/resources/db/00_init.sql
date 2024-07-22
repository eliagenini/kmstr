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
    id       serial NOT NULL,
    vin      text   NOT NULL,
    model    text,
    nickname text,
    image    text,
    last_update timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_change timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kmstr.fuel_type
(
    id   serial NOT NULL,
    type text   NOT NULL
);

CREATE TABLE IF NOT EXISTS kmstr.fuel_level
(
    id            serial    NOT NULL,
    vehicle       integer   NOT NULL,
    level         integer   NOT NULL,
    last_modified timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kmstr.total_range
(
    id            serial    NOT NULL,
    vehicle       integer   NOT NULL,
    range         integer   NOT NULL,
    last_modified timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kmstr.mileage
(
    id            serial    NOT NULL,
    vehicle       integer   NOT NULL,
    mileage       integer   NOT NULL,
    last_modified timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kmstr.parking
(
    id            serial    NOT NULL,
    vehicle       integer   NOT NULL,
    latitude      numeric   NOT NULL,
    longitude     numeric   NOT NULL,
    last_modified timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE ONLY kmstr.vehicles
    ADD CONSTRAINT vehicles_pk PRIMARY KEY (id);
ALTER TABLE ONLY kmstr.fuel_type
    ADD CONSTRAINT fuel_type_pk PRIMARY KEY (id);
ALTER TABLE ONLY kmstr.fuel_level
    ADD CONSTRAINT fuel_level_pk PRIMARY KEY (id),
    ADD CONSTRAINT fuel_level_fk_vehicle FOREIGN KEY (vehicle) REFERENCES kmstr.vehicles (id);
ALTER TABLE ONLY kmstr.total_range
    ADD CONSTRAINT total_range_pk PRIMARY KEY (id),
    ADD CONSTRAINT total_range_fk_vehicle FOREIGN KEY (vehicle) REFERENCES kmstr.vehicles (id);
ALTER TABLE ONLY kmstr.mileage
    ADD CONSTRAINT mileage_pk PRIMARY KEY (id),
    ADD CONSTRAINT mileage_fk_vehicle FOREIGN KEY (vehicle) REFERENCES kmstr.vehicles (id);
ALTER TABLE ONLY kmstr.parking
    ADD CONSTRAINT parking_pk PRIMARY KEY (id),
    ADD CONSTRAINT parking_fk_vehicle FOREIGN KEY (vehicle) REFERENCES kmstr.vehicles (id);

COMMIT;

BEGIN;

INSERT INTO kmstr.fuel_type (id, type)
VALUES (1, 'Gasoline');
INSERT INTO kmstr.fuel_type (id, type)
VALUES (2, 'Diesel');
INSERT INTO kmstr.fuel_type (id, type)
VALUES (3, 'Other');

COMMIT;

NOTIFY pgrst, 'reload schema';