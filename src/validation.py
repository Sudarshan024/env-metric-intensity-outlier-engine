import pandas as pd
import numpy as np
from .rules import iqr_bounds, yoy_change, safe_div

METRICS = {
    "energy_kwh": {"unit": "kWh", "intensity_name": "energy_kwh_per_m2"},
    "ghg_tco2e": {"unit": "tCO2e", "intensity_name": "ghg_kgco2e_per_m2"},
    "water_m3": {"unit": "m3", "intensity_name": "water_m3_per_m2"},
}

def compute_intensities(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # energy intensity
    df["energy_kwh_per_m2"] = df.apply(lambda r: safe_div(r["energy_kwh"], r["floor_area_m2"]), axis=1)

    # ghg intensity in kgCO2e/m2 for readability
    df["ghg_kgco2e_per_m2"] = df.apply(lambda r: safe_div(r["ghg_tco2e"] * 1000.0, r["floor_area_m2"]), axis=1)

    # water intensity
    df["water_m3_per_m2"] = df.apply(lambda r: safe_div(r["water_m3"], r["floor_area_m2"]), axis=1)

    return df

def base_checks(row: pd.Series):
    """Return (status, reason_code, explanation) or (None, None, None) if OK."""
    # Completeness / schema-like checks
    required = ["asset_id", "year", "floor_area_m2", "energy_kwh", "ghg_tco2e", "water_m3"]
    missing = [c for c in required if c not in row.index or pd.isna(row[c])]
    if missing:
        return ("INVALID", "DQ_MISSING_FIELDS", f"Missing required fields: {', '.join(missing)}")

    # Non-negative checks
    for c in ["floor_area_m2", "energy_kwh", "ghg_tco2e", "water_m3"]:
        if not pd.isna(row[c]) and row[c] < 0:
            return ("INVALID", "DQ_NEGATIVE_VALUE", f"{c} is negative ({row[c]}).")

    # Logical checks
    if row["energy_kwh"] == 0 and row["ghg_tco2e"] > 0:
        return ("FLAGGED", "LOGIC_GHG_WITH_ZERO_ENERGY", "GHG > 0 while energy is 0; check reporting boundary or unit issues.")
    if row["energy_kwh"] > 0 and row["ghg_tco2e"] == 0:
        return ("FLAGGED", "LOGIC_ZERO_GHG_WITH_ENERGY", "Energy > 0 while GHG is 0; check emission factors / scope coverage.")
    if row["floor_area_m2"] <= 0:
        return ("INVALID", "DQ_INVALID_FLOOR_AREA", f"floor_area_m2 must be > 0 (found {row['floor_area_m2']}).")

    return (None, None, None)

def run_validation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produces a row per asset-year-metric with:
    - value, intensity, status, reason_code, explanation, decision
    """
    df = df.copy()
    df = compute_intensities(df)

    # sort for YoY checks
    df = df.sort_values(["asset_id", "year"]).reset_index(drop=True)

    results = []

    # Precompute IQR bounds per year & metric intensity (portfolio-level peer comparison)
    bounds = {}
    for metric, meta in METRICS.items():
        inten = meta["intensity_name"]
        bounds[inten] = {}
        for yr, grp in df.groupby("year"):
            lo, hi = iqr_bounds(grp[inten])
            bounds[inten][yr] = (lo, hi)

    # Iterate rows and create metric-level validation records
    for idx, row in df.iterrows():
        base_status, base_code, base_expl = base_checks(row)

        # fetch prev year row for YoY (same asset)
        prev_row = None
        if idx > 0 and df.loc[idx-1, "asset_id"] == row["asset_id"]:
            prev_row = df.loc[idx-1]

        for metric, meta in METRICS.items():
            inten_col = meta["intensity_name"]

            value = row.get(metric, np.nan)
            intensity = row.get(inten_col, np.nan)

            status = "ACCEPTED"
            reason_code = ""
            explanation = ""

            # Apply base checks first (can override)
            if base_status is not None:
                status = base_status
                reason_code = base_code
                explanation = base_expl

            # IQR intensity outlier check
            lo, hi = bounds[inten_col].get(row["year"], (np.nan, np.nan))
            if status != "INVALID" and not pd.isna(intensity) and not pd.isna(lo) and not pd.isna(hi):
                if intensity < lo or intensity > hi:
                    status = "FLAGGED"
                    reason_code = f"OUTLIER_IQR_{inten_col.upper()}"
                    explanation = (
                        f"Intensity {inten_col}={intensity:.4f} outside IQR bounds "
                        f"[{lo:.4f}, {hi:.4f}] for year {int(row['year'])}."
                    )

            # YoY check (only if we have prev row)
            if status != "INVALID" and prev_row is not None:
                prev_intensity = prev_row.get(inten_col, np.nan)
                change = yoy_change(intensity, prev_intensity)
                if not pd.isna(change) and abs(change) >= 1.0:  # >= 100% change
                    status = "FLAGGED"
                    reason_code = f"TREND_YOY_SPIKE_{inten_col.upper()}"
                    explanation = (
                        f"YoY change in {inten_col} is {change*100:.1f}% "
                        f"(prev={prev_intensity:.4f}, curr={intensity:.4f})."
                    )

            # Optional occupancy logic (if column exists)
            if status != "INVALID" and "occupancy_rate" in row.index and prev_row is not None:
                occ_curr = row.get("occupancy_rate", np.nan)
                occ_prev = prev_row.get("occupancy_rate", np.nan)
                if not pd.isna(occ_curr) and not pd.isna(occ_prev) and not pd.isna(intensity) and not pd.isna(prev_row.get(inten_col, np.nan)):
                    # If occupancy drops a lot but intensity jumps, flag
                    occ_drop = yoy_change(occ_curr, occ_prev)
                    inten_change = yoy_change(intensity, prev_row.get(inten_col, np.nan))
                    if not pd.isna(occ_drop) and not pd.isna(inten_change):
                        if occ_drop <= -0.2 and inten_change >= 0.5:
                            status = "FLAGGED"
                            reason_code = f"LOGIC_OCCUPANCY_INTENSITY_{inten_col.upper()}"
                            explanation = (
                                f"Occupancy dropped {occ_drop*100:.1f}% while {inten_col} increased {inten_change*100:.1f}%."
                            )

            # Decision mapping
            if status == "ACCEPTED":
                decision = "ACCEPT"
            elif status == "FLAGGED":
                decision = "NEEDS_EXPLANATION"
            else:
                decision = "NEEDS_CORRECTION"

            results.append({
                "asset_id": row["asset_id"],
                "asset_name": row.get("asset_name", ""),
                "year": int(row["year"]),
                "metric": metric,
                "value": value,
                "intensity": intensity,
                "status": status,
                "reason_code": reason_code,
                "explanation": explanation,
                "decision": decision,
                "country": row.get("country", ""),
                "asset_type": row.get("asset_type", ""),
            })

    return pd.DataFrame(results)
