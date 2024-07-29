'use client';

import {
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  Table
} from '@/components/ui/table';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { VehicleCard } from './vehicle-card';
import { SelectVehicle } from '@/lib/db';
import { useRouter } from 'next/navigation';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function VehiclesTable({
  vehicles,
  totalVehicles
}: {
  vehicles;
  totalVehicles: number;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Vehicles</CardTitle>
        <CardDescription>
          Manage your vehicles
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="hidden w-[100px] sm:table-cell">
                <span className="sr-only">Image</span>
              </TableHead>
              <TableHead>Nickname</TableHead>
              <TableHead>Model</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden md:table-cell">Created at</TableHead>
              <TableHead>
                <span className="sr-only">Actions</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {vehicles.map((vehicle) => (
              <VehicleCard key={vehicle.vin} vehicle={vehicle} />
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
