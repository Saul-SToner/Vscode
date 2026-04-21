import numpy as np

def fit_ab(y_exp, y_model):
    """
    拟合 y_exp ≈ a * y_model + b
    返回 a, b, rmse, y_fit
    """
    y_exp = np.asarray(y_exp).ravel()
    y_model = np.asarray(y_model).ravel()

    X = np.column_stack([y_model, np.ones_like(y_model)])
    beta, *_ = np.linalg.lstsq(X, y_exp, rcond=None)
    a, b = beta

    y_fit = a * y_model + b
    rmse = np.sqrt(np.mean((y_exp - y_fit) ** 2))
    return a, b, rmse, y_fit

def normalized_rmse(y_exp, y_fit, eps=1e-12):
    y_exp = np.asarray(y_exp).ravel()
    y_fit = np.asarray(y_fit).ravel()

    scale = np.max(y_exp) - np.min(y_exp)
    scale = max(scale, eps)
    return np.sqrt(np.mean((y_exp - y_fit) ** 2)) / scale

def interp_to_exp(lambda_model, y_model, lambda_exp):
    return np.interp(lambda_exp, lambda_model, y_model)