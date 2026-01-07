# 📊 ESG Validation Engine  
**Flag → Explain → Decide**

A rule-based environmental data validation engine that transforms messy asset-level sustainability data into decision-ready validation outputs.

Instead of only flagging outliers, the tool explains *why* values are flagged and clearly indicates what action is required (accept, follow-up, or correction).

Built as a lightweight internal-style tool using **Python and Streamlit**.

---

## 🔍 Problem
ESG data is often:
- incomplete or inconsistent  
- reported with unit or boundary issues  
- manually validated using ad-hoc checks  

This makes validation:
- slow  
- hard to scale  
- difficult to explain to stakeholders  

---

## ✅ Solution
This project implements a **rule-based ESG validation engine** that:

- validates asset-level energy, GHG, and water data  
- applies statistical and logical checks  
- generates **human-readable explanations**  
- outputs clear **follow-up decisions**  

The result is a transparent, reproducible validation workflow suitable for ESG analytics, assurance, and sustainability platforms.

---

## ⚙️ What the engine does

### 1. Compute intensities
- Energy intensity (kWh / m²)  
- GHG intensity (kgCO₂e / m²)  
- Water intensity (m³ / m²)  

---

### 2. Run validation rules

**Data quality**
- missing values  
- negative values  
- invalid floor area  

**Logical consistency**
- GHG > 0 while energy = 0  
- energy > 0 while GHG = 0  

**Statistical outliers**
- IQR-based intensity outlier detection (year-level peer comparison)  

**Temporal logic**
- ≥100% year-over-year intensity changes  
- occupancy drop with rising intensity (if available)  

---

### 3. Flag → Explain → Decide
Each asset–metric–year receives:
- **Status**: `ACCEPTED`, `FLAGGED`, `INVALID`  
- **Reason code** (machine-readable)  
- **Explanation** (human-readable)  
- **Decision**:
  - `ACCEPT`  
  - `NEEDS_EXPLANATION`  
  - `NEEDS_CORRECTION`  

---

## 🖥️ Streamlit dashboard
The Streamlit UI provides:
- portfolio-level overview of validation outcomes  
- top reason codes driving flags  
- asset-level drill-down with trends and explanations  
- exportable validation results  

**Tabs**
- Overview  
- Asset drill-down  
- Validation table  

---

## 🧪 Sample data
A synthetic ESG dataset is generated to demonstrate:
- realistic reporting patterns  
- intentional data quality issues (spikes, missing values, logic errors)  

Generate sample data:
```bash
python src/generate_sample_data.py
```
---

## 🛠️ Tech stack

- Python
- Pandas / NumPy
- Rule-based validation logic
- Streamlit (UI)
- Altair (charts)

---
## ▶️ How to run locally
```bash
# create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # macOS / Linux

# install dependencies
pip install -r requirements.txt

# generate sample data
python src/generate_sample_data.py

# run app
python -m streamlit run app.py
```
---
## 📁 Project structure
``` bash
esg-validation-engine/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── sample_raw.csv
├── src/
│   ├── validation.py
│   ├── rules.py
│   └── generate_sample_data.py
└── outputs/
```
---
## 🚀 Next improvements

- peer-group outlier detection (by country or asset type)
- confidence scoring for validation flags
- follow-up queue for flagged metrics
- API wrapper for integration with web or product UIs (if needed)
---

## 👤 Author

Sudarshan Ethirajah
Focus: ESG data quality, validation automation, and sustainability analytics.

