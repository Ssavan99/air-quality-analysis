"""Render the README figure from results.json.

Reads the same file the web front end reads, so the image cannot drift from
what the site and the analysis report.

    python3 analysis/make_figure.py
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "web", "src", "data", "results.json")
OUT = os.path.join(HERE, "..", "docs", "headline.png")

INK = "#0f172a"
MUTED = "#55637a"
GRID = "#dbe3ee"
SERIES = "#1e40af"
SERIES_CV = "#6d28d9"


def main():
    with open(RESULTS) as handle:
        data = json.load(handle)

    repeated = data["validation"]["biweekly"]["repeated_cv"]
    models = ["Linear", "Quadratic", "Cubic"]
    in_sample = [
        next(m["in_sample_r2"] for m in data["validation"]["biweekly"]["models"] if m["model"] == name)
        for name in models
    ]
    cv_mean = [repeated[name]["mean_cv_r2"] for name in models]
    cv_sd = [repeated[name]["sd"] for name in models]

    dist = data["seasonality"]["aqi_distribution"]
    categories = [c["name"] for c in data["aqi_categories"]] + ["Beyond the AQI scale"]
    colours = [c["colour"] for c in data["aqi_categories"]] + ["#7E0023"]
    percents = [dist["percent"].get(name, 0.0) for name in categories]
    short = [
        n.replace("Unhealthy for Sensitive Groups", "Sensitive groups").replace(
            "Beyond the AQI scale", "Beyond scale"
        )
        for n in categories
    ]

    fig, (left, right) = plt.subplots(1, 2, figsize=(13, 4.6), dpi=150)
    fig.patch.set_facecolor("white")

    width = 0.36
    positions = range(len(models))
    left.bar([p - width / 2 for p in positions], in_sample, width, label="In-sample $R^2$", color=SERIES)
    left.bar(
        [p + width / 2 for p in positions],
        cv_mean,
        width,
        yerr=cv_sd,
        capsize=4,
        label=f"Cross-validated $R^2$ ({repeated['repeats']} repeats)",
        color=SERIES_CV,
        error_kw={"ecolor": MUTED, "lw": 1},
    )
    # Full axis on purpose: zooming in would turn a small gap into a landslide.
    left.set_ylim(0, 1)
    left.set_xticks(list(positions))
    left.set_xticklabels(models)
    left.set_ylabel("$R^2$")
    left.set_title(
        "The best-fitting model is the wrong one\n"
        "in-sample $R^2$ rises with degree; cross-validated $R^2$ falls",
        fontsize=12, fontweight="600", color=INK, loc="left",
    )
    left.legend(frameon=False, fontsize=9, loc="center left", labelcolor=MUTED)
    left.grid(axis="y", color=GRID, linestyle="--", alpha=0.8)
    left.set_axisbelow(True)
    for spine in ("top", "right"):
        left.spines[spine].set_visible(False)
    for i, (a, b) in enumerate(zip(in_sample, cv_mean)):
        left.text(i - width / 2, a + 0.02, f"{a:.3f}", ha="center", fontsize=8, color=MUTED)
        left.text(i + width / 2, b + 0.06, f"{b:.3f}", ha="center", fontsize=8, color=MUTED)
        # On a truthful 0-1 axis the divergence is small, so state it rather
        # than zooming the axis in to manufacture a visible difference.
        left.text(
            i, 0.09, f"gap\n{a - b:.3f}",
            ha="center", va="center", fontsize=9, color="white", fontweight="600",
        )

    bars = right.barh(short, percents, color=colours, edgecolor=MUTED, linewidth=0.6)
    # The off-scale band carries no EPA colour, so it is hatched rather than
    # recoloured -- the maroon is already about as dark as a fill can go.
    bars[-1].set_hatch("////")
    right.invert_yaxis()
    right.set_xlabel("share of days (%)")
    right.set_title(
        f"Not one Good day in {dist['total_days']:,}",
        fontsize=12, fontweight="600", color=INK, loc="left",
    )
    right.grid(axis="x", color=GRID, linestyle="--", alpha=0.8)
    right.set_axisbelow(True)
    for spine in ("top", "right"):
        right.spines[spine].set_visible(False)
    for bar, value in zip(bars, percents):
        right.text(
            bar.get_width() + 0.6,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%",
            va="center", fontsize=8, color=MUTED,
        )
    right.set_xlim(0, max(percents) * 1.2)

    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight", facecolor="white")
    print(f"wrote {os.path.relpath(OUT, os.path.join(HERE, '..'))}")


if __name__ == "__main__":
    main()
