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


def conditioning(X, y):
    """Condition number of X^T X per degree, and what it actually costs.

    The classes solve the normal equation with np.linalg.inv(X.T @ X). CO is on
    the order of 10^3, so its cube is on the order of 10^9 and X^T X spans
    roughly 10^24 against the ~10^16 double precision carries.

    That number is alarming but it is a worst-case bound, not the realised
    error, and it would be wrong to claim the coefficients are meaningless.
    Solving the same system by least squares instead of inverting agrees to
    about eight significant figures, so the reported R2 is sound. What the
    conditioning does mean is that the method has no margin left: the trailing
    digits are not reproducible across machines or BLAS builds. Centring the
    predictor, or using lstsq, removes the risk outright.
    """
    out = {}
    for degree, name in ((1, "Linear"), (2, "Quadratic"), (3, "Cubic")):
        design = np.hstack([np.ones((len(X), 1))] + [X ** k for k in range(1, degree + 1)])
        normal_cond = float(np.linalg.cond(design.T @ design))

        # Same fit, solved stably, to measure the damage rather than assume it.
        inverted = np.linalg.inv(design.T @ design).dot(design.T).dot(y)
        least_squares = np.linalg.lstsq(design, y, rcond=None)[0]
        agreement = float(
            np.max(np.abs(inverted - least_squares) / np.maximum(np.abs(least_squares), 1e-30))
        )
        out[name] = {
            "cond_normal_equation": normal_cond,
            "cond_design": float(np.linalg.cond(design)),
            "max_relative_disagreement_vs_lstsq": agreement,
            "r2_inv": float(_r2(y, design @ inverted)),
            "r2_lstsq": float(_r2(y, design @ least_squares)),
        }
    return out


def repeated_cv(X, y, repeats=200, n_splits=5):
    """Repeat the k-fold CV many times.

    A single seed is a draw, not a measurement. Seed 0 happens to be a
    favourable one: it puts the linear/cubic gap at about 0.017 when the
    typical gap is nearer 0.010. Reporting the distribution keeps the
    conclusion (linear wins) without overstating the size of the effect.
    """
    scores = {name: [] for name, _ in MODELS}
    for seed in range(repeats):
        splitter = KFold(n_splits, shuffle=True, random_state=seed)
        folds = list(splitter.split(X))
        for name, factory in MODELS:
            fold_scores = []
            for train_idx, test_idx in folds:
                model = factory()
                model.fit(X[train_idx], y[train_idx])
                fold_scores.append(_r2(y[test_idx], model.predict(X[test_idx])))
            scores[name].append(float(np.mean(fold_scores)))

    linear = np.array(scores["Linear"])
    summary = {}
    for name, values in scores.items():
        arr = np.array(values)
        summary[name] = {
            "mean_cv_r2": float(arr.mean()),
            "sd": float(arr.std()),
            "p5": float(np.percentile(arr, 5)),
            "p95": float(np.percentile(arr, 95)),
        }
    summary["linear_beats_cubic_rate"] = float(
        (linear > np.array(scores["Cubic"])).mean()
    )
    summary["repeats"] = repeats
    return summary


def aggregation_placebo(draws=200, seed=0):
    """Test *why* fortnightly means score higher than hourly rows.

    The obvious explanation - averaging removes noise the model would have had
    to explain - is testable and turns out to be wrong. Averaging the same
    hourly rows into random groups of the same sizes applies exactly as much
    averaging but destroys the time structure. If noise removal were the cause,
    R2 would rise just as much. It does not: it lands back at the hourly value.

    What is really happening is aggregation over time structure. Most of the
    hourly PM2.5 variance is within-fortnight, where CO co-varies weakly, and
    averaging discards precisely that part. The two R2 values answer different
    questions - hour-to-hour variation versus fortnight-to-fortnight - so
    neither is 'inflated' relative to the other.
    """
    frame = pd.read_csv(os.path.join(DATA, "delhi_aqi.csv"), parse_dates=["date"])
    indexed = frame.set_index("date")
    bins = indexed.resample("2W")
    group_sizes = [len(group) for _label, group in bins if len(group) > 0]

    def fit_r2(co, pm):
        X_ = np.asarray(co).reshape(-1, 1)
        model = LinearRegression()
        model.fit(X_, np.asarray(pm))
        return _r2(np.asarray(pm), model.predict(X_))

    real = indexed.resample("2W").mean().dropna()
    real_r2 = fit_r2(real["co"], real["pm2_5"])
    hourly_r2 = fit_r2(frame["co"], frame["pm2_5"])

    rng = np.random.default_rng(seed)
    placebo_scores = []
    values = frame[["co", "pm2_5"]].to_numpy()
    for _ in range(draws):
        order = rng.permutation(len(values))
        shuffled = values[order]
        means, start = [], 0
        for size in group_sizes:
            chunk = shuffled[start : start + size]
            start += size
            if len(chunk):
                means.append(chunk.mean(axis=0))
        means = np.array(means)
        placebo_scores.append(fit_r2(means[:, 0], means[:, 1]))

    placebo = np.array(placebo_scores)
    return {
        "biweekly_r2": float(real_r2),
        "hourly_r2": float(hourly_r2),
        "random_bins_r2_mean": float(placebo.mean()),
        "random_bins_r2_sd": float(placebo.std()),
        "draws": draws,
        "n_bins": len(group_sizes),
    }


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
            "conditioning": conditioning(X, y),
        }
    X, y = load("biweekly")
    results["biweekly"]["repeated_cv"] = repeated_cv(X, y)
    results["aggregation_placebo"] = aggregation_placebo()
    return results


def report(results):
    for which in ("biweekly", "hourly"):
        block = results[which]
        print(f"\n{which.upper()}  ({block['n_rows']:,} rows)")
        print(f"{'model':<12}{'in-sample':>12}{'5-fold CV':>12}{'held-out':>12}{'gap':>10}")
        for row in block["models"]:
            print(
                f"{row['model']:<12}{row['in_sample_r2']:>12.6f}"
                f"{row['cv_r2']:>12.6f}{row['holdout_r2']:>12.6f}{row['overfit_gap']:>10.6f}"
            )

    repeated = results["biweekly"]["repeated_cv"]
    print(f"\nCross-validated R2 over {repeated['repeats']} repeats of 5-fold CV (biweekly):")
    print(f"{'model':<12}{'mean':>10}{'sd':>9}{'p5':>9}{'p95':>9}")
    for name in ("Linear", "Quadratic", "Cubic"):
        stats = repeated[name]
        print(
            f"{name:<12}{stats['mean_cv_r2']:>10.4f}{stats['sd']:>9.4f}"
            f"{stats['p5']:>9.4f}{stats['p95']:>9.4f}"
        )
    print(
        f"  linear beats cubic in {repeated['linear_beats_cubic_rate'] * 100:.1f}% of repeats"
    )
    print(
        "  Note the spread: with a standard deviation near 0.01 these figures do not\n"
        "  support six decimal places. The ordering is the finding, not the digits."
    )

    print("\nConditioning (biweekly), and what it actually costs:")
    print(f"{'model':<12}{'cond(X^T X)':>14}{'vs lstsq':>12}{'R2 (inv)':>12}{'R2 (lstsq)':>12}")
    for name, block in results["biweekly"]["conditioning"].items():
        print(
            f"{name:<12}{block['cond_normal_equation']:>14.2e}"
            f"{block['max_relative_disagreement_vs_lstsq']:>12.1e}"
            f"{block['r2_inv']:>12.6f}{block['r2_lstsq']:>12.6f}"
        )

    placebo = results["aggregation_placebo"]
    print("\nWhy do fortnightly means score higher than hourly rows?")
    print(f"  fortnightly means (real bins) R2 = {placebo['biweekly_r2']:.4f}")
    print(f"  raw hourly rows               R2 = {placebo['hourly_r2']:.4f}")
    print(
        f"  random bins, same sizes       R2 = {placebo['random_bins_r2_mean']:.4f} "
        f"(sd {placebo['random_bins_r2_sd']:.4f}, {placebo['draws']} draws)"
    )

    bi = {r["model"]: r for r in results["biweekly"]["models"]}
    hr = {r["model"]: r for r in results["hourly"]["models"]}
    print("\nWhat this shows:")
    print(
        f"  1. On {results['biweekly']['n_rows']} fortnightly points the in-sample R2 rises with "
        f"degree while the cross-validated R2 falls: linear "
        f"{repeated['Linear']['mean_cv_r2']:.3f} against cubic "
        f"{repeated['Cubic']['mean_cv_r2']:.3f} averaged over {repeated['repeats']} repeats. "
        f"The cubic is not better, it is overfitting. In-sample R2 cannot fall when a term is "
        f"added, so its rise is not evidence of anything - only the CV column is."
    )
    print(
        f"  2. This is a small-sample result. On all {results['hourly']['n_rows']:,} hourly rows "
        f"the gap collapses to {hr['Cubic']['overfit_gap']:.4f} and the cubic very slightly "
        f"*wins* on CV ({hr['Cubic']['cv_r2']:.4f} against {hr['Linear']['cv_r2']:.4f}). "
        f"'The cubic overfits' is a statement about n=58, not about the relationship."
    )
    print(
        f"  3. Fitting fortnightly means answers a different question from fitting hourly "
        f"values, and scores higher for it ({bi['Linear']['in_sample_r2']:.3f} against "
        f"{hr['Linear']['in_sample_r2']:.3f}). It is not noise removal: averaging the same rows "
        f"into random bins of the same sizes gives {placebo['random_bins_r2_mean']:.3f}, back at "
        f"the hourly value. Aggregating over time discards the within-fortnight variation, which "
        f"is the part CO explains least."
    )
    print(
        f"  4. The cubic normal equation is poorly conditioned "
        f"(cond ~ {results['biweekly']['conditioning']['Cubic']['cond_normal_equation']:.1e}), but "
        f"it still agrees with a least-squares solve to "
        f"{results['biweekly']['conditioning']['Cubic']['max_relative_disagreement_vs_lstsq']:.0e} "
        f"relative, so the reported R2 is sound. The method simply has no margin left."
    )
    print(
        "\nNote on the held-out column: with 58 rows a single 25% split leaves 14 test "
        "points, so that number is noisy and should not be read on its own. The repeated "
        "figures above are the reliable signal."
    )


if __name__ == "__main__":
    report(run())
