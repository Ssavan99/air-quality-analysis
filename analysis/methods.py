"""Importable versions of the exponential fit and Simpson integration.

Both live inside notebooks in this repo, which makes them hard to reuse or
test. These functions mirror that logic exactly so results can be exported
without executing a notebook; the values they produce are asserted against the
notebooks' own published figures in export_results.py.
"""

import os

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "Data")

EXPONENTIAL_POLLUTANTS = ["co", "no", "no2", "o3", "so2", "nh3"]
SIMPSON_POLLUTANTS = ["no2", "so2", "no"]
NUM_INTERVALS = 6


def exponential_model(x, a, b):
    return a * np.exp(b * x)


def exponential_fits(frame):
    """Scale the pollutants to [0, 1], then fit a*exp(b*x) against PM2.5."""
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(frame[EXPONENTIAL_POLLUTANTS])
    y = frame["pm2_5"].values
    if (y <= 0).any():
        y = y + 1e-6

    out = {}
    for index, pollutant in enumerate(EXPONENTIAL_POLLUTANTS):
        x = scaled[:, index]
        try:
            params, _ = curve_fit(exponential_model, x, y, maxfev=10000)
        except RuntimeError:
            out[pollutant] = None
            continue
        y_pred = exponential_model(x, *params)
        out[pollutant] = {
            "a": float(params[0]),
            "b": float(params[1]),
            "r2": float(r2_score(y, y_pred)),
            "mse": float(mean_squared_error(y, y_pred)),
            "correlation": float(frame["pm2_5"].corr(frame[pollutant])),
        }
    return out


def simpsons_method(y, x):
    """Composite Simpson's rule. Needs an odd number of sample points."""
    if len(x) < 3 or len(x) % 2 == 0:
        raise ValueError("Simpson's method requires an odd number of points.")

    h = (x[-1] - x[0]) / (len(x) - 1)
    integral = y[0] + y[-1]
    for i in range(1, len(y) - 1):
        integral += (4 if i % 2 != 0 else 2) * y[i]
    return (h / 3) * integral


def cumulative_exposure(frame):
    """Yearly cumulative exposure per pollutant, over sixths of each year.

    This reproduces the original notebook exactly, including its limitations,
    which the returned coverage block makes explicit rather than hiding:

    - The record starts in November 2020 and ends in January 2023, so 2020 and
      2023 are stubs. Every year is nonetheless integrated over the same
      x = linspace(1, 6) axis, so a two-month year and a twelve-month year
      produce numbers on the same scale. They are not comparable, and 2020
      scores highest for NO2 purely because five weeks of December is not a
      year.
    - With an even point count the last value is duplicated to force an odd
      one, which double-weights the final month.
    - Because the axis is fixed, the result is about five times the mean of the
      inputs. As a summary of a year it carries no more information than the
      mean does.
    """
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["year"] = frame["date"].dt.year
    frame["month"] = frame["date"].dt.month
    monthly = frame.groupby(["year", "month"])[SIMPSON_POLLUTANTS].mean().reset_index()

    coverage = {
        int(year): {
            "months": int(group["month"].nunique()),
            "complete": bool(group["month"].nunique() >= 12),
        }
        for year, group in monthly.groupby("year")
    }

    out = {"coverage": coverage}
    for pollutant in SIMPSON_POLLUTANTS:
        per_year = {}
        for year in monthly["year"].unique():
            values = monthly[monthly["year"] == year][pollutant].values

            if len(values) < NUM_INTERVALS:
                x_original = np.linspace(1, len(values), len(values))
                x_new = np.linspace(1, NUM_INTERVALS, NUM_INTERVALS)
                values = np.interp(x_new, x_original, values)

            if len(values) % 2 == 0:
                values = np.append(values, values[-1])

            x = np.linspace(1, NUM_INTERVALS, len(values))
            try:
                per_year[int(year)] = float(simpsons_method(values, x))
            except ValueError:
                per_year[int(year)] = None
        out[pollutant] = per_year
    return out


def load_biweekly():
    return pd.read_csv(os.path.join(DATA, "biweekly_air_quality_data.csv"))
