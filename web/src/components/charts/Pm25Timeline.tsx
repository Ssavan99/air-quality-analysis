import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { axisProps, gridProps, TooltipRow, TooltipShell } from "./chart-parts"
import { categoryColour, formatNumber, results, shortCategory } from "@/lib/data"
import { useIsNarrow } from "@/hooks/useIsNarrow"

/** PM2.5 concentration breakpoints, in ug/m3, from the EPA 2024 revision. */
const BANDS = [
  { from: 0, to: 9.0, name: "Good" },
  { from: 9.0, to: 35.4, name: "Moderate" },
  { from: 35.4, to: 55.4, name: "Unhealthy for Sensitive Groups" },
  { from: 55.4, to: 125.4, name: "Unhealthy" },
  { from: 125.4, to: 225.4, name: "Very Unhealthy" },
  { from: 225.4, to: 325.4, name: "Hazardous" },
]

export function Pm25Timeline() {
  const narrow = useIsNarrow()
  const data = results.series
  const max = Math.max(...data.map((d) => d.pm2_5))
  const top = Math.ceil(max / 100) * 100

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 8, left: narrow ? -12 : 4, bottom: 24 }}>
        {BANDS.map((band) => (
          <ReferenceArea
            key={band.name}
            y1={band.from}
            y2={Math.min(band.to, top)}
            fill={categoryColour(band.name)}
            fillOpacity={0.13}
            ifOverflow="hidden"
          />
        ))}
        {top > 325.4 ? (
          <ReferenceArea
            y1={325.4}
            y2={top}
            fill={categoryColour("Hazardous")}
            fillOpacity={0.24}
            ifOverflow="hidden"
          />
        ) : null}
        <CartesianGrid {...gridProps} />
        <XAxis
          dataKey="date"
          {...axisProps}
          interval={narrow ? 11 : 5}
          tickFormatter={(v: string) => v.slice(0, 7)}
        />
        <YAxis
          {...axisProps}
          domain={[0, top]}
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
            const point = payload[0].payload as (typeof data)[number]
            return (
              <TooltipShell label={point.date}>
                <TooltipRow name="PM2.5" value={`${formatNumber(point.pm2_5, 1)} µg/m³`} />
                <TooltipRow name="PM10" value={`${formatNumber(point.pm10, 1)} µg/m³`} />
                <TooltipRow
                  swatch={categoryColour(point.category)}
                  name={point.aqi === null ? "AQI" : "AQI"}
                  value={point.aqi === null ? "off scale" : String(point.aqi)}
                />
                <TooltipRow name="Category" value={shortCategory(point.category)} />
              </TooltipShell>
            )
          }}
        />
        <Line
          type="monotone"
          dataKey="pm2_5"
          stroke="var(--series)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
