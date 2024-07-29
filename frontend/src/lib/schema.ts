import {
  pgTable,
  pgSchema,
  text,
  numeric,
  integer,
  timestamp,
  pgEnum,
  serial
} from 'drizzle-orm/pg-core';
import { relations } from "drizzle-orm"


export const mySchema = pgSchema("kmstr")

export const current_mileage = mySchema.table(
  'current_mileage',
  {
    id: integer('id'),
    vin: text('vin'),
    km: integer('mileage_km'),
    captured: timestamp('captured_timestamp')
  });

export const current_fuel_level = mySchema.table(
    'current_fuel_level',
    {
        id: integer('id'),
        vin: text('vin'),
        level: integer('primary_current_pct'),
        captured: timestamp('captured_timestamp')
    });

export const current_ranges = mySchema.table(
    'current_ranges',
    {
        id: integer('id'),
        vin: text('vin'),
        km: integer('total_range_km'),
        captured: timestamp('captured_timestamp')
    });
export const vehicles = mySchema.table(
  'vehicles',
  {
    vin: text('vin').primaryKey(),
    model: text('model'),
    nickname: text('nickname'),
    lastUpdate: timestamp('last_update'),
    lastChange: timestamp('last_change'),
  });

export const pictures = mySchema.table(
  'pictures',
  {
    id: serial('id').primaryKey(),
    vin: text('vin').notNull().references(() => vehicles.vin),
    type: text('name'),
    image: text('image')
  });

export const picturesRelations = relations(pictures,({one}) => ({
  vehicle: one(vehicles, {
    fields: [pictures.vin],
    references: [vehicles.vin]
  })
}));

export const vehiclesRelations = relations(vehicles,({many})=> ({
  pictures: many(pictures)
}));