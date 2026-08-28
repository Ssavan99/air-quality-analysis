import { ChartCard } from "@/components/ChartCard"
import { Section } from "@/components/Section"
import { StatTile } from "@/components/StatTile"
import { ThemeToggle } from "@/components/ThemeToggle"
import { AqiDistribution } from "@/components/charts/AqiDistribution"
import { CoScatter } from "@/components/charts/CoScatter"
import { DiurnalProfile } from "@/components/charts/DiurnalProfile"
import { ExponentialQuality } from "@/components/charts/ExponentialQuality"
import { ModelComparison } from "@/components/charts/ModelComparison"
import { Pm25Timeline } from "@/components/charts/Pm25Timeline"
import { SeasonalProfile } from "@/components/charts/SeasonalProfile"
import { SimpsonExposure } from "@/components/charts/SimpsonExposure"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { categoryColour, formatNumber, results } from "@/lib/data"

const { meta, seasonality, validation, polynomial } = results

const hourlyLinear = validation.hourly.models.find((m) => m.model === "Linear")!
const cubicPoly = polynomial.find((p) => p.model === "Cubic")!
const summary = seasonality.summary as Record<string, number | string>
const dist = seasonality.aqi_distribution
const goodDays = dist.counts["Good"] ?? 0
const beyondPercent = dist.percent["Beyond the AQI scale"] ?? 0
const repeated = validation.biweekly.repeated_cv
const cvMean = (m: string) => (repeated[m] as { mean_cv_r2: number }).mean_cv_r2
const cvSd = (m: string) => (repeated[m] as { sd: number }).sd
const placebo = validation.aggregation_placebo
const cubicCond = validation.biweekly.conditioning.Cubic
const hourlyCubic = validation.hourly.models.find((m) => m.model === "Cubic")!

export default function App() {
  return (
    <div className="min-h-dvh">
      <header className="bg-background/85 sticky top-0 z-20 border-b backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <div className="min-w-0">
            <p className="truncate font-mono text-sm font-semibold">Delhi Air Quality</p>
            <p className="text-muted-foreground truncate text-xs">
              {meta.hourly_rows.toLocaleString("en-GB")} hourly readings · 2020–2023
            </p>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-14 px-4 py-10 sm:py-14">
        {/* Hero */}
        <div>
          <Badge variant="secondary" className="mb-3 font-mono text-xs">
            Numerical methods on real data
          </Badge>
          <h1 className="text-3xl leading-tight font-semibold tracking-tight sm:text-4xl">
            Three ways to model Delhi&rsquo;s air, and what each one gets wrong
          </h1>
          <p className="text-muted-foreground mt-4 max-w-[68ch] leading-relaxed">
            Polynomial regression, exponential regression and Simpson&rsquo;s rule applied to{" "}
            {meta.hourly_rows.toLocaleString("en-GB")} hourly pollution readings from Delhi between{" "}
            {meta.start.slice(0, 10)} and {meta.end.slice(0, 10)}. The interesting result is not
            which model fits best &mdash; it is that the model which <em>looks</em> best is the one
            you should throw away.
          </p>

          <div className="mt-7 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile
              value={goodDays.toLocaleString("en-GB")}
              label="Days rated Good"
              hint={`Out of ${dist.total_days.toLocaleString("en-GB")} days measured. Not one.`}
            />
            <StatTile
              value={`${beyondPercent.toFixed(1)}%`}
              label="Days off the scale"
              hint="Past the top of the US EPA index, which stops at 500."
              accent={categoryColour("Hazardous")}
            />
            <StatTile
              value={`${formatNumber(Number(summary.winter_monsoon_ratio), 1)}×`}
              label="Winter vs monsoon"
              hint={`${summary.winter_mean_pm25} against ${summary.monsoon_mean_pm25} µg/m³ mean PM2.5 (${summary.winter_months} vs ${summary.monsoon_months}).`}
            />
            <StatTile
              value={`${formatNumber(Number(summary.diurnal_ratio), 1)}×`}
              label="Night vs afternoon"
              hint={`Peak ${summary.peak_hour_label} IST, trough ${summary.trough_hour_label} IST.`}
            />
          </div>
        </div>

        <Separator />

        {/* The air itself */}
        <Section
          id="air"
          eyebrow="The data"
          title="What the air was actually like"
          lede={
            <>
              PM2.5 is fine particulate matter &mdash; small enough to reach the bloodstream. The
              shaded bands are the US EPA&rsquo;s categories ({meta.aqi_standard}). Every fortnight
              in this record sits in the top three bands.
            </>
          }
        >
          <ChartCard
            title="PM2.5 over time"
            description="Fortnightly means, against the EPA category bands."
            height={340}
            note={
              <>
                Bands are PM2.5 concentration breakpoints, not index values. The record never enters
                the Good or Moderate band, so neither is visible on this scale.
              </>
            }
          >
            <Pm25Timeline />
          </ChartCard>

          <ChartCard
            title="Where the days fall"
            description={`Share of all ${dist.total_days.toLocaleString("en-GB")} days by EPA category.`}
            height={300}
            note={
              <>
                Computed on <strong>daily means</strong>, because the EPA index is defined on
                24-hour averages &mdash; putting a single hour through a 24-hour breakpoint table
                does not produce an AQI. &ldquo;Beyond scale&rdquo; means the concentration exceeded
                325.4 µg/m³, above which the EPA defines no index value; those days are counted as
                off-scale rather than quietly clipped to 500 or dropped. That band is hatched
                because the EPA assigns it no colour &mdash; every other bar uses the official one.
              </>
            }
          >
            <AqiDistribution />
          </ChartCard>
        </Section>

        {/* Model selection - the core finding */}
        <Section
          id="models"
          eyebrow="The finding"
          title="The best-fitting model is the wrong one"
          lede={
            <>
              Fitting CO against PM2.5 with polynomials of increasing degree, the cubic scores the
              highest R². It is also the only one that predicts a <em>negative</em> concentration,
              and the only one that falls apart on data it has not seen.
            </>
          }
        >
          <ChartCard
            title="CO against PM2.5, with all three fits"
            description="58 fortnightly observations and the three fitted curves."
            height={360}
            note={
              <>
                Curves are dashed and dotted as well as coloured, so they stay distinguishable
                without relying on colour.
              </>
            }
          >
            <CoScatter />
          </ChartCard>

          <ChartCard
            title="In-sample R² against cross-validated R²"
            description="Same models, scored on the data they were fitted to, then on data they were not."
            height={330}
            note={
              <>
                In-sample R² cannot fall when a term is added, so a higher degree always looks at
                least as good &mdash; its rise is not evidence of anything. Only the
                cross-validated column carries information, and it inverts the ranking. Averaged
                over {repeated.repeats} repeats of 5-fold CV, linear scores{" "}
                {formatNumber(cvMean("Linear"), 3)} against cubic {formatNumber(cvMean("Cubic"), 3)},
                and linear wins in{" "}
                {(Number(repeated.linear_beats_cubic_rate) * 100).toFixed(0)}% of them. The bars
                above show a single split; the spread across repeats is about ±
                {formatNumber(cvSd("Cubic"), 3)}, which is why this is a claim about the ordering
                and not about the decimals.
              </>
            }
          >
            <ModelComparison />
          </ChartCard>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="bg-card rounded-lg border p-5">
              <p className="font-mono text-xs tracking-widest uppercase" style={{ color: categoryColour("Unhealthy") }}>
                The solver gives up
              </p>
              <p className="tabular mt-2 text-2xl font-semibold">
                {formatNumber(cubicPoly.safe_co_for_pm25_15, 2)} µg/m³
              </p>
              <p className="text-muted-foreground mt-2 text-sm leading-relaxed">
                Asked what CO level would bring PM2.5 to the 15 µg/m³ safe threshold, the cubic
                returns a negative concentration. It is tempting to call that a prediction, but it
                is not one: the root-finder reports that it failed to converge, and the value it
                returns leaves a residual of{" "}
                {formatNumber(cubicPoly.residual_at_returned_value ?? 0, 2)} &mdash; it is not a root
                at all. The fitted cubic simply has no real solution anywhere near the observed CO
                range. The linear and quadratic models answer the same question at{" "}
                {formatNumber(polynomial[0].safe_co_for_pm25_15, 0)} and{" "}
                {formatNumber(polynomial[1].safe_co_for_pm25_15, 0)} µg/m³.
              </p>
            </div>
            <div className="bg-card rounded-lg border p-5">
              <p className="text-muted-foreground font-mono text-xs tracking-widest uppercase">
                No margin left
              </p>
              <p className="tabular mt-2 text-2xl font-semibold">
                cond ≈ {cubicCond.cond_normal_equation.toExponential(1)}
              </p>
              <p className="text-muted-foreground mt-2 text-sm leading-relaxed">
                Condition number of XᵀX for the cubic normal equation, against the roughly 1×10¹⁶
                double precision carries. That sounds fatal, and it would be easy to claim the
                coefficients are meaningless &mdash; but it is a worst-case bound. Solving the same
                system by least squares instead of inverting agrees to{" "}
                {cubicCond.max_relative_disagreement_vs_lstsq.toExponential(0)} relative, so the R²
                above is sound. What it does mean is that the method has no headroom: the trailing
                digits would not survive a different machine.
              </p>
            </div>
          </div>
        </Section>

        {/* The averaging finding */}
        <Section
          id="averaging"
          eyebrow="A second finding"
          title="The two R² values answer different questions"
          lede={
            <>
              The analysis averages {meta.hourly_rows.toLocaleString("en-GB")} hourly rows down to{" "}
              {meta.biweekly_rows} fortnightly means. Fitting the averages scores{" "}
              {formatNumber(placebo.biweekly_r2, 3)}; fitting the raw hours scores{" "}
              {formatNumber(placebo.hourly_r2, 3)}. Neither is wrong &mdash; they are measuring
              different things.
            </>
          }
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <StatTile
              value={formatNumber(placebo.biweekly_r2, 3)}
              label={`Linear R² on ${meta.biweekly_rows} fortnightly means`}
              hint="Fortnight-to-fortnight variation — largely the seasonal signal."
            />
            <StatTile
              value={formatNumber(placebo.hourly_r2, 3)}
              label={`Linear R² on all ${meta.hourly_rows.toLocaleString("en-GB")} hourly rows`}
              hint="Hour-to-hour variation, which CO explains less well."
            />
          </div>
          <div className="bg-card rounded-lg border p-5">
            <p className="text-muted-foreground font-mono text-xs tracking-widest uppercase">
              The obvious explanation is wrong
            </p>
            <p className="mt-2 text-sm leading-relaxed">
              It is natural to say averaging &ldquo;removes noise the model would otherwise have to
              explain&rdquo;. That is testable, and it fails. Averaging the same hourly rows into{" "}
              {placebo.n_bins} <em>random</em> groups of the identical sizes applies exactly as much
              averaging but destroys the time structure. Over {placebo.draws} draws it scores{" "}
              <span className="tabular font-semibold">{formatNumber(placebo.random_bins_r2_mean, 3)}</span>{" "}
              &mdash; back at the hourly value, not the fortnightly one.
            </p>
            <p className="text-muted-foreground mt-3 text-sm leading-relaxed">
              So the gain is not noise removal, it is aggregation over time. Most of the hourly
              PM2.5 variance sits <em>within</em> a fortnight, where CO co-varies weakly; averaging
              discards precisely that part and keeps the between-fortnight seasonal swing, which CO
              tracks closely. The fortnightly {formatNumber(placebo.biweekly_r2, 3)} describes the
              seasonal relationship. It is not an estimate of the hour-to-hour one.
            </p>
          </div>
          <ChartCard
            title="The same comparison on the full hourly series"
            description="With 18,776 rows instead of 58, the choice of degree stops mattering."
            height={330}
            note={
              <>
                The overfit gap collapses to about{" "}
                {formatNumber(hourlyCubic.overfit_gap, 4)}, and the cubic now very slightly{" "}
                <em>wins</em> on cross-validation ({formatNumber(hourlyCubic.cv_r2, 4)} against{" "}
                {formatNumber(hourlyLinear.cv_r2, 4)}). That is worth stating plainly: &ldquo;the
                cubic overfits&rdquo; is a claim about {meta.biweekly_rows} points, not about the
                relationship itself. With 18,776 rows there is enough data to support the extra
                terms, and the degree stops mattering. On the fortnightly data the project actually
                uses, linear remains the right choice.
              </>
            }
          >
            <ModelComparison dataset="hourly" />
          </ChartCard>
        </Section>

        {/* Cycles */}
        <Section
          id="cycles"
          eyebrow="Recovered detail"
          title="The cycles the averaging erased"
          lede={
            <>
              A fortnightly mean cannot show a daily cycle, and 58 points across 26 months barely
              resolve the seasonal one. Both are strong, and both are in the raw hourly data.
            </>
          }
        >
          <ChartCard
            title="Mean PM2.5 by month"
            description="Bars carry their EPA category colour."
            height={300}
            note={
              <>
                Winter ({summary.winter_months}) runs about{" "}
                {formatNumber(Number(summary.winter_monsoon_ratio), 1)}× the monsoon months (
                {summary.monsoon_months}). No single worst month is named on purpose: the record
                spans 26 months, so some appear three times and others twice, and February rests on
                two readings 143 µg/m³ apart &mdash; drop one and December takes the top spot. The
                season-level contrast is the part that survives.
              </>
            }
          >
            <SeasonalProfile />
          </ChartCard>

          <ChartCard
            title="Mean PM2.5 by hour of day"
            description="All hourly readings, folded onto a single day, in IST."
            height={300}
            note={
              <>
                {meta.timezone_note} Read as stored the cycle troughs at 09:00 and peaks at 17:00,
                which is inverted for a city: PM2.5 should be lowest in the afternoon when the
                boundary layer is deepest and highest at night when it collapses. Shifted to IST the
                trough falls at {summary.trough_hour_label} and the peak at{" "}
                {summary.peak_hour_label}, with a morning-commute bump. (Every shifted sample lands
                on the half hour, since the source readings are on the hour in UTC.)
              </>
            }
          >
            <DiurnalProfile />
          </ChartCard>
        </Section>

        {/* Other methods */}
        <Section
          id="methods"
          eyebrow="The other two methods"
          title="Exponential fits and cumulative exposure"
          lede="Which pollutants track PM2.5 exponentially, and how much total exposure each year carried."
        >
          <ChartCard
            title="Exponential fit quality by pollutant"
            description="R² for PM2.5 = a·e^(b·x), fitted per pollutant on min-max scaled inputs."
            height={300}
            note={
              <>
                CO dominates at R² {formatNumber(results.exponential.co.r2, 3)}; ozone is close to
                useless at {formatNumber(results.exponential.o3.r2, 3)}, which is expected since O3
                correlates <em>negatively</em> with PM2.5 ({formatNumber(results.exponential.o3.correlation, 2)}).
                An exponential model assumes a monotonic relationship, so a negative correlation is
                a poor candidate for it.
              </>
            }
          >
            <ExponentialQuality />
          </ChartCard>

          <ChartCard
            title="Cumulative exposure by year"
            description="Simpson's rule over sixths of each year, for the three pollutants most correlated with PM2.5."
            height={300}
            note={
              <>
                Only complete years are shown. The record starts in November 2020 and ends in
                January 2023, leaving two-month stubs at each end which the original method
                interpolates onto the same six intervals as a full year &mdash; on that footing 2020
                scored highest of all four, which says nothing except that five weeks of December is
                not a year. Note too that with a fixed interval axis this integral works out at
                about five times the annual mean, so it carries no more information than the mean.
              </>
            }
          >
            <SimpsonExposure />
          </ChartCard>
        </Section>

        {/* Honest limitations */}
        <Section id="limits" eyebrow="Caveats" title="What this does not show">
          <div className="bg-card rounded-lg border p-5">
            <ul className="text-muted-foreground space-y-3 text-sm leading-relaxed">
              <li>
                <span className="text-foreground font-medium">Correlation, not causation.</span> CO
                predicts PM2.5 well because both come largely from combustion. Reducing CO would not
                mechanically reduce PM2.5.
              </li>
              <li>
                <span className="text-foreground font-medium">The safe-threshold figures are extrapolation.</span>{" "}
                The 15 µg/m³ target is far below anything in this record, whose minimum fortnightly
                mean is 77 µg/m³. All three models are being asked about a regime they never saw.
              </li>
              <li>
                <span className="text-foreground font-medium">One city, 26 months.</span> Nothing
                here generalises to other cities or to longer-run trends.
              </li>
              <li>
                <span className="text-foreground font-medium">Single-station provenance.</span> The
                source dataset does not document its monitoring stations or its collection method.
              </li>
              <li>
                <span className="text-foreground font-medium">The timezone is inferred.</span> It is
                deduced from the shape of the daily cycle, not stated by the source.
              </li>
            </ul>
          </div>
        </Section>
      </main>

      <footer className="mt-8 border-t">
        <div className="text-muted-foreground mx-auto max-w-5xl space-y-3 px-4 py-8 text-xs leading-relaxed">
          <p>
            Data:{" "}
            <a className="text-foreground underline underline-offset-2" href={meta.source_url} target="_blank" rel="noreferrer noopener">
              {meta.source_name}
            </a>{" "}
            &mdash; licensed {meta.data_licence}. Redistributed under those terms; the data is not
            covered by this project&rsquo;s MIT licence.
          </p>
          <p>
            Every figure on this page is generated from the data by{" "}
            <code className="font-mono">analysis/export_results.py</code>. None are typed in by hand.
          </p>
          <p>Built by Akshita Goel, Morenzo MinarWidjaja and Savan Patel.</p>
        </div>
      </footer>
    </div>
  )
}
