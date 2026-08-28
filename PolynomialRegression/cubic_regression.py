import numpy as np
from scipy.optimize import fsolve

class CubicRegression: 
  def __init__(self):
    self.coefficients = None
    self.inverse_converged = None
    self.inverse_message = ""

  def fit(self, X, y): 
    X_cubic = np.hstack([np.ones((X.shape[0],1)), X, X**2, X**3])
    self.coefficients = np.linalg.inv(X_cubic.T.dot(X_cubic)).dot(X_cubic.T).dot(y)

  def predict(self, X):
    X_cubic = np.hstack([np.ones((X.shape[0], 1)), X, X**2, X**3])
    return X_cubic.dot(self.coefficients)
  
  def r2_score(self, y, y_pred): 
    ss_total = np.sum((y - np.mean(y))**2)
    ss_residual = np.sum((y - y_pred)**2)
    return 1 - (ss_residual / ss_total)
  
  def predict_inverse(self, target_pm25):
    """Solve the fitted cubic for the CO level giving target_pm25.

    The solver's diagnostics are kept on the instance rather than discarded.
    This root does not converge cleanly on this dataset and lands on a negative
    concentration, which is the finding rather than something to hide.
    """

    def cubic_equation(CO):
      return self.coefficients[0] + self.coefficients[1] * CO + self.coefficients[2] * CO**2 + self.coefficients[3] * CO**3 - target_pm25

    CO_safe, _info, ier, msg = fsolve(cubic_equation, x0=0, full_output=True)
    self.inverse_converged = (ier == 1)
    self.inverse_message = msg.strip()

    return CO_safe[0]
