import warnings

import numpy as np
from scipy.optimize import fsolve

from base_regression import PolynomialModel

class CubicRegression(PolynomialModel):
  def __init__(self):
    super().__init__()
    self.inverse_converged = None
    self.inverse_message = ""

  def fit(self, X, y):
    X_cubic = np.hstack([np.ones((X.shape[0],1)), X, X**2, X**3])
    self.coefficients = np.linalg.inv(X_cubic.T.dot(X_cubic)).dot(X_cubic.T).dot(y)

  def predict(self, X):
    self._check_fitted("predict")
    X_cubic = np.hstack([np.ones((X.shape[0], 1)), X, X**2, X**3])
    return X_cubic.dot(self.coefficients)

  def predict_inverse(self, target_pm25):
    self._check_fitted("predict_inverse")
    """Solve the fitted cubic for the CO level giving target_pm25.

    The solver's diagnostics are kept on the instance rather than discarded.
    This root does not converge cleanly on this dataset and lands on a negative
    concentration, which is the finding rather than something to hide.
    """

    def cubic_equation(CO):
      return self.coefficients[0] + self.coefficients[1] * CO + self.coefficients[2] * CO**2 + self.coefficients[3] * CO**3 - target_pm25

    with warnings.catch_warnings():
      warnings.filterwarnings("ignore", message="The iteration is not making good progress")
      CO_safe, _info, ier, msg = fsolve(cubic_equation, x0=0, full_output=True)
    self.inverse_converged = (ier == 1)
    # scipy wraps this message across lines and the indentation differs
    # between releases, so collapse the whitespace rather than exporting the
    # library's formatting.
    self.inverse_message = " ".join(msg.split())

    return CO_safe[0]
