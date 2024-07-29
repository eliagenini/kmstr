"use client"

import { Bar, BarChart, CartesianGrid } from "recharts"
import React, {useState, useEffect} from 'react'

import { ChartConfig, ChartContainer } from "@/components/ui/chart"

const chartConfig = {
    desktop: {
        label: "Desktop",
        color: "#2563eb",
    },
    mobile: {
        label: "Mobile",
        color: "#60a5fa",
    },
} satisfies ChartConfig

const BasicChart = data => {
    const [newData, setNewData] = useState([])
    console.log(data.data)
    useEffect(() => {
        setNewData(data.data)
    }, [data])

    return (
        <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
            <BarChart accessibilityLayer data={newData}>
                <Bar dataKey="desktop" fill="var(--color-desktop)" radius={4} />
                <Bar dataKey="mobile" fill="var(--color-mobile)" radius={4} />
            </BarChart>
        </ChartContainer>
    )
}
export default BasicChart;