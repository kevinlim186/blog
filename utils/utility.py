from numba import jit, prange
import numpy as np
from scipy.stats import linregress
from dash import dcc

@jit(nopython=True, cache=True)
def ols_regression(y, X):
    n, k = X.shape

    # Compute OLS coefficients
    beta = np.linalg.inv(X.T @ X) @ X.T @ y

    # Compute residuals
    e = y - X @ beta

    # Residual sum of squares
    RSS = np.sum(e**2)

    # Degrees of freedom
    dof = n - k

    # Residual standard error
    RSE = np.sqrt(RSS / dof)

    # Covariance matrix of beta
    cov_beta = np.linalg.inv(X.T @ X) * RSE**2

    # Standard errors of coefficients
    se_beta = np.sqrt(np.diag(cov_beta))

    # t-values
    t_values = beta / se_beta

    return beta, se_beta, t_values

@jit(nopython=True, cache=True)
def tValLinR(close):
    n = close.shape[0]
    X = np.column_stack((np.ones(n), np.arange(n)))
    y = close.astype(np.float64)  # Convert to native type for Numba compatibility

    # Perform OLS regression
    beta, se_beta, t_values = ols_regression(y, X)
    slope = beta[1]
    return t_values[1], slope  # Return t-value for the second coefficient (excluding intercept)


@jit(nopython=True, cache=True)
def getBinsFromTrend(close,span,threshold,slope_threshold):
    '''
    Derive labels from the sign of t-value of linear trend
    Output includes:
    - t1: End time for the identified trend
    - tVal: t-value associated with the estimated trend coefficient - bin: Sign of the trend
    '''
    max_length = len(close)
    hrzns=prange(*span)
    out= np.zeros(max_length)
    t_values= np.zeros(max_length)
    slopes = np.zeros(max_length)
    for idx in prange(max_length):
        if idx+max(hrzns)>max_length:continue
        max_tvalue = -np.inf
        selected_tvalue=0
        best_t_val = 0.0
        best_slope = 0.0
        for hrzn in hrzns: 
            end_idx = hrzn+idx
            t_value, slope =tValLinR(close[idx:end_idx])
            if np.isinf(t_value) or np.isnan(t_value):
                t_value=0
                slope=0
            abs_tvalue =  abs(t_value)
            max_tvalue = max(abs_tvalue, max_tvalue)
            if max_tvalue ==abs_tvalue and abs_tvalue>=threshold and slope_threshold <=abs(slope):
                selected_tvalue=end_idx*np.sign(t_value)
                best_t_val = t_value
                best_slope = slope

        out[idx] = selected_tvalue
        t_values[idx] = best_t_val
        slopes[idx] =best_slope
    return out, t_values, slopes

def find_graph(component):
    if isinstance(component, dcc.Graph):
        return component.figure
    if hasattr(component, "children"):
        children = component.children
        if isinstance(children, list):
            for child in children:
                result = find_graph(child)
                if result:
                    return result
        else:
            return find_graph(children)
    return None