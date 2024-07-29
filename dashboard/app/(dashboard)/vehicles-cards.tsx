import { VehicleCard } from './vehicle-card';

export function VehiclesCards({
  vehicles,
}: {
  vehicles;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2 md:gap-8 lg:grid-cols-4">
      {vehicles.map((vehicle) => (
        <VehicleCard key={vehicle.vin} vehicle={vehicle} />
      ))}
    </div>
  );
}
