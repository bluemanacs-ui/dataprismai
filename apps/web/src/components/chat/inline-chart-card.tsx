"use client";

import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { ChartConfig } from "@/types/chat";

type InlineChartCardProps = {
    chartConfig?: ChartConfig;
};

export function InlineChartCard({ chartConfig }: InlineChartCardProps) {
    if (!chartConfig || !chartConfig.data?.length) {
        return null;
    }

    return (
        <div className="mt-4 rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
            <div className="mb-1 text-sm font-semibold">{chartConfig.title}</div>
            <div className="mb-4 text-xs text-zinc-500">{chartConfig.description}</div>

            <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    {chartConfig.chart_type === "bar" ? (
                        <BarChart data={chartConfig.data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey={chartConfig.x_key} />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            {chartConfig.series.map((series) => (
                                <Bar key={series.key} dataKey={series.key} name={series.label} />
                            ))}
                        </BarChart>
                    ) : (
                        <LineChart data={chartConfig.data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey={chartConfig.x_key} />
                            <YAxis />
                            <Tooltip />
                            <Legend />
                            {chartConfig.series.map((series) => (
                                <Line
                                    key={series.key}
                                    type="monotone"
                                    dataKey={series.key}
                                    name={series.label}
                                    dot={false}
                                />
                            ))}
                        </LineChart>
                    )}
                </ResponsiveContainer>
            </div>
        </div>
    );
}
