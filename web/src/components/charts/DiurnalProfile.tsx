import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { axisProps, gridProps, TooltipRow, TooltipShell } from "./chart-parts"
import { formatNumber, results } from "@/lib/data"
import { useIsNarrow } from "@/hooks/useIsNarrow"

export function DiurnalProfile() {
  const narrow = useIsNarrow()
  const data = results.seasonality.diurnal

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 8, right: 8, left: narrow ? -16 : 4, bottom: 24 }}>
        <defs>
          <linearGradient id="diurnalFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--series)" stopOpacity={0.28} />
            <stop offset="100%" stopColor="var(--series)" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid {...gridProps} />
        <XAxis
          dataKey="hour"
          {...axisProps}
          interval={narrow ? 3 : 1}
          tickFormatter={(v: number) => `${String(v).padStart(2, "0")}`}
          label={{
            value: "Hour of day (IST)",
            position: "insideBottom",
            offset: -12,
            style: { fill: "var(--axis)", fontSize: 11 },
          }}
        />
        <YAxis
          {...axisProps}
          width={narrow ? 34 : 56}
          label={
            narrow
              ? undefined
              : {
                  value: "Mean PM2.5 (µg/m³)",
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
            const p = payload[0].payload as (typeof data)[number]
            return (
              <TooltipShell label={`${String(p.hour).padStart(2, "0")}:30 IST`}>
                <TooltipRow swatch="var(--series)" name="Mean PM2.5" value={`${formatNumber(p.mean_pm25, 1)} µg/m³`} />
                <TooltipRow name="Median" value={`${formatNumber(p.median_pm25, 1)} µg/m³`} />
              </TooltipShell>
            )
          }}
        />
        <Area
          type="monotone"
          dataKey="mean_pm25"
          stroke="var(--series)"
          strokeWidth={2}
          fill="url(#diurnalFill)"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
