import {
    getCurrentMileageByVehicle,
    getCurrentFuelByVehicle,
    getCurrentRangeByVehicle,
    getCurrentParkingByVehicle
} from "@/lib/db";
import {SummaryCard} from "@/app/dashboard/vehicle/summary-card";
import {MileageCard} from "@/app/dashboard/vehicle/mileage-card";
import {FuelCard} from "@/app/dashboard/vehicle/fuel-card";
import {RangeCard} from "@/app/dashboard/vehicle/range-card";
import dynamic from "next/dynamic";
import {useMemo} from "react";

export default async function VehiclePage() {
    const Map = useMemo(() => dynamic(
        () => import('@/components/map'),
        {
            loading: () => <p>A map is loading</p>,
            ssr: false
        }), [])

    const vin = 'WVWZZZAWZMY037089';
    const { mileage} = await getCurrentMileageByVehicle(vin);
    const { fuel } = await getCurrentFuelByVehicle(vin);
    const { range } = await getCurrentRangeByVehicle(vin);
    const { parking } = await getCurrentParkingByVehicle(vin);
console.log(parking[0]);
    return (
        <div className="grid gap-4 md:grid-cols-4 md:gap-8 lg:grid-cols-4">
            <MileageCard mileage={mileage[0].km} />
            <FuelCard fuel={fuel[0].level} />
            <RangeCard range={range[0].km} />
            <Map position={[parking[0].latitude, parking[0].longitude]} zoom="16" />
        </div>
    );
}
