import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { axisProps, TooltipRow, TooltipShell } from "./chart-parts"
import { CATEGORY_ORDER, categoryColour, results, shortCategory } from "@/lib/data"
import { useIsNarrow } from "@/hooks/useIsNarrow"

/**
 * "Beyond the AQI scale" has no EPA colour, because the EPA defines no index
 * up there. Reusing the Hazardous maroon made the two bars identical, and
 * darkening it is not an option -- that maroon is already only 1.6:1 against
 * the dark card, so anything darker disappears. It gets the same maroon with a
 * hatch instead, which reads as "off the end of the scale" rather than as a
 * different severity, and survives being printed or viewed without colour.
 */
function HatchDef() {
  return (
    <defs>
      <pattern id="beyondScale" width={7} height={7} patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
        <rect width={7} height={7} fill="#7E0023" />
        <line x1={0} y1={0} x2={0} y2={7} stroke="#F2C4D0" strokeWidth={2.5} />
      </pattern>
    </defs>
  )
}

export function AqiDistribution() {
  const narrow = useIsNarrow()
  const dist = results.seasonality.aqi_distribution
  const data = CATEGORY_ORDER.map((name) => ({
    name,
    label: shortCategory(name),
    days: dist.counts[name] ?? 0,
    percent: dist.percent[name] ?? 0,
  }))

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 44, left: 4, bottom: 4 }}
        barCategoryGap={6}
      >
        <HatchDef />
        <XAxis type="number" hide domain={[0, Math.max(...data.map((d) => d.percent)) * 1.18]} />
        <YAxis
          type="category"
          dataKey="label"
          {...axisProps}
          width={narrow ? 96 : 132}
          tick={{ fill: "var(--foreground)", fontSize: narrow ? 10 : 12 }}
        />
        <Tooltip
          cursor={{ fill: "var(--muted)" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const point = payload[0].payload as (typeof data)[number]
            return (
              <TooltipShell label={point.name}>
                <TooltipRow
                  swatch={categoryColour(point.name)}
                  name="Days"
                  value={point.days.toLocaleString("en-GB")}
                />
                <TooltipRow name="Share" value={`${point.percent.toFixed(2)}%`} />
              </TooltipShell>
            )
          }}
        />
        <Bar dataKey="percent" radius={[0, 4, 4, 0]} isAnimationActive={false}>
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={
                entry.name === "Beyond the AQI scale"
                  ? "url(#beyondScale)"
                  : categoryColour(entry.name)
              }
              // The EPA maroons are very dark; a hairline keeps them legible
              // against a dark card without altering the mandated fill.
              stroke="var(--axis)"
              strokeOpacity={0.35}
              strokeWidth={1}
            />
          ))}
          <LabelList
            dataKey="percent"
            position="right"
            formatter={(v: unknown) => (Number(v) === 0 ? "0%" : `${Number(v).toFixed(1)}%`)}
            style={{ fill: "var(--foreground)", fontSize: 11, fontFamily: "Fira Code, monospace" }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
