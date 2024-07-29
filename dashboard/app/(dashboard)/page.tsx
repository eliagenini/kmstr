import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { File, PlusCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { VehiclesTable } from './vehicles-table';
import { getVehicles, getVehiclesWithPictures } from '@/lib/db';
import { VehiclesCards } from './vehicles-cards';

export default async function VehiclePage({
  searchParams
}: {
  searchParams: { q: string; offset: string };
}) {
  const search = searchParams.q ?? '';
  const offset = searchParams.offset ?? 0;
  const { vehicles, totalVehicles } = await getVehiclesWithPictures();

  console.log(vehicles);
  return (
    <VehiclesCards vehicles={vehicles} totalVehicles={totalVehicles} />
  );
}
