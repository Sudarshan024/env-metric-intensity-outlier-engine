import numpy as np
import pandas as pd

def iqr_bounds(series: pd.Series, k: float = 1.5):
    """
    Returns (lower, upper) bounds based on IQR.
    If not enough non-null points, returns (nan, nan).
    """
    s = series.dropna().astype(float)
    if len(s) < 8:
        return (np.nan, np.nan)

    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    return (lower, upper)

def yoy_change(curr: float, prev: float):
    """
    YoY % change as a fraction (e.g., 0.25 = +25%).
    Returns nan if prev is 0 or missing.
    """
    if pd.isna(curr) or pd.isna(prev) or prev == 0:
        return np.nan
    return (curr - prev) / abs(prev)

def safe_div(n, d):
    """
    Safe division that returns nan if denominator is 0 or missing.
    """
    if pd.isna(n) or pd.isna(d) or d == 0:
        return np.nan
    return n / d
