import raw from "@/data/results.json"

export type AqiCategory = {
  low: number
  high: number
  name: string
  colour: string
}

export type Pm25Breakpoint = {
  from: number
  to: number
  name: string
}

export type PolynomialRow = {
  model: string
  n_params: number
  r2: number
  coefficients: number[]
  safe_co_for_pm25_15: number
  safe_co_valid: boolean
  /** Present only where a root-finder was used (the cubic). */
  solver_converged?: boolean
  solver_message?: string
  residual_at_returned_value?: number
}

export type ValidationRow = {
  model: string
  in_sample_r2: number
  cv_r2: number
  cv_std: number
  holdout_r2: number
  overfit_gap: number
}

export type ExponentialFit = {
  a: number
  b: number
  r2: number
  mse: number
  correlation: number
}

export type SeriesPoint = {
  date: string
  pm2_5: number
  pm10: number
  co: number
  aqi: number | null
  category: string
}

export type MonthPoint = {
  month: number
  name: string
  mean_pm25: number
  median_pm25: number
  hours: number
  years_covered: number
  aqi: number | null
  category: string
}

export type HourPoint = {
  hour: number
  mean_pm25: number
  median_pm25: number
}

export type Conditioning = {
  cond_normal_equation: number
  cond_design: number
  agrees_with_lstsq_within: number
  agreement_bound_holds: boolean
  r2_inv: number
  r2_lstsq: number
}

export type RepeatedCv = {
  repeats: number
  linear_beats_cubic_rate: number
} & Record<string, { mean_cv_r2: number; sd: number; p5: number; p95: number } | number>

export type Results = {
  meta: {
    city: string
    source_name: string
    source_url: string
    data_licence: string
    hourly_rows: number
    biweekly_rows: number
    start: string
    end: string
    pollutants: string[]
    timezone_note: string
    aqi_standard: string
  }
  aqi_categories: AqiCategory[]
  pm25_breakpoints: Pm25Breakpoint[]
  polynomial: PolynomialRow[]
  polynomial_curves: Record<string, number[]>
  exponential: Record<string, ExponentialFit>
  simpson: {
    coverage: Record<string, { months: number; complete: boolean }>
  } & Record<string, unknown>
  validation: {
    biweekly: {
      n_rows: number
      models: ValidationRow[]
      conditioning: Record<string, Conditioning>
      repeated_cv: RepeatedCv
    }
    hourly: {
      n_rows: number
      models: ValidationRow[]
      conditioning: Record<string, Conditioning>
    }
    aggregation_placebo: {
      biweekly_r2: number
      hourly_r2: number
      random_bins_r2_mean: number
      random_bins_r2_sd: number
      draws: number
      n_bins: number
    }
  }
  seasonality: {
    monthly: MonthPoint[]
    diurnal: HourPoint[]
    aqi_distribution: {
      total_days: number
      counts: Record<string, number>
      percent: Record<string, number>
    }
    summary: Record<string, string | number>
  }
  series: SeriesPoint[]
}

export const results = raw as unknown as Results

/** EPA colour for a category name. Beyond-scale reuses the Hazardous maroon. */
export function categoryColour(name: string): string {
  const match = results.aqi_categories.find((c) => c.name === name)
  return match ? match.colour : "#7E0023"
}

/**
 * Categories whose fill is light enough that white text on them fails
 * contrast. Yellow is the obvious one and the usual mistake.
 */
export function categoryTextColour(name: string): string {
  return name === "Moderate" || name === "Good" ? "#0f172a" : "#ffffff"
}

export const CATEGORY_ORDER = [
  "Good",
  "Moderate",
  "Unhealthy for Sensitive Groups",
  "Unhealthy",
  "Very Unhealthy",
  "Hazardous",
  "Beyond the AQI scale",
]

export const SHORT_CATEGORY: Record<string, string> = {
  "Unhealthy for Sensitive Groups": "Sensitive groups",
  "Beyond the AQI scale": "Beyond scale",
}

export function shortCategory(name: string): string {
  return SHORT_CATEGORY[name] ?? name
}

export function formatNumber(value: number, digits = 2): string {
  return value.toLocaleString("en-GB", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}
