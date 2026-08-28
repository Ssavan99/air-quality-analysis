"""Seasonal and daily structure in the hourly series.

Averaging to fortnightly means removes both of these entirely: a two-week mean
cannot show a daily cycle, and 58 points across 26 months barely resolve the
seasonal one. Both are strong in Delhi and both are visible in the raw hourly
data the project already ships.
"""

import os

import pandas as pd

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
    """How many hours fall in each AQI category."""
    categories = [
        category(overall_aqi(pm25, pm10))
        for pm25, pm10 in zip(frame["pm2_5"], frame["pm10"])
    ]
    counts = pd.Series(categories).value_counts()
    total = int(counts.sum())
    return {
        "total_hours": total,
        "counts": {str(name): int(value) for name, value in counts.items()},
        "percent": {str(name): round(100 * int(value) / total, 2) for name, value in counts.items()},
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
    summer = [m for m in monthly if m["month"] in (6, 7, 8, 9)]
    winter_mean = sum(m["mean_pm25"] for m in winter) / len(winter)
    summer_mean = sum(m["mean_pm25"] for m in summer) / len(summer)
    peak_hour = max(diurnal, key=lambda h: h["mean_pm25"])
    trough_hour = min(diurnal, key=lambda h: h["mean_pm25"])
    return {
        "monthly": monthly,
        "diurnal": diurnal,
        "aqi_distribution": aqi_distribution(frame),
        "summary": {
            "worst_month": worst_month["name"],
            "worst_month_pm25": worst_month["mean_pm25"],
            "best_month": best_month["name"],
            "best_month_pm25": best_month["mean_pm25"],
            "seasonal_ratio": round(worst_month["mean_pm25"] / best_month["mean_pm25"], 2),
            "winter_mean_pm25": round(winter_mean, 2),
            "summer_mean_pm25": round(summer_mean, 2),
            "winter_summer_ratio": round(winter_mean / summer_mean, 2),
            "timezone": "IST (UTC+5:30); source timestamps are UTC",
            "peak_hour": peak_hour["hour"],
            "peak_hour_pm25": peak_hour["mean_pm25"],
            "trough_hour": trough_hour["hour"],
            "trough_hour_pm25": trough_hour["mean_pm25"],
            "diurnal_ratio": round(peak_hour["mean_pm25"] / trough_hour["mean_pm25"], 2),
        },
    }


if __name__ == "__main__":
    result = run()
    s = result["summary"]
    print(f"Worst month: {s['worst_month']} at {s['worst_month_pm25']} ug/m3")
    print(f"Best month:  {s['best_month']} at {s['best_month_pm25']} ug/m3")
    print(f"Seasonal swing: {s['seasonal_ratio']}x")
    print(f"Winter (Nov-Feb) mean {s['winter_mean_pm25']} vs monsoon (Jun-Sep) "
          f"{s['summer_mean_pm25']} ug/m3 -> {s['winter_summer_ratio']}x")
    print(f"Daily peak {s['peak_hour']:02d}:00 IST at {s['peak_hour_pm25']} ug/m3, "
          f"trough {s['trough_hour']:02d}:00 IST at {s['trough_hour_pm25']} ug/m3 "
          f"({s['diurnal_ratio']}x)")
    print("Times are IST; the source timestamps are UTC (see module docstring).")
    print("\nHours per AQI category:")
    dist = result["aqi_distribution"]
    for name, count in sorted(dist["counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {name:<32}{count:>7,}  ({dist['percent'][name]:>5.2f}%)")
