"""Seasonal and daily structure in the hourly series.

Averaging to fortnightly means removes both of these entirely: a two-week mean
cannot show a daily cycle, and 58 points across 26 months barely resolve the
seasonal one. Both are strong in Delhi and both are visible in the raw hourly
data the project already ships.
"""

import os

import pandas as pd

from aqi import BEYOND_INDEX as BEYOND_LABEL
from aqi import category, overall_aqi, pm25_to_aqi

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "Data")

# The CSV timestamps carry no timezone. Read as-is, the daily cycle troughs at
# 09:00 and peaks at 17:00, which is backwards for a city: PM2.5 should be
# lowest in the afternoon, when the boundary layer is deepest, and highest at
# night, when it collapses. Shifting by +5:30 puts the trough at 14:00 IST and
# the peak at 22:00 IST, with a secondary bump at 08:00 for the morning commute
# -- the standard shape for a South Asian megacity. The source API reports UTC,
# and the physics agrees, so the series is treated as UTC and converted to IST.
# Samples land on the half hour once shifted.
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def load_hourly():
    frame = pd.read_csv(os.path.join(DATA, "delhi_aqi.csv"), parse_dates=["date"])
    frame["local_time"] = frame["date"] + IST_OFFSET
    frame["month"] = frame["local_time"].dt.month
    frame["hour"] = frame["local_time"].dt.hour
    return frame


def monthly_profile(frame):
    years = frame.groupby("month")["local_time"].apply(lambda s: s.dt.year.nunique())
    grouped = frame.groupby("month")["pm2_5"].agg(["mean", "median", "count"])
    grouped["years"] = years
    return [
        {
            "month": int(month),
            "name": MONTH_NAMES[month - 1],
            "mean_pm25": round(float(row["mean"]), 2),
            "median_pm25": round(float(row["median"]), 2),
            "hours": int(row["count"]),
            "years_covered": int(row["years"]),
            "aqi": pm25_to_aqi(float(row["mean"])),
            "category": category(pm25_to_aqi(float(row["mean"]))),
        }
        for month, row in grouped.iterrows()
    ]


def diurnal_profile(frame):
    grouped = frame.groupby("hour")["pm2_5"].agg(["mean", "median"])
    return [
        {
            "hour": int(hour),
            "mean_pm25": round(float(row["mean"]), 2),
            "median_pm25": round(float(row["median"]), 2),
        }
        for hour, row in grouped.iterrows()
    ]


def aqi_distribution(frame):
    """How many calendar days fall in each AQI category.

    The EPA index is defined on 24-hour average concentrations, so it is
    computed here on daily means rather than on individual hourly readings.
    Feeding a single hour into a 24-hour breakpoint table produces a number
    that is not an AQI, and it inflates the tails in both directions.
    """
    daily = (
        frame.set_index("local_time")[["pm2_5", "pm10"]]
        .resample("D")
        .mean()
        .dropna()
    )
    categories = [
        category(overall_aqi(pm25, pm10))
        for pm25, pm10 in zip(daily["pm2_5"], daily["pm10"])
    ]
    counts = pd.Series(categories).value_counts()
    total = int(counts.sum())
    # Every category is present, including the ones with no days at all, so a
    # consumer iterating the category list never indexes a missing key.
    from aqi import CATEGORIES  # local import keeps the module import list short

    names = [name for _low, _high, name, _colour in CATEGORIES] + [BEYOND_LABEL]
    return {
        "total_days": total,
        "counts": {name: int(counts.get(name, 0)) for name in names},
        "percent": {name: round(100 * int(counts.get(name, 0)) / total, 2) for name in names},
    }


def run():
    frame = load_hourly()
    monthly = monthly_profile(frame)
    diurnal = diurnal_profile(frame)
    worst_month = max(monthly, key=lambda m: m["mean_pm25"])
    best_month = min(monthly, key=lambda m: m["mean_pm25"])
    # Nov-Feb are all within about 20% of each other and the record does not
    # cover every month the same number of times, so name the season rather
    # than crowning a single month.
    winter = [m for m in monthly if m["month"] in (11, 12, 1, 2)]
    # Jul-Sep. June is pre-monsoon in Delhi and runs markedly higher, so
    # including it would understate the contrast it is meant to measure.
    summer = [m for m in monthly if m["month"] in (7, 8, 9)]
    winter_mean = sum(m["mean_pm25"] for m in winter) / len(winter)
    summer_mean = sum(m["mean_pm25"] for m in summer) / len(summer)
    peak_hour = max(diurnal, key=lambda h: h["mean_pm25"])
    trough_hour = min(diurnal, key=lambda h: h["mean_pm25"])
    return {
        "monthly": monthly,
        "diurnal": diurnal,
        "aqi_distribution": aqi_distribution(frame),
        "summary": {
            # Deliberately no "worst month". Month coverage is uneven (three
            # years for Jan/Nov/Dec, two for the rest) and February rests on
            # two readings 143 ug/m3 apart, so the ranking is unstable: drop
            # one February and December takes the top spot. The season-level
            # comparison below is the figure that survives.
            "winter_mean_pm25": round(winter_mean, 2),
            "winter_months": "Nov-Feb",
            "monsoon_mean_pm25": round(summer_mean, 2),
            "monsoon_months": "Jul-Sep",
            "winter_monsoon_ratio": round(winter_mean / summer_mean, 2),
            "timezone": "IST (UTC+5:30); source timestamps are UTC",
            "peak_hour": peak_hour["hour"],
            "peak_hour_label": f"{peak_hour['hour']:02d}:30",
            "peak_hour_pm25": peak_hour["mean_pm25"],
            "trough_hour": trough_hour["hour"],
            "trough_hour_label": f"{trough_hour['hour']:02d}:30",
            "trough_hour_pm25": trough_hour["mean_pm25"],
            "diurnal_ratio": round(peak_hour["mean_pm25"] / trough_hour["mean_pm25"], 2),
        },
    }


if __name__ == "__main__":
    result = run()
    s = result["summary"]
    print(f"Winter ({s['winter_months']}) mean {s['winter_mean_pm25']} vs monsoon "
          f"({s['monsoon_months']}) {s['monsoon_mean_pm25']} ug/m3 "
          f"-> {s['winter_monsoon_ratio']}x")
    print(f"Daily peak {s['peak_hour_label']} IST at {s['peak_hour_pm25']} ug/m3, "
          f"trough {s['trough_hour_label']} IST at {s['trough_hour_pm25']} ug/m3 "
          f"({s['diurnal_ratio']}x)")
    print("Times are IST; the source timestamps are UTC (see module docstring).")
    print("No single worst month is reported: month coverage is uneven and the")
    print("February ranking rests on two readings 143 ug/m3 apart.")

    print("\nDays per AQI category (the EPA index is a 24-hour statistic):")
    dist = result["aqi_distribution"]
    for name, count in sorted(dist["counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {name:<32}{count:>6,}  ({dist['percent'][name]:>5.2f}%)")
    print(f"  {'total':<32}{dist['total_days']:>6,}")
