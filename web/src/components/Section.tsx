import type { ReactNode } from "react"

export function Section({
  id,
  eyebrow,
  title,
  lede,
  children,
}: {
  id: string
  eyebrow: string
  title: string
  lede?: ReactNode
  children: ReactNode
}) {
  return (
    <section id={id} className="scroll-mt-20">
      <div className="mb-5">
        <p className="text-muted-foreground font-mono text-xs tracking-widest uppercase">{eyebrow}</p>
        <h2 className="mt-1 text-xl font-semibold sm:text-2xl">{title}</h2>
        {lede ? (
          <p className="text-muted-foreground mt-2 max-w-[68ch] text-sm leading-relaxed sm:text-base">{lede}</p>
        ) : null}
      </div>
      <div className="space-y-5">{children}</div>
    </section>
  )
}
