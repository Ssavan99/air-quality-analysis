import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { axisProps, gridProps, TooltipRow, TooltipShell } from "./chart-parts"
import { formatNumber, results } from "@/lib/data"
import { useIsNarrow } from "@/hooks/useIsNarrow"

const COLOURS: Record<string, string> = {
  no2: "var(--series)",
  so2: "var(--series-2)",
  no: "var(--series-3)",
}

export function SimpsonExposure() {
  const narrow = useIsNarrow()
  const simpson = results.simpson as unknown as Record<string, Record<string, number | null>>
  const coverage = results.simpson.coverage
  // "coverage" is metadata, not a pollutant.
  const pollutants = Object.keys(simpson).filter((k) => k !== "coverage")
  // 2020 and 2023 are two-month stubs integrated over the same axis as the
  // full years, so their bars are not comparable. Showing them next to
  // complete years invites exactly the wrong reading.
  const years = Object.keys(coverage).filter((y) => coverage[y].complete)

  const data = years.map((year) => {
    const row: Record<string, string | number> = { year }
    for (const p of pollutants) row[p] = simpson[p][year] ?? 0
    return row
  })

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, left: narrow ? -16 : 4, bottom: 8 }}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="year" {...axisProps} />
        <YAxis
          {...axisProps}
          width={narrow ? 38 : 56}
          label={
            narrow
              ? undefined
              : {
                  value: "Cumulative exposure",
                  angle: -90,
                  position: "insideLeft",
                  style: { fill: "var(--axis)", fontSize: 11 },
                }
          }
        />
        <Tooltip
          cursor={{ fill: "var(--muted)" }}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null
            return (
              <TooltipShell label={`Year ${label}`}>
                {pollutants.map((p) => (
                  <TooltipRow
                    key={p}
                    swatch={COLOURS[p]}
                    name={p.toUpperCase()}
                    value={formatNumber(Number((payload[0].payload as Record<string, number>)[p]), 2)}
                  />
                ))}
              </TooltipShell>
            )
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 4 }}
          formatter={(value) => <span className="text-muted-foreground">{String(value).toUpperCase()}</span>}
        />
        {pollutants.map((p) => (
          <Bar key={p} dataKey={p} fill={COLOURS[p]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
