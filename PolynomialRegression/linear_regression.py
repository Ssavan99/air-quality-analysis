import numpy as np

from base_regression import PolynomialModel

class LinearRegression(PolynomialModel):
  def fit(self, X, y):
    X_linear = np.hstack([np.ones((X.shape[0],1)), X])
    self.coefficients = np.linalg.inv(X_linear.T.dot(X_linear)).dot(X_linear.T).dot(y)

  def predict(self, X):
    self._check_fitted("predict")
    X_linear = np.hstack([np.ones((X.shape[0], 1)), X])
    return X_linear.dot(self.coefficients)

  def predict_inverse(self, target_pm25):
    self._check_fitted("predict_inverse")
    b0, b1 = self.coefficients
    if b1 != 0:
      CO_safe = (target_pm25 - b0) / b1
      return CO_safe
    else:
      raise ValueError("Slope coefficient is zero, cannot calculate required CO value.")