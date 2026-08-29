import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { axisProps, gridProps, TooltipRow, TooltipShell } from "./chart-parts"
import { categoryColour, formatNumber, results, shortCategory } from "@/lib/data"
import { useIsNarrow } from "@/hooks/useIsNarrow"

export function SeasonalProfile() {
  const narrow = useIsNarrow()
  const data = results.seasonality.monthly

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, left: narrow ? -16 : 4, bottom: 8 }}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="name" {...axisProps} interval={0} tick={{ fill: "var(--axis)", fontSize: narrow ? 9 : 11 }} />
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
          cursor={{ fill: "var(--muted)" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const p = payload[0].payload as (typeof data)[number]
            return (
              <TooltipShell label={p.name}>
                <TooltipRow swatch={categoryColour(p.category)} name="Mean PM2.5" value={`${formatNumber(p.mean_pm25, 1)} µg/m³`} />
                <TooltipRow name="Median" value={`${formatNumber(p.median_pm25, 1)} µg/m³`} />
                <TooltipRow name="Category" value={shortCategory(p.category)} />
                <TooltipRow name="Hours" value={p.hours.toLocaleString("en-GB")} />
                <TooltipRow name="Years covered" value={String(p.years_covered)} />
              </TooltipShell>
            )
          }}
        />
        <Bar dataKey="mean_pm25" radius={[3, 3, 0, 0]} isAnimationActive={false}>
          {data.map((d) => (
            // Hairline so the darker EPA category fills stay visible on a dark card.
            <Cell
              key={d.month}
              fill={categoryColour(d.category)}
              stroke="var(--axis)"
              strokeOpacity={0.35}
              strokeWidth={1}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
