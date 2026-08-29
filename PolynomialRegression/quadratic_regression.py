import warnings

import numpy as np
from scipy.optimize import fsolve

from base_regression import PolynomialModel

class QuadraticRegression(PolynomialModel):
  def __init__(self):
    super().__init__()
    self.inverse_converged = None
    self.inverse_message = ""

  def fit(self, X, y):
    X_quad = np.hstack([np.ones((X.shape[0],1)), X, X**2])
    self.coefficients = np.linalg.inv(X_quad.T.dot(X_quad)).dot(X_quad.T).dot(y)

  def predict(self, X):
    self._check_fitted("predict")
    X_quad = np.hstack([np.ones((X.shape[0], 1)), X, X**2])
    return X_quad.dot(self.coefficients)

  def predict_inverse(self, target_pm25):
    self._check_fitted("predict_inverse")

    b0, b1, b2 = self.coefficients
    
    def equation(co):
        return b2 * co**2 + b1 * co + b0 - target_pm25
    
    with warnings.catch_warnings():
      warnings.filterwarnings("ignore", message="The iteration is not making good progress")
      co_solution, _info, ier, msg = fsolve(equation, x0=0, full_output=True)
    self.inverse_converged = (ier == 1)
    self.inverse_message = msg.strip()

    return co_solution[0]
  
