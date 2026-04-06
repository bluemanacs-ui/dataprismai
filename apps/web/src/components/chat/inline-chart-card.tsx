"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { ChartConfig, VisualizationConfig } from "@/types/chat";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Returns true if two series have very different magnitudes (>10× ratio) */
function _needsDualAxis(data: Record<string, string | number | null>[], s0key: string, s1key: string): boolean {
  const vals0 = data.map(r => Math.abs(Number(r[s0key] ?? 0))).filter(v => v > 0);
  const vals1 = data.map(r => Math.abs(Number(r[s1key] ?? 0))).filter(v => v > 0);
  if (!vals0.length || !vals1.length) return false;
  const max0 = Math.max(...vals0);
  const max1 = Math.max(...vals1);
  return max0 > 0 && max1 > 0 && (max0 / max1 > 10 || max1 / max0 > 10);
}

// ── Legacy ChartConfig adapter ───────────────────────────────────────────────
function buildEChartsOption(
  chartConfig: ChartConfig,
  xOverride?: string,
  yOverride?: string,
) {
  const data = chartConfig.data;
  const type = chartConfig.chart_type;
  // Respect axis overrides from the chooser UI
  const x_key = xOverride ?? chartConfig.x_key;
  const series = yOverride
    ? [{ key: yOverride, label: yOverride.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()) }]
    : chartConfig.series;

  const categories = data.map((row) => String(row[x_key] ?? ""));

  if (type === "pie" || type === "donut") {
    const key = series?.[0]?.key ?? "value";
    return {
      tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
      series: [{
        type: "pie",
        radius: type === "donut" ? ["40%", "70%"] : "60%",
        data: data.map((row) => ({ name: String(row[x_key] ?? ""), value: Number(row[key] ?? 0) })),
        label: { formatter: "{b}: {d}%" },
        emphasis: { itemStyle: { shadowBlur: 10 } },
      }],
    };
  }

  if (type === "funnel") {
    const key = series?.[0]?.key ?? "value";
    const funnelData = [...data]
      .sort((a, b) => Number(b[key] ?? 0) - Number(a[key] ?? 0))
      .map((row) => ({ name: String(row[x_key] ?? ""), value: Number(row[key] ?? 0) }));
    return {
      tooltip: { trigger: "item", formatter: "{b}: {c}" },
      series: [{
        type: "funnel",
        left: "5%", width: "90%", minSize: "5%",
        label: { position: "inside", formatter: "{b}" },
        data: funnelData,
      }],
    };
  }

  if (type === "treemap") {
    const key = series?.[0]?.key ?? "value";
    return {
      tooltip: { trigger: "item", formatter: "{b}: {c}" },
      series: [{
        type: "treemap",
        roam: false,
        data: data.map((row) => ({ name: String(row[x_key] ?? ""), value: Number(row[key] ?? 0) })),
      }],
    };
  }

  if (type === "sunburst") {
    const key = series?.[0]?.key ?? "value";
    return {
      tooltip: { formatter: "{b}: {c}" },
      series: [{
        type: "sunburst",
        data: data.map((row) => ({ name: String(row[x_key] ?? ""), value: Number(row[key] ?? 0) })),
        radius: ["0%", "90%"],
        label: { rotate: "radial", fontSize: 10 },
      }],
    };
  }

  if (type === "scatter") {
    const key1 = series?.[0]?.key ?? "";
    const key2 = series?.[1]?.key ?? key1;
    return {
      tooltip: {
        trigger: "item",
        formatter: (p: { name: string; value: [number, number] }) =>
          `${p.name}<br/>${series?.[0]?.label ?? key1}: ${p.value[0]}<br/>${series?.[1]?.label ?? key2}: ${p.value[1]}`,
      },
      xAxis: { type: "value", name: series?.[0]?.label ?? key1, nameLocation: "middle", nameGap: 25 },
      yAxis: { type: "value", name: series?.[1]?.label ?? key2, nameLocation: "middle", nameGap: 40 },
      series: [{
        type: "scatter",
        symbolSize: 12,
        data: data.map((row) => ({
          name: String(row[x_key] ?? ""),
          value: [Number(row[key1] ?? 0), Number(row[key2] ?? 0)],
        })),
      }],
    };
  }

  if (type === "gauge") {
    const key = series?.[0]?.key ?? "value";
    const vals = data.map((r) => Number(r[key] ?? 0));
    const val = vals[0] ?? 0;
    const maxV = Math.ceil((Math.max(...vals) || 100) * 1.25);
    return {
      series: [{
        type: "gauge",
        max: maxV,
        progress: { show: true, width: 18 },
        axisLine: { lineStyle: { width: 18 } },
        detail: { valueAnimation: true, formatter: "{value}", fontSize: 20 },
        data: [{ value: val, name: series?.[0]?.label ?? key }],
      }],
    };
  }

  if (type === "heatmap") {
    const yKey = series?.[0]?.key ?? "";
    const valKey = series?.[1]?.key ?? yKey;
    const xVals = [...new Set(data.map((r) => String(r[x_key] ?? "")))];
    const yVals = [...new Set(data.map((r) => String(r[yKey] ?? "")))];
    const maxV = Math.max(...data.map((r) => Number(r[valKey] ?? 0)));
    return {
      tooltip: { position: "top" },
      xAxis: { type: "category", data: xVals },
      yAxis: { type: "category", data: yVals },
      visualMap: { min: 0, max: maxV || 1, calculable: true, orient: "horizontal", left: "center", bottom: "5%" },
      series: [{
        type: "heatmap",
        data: data.map((r) => [String(r[x_key] ?? ""), String(r[yKey] ?? ""), Number(r[valKey] ?? 0)]),
        label: { show: false },
      }],
    };
  }

  if (type === "network") {
    // Force-directed graph: nodes sized by value, colored by natural grouping
    const valueKey = series?.[0]?.key ?? "";
    const allVals = data.map(r => Number(r[valueKey] ?? 0));
    const minVal = Math.min(...allVals);
    const maxVal = Math.max(...allVals);
    const range = maxVal - minVal || 1;

    const CLUSTER_COLORS = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e", "#a855f7"];

    // Decide how many buckets to use based on node count — no phantom legend entries
    const n = data.length;
    const numBuckets = n <= 2 ? n : n <= 4 ? n : n <= 8 ? 3 : 4;

    // Build only the buckets that will actually be used
    const BUCKET_LABELS = ["Low", "Mid-Low", "Mid-High", "High"];
    const bucketLabels = numBuckets === 1
      ? [String(data[0]?.[x_key] ?? "")]
      : numBuckets === 2
        ? ["Low", "High"]
        : numBuckets === 3
          ? ["Low", "Mid", "High"]
          : BUCKET_LABELS;

    const categories = bucketLabels.map((name, i) => ({
      name,
      itemStyle: { color: CLUSTER_COLORS[i % CLUSTER_COLORS.length] },
    }));

    const getCategory = (val: number) => {
      if (numBuckets === 1) return 0;
      const ratio = (val - minVal) / range; // 0..1
      return Math.min(numBuckets - 1, Math.floor(ratio * numBuckets));
    };

    const MAX_NODES = 60;
    const nodeData = data.slice(0, MAX_NODES);

    const nodes = nodeData.map((r, i) => {
      const val = Number(r[valueKey] ?? 0);
      const cat = getCategory(val);
      const size = 8 + ((val - minVal) / range) * 32; // 8-40px
      return {
        id: String(i),
        name: String(r[x_key] ?? ""),
        value: val,
        category: cat,
        symbolSize: Math.max(8, Math.min(40, size)),
        label: { show: size > 18, fontSize: 9, color: "#fff" },
      };
    });

    // Build edges: each node connects to 2-3 nearest neighbors by value
    const edgeSet = new Set<string>();
    const edges: { source: string; target: string }[] = [];
    nodeData.forEach((_, i) => {
      const vi = Number(nodeData[i][valueKey] ?? 0);
      const neighbors = nodeData
        .map((__, j) => ({ j, dist: Math.abs(Number(nodeData[j][valueKey] ?? 0) - vi) }))
        .filter(({ j }) => j !== i)
        .sort((a, b) => a.dist - b.dist)
        .slice(0, 3);
      neighbors.forEach(({ j }) => {
        const key = [Math.min(i, j), Math.max(i, j)].join("-");
        if (!edgeSet.has(key)) {
          edgeSet.add(key);
          edges.push({ source: String(i), target: String(j) });
        }
      });
    });

    return {
      backgroundColor: "transparent",
      tooltip: {
        formatter: (p: { name: string; value: number; data: { category: number } }) =>
          `<b>${p.name}</b><br/>${series?.[0]?.label ?? "Value"}: ${Number(p.value ?? 0).toLocaleString()}<br/>Cluster: ${categories[p.data?.category ?? 0]?.name}`,
      },
      legend: {
        data: categories.map(c => c.name),
        bottom: 0,
        show: numBuckets > 1,
        textStyle: { color: "#a1a1aa", fontSize: 10 },
        icon: "circle",
      },
      series: [{
        type: "graph",
        layout: "force",
        roam: true,
        draggable: true,
        categories,
        nodes,
        edges,
        force: {
          repulsion: 120,
          gravity: 0.08,
          edgeLength: [40, 100],
          layoutAnimation: true,
        },
        emphasis: { focus: "adjacency", lineStyle: { width: 3 } },
        lineStyle: { color: "source", opacity: 0.4, width: 1, curveness: 0.1 },
        itemStyle: { borderColor: "#fff", borderWidth: 1, opacity: 0.9 },
        label: { position: "right", formatter: "{b}", color: "#e4e4e7" },
      }],
    };
  }

  // combo chart: first series → bar, rest → line (dual-axis when magnitudes differ)
  if (type === "combo") {
    const dual = series.length >= 2 && _needsDualAxis(data, series[0].key, series[1]?.key ?? series[0].key);
    const comboSeries = series.map((s, i) => ({
      name: s.label,
      type: i === 0 ? "bar" : "line",
      yAxisIndex: dual && i > 0 ? 1 : 0,
      smooth: i > 0,
      data: data.map((row) => Number(row[s.key] ?? 0)),
    }));
    const yAxes = dual
      ? [{ type: "value" as const, name: series[0].label }, { type: "value" as const, name: series[1].label, splitLine: { show: false } }]
      : [{ type: "value" as const }];
    return {
      tooltip: { trigger: "axis" },
      legend: { bottom: 0 },
      xAxis: { type: "category" as const, data: categories },
      yAxis: yAxes,
      series: comboSeries,
    };
  }

  // bar, line, area — with dual Y-axis when series magnitudes differ greatly
  const dual = series.length >= 2 && _needsDualAxis(data, series[0].key, series[1].key);
  const seriesData = series.map((s, i) => ({
    name: s.label,
    type: type === "bar" ? "bar" : "line",
    yAxisIndex: dual && i > 0 ? 1 : 0,
    areaStyle: type === "area" ? { opacity: 0.3 } : undefined,
    data: data.map((row) => Number(row[s.key] ?? 0)),
    smooth: type === "line" || type === "area",
  }));

  const yAxes = dual
    ? [
        { type: "value" as const, name: series[0].label, nameLocation: "middle" as const, nameGap: 50 },
        { type: "value" as const, name: series[1].label, nameLocation: "middle" as const, nameGap: 50, splitLine: { show: false } },
      ]
    : [{ type: "value" as const }];

  return {
    tooltip: { trigger: "axis" },
    legend: { bottom: 0 },
    xAxis: { type: "category" as const, data: categories },
    yAxis: yAxes,
    series: seriesData,
  };
}

// ── VisualizationConfig renderer ─────────────────────────────────────────────
function VisualizationRenderer({ config }: { config: VisualizationConfig }) {
  const { visualization_type, title, description, payload } = config;
  const p = payload as Record<string, unknown>;

  const option = useMemo(() => {
    if (["bar", "line", "area", "pie", "donut", "scatter", "funnel", "treemap", "sunburst", "gauge", "heatmap"].includes(visualization_type)) {
      const data = (p.data as Record<string, string | number | null>[]) ?? [];
      const x_key = (p.x_key as string) ?? "";
      const series = (p.series as { key: string; label: string }[]) ?? [];
      const categories = data.map((row) => String(row[x_key] ?? ""));

      if (visualization_type === "pie" || visualization_type === "donut") {
        const key = series?.[0]?.key ?? "value";
        return {
          tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
          series: [{
            type: "pie",
            radius: visualization_type === "donut" ? ["40%", "70%"] : "60%",
            data: data.map((row) => ({ name: String(row[x_key] ?? ""), value: Number(row[key] ?? 0) })),
            label: { formatter: "{b}: {d}%" },
            emphasis: { itemStyle: { shadowBlur: 10 } },
          }],
        };
      }

      if (visualization_type === "funnel") {
        const key = series?.[0]?.key ?? "value";
        const funnelData = [...data]
          .sort((a, b) => Number(b[key] ?? 0) - Number(a[key] ?? 0))
          .map((row) => ({ name: String(row[x_key] ?? ""), value: Number(row[key] ?? 0) }));
        return {
          tooltip: { trigger: "item", formatter: "{b}: {c}" },
          series: [{ type: "funnel", left: "5%", width: "90%", minSize: "5%", label: { position: "inside", formatter: "{b}" }, data: funnelData }],
        };
      }

      if (visualization_type === "treemap") {
        const key = series?.[0]?.key ?? "value";
        return {
          tooltip: { trigger: "item", formatter: "{b}: {c}" },
          series: [{ type: "treemap", roam: false, data: data.map((row) => ({ name: String(row[x_key] ?? ""), value: Number(row[key] ?? 0) })) }],
        };
      }

      if (visualization_type === "sunburst") {
        const key = series?.[0]?.key ?? "value";
        return {
          tooltip: { formatter: "{b}: {c}" },
          series: [{ type: "sunburst", data: data.map((row) => ({ name: String(row[x_key] ?? ""), value: Number(row[key] ?? 0) })), radius: ["0%", "90%"], label: { rotate: "radial", fontSize: 10 } }],
        };
      }

      if (visualization_type === "scatter") {
        const key1 = series?.[0]?.key ?? "";
        const key2 = series?.[1]?.key ?? key1;
        return {
          tooltip: { trigger: "item" },
          xAxis: { type: "value", name: series?.[0]?.label ?? key1, nameLocation: "middle" as const, nameGap: 25 },
          yAxis: { type: "value", name: series?.[1]?.label ?? key2, nameLocation: "middle" as const, nameGap: 40 },
          series: [{ type: "scatter", symbolSize: 12, data: data.map((row) => ({ name: String(row[x_key] ?? ""), value: [Number(row[key1] ?? 0), Number(row[key2] ?? 0)] })) }],
        };
      }

      if (visualization_type === "gauge") {
        const key = series?.[0]?.key ?? "value";
        const vals = data.map((r) => Number(r[key] ?? 0));
        const val = vals[0] ?? 0;
        const maxV = Math.ceil((Math.max(...vals) || 100) * 1.25);
        return {
          series: [{ type: "gauge", max: maxV, progress: { show: true, width: 18 }, axisLine: { lineStyle: { width: 18 } }, detail: { valueAnimation: true, formatter: "{value}", fontSize: 20 }, data: [{ value: val, name: series?.[0]?.label ?? key }] }],
        };
      }

      if (visualization_type === "heatmap") {
        const yKey = series?.[0]?.key ?? "";
        const valKey = series?.[1]?.key ?? yKey;
        const xVals = [...new Set(data.map((r) => String(r[x_key] ?? "")))];
        const yVals = [...new Set(data.map((r) => String(r[yKey] ?? "")))];
        const maxV = Math.max(...data.map((r) => Number(r[valKey] ?? 0)));
        return {
          tooltip: { position: "top" },
          xAxis: { type: "category", data: xVals },
          yAxis: { type: "category", data: yVals },
          visualMap: { min: 0, max: maxV || 1, calculable: true, orient: "horizontal" as const, left: "center", bottom: "5%" },
          series: [{ type: "heatmap", data: data.map((r) => [String(r[x_key] ?? ""), String(r[yKey] ?? ""), Number(r[valKey] ?? 0)]), label: { show: false } }],
        };
      }

      return {
        tooltip: { trigger: "axis" },
        legend: { bottom: 0 },
        xAxis: { type: "category", data: categories },
        yAxis: { type: "value" },
        series: series.map((s) => ({
          name: s.label,
          type: visualization_type === "area" ? "line" : visualization_type,
          areaStyle: visualization_type === "area" ? { opacity: 0.3 } : undefined,
          smooth: ["line", "area"].includes(visualization_type),
          data: data.map((row) => Number(row[s.key] ?? 0)),
        })),
      };
    }
    return null;
  }, [config]);

  if (visualization_type === "metric") {
    const value = p.value ?? p.primary ?? "—";
    const label = p.label ?? title;
    const delta = p.delta as string | undefined;
    return (
      <div className="flex flex-col items-center justify-center py-8">
        <div className="text-xs uppercase tracking-widest text-cyan-400">{String(label)}</div>
        <div className="mt-2 text-5xl font-bold text-cyan-100">{String(value)}</div>
        {delta && <div className="mt-1 text-sm text-emerald-400">{delta}</div>}
        {description && <div className="mt-2 text-xs text-slate-400">{description}</div>}
      </div>
    );
  }

  if (visualization_type === "table") {
    const rows = (p.rows as Record<string, unknown>[]) ?? [];
    const columns = (p.columns as string[]) ?? (rows[0] ? Object.keys(rows[0]) : []);
    return (
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col} className="border border-slate-700 bg-slate-800 px-3 py-1 text-left text-cyan-300">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 20).map((row, i) => (
              <tr key={i} className="odd:bg-slate-900 even:bg-slate-800/60">
                {columns.map((col) => (
                  <td key={col} className="border border-slate-700 px-3 py-1 text-slate-300">{String(row[col] ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length > 20 && <div className="mt-1 text-xs text-slate-500">{rows.length - 20} more rows…</div>}
      </div>
    );
  }

  if (!option) return null;

  return (
    <ReactECharts
      option={option}
      notMerge
      style={{ height: 288 }}
      theme="dark"
      opts={{ renderer: "canvas" }}
    />
  );
}

// ── Public component ──────────────────────────────────────────────────────────
type InlineChartCardProps = {
  chartConfig?: ChartConfig;
  visualizationConfig?: VisualizationConfig;
};

const RADIAL_TYPES = new Set(["pie", "donut", "funnel", "treemap", "sunburst", "gauge"]);
// Chart types that support a single label override (the category field)
const LABEL_ONLY_TYPES = new Set(["pie", "donut", "funnel", "treemap", "sunburst"]);

export function InlineChartCard({ chartConfig, visualizationConfig }: InlineChartCardProps) {
  const allColumns = useMemo(() => {
    const data = chartConfig?.data ?? [];
    return data.length ? Object.keys(data[0]) : [];
  }, [chartConfig]);

  const [chartTypeOverride, setChartTypeOverride] = useState<string | undefined>(undefined);
  const [xOverride, setXOverride] = useState<string | undefined>(undefined);
  const [yOverride, setYOverride] = useState<string | undefined>(undefined);

  // Effective config with optional chart type override
  const effectiveConfig = useMemo(() => {
    if (!chartConfig) return chartConfig;
    if (!chartTypeOverride) return chartConfig;
    return { ...chartConfig, chart_type: chartTypeOverride };
  }, [chartConfig, chartTypeOverride]);

  const activeType = chartTypeOverride ?? chartConfig?.chart_type ?? "";
  const isRadial = RADIAL_TYPES.has(activeType);
  const isLabelOnly = LABEL_ONLY_TYPES.has(activeType);

  const legacyOption = useMemo(() => {
    if (!effectiveConfig?.data?.length) return null;
    // For radial charts, x override is the label field; y override ignored
    return buildEChartsOption(effectiveConfig, xOverride, isRadial ? undefined : yOverride);
  }, [effectiveConfig, xOverride, yOverride, isRadial]);

  if (!legacyOption && !visualizationConfig) return null;

  const displayTitle = chartConfig?.title ?? visualizationConfig?.title ?? "";
  const displayDesc = chartConfig?.description ?? visualizationConfig?.description ?? "";

  // Available chart type switchers
  const CHART_TYPES = [
    { t: "bar", label: "Bar" }, { t: "line", label: "Line" }, { t: "area", label: "Area" },
    { t: "combo", label: "Bar+Line" }, { t: "pie", label: "Pie" }, { t: "donut", label: "Donut" },
    { t: "scatter", label: "Scatter" }, { t: "funnel", label: "Funnel" },
    { t: "treemap", label: "Treemap" }, { t: "sunburst", label: "Sunburst" },
    { t: "heatmap", label: "Heatmap" }, { t: "network", label: "Network" }, { t: "gauge", label: "Gauge" },
  ];

  return (
    <div className="mt-4 rounded-2xl p-4" style={{ border: "1px solid var(--card-border)", backgroundColor: "var(--card-bg)" }}>
      <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
        <div>
          {displayTitle && <div className="text-sm font-semibold" style={{ color: "var(--foreground)" }}>{displayTitle}</div>}
        </div>

        {/* Axis chooser — context-aware: hide X/Y for radial, show Label for pie-type */}
        {allColumns.length > 1 && (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {isLabelOnly ? (
              <label className="flex items-center gap-1" style={{ color: "var(--muted)" }}>
                Label:
                <select value={xOverride ?? chartConfig?.x_key ?? ""} onChange={e => setXOverride(e.target.value)}
                  className="rounded px-2 py-0.5 outline-none"
                  style={{ backgroundColor: "var(--tag-bg)", color: "var(--foreground)", border: "1px solid var(--card-border)" }}>
                  {allColumns.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </label>
            ) : !isRadial ? (
              <>
                <label className="flex items-center gap-1" style={{ color: "var(--muted)" }}>
                  X:
                  <select value={xOverride ?? chartConfig?.x_key ?? ""} onChange={e => setXOverride(e.target.value)}
                    className="rounded px-2 py-0.5 outline-none"
                    style={{ backgroundColor: "var(--tag-bg)", color: "var(--foreground)", border: "1px solid var(--card-border)" }}>
                    {allColumns.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </label>
                <label className="flex items-center gap-1" style={{ color: "var(--muted)" }}>
                  Y:
                  <select value={yOverride ?? chartConfig?.series?.[0]?.key ?? ""} onChange={e => setYOverride(e.target.value)}
                    className="rounded px-2 py-0.5 outline-none"
                    style={{ backgroundColor: "var(--tag-bg)", color: "var(--foreground)", border: "1px solid var(--card-border)" }}>
                    {allColumns.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </label>
              </>
            ) : null}
            {(xOverride || yOverride) && (
              <button onClick={() => { setXOverride(undefined); setYOverride(undefined); }}
                className="rounded px-1.5 py-0.5" style={{ color: "var(--muted)" }} title="Reset axes">↺</button>
            )}
          </div>
        )}
      </div>

      {/* Chart type switcher row */}
      <div className="mb-3 flex flex-wrap gap-1.5">
        {CHART_TYPES.map(({ t, label }) => (
          <button key={t}
            onClick={() => {
              setChartTypeOverride(t === (chartConfig?.chart_type ?? "") && !chartTypeOverride ? undefined : t);
              setXOverride(undefined);
              setYOverride(undefined);
            }}
            className="rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-all"
            style={activeType === t
              ? { backgroundColor: "var(--accent-1)", color: "white" }
              : { border: "1px solid var(--card-border)", color: "var(--muted)", backgroundColor: "var(--tag-bg)" }}
          >{label}</button>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl">
        {legacyOption ? (
          <ReactECharts option={legacyOption} notMerge style={{ height: 320 }} theme="dark" opts={{ renderer: "canvas" }} />
        ) : visualizationConfig ? (
          <VisualizationRenderer config={visualizationConfig} />
        ) : null}
      </div>
    </div>
  );
}
