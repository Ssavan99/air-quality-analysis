import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { axisProps, gridProps, TooltipRow, TooltipShell } from "./chart-parts"
import { formatNumber, results } from "@/lib/data"
import { useIsNarrow } from "@/hooks/useIsNarrow"

export function ExponentialQuality() {
  const narrow = useIsNarrow()
  const data = Object.entries(results.exponential)
    .map(([pollutant, fit]) => ({
      pollutant: pollutant.toUpperCase(),
      r2: fit.r2,
      mse: fit.mse,
      correlation: fit.correlation,
    }))
    .sort((a, b) => b.r2 - a.r2)

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, left: narrow ? -16 : 4, bottom: 8 }}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="pollutant" {...axisProps} />
        <YAxis
          {...axisProps}
          domain={[0, 1]}
          ticks={[0, 0.2, 0.4, 0.6, 0.8, 1]}
          width={narrow ? 34 : 52}
          label={
            narrow
              ? undefined
              : { value: "R²", angle: -90, position: "insideLeft", style: { fill: "var(--axis)", fontSize: 11 } }
          }
        />
        <Tooltip
          cursor={{ fill: "var(--muted)" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const p = payload[0].payload as (typeof data)[number]
            return (
              <TooltipShell label={`PM2.5 vs ${p.pollutant}`}>
                <TooltipRow swatch="var(--series)" name="R²" value={formatNumber(p.r2, 6)} />
                <TooltipRow name="MSE" value={formatNumber(p.mse, 2)} />
                <TooltipRow name="Correlation" value={formatNumber(p.correlation, 2)} />
              </TooltipShell>
            )
          }}
        />
        <Bar dataKey="r2" fill="var(--series)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  )
}
