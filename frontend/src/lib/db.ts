import 'server-only';

import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

import { count, eq } from 'drizzle-orm';
import { vehicles, pictures, picturesRelations, vehiclesRelations } from "./schema";
import { current_mileage, current_ranges, current_fuel_level } from "./schema"; // views

export const db = drizzle(
    postgres(process.env.POSTGRES_URL!),
    {
      schema:
          {
            vehicles,
            pictures,
            picturesRelations,
            vehiclesRelations,
            current_mileage,
            current_fuel_level,
            current_ranges}
    });

export const getVehiclesWithPictures = async () => {
  return {
    vehicles: await db.query.vehicles.findMany({with: {pictures: true}}),
    totalVehicles: await db.select({ count: count() }).from(vehicles)
  };
}

export const getCurrentMileage = async () => {
  const mileages = await db.query.current_mileage.findMany()
  return {
    mileage: mileages.reduce((total: number, current) => total + current.km, 0)
  }
}

export const getCurrentMileageByVehicle = async (vin: string) => {
  return {
    mileage: await db
        .select({
          km: current_mileage.km
        })
        .from(current_mileage)
        .where(eq(current_mileage.vin, vin))
  }
}


export const getCurrentFuelByVehicle = async (vin: string) => {
    return {
        fuel: await db
            .select({
                level: current_fuel_level.level
            })
            .from(current_fuel_level)
            .where(eq(current_fuel_level.vin, vin))
    }
}

export const getCurrentRangeByVehicle = async (vin: string) => {
    return {
        range: await db
            .select({
                km: current_ranges.km
            })
            .from(current_ranges)
            .where(eq(current_ranges.vin, vin))
    }
}

export type SelectVehicle = typeof vehicles.$inferSelect;
export type SelectPicture = typeof pictures.$inferSelect;

export async function getVehicles(
  search: string,
  offset: number
): Promise<{
  vehicles: SelectVehicle[];
  newOffset: number | null;
  totalVehicles: number;
}> {
  // Always search the full table, not per page
  if (search) {
    return {
      vehicles: await db
        .select()
        .from(vehicles)
        .rightJoin(pictures, eq(vehicles.vin, pictures.vin)),
      newOffset: null,
      totalVehicles: 0
    };
  }

  if (offset === null) {
    return { vehicles: [], newOffset: null, totalVehicles: 0 };
  }

  let totalVehicles = await db.select({ count: count() }).from(vehicles);
  let moreVehicles = await db.select().from(vehicles).limit(5).offset(offset);
  let newOffset = moreVehicles.length >= 5 ? offset + 5 : null;

  return {
    vehicles: moreVehicles,
    newOffset,
    totalVehicles: totalVehicles[0].count
  };
}
