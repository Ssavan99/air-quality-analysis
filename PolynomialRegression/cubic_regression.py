import numpy as np
import warnings
from scipy.optimize import fsolve

warnings.filterwarnings("ignore", message="The iteration is not making good progress")

class CubicRegression: 
  def __init__(self):
    self.coefficients = None

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

    def cubic_equation(CO):
      return self.coefficients[0] + self.coefficients[1] * CO + self.coefficients[2] * CO**2 + self.coefficients[3] * CO**3 - target_pm25

    CO_safe = fsolve(cubic_equation, x0=0) 

    return CO_safe[0]
  