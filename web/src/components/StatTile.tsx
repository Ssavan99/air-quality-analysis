import type { ReactNode } from "react"

export function StatTile({
  value,
  label,
  hint,
  accent,
}: {
  value: ReactNode
  label: string
  hint?: string
  accent?: string
}) {
  return (
    <div className="bg-card rounded-lg border p-4">
      <div
        className="tabular text-2xl leading-tight font-semibold sm:text-3xl"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </div>
      <div className="mt-1 text-sm font-medium">{label}</div>
      {hint ? <div className="text-muted-foreground mt-1 text-xs leading-relaxed">{hint}</div> : null}
    </div>
  )
}
