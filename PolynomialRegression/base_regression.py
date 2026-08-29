import numpy as np


class PolynomialModel:
  """Shared fitted-state guard and R^2 scoring for the linear/quadratic/cubic models."""

  def __init__(self):
    self.coefficients = None

  def _check_fitted(self, method_name):
    if self.coefficients is None:
      raise RuntimeError(f"call fit() before {method_name}()")

  def r2_score(self, y, y_pred):
    ss_total = np.sum((y - np.mean(y)) ** 2)
    ss_residual = np.sum((y - y_pred) ** 2)
    return 1 - (ss_residual / ss_total)
