import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from linear_regression import LinearRegression
from quadratic_regression import QuadraticRegression
from cubic_regression import CubicRegression

data = pd.read_csv('../Data/biweekly_air_quality_data.csv')

X = data['co'].values.reshape(-1, 1)
y = data['pm2_5'].values

SAFE_PM25_THRESHOLD = 15

Linear = LinearRegression()
Quadratic = QuadraticRegression()
Cubic = CubicRegression()

Linear.fit(X, y)
Quadratic.fit(X, y)
Cubic.fit (X,y)

co_safe_cubic = Cubic.predict_inverse(SAFE_PM25_THRESHOLD)
co_safe_linear = Linear.predict_inverse(SAFE_PM25_THRESHOLD)
co_safe_quadratic = Quadratic.predict_inverse(SAFE_PM25_THRESHOLD)

prediction_Linear = Linear.predict(X)
prediction_Quadratic = Quadratic.predict(X)
prediction_Cubic = Cubic.predict(X)

r2_Linear = Linear.r2_score(y, prediction_Linear)
r2_Quadratic = Quadratic.r2_score(y, prediction_Quadratic)
r2_Cubic = Cubic.r2_score(y, prediction_Cubic)

sort = np.argsort(X.flatten())
X_sorted = X[sort]
prediction_Linear_Sorted = Linear.predict(X_sorted)
prediction_Quadratic_Sorted = Quadratic.predict(X_sorted)
prediction_Cubic_Sorted = Cubic.predict(X_sorted)

plt.scatter(data['co'], data['pm2_5'], color='blue', label='Actual Data')

plt.plot(X_sorted, prediction_Linear_Sorted, color='red', linewidth=2, linestyle="--", label=f'Linear Regression (R²: {r2_Linear:.6f})')
plt.plot(X_sorted, prediction_Quadratic_Sorted, color='green', linewidth=2, linestyle="-.", label=f'Quadratic Regression (R²: {r2_Quadratic:.6f})')
plt.plot(X_sorted, prediction_Cubic_Sorted, color='purple', linewidth=1.5, linestyle="-", label=f'Cubic Regression (R²: {r2_Cubic:.6f})')

# CO level each model says would bring PM2.5 down to the safe threshold.
# A negative concentration is not physically meaningful, so label it as such
# instead of printing it as if it were a result.
def label(value):
    return f"{value:.2f} µg/m³" + ("  (invalid)" if value < 0 else "")

plt.text(0.95, 0.12, f"Linear: {label(co_safe_linear)}", ha='right', va='bottom', transform=plt.gca().transAxes, fontsize=10, color="red")
plt.text(0.95, 0.07, f"Quadratic: {label(co_safe_quadratic)}", ha='right', va='bottom', transform=plt.gca().transAxes, fontsize=10, color="green")
plt.text(0.95, 0.02, f"Cubic: {label(co_safe_cubic)}", ha='right', va='bottom', transform=plt.gca().transAxes, fontsize=10, color="purple")

print(f"CO needed for PM2.5 = {SAFE_PM25_THRESHOLD} µg/m³")
print(f"  Linear:    {label(co_safe_linear)}")
print(f"  Quadratic: {label(co_safe_quadratic)}")
print(f"  Cubic:     {label(co_safe_cubic)}")
if not Cubic.inverse_converged:
    print(f"  cubic root solver did not converge: {Cubic.inverse_message}")

plt.xlabel('Carbon Monoxide (µg/m³)')
plt.ylabel('PM2.5 (µg/m³)')
plt.title('Concentration of Carbon Monoxide vs PM2.5')
plt.legend()
plt.show()
