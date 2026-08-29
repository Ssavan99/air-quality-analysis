import type { ReactNode } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

type Props = {
  title: string
  description?: string
  /** Method or caveat text. Shown under the chart, not floating over it. */
  note?: ReactNode
  children: ReactNode
  height?: number
}

export function ChartCard({ title, description, note, children, height = 320 }: Props) {
  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle className="text-base font-semibold sm:text-lg">{title}</CardTitle>
        {description ? (
          <CardDescription className="text-sm leading-relaxed">{description}</CardDescription>
        ) : null}
      </CardHeader>
      <CardContent className="px-2 sm:px-6">
        <div style={{ height }} className="w-full">
          {children}
        </div>
        {note ? (
          <p className="text-muted-foreground mt-4 px-2 text-xs leading-relaxed sm:px-0">{note}</p>
        ) : null}
      </CardContent>
    </Card>
  )
}
