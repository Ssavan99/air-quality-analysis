import type { ReactNode } from "react"

/** Shared axis styling so every chart reads the same way. */
export const axisProps = {
  stroke: "var(--axis)",
  tick: { fill: "var(--axis)", fontSize: 11, fontFamily: "Fira Code, monospace" },
  tickLine: { stroke: "var(--axis)" },
  axisLine: { stroke: "var(--grid)" },
} as const

export const gridProps = {
  stroke: "var(--grid)",
  strokeDasharray: "3 3",
  vertical: false,
} as const

export function TooltipShell({
  label,
  children,
}: {
  label: ReactNode
  children: ReactNode
}) {
  return (
    <div className="bg-popover text-popover-foreground rounded-lg border px-3 py-2 shadow-md">
      <p className="mb-1 text-xs font-semibold">{label}</p>
      <div className="tabular space-y-0.5 text-xs">{children}</div>
    </div>
  )
}

export function TooltipRow({
  swatch,
  name,
  value,
}: {
  swatch?: string
  name: string
  value: string
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="flex items-center gap-1.5">
        {swatch ? (
          <span
            aria-hidden
            className="inline-block size-2 shrink-0 rounded-[2px]"
            style={{ background: swatch }}
          />
        ) : null}
        <span className="text-muted-foreground">{name}</span>
      </span>
      <span className="font-medium">{value}</span>
    </div>
  )
}
