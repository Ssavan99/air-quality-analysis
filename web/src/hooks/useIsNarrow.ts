import { useEffect, useState } from "react"

/** True on phone-width viewports, so charts can thin out their ticks. */
export function useIsNarrow(breakpoint = 640) {
  const [narrow, setNarrow] = useState(
    () => typeof window !== "undefined" && window.innerWidth < breakpoint
  )

  useEffect(() => {
    const query = window.matchMedia(`(max-width: ${breakpoint - 1}px)`)
    const update = () => setNarrow(query.matches)
    update()
    query.addEventListener("change", update)
    return () => query.removeEventListener("change", update)
  }, [breakpoint])

  return narrow
}
