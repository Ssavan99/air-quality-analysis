import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { axisProps, gridProps, TooltipRow, TooltipShell } from "./chart-parts"
import { formatNumber, results } from "@/lib/data"
import { useIsNarrow } from "@/hooks/useIsNarrow"

/**
 * The y-axis runs the full 0 to 1. Zooming into 0.90-0.95 would make a
 * difference of ~0.03 look like a landslide; the point is that in-sample and
 * cross-validated R2 diverge, not that either is small.
 */
export function ModelComparison({ dataset = "biweekly" }: { dataset?: "biweekly" | "hourly" }) {
  const narrow = useIsNarrow()
  const rows = results.validation[dataset].models
  const data = rows.map((r) => ({
    model: r.model,
    inSample: r.in_sample_r2,
    cv: r.cv_r2,
    gap: r.overfit_gap,
  }))

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, left: narrow ? -16 : 4, bottom: 8 }}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey="model" {...axisProps} />
        <YAxis
          {...axisProps}
          domain={[0, 1]}
          ticks={[0, 0.2, 0.4, 0.6, 0.8, 1]}
          width={narrow ? 34 : 52}
          label={
            narrow
              ? undefined
              : {
                  value: "R²",
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
              <TooltipShell label={`${p.model} regression`}>
                <TooltipRow swatch="var(--series)" name="In-sample R²" value={formatNumber(p.inSample, 6)} />
                <TooltipRow swatch="var(--series-3)" name="5-fold CV R²" value={formatNumber(p.cv, 6)} />
                <TooltipRow name="Overfit gap" value={formatNumber(p.gap, 6)} />
              </TooltipShell>
            )
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 4 }}
          formatter={(value) => <span className="text-muted-foreground">{value}</span>}
        />
        <Bar dataKey="inSample" name="In-sample R²" fill="var(--series)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
        <Bar dataKey="cv" name="5-fold CV R²" fill="var(--series-3)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  )
}
