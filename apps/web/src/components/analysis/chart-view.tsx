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

type ChartViewProps = {
    chartConfig?: ChartConfig;
};

export function ChartView({ chartConfig }: ChartViewProps) {
    if (!chartConfig || !chartConfig.data?.length) {
        return (
            <div className="flex h-56 items-center justify-center rounded-xl border border-dashed border-zinc-700 text-sm text-zinc-500">
                No chart data available
            </div>
        );
    }

    const commonProps = {
        data: chartConfig.data,
    };

    return (
        <div className="space-y-3">
            <div>
                <div className="text-sm font-semibold">{chartConfig.title}</div>
                <div className="text-xs text-zinc-500">{chartConfig.description}</div>
            </div>

            <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    {chartConfig.chart_type === "bar" ? (
                        <BarChart {...commonProps}>
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
                        <LineChart {...commonProps}>
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
