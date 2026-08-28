"""Regenerate web/src/data/results.json from the data.

Every figure the site displays is produced here. Nothing in the front end is
typed in by hand. Run this after changing any analysis code:

    python3 analysis/export_results.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "PolynomialRegression"))

import methods                                        # noqa: E402
import seasonality                                    # noqa: E402
import validation                                     # noqa: E402
from aqi import CATEGORIES, category, overall_aqi     # noqa: E402
from cubic_regression import CubicRegression          # noqa: E402
from linear_regression import LinearRegression        # noqa: E402
from quadratic_regression import QuadraticRegression  # noqa: E402

DATA = os.path.join(HERE, "..", "Data")
OUT = os.path.join(HERE, "..", "web", "src", "data", "results.json")

SAFE_PM25_THRESHOLD = 15

# Published figures from the notebooks. The export asserts against these so a
# change in the analysis cannot silently rewrite what the project claims.
EXPECTED_EXPONENTIAL_R2 = {
    "co": 0.901678, "no": 0.791526, "no2": 0.699988,
    "o3": 0.194487, "so2": 0.232432, "nh3": 0.406552,
}
EXPECTED_POLYNOMIAL_R2 = {
    "Linear": 0.942251, "Quadratic": 0.942252, "Cubic": 0.943709,
}


def polynomial_block(frame):
    X = frame["co"].values.reshape(-1, 1)
    y = frame["pm2_5"].values
    rows = []
    for name, factory, n_params in (
        ("Linear", LinearRegression, 2),
        ("Quadratic", QuadraticRegression, 3),
        ("Cubic", CubicRegression, 4),
    ):
        model = factory()
        model.fit(X, y)
        safe_co = float(model.predict_inverse(SAFE_PM25_THRESHOLD))
        entry = {
            "model": name,
            "n_params": n_params,
            "r2": float(model.r2_score(y, model.predict(X))),
            "coefficients": [float(c) for c in np.ravel(model.coefficients)],
            "safe_co_for_pm25_15": safe_co,
            "safe_co_valid": safe_co > 0,
        }
        # The cubic keeps its root-finder diagnostics. Without them the site
        # would report "-350.51, invalid" as though the model had predicted a
        # negative concentration, when in fact the solver failed to converge
        # and the returned value is not a root at all.
        converged = getattr(model, "inverse_converged", None)
        if converged is not None:
            entry["solver_converged"] = bool(converged)
            entry["solver_message"] = getattr(model, "inverse_message", "")
            entry["residual_at_returned_value"] = float(
                abs(model.predict(np.array([[safe_co]]))[0] - SAFE_PM25_THRESHOLD)
            )
        rows.append(entry)
    return rows


def curve_points(frame, n=120):
    """Fitted curves sampled over the observed CO range, for plotting."""
    X = frame["co"].values.reshape(-1, 1)
    y = frame["pm2_5"].values
    grid = np.linspace(float(X.min()), float(X.max()), n).reshape(-1, 1)
    out = {"co": [round(float(v), 2) for v in grid.ravel()]}
    for name, factory in (
        ("Linear", LinearRegression),
        ("Quadratic", QuadraticRegression),
        ("Cubic", CubicRegression),
    ):
        model = factory()
        model.fit(X, y)
        out[name.lower()] = [round(float(v), 3) for v in model.predict(grid)]
    return out


def series_block(frame):
    rows = []
    for _, row in frame.iterrows():
        aqi = overall_aqi(row["pm2_5"], row["pm10"])
        rows.append({
            "date": str(row["date"])[:10],
            "pm2_5": round(float(row["pm2_5"]), 2),
            "pm10": round(float(row["pm10"]), 2),
            "co": round(float(row["co"]), 2),
            "aqi": aqi,
            "category": category(aqi),
        })
    return rows


def main():
    biweekly = methods.load_biweekly()
    hourly = pd.read_csv(os.path.join(DATA, "delhi_aqi.csv"), parse_dates=["date"])

    polynomial = polynomial_block(biweekly)
    exponential = methods.exponential_fits(biweekly)

    for row in polynomial:
        expected = EXPECTED_POLYNOMIAL_R2[row["model"]]
        # The cubic normal equation is badly conditioned, so its last digits
        # drift with BLAS build and row order. A tight bound here would fire on
        # a different machine and read as a scientific regression when it is
        # only round-off.
        tolerance = 1e-5 if row["model"] == "Cubic" else 5e-7
        if abs(row["r2"] - expected) >= tolerance:
            raise SystemExit(
                f"{row['model']} R2 moved: {row['r2']:.8f} vs published {expected}"
            )
    for pollutant, expected in EXPECTED_EXPONENTIAL_R2.items():
        got = exponential[pollutant]["r2"]
        if abs(got - expected) >= 5e-7:
            raise SystemExit(
                f"exponential {pollutant} R2 moved: {got:.8f} vs published {expected}"
            )

    season = seasonality.run()
    validation_results = validation.run()

    payload = {
        "meta": {
            "city": "Delhi, India",
            "source_name": "Delhi air quality (Kaggle)",
            "source_url": "https://www.kaggle.com/datasets/deepaksirohiwal/delhi-air-quality",
            "data_licence": "CC BY-NC-SA 4.0",
            "hourly_rows": int(len(hourly)),
            "biweekly_rows": int(len(biweekly)),
            "start": str(hourly["date"].min()),
            "end": str(hourly["date"].max()),
            "pollutants": ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"],
            "timezone_note": (
                "Source timestamps are UTC. Times shown are IST (UTC+5:30); the daily "
                "cycle is only physically sensible under that reading."
            ),
            "aqi_standard": "US EPA, revision effective 6 May 2024",
        },
        "aqi_categories": [
            {"low": low, "high": high, "name": name, "colour": colour}
            for low, high, name, colour in CATEGORIES
        ],
        "polynomial": polynomial,
        "polynomial_curves": curve_points(biweekly),
        "exponential": exponential,
        "simpson": methods.cumulative_exposure(biweekly),
        "validation": validation_results,
        "seasonality": season,
        "series": series_block(biweekly),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")

    print(f"wrote {os.path.relpath(OUT, os.path.join(HERE, '..'))}")
    print(f"  {payload['meta']['hourly_rows']:,} hourly rows, "
          f"{payload['meta']['biweekly_rows']} biweekly rows")
    print("  polynomial and exponential R2 match their published values")
    print("  (validation, seasonality, AQI and Simpson blocks are not covered by that check)")


if __name__ == "__main__":
    main()
