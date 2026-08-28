import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { axisProps, gridProps, TooltipRow, TooltipShell } from "./chart-parts"
import { formatNumber, results } from "@/lib/data"
import { useIsNarrow } from "@/hooks/useIsNarrow"

type Row = {
  co: number
  observed?: number
  linear?: number
  quadratic?: number
  cubic?: number
}

/** Observed points plus the three fitted curves, on one shared CO axis. */
function buildData(): Row[] {
  const curves = results.polynomial_curves
  const rows: Row[] = curves.co.map((co, i) => ({
    co,
    linear: curves.linear[i],
    quadratic: curves.quadratic[i],
    cubic: curves.cubic[i],
  }))
  for (const point of results.series) {
    rows.push({ co: point.co, observed: point.pm2_5 })
  }
  return rows.sort((a, b) => a.co - b.co)
}

export function CoScatter() {
  const narrow = useIsNarrow()
  const data = buildData()

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data} margin={{ top: 8, right: 8, left: narrow ? -14 : 4, bottom: 28 }}>
        <CartesianGrid {...gridProps} />
        <XAxis
          type="number"
          dataKey="co"
          {...axisProps}
          domain={["dataMin", "dataMax"]}
          tickFormatter={(v: number) => `${Math.round(v / 1000)}k`}
          label={{
            value: "CO (µg/m³)",
            position: "insideBottom",
            offset: -14,
            style: { fill: "var(--axis)", fontSize: 11 },
          }}
        />
        <YAxis
          {...axisProps}
          width={narrow ? 38 : 56}
          label={
            narrow
              ? undefined
              : {
                  value: "PM2.5 (µg/m³)",
                  angle: -90,
                  position: "insideLeft",
                  style: { fill: "var(--axis)", fontSize: 11 },
                }
          }
        />
        <Tooltip
          cursor={{ stroke: "var(--axis)", strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const p = payload[0].payload as Row
            return (
              <TooltipShell label={`CO ${formatNumber(p.co, 0)} µg/m³`}>
                {p.observed !== undefined ? (
                  <TooltipRow swatch="var(--series)" name="Observed PM2.5" value={formatNumber(p.observed, 1)} />
                ) : null}
                {p.linear !== undefined ? (
                  <>
                    <TooltipRow swatch="var(--series-2)" name="Linear fit" value={formatNumber(p.linear, 1)} />
                    <TooltipRow swatch="var(--series-3)" name="Quadratic fit" value={formatNumber(p.quadratic!, 1)} />
                    <TooltipRow swatch="var(--destructive)" name="Cubic fit" value={formatNumber(p.cubic!, 1)} />
                  </>
                ) : null}
              </TooltipShell>
            )
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
          formatter={(value) => <span className="text-muted-foreground">{value}</span>}
        />
        <Scatter name="Observed" dataKey="observed" fill="var(--series)" isAnimationActive={false} />
        {/* Dashed and dotted so the three fits stay distinguishable without colour. */}
        <Line type="monotone" dataKey="linear" name="Linear" stroke="var(--series-2)" strokeWidth={2} dot={false} connectNulls isAnimationActive={false} />
        <Line type="monotone" dataKey="quadratic" name="Quadratic" stroke="var(--series-3)" strokeWidth={2} strokeDasharray="6 3" dot={false} connectNulls isAnimationActive={false} />
        <Line type="monotone" dataKey="cubic" name="Cubic" stroke="var(--destructive)" strokeWidth={2} strokeDasharray="2 3" dot={false} connectNulls isAnimationActive={false} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
