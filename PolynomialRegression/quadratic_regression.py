import numpy as np;
from scipy.optimize import fsolve

class QuadraticRegression: 
  def __init__(self):
    self.coefficients = None

  def fit(self, X, y): 
    X_quad = np.hstack([np.ones((X.shape[0],1)), X, X**2])
    self.coefficients = np.linalg.inv(X_quad.T.dot(X_quad)).dot(X_quad.T).dot(y)

  def predict(self, X):
    if self.coefficients is None:
      raise RuntimeError("call fit() before predict()")
    X_quad = np.hstack([np.ones((X.shape[0], 1)), X, X**2])
    return X_quad.dot(self.coefficients)
  
  def r2_score(self, y, y_pred): 
    ss_total = np.sum((y - np.mean(y))**2)
    ss_residual = np.sum((y - y_pred)**2)
    return 1 - (ss_residual / ss_total)
  
  def predict_inverse(self, target_pm25):
    if self.coefficients is None:
      raise RuntimeError("call fit() before predict_inverse()")
      
    b0, b1, b2 = self.coefficients  
    
    def equation(co):
        return b2 * co**2 + b1 * co + b0 - target_pm25
    
    co_solution = fsolve(equation, x0=0)
    
    return co_solution[0]
  
