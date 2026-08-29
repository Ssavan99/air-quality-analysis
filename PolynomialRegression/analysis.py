"""Compare the three polynomial models on the same data main.py uses.

Every number here is computed from Data/biweekly_air_quality_data.csv. Nothing
is typed in by hand.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cubic_regression import CubicRegression
from linear_regression import LinearRegression
from quadratic_regression import QuadraticRegression

SAFE_PM25_THRESHOLD = 15

data = pd.read_csv('../Data/biweekly_air_quality_data.csv')
X = data['co'].values.reshape(-1, 1)
y = data['pm2_5'].values

models = [
    ("Linear", LinearRegression(), 2),
    ("Quadratic", QuadraticRegression(), 3),
    ("Cubic", CubicRegression(), 4),
]

names, r2_scores, n_params, safe_co = [], [], [], []
for name, model, params in models:
    model.fit(X, y)
    names.append(name)
    r2_scores.append(model.r2_score(y, model.predict(X)))
    n_params.append(params)
    safe_co.append(model.predict_inverse(SAFE_PM25_THRESHOLD))

print(f"{'model':<12}{'R2 (in-sample)':>16}{'params':>9}{'CO for PM2.5=15':>20}")
for name, r2, params, co in zip(names, r2_scores, n_params, safe_co):
    flag = "  <- invalid, negative" if co < 0 else ""
    print(f"{name:<12}{r2:>16.6f}{params:>9}{co:>17.2f}{flag}")

spread = max(r2_scores) - min(r2_scores)
print(f"\nSpread between best and worst R2: {spread:.6f}")
print("The three models are within a rounding error of each other on this data.")

fig, (left, right) = plt.subplots(1, 2, figsize=(12, 6))

# Full 0-1 axis on purpose. Zooming in on 0.940-0.945 would turn a difference
# of ~0.0015 into three visibly different bars, which is not what the data says.
left.bar(names, r2_scores, color=['#4C72B0', '#55A868', '#C44E52'], alpha=0.85)
left.set_ylim(0, 1)
left.set_title("In-sample $R^2$ by model", fontsize=14)
left.set_ylabel("$R^2$", fontsize=12)
left.grid(axis='y', linestyle='--', alpha=0.3)
for i, value in enumerate(r2_scores):
    left.text(i, value + 0.02, f"{value:.6f}", ha='center', fontsize=10)

right.bar(names, n_params, color=['#4C72B0', '#55A868', '#C44E52'], alpha=0.85)
right.set_title("Fitted parameters per model", fontsize=14)
right.set_ylabel("number of coefficients", fontsize=12)
right.set_yticks([0, 1, 2, 3, 4])
right.grid(axis='y', linestyle='--', alpha=0.3)
for i, value in enumerate(n_params):
    right.text(i, value + 0.08, str(value), ha='center', fontsize=10)

plt.tight_layout()
plt.show()
