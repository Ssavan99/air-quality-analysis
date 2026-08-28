import numpy as np;

class LinearRegression: 
  def __init__(self):
    self.coefficients = None

  def fit(self, X, y): 
    X_linear = np.hstack([np.ones((X.shape[0],1)), X])
    self.coefficients = np.linalg.inv(X_linear.T.dot(X_linear)).dot(X_linear.T).dot(y)

  def predict(self, X):
    X_linear = np.hstack([np.ones((X.shape[0], 1)), X])
    return X_linear.dot(self.coefficients)
  
  def r2_score(self, y, y_pred): 
    ss_total = np.sum((y - np.mean(y))**2)
    ss_residual = np.sum((y - y_pred)**2)
    return 1- (ss_residual / ss_total)
  
  def predict_inverse(self, target_pm25):
    b0, b1 = self.coefficients 
    if b1 != 0:
      CO_safe = (target_pm25 - b0) / b1
      return CO_safe
    else:
      raise ValueError("Slope coefficient is zero, cannot calculate required CO value.")