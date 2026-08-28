"""Out-of-sample validation for the polynomial models.

The original comparison scored R^2 on the same rows it fitted. In-sample R^2
cannot fall when you add a term, so a higher-degree polynomial always looks at
least as good -- which is exactly why the cubic appeared to win. Cross-
validation asks the question the project actually cares about: does the extra
term help on data the model has not seen?

This module also refits on the full hourly series. The published analysis uses
58 biweekly averages derived from 18,776 hourly rows.
"""

import os
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, train_test_split

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "PolynomialRegression")
)

from cubic_regression import CubicRegression          # noqa: E402
from linear_regression import LinearRegression        # noqa: E402
from quadratic_regression import QuadraticRegression  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "Data")

MODELS = [
    ("Linear", LinearRegression),
    ("Quadratic", QuadraticRegression),
    ("Cubic", CubicRegression),
]


def _r2(y, y_pred):
    ss_total = np.sum((y - np.mean(y)) ** 2)
    ss_residual = np.sum((y - y_pred) ** 2)
    return 1 - (ss_residual / ss_total)


def evaluate(X, y, n_splits=5, seed=0):
    """In-sample R^2, k-fold CV R^2 and a held-out test R^2 per model."""
    rows = []
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=seed)

    for name, factory in MODELS:
        model = factory()
        model.fit(X, y)
        in_sample = _r2(y, model.predict(X))

        fold_scores = []
        for train_idx, test_idx in KFold(n_splits, shuffle=True, random_state=seed).split(X):
            fold = factory()
            fold.fit(X[train_idx], y[train_idx])
            fold_scores.append(_r2(y[test_idx], fold.predict(X[test_idx])))

        holdout = factory()
        holdout.fit(X_tr, y_tr)
        test_r2 = _r2(y_te, holdout.predict(X_te))

        rows.append(
            {
                "model": name,
                "in_sample_r2": float(in_sample),
                "cv_r2": float(np.mean(fold_scores)),
                "cv_std": float(np.std(fold_scores)),
                "holdout_r2": float(test_r2),
                "overfit_gap": float(in_sample - np.mean(fold_scores)),
            }
        )
    return rows


def conditioning(X):
    """Condition number of X^T X for each polynomial degree.

    The classes solve the normal equation with np.linalg.inv(X.T @ X). CO is on
    the order of 10^3, so its cube is on the order of 10^9 and X^T X spans
    roughly 10^24. Double precision carries about 16 significant digits, so at
    that conditioning the cubic coefficients retain essentially none of them.
    Centring and scaling the predictor, or solving by QR / lstsq instead of
    inverting, would fix it.
    """
    out = {}
    for degree, name in ((1, "Linear"), (2, "Quadratic"), (3, "Cubic")):
        design = np.hstack([np.ones((len(X), 1))] + [X ** k for k in range(1, degree + 1)])
        out[name] = float(np.linalg.cond(design.T @ design))
    return out


def cv_stability(X, y, seeds=range(5), n_splits=5):
    """Repeat the CV under several shuffles to show the ordering is not luck."""
    out = {name: [] for name, _ in MODELS}
    for seed in seeds:
        for name, factory in MODELS:
            scores = []
            for train_idx, test_idx in KFold(n_splits, shuffle=True, random_state=seed).split(X):
                model = factory()
                model.fit(X[train_idx], y[train_idx])
                scores.append(_r2(y[test_idx], model.predict(X[test_idx])))
            out[name].append(float(np.mean(scores)))
    return out


def load(which):
    """Load either the 58-row biweekly averages or the full hourly series."""
    filename = "biweekly_air_quality_data.csv" if which == "biweekly" else "delhi_aqi.csv"
    frame = pd.read_csv(os.path.join(DATA, filename))
    X = frame["co"].values.reshape(-1, 1)
    y = frame["pm2_5"].values
    return X, y


def run():
    results = {}
    for which in ("biweekly", "hourly"):
        X, y = load(which)
        results[which] = {
            "n_rows": int(len(y)),
            "models": evaluate(X, y),
            "conditioning": conditioning(X),
        }
    X, y = load("biweekly")
    results["biweekly"]["cv_stability"] = cv_stability(X, y)
    return results


def report(results):
    for which, block in results.items():
        print(f"\n{which.upper()}  ({block['n_rows']:,} rows)")
        print(f"{'model':<12}{'in-sample':>12}{'5-fold CV':>12}{'held-out':>12}{'gap':>10}")
        for row in block["models"]:
            print(
                f"{row['model']:<12}{row['in_sample_r2']:>12.6f}"
                f"{row['cv_r2']:>12.6f}{row['holdout_r2']:>12.6f}{row['overfit_gap']:>10.6f}"
            )

    print("\nCondition number of X^T X (biweekly). Double precision carries ~1e16:")
    for name, value in results["biweekly"]["conditioning"].items():
        warn = "   <- past what float64 can represent" if value > 1e16 else ""
        print(f"  {name:<12}{value:>12.3e}{warn}")

    print("\n5-fold CV mean R2 under five different shuffles:")
    stability = results["biweekly"]["cv_stability"]
    for name in stability:
        runs = "  ".join(f"{v:.4f}" for v in stability[name])
        print(f"  {name:<12}{runs}")
    runs = len(stability["Linear"])
    linear_best = sum(
        stability["Linear"][i] > max(stability["Quadratic"][i], stability["Cubic"][i])
        for i in range(runs)
    )
    strict = sum(
        stability["Linear"][i] > stability["Quadratic"][i] > stability["Cubic"][i]
        for i in range(runs)
    )
    print(f"  linear scores best in {linear_best} of {runs} shuffles")
    print(
        f"  the full linear > quadratic > cubic ordering holds in {strict} of {runs}; "
        "the quadratic/cubic ordering swaps once, so the claim worth making is that "
        "linear wins, not that the ranking below it is fixed"
    )

    bi = {r["model"]: r for r in results["biweekly"]["models"]}
    hr = {r["model"]: r for r in results["hourly"]["models"]}
    print("\nWhat this shows:")
    print(
        f"  1. On the biweekly data the in-sample R2 rises with degree "
        f"({bi['Linear']['in_sample_r2']:.6f} -> {bi['Cubic']['in_sample_r2']:.6f}) while the "
        f"cross-validated R2 falls ({bi['Linear']['cv_r2']:.6f} -> {bi['Cubic']['cv_r2']:.6f}). "
        f"The cubic is not better, it is overfitting."
    )
    print(
        f"  2. Averaging to biweekly inflates the headline R2: linear scores "
        f"{bi['Linear']['in_sample_r2']:.3f} on 58 averaged points but "
        f"{hr['Linear']['in_sample_r2']:.3f} on all {results['hourly']['n_rows']:,} hourly rows. "
        f"Averaging smooths away the noise the model would otherwise have to explain."
    )
    print(
        "  3. The cubic normal equation is numerically unsound here regardless of fit "
        "quality: cond(X^T X) is about 1e24 against roughly 1e16 of available precision."
    )
    print(
        "\nNote on the held-out column: with 58 rows a single 25% split leaves 14 test "
        "points, so that number is noisy and should not be read on its own. The 5-fold "
        "figures, and their stability across shuffles, are the reliable signal."
    )


if __name__ == "__main__":
    report(run())
