import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card"

export function MileageCard({ mileage }: { mileage }) {

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                    Total mileage
                </CardTitle>

            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{mileage} Km</div>
                <p className="text-xs text-muted-foreground">
                    +20.1% from last month
                </p>
            </CardContent>
        </Card>
    )

}