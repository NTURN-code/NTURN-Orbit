"""Transparent statistical anomaly detection helpers (not a trained ML model)."""
import numpy as np
import pandas as pd


def find_outliers(df, cols, z=3.0):
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    if not cols:
        raise ValueError("Select at least one numeric column")
    if z <= 0:
        raise ValueError("z must be greater than zero")
    sub = df[cols].apply(pd.to_numeric, errors="coerce")
    std = sub.std(ddof=0).replace(0, np.nan)
    score = ((sub - sub.mean()) / std).abs().max(axis=1).fillna(0)
    out = df.copy()
    out["anomaly_score"] = score.round(2)
    out["is_anomaly"] = score > float(z)
    return out


def rolling_anomaly(series, window=20, z=3.0):
    """Flag deviations from prior rolling behaviour; first points are unscored."""
    if window < 2:
        raise ValueError("window must be at least 2")
    if z <= 0:
        raise ValueError("z must be greater than zero")
    s = pd.to_numeric(series, errors="coerce")
    mean = s.rolling(window, min_periods=max(2, min(5, window))).mean().shift(1)
    std = s.rolling(window, min_periods=max(2, min(5, window))).std().shift(1).replace(0, np.nan)
    delta = s - mean
    zs = delta / std
    # A constant recent baseline has zero standard deviation. Any non-zero
    # deviation from that baseline is therefore flagged rather than discarded.
    zero_std_jump = std.isna() & mean.notna() & delta.notna() & (delta != 0)
    zs = zs.mask(zero_std_jump, np.sign(delta) * np.inf)
    return (zs.abs() > z).fillna(False), zs
