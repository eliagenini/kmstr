import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal } from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import clsx from 'clsx';
import Link from 'next/link';

export function VehicleCard({ vehicle }: { vehicle }) {
  let imageBuffer = vehicle.pictures[1].image;
  Buffer.from(imageBuffer).toString('base64')
  const base64Image = Buffer.from(imageBuffer).toString('base64');
  const picture = `data:image/png;base64,${base64Image}`;
  return (
    <Card>
      <CardHeader>
        <CardTitle>{vehicle.nickname}</CardTitle>
        <CardDescription>{vehicle.vin}</CardDescription>
      </CardHeader>
      <CardContent>
        <Image
          src={picture}
          alt={vehicle.nickname}
          width={300}
          height={200}
        />
      </CardContent>
      <CardFooter>
        <Link
          href={`/vehicle/${vehicle.vin}`}
        >
          <Button>Seleziona</Button>
        </Link>
      </CardFooter>
    </Card>
  );
}
