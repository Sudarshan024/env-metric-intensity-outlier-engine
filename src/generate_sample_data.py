import pandas as pd
import numpy as np

np.random.seed(42)

assets = [
    ("A001", "Canal View Offices", "NL", "Office", 12000),
    ("A002", "Riverside Apartments", "NL", "Residential", 8500),
    ("A003", "Desert Business Bay", "UAE", "Office", 14000),
    ("A004", "Marina Residences", "UAE", "Residential", 9000),
    ("A005", "Logistics Hub North", "NL", "Industrial", 20000),
]

years = [2022, 2023, 2024]

rows = []
for asset_id, name, country, asset_type, area in assets:
    base_occ = np.clip(np.random.normal(0.85, 0.08), 0.4, 1.0)

    # baseline intensities (roughly realistic-ish)
    if asset_type == "Office":
        energy_int = np.random.uniform(140, 260)  # kWh/m2
        water_int = np.random.uniform(0.30, 0.70) # m3/m2
    elif asset_type == "Residential":
        energy_int = np.random.uniform(80, 160)
        water_int = np.random.uniform(0.25, 0.60)
    else:
        energy_int = np.random.uniform(60, 180)
        water_int = np.random.uniform(0.10, 0.35)

    for y in years:
        occ = np.clip(base_occ + np.random.normal(0, 0.04), 0.3, 1.0)

        # Year drift
        drift = 1 + np.random.normal(0.02, 0.05)

        energy_kwh = energy_int * area * drift
        water_m3 = water_int * area * drift

        # Simple emissions factor assumption
        ghg_tco2e = (energy_kwh * np.random.uniform(0.00012, 0.00022))

        rows.append({
            "asset_id": asset_id,
            "asset_name": name,
            "year": y,
            "country": country,
            "asset_type": asset_type,
            "floor_area_m2": float(area),
            "occupancy_rate": float(occ),
            "energy_kwh": float(round(energy_kwh, 2)),
            "ghg_tco2e": float(round(ghg_tco2e, 4)),
            "water_m3": float(round(water_m3, 2)),
        })

df = pd.DataFrame(rows)

# Inject some intentional “bad data” to show flags:
df.loc[(df["asset_id"] == "A003") & (df["year"] == 2024), "energy_kwh"] *= 3.2   # spike
df.loc[(df["asset_id"] == "A004") & (df["year"] == 2023), "ghg_tco2e"] = 0       # logic issue
df.loc[(df["asset_id"] == "A002") & (df["year"] == 2022), "water_m3"] = np.nan   # missing

df.to_csv("data/sample_raw.csv", index=False)
print("Created data/sample_raw.csv with sample ESG data.")
