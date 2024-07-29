import {getCurrentMileageByVehicle, getCurrentFuelByVehicle, getCurrentRangeByVehicle} from "@/lib/db";
import {SummaryCard} from "@/app/dashboard/vehicle/summary-card";
import {MileageCard} from "@/app/dashboard/vehicle/mileage-card";
import {FuelCard} from "@/app/dashboard/vehicle/fuel-card";
import {RangeCard} from "@/app/dashboard/vehicle/range-card";

export default async function VehiclePage() {
    const vin = 'WVGZZZ1T5RW028165';
    const { mileage} = await getCurrentMileageByVehicle(vin);
    const { fuel } = await getCurrentFuelByVehicle(vin);
    const { range } = await getCurrentRangeByVehicle(vin);
    return (
        <div className="grid gap-4 md:grid-cols-3 md:gap-8 lg:grid-cols-3">
            <MileageCard mileage={mileage[0].km} />
            <FuelCard fuel={fuel[0].level} />
            <RangeCard range={range[0].km} />
        </div>
    );
}
