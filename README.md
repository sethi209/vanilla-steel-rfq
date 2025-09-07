# Vanilla Steel RFQ Analysis Pipeline

This repository contains a reproducible workflow for **Scenario A — Supplier Data Cleaning** and **Scenario B — RFQ Similarity Analysis**, including optional bonus analyses (ablation, alternative similarity metrics, and clustering).  

It is designed to clean, enrich, and analyze steel RFQs, and produce a **top-3 similarity ranking** for each RFQ based on multiple feature types.

---

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/sethi209/vanilla-steel-rfq.git
cd vanilla-steel-rfq
```

2. **Create a Python virtual environment**

```python -m venv venv
# Activate environment
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

3. **Install dependencies**

```
pip install -r requirements.txt
```

---

## Scenario A — Supplier Data Cleaning

- **Script**: `scenario_a_run.py`
- **Purpose**: Clean and normalize supplier datasets, unify units and column names, handle missing values, and merge into a single inventory table.
- **Inputs**:
    - `supplier_data1.xlsx`
    - `supplier_data2.xlsx`
- **Outputs**:
    - `outputs/inventory_dataset.csv`
    - `outputs/inventory_dataset.xlsx`
- **Run**:
```
python scenario_a_run.py
```
- **Notes**:
    - Deduplicates based on key columns: grade, finish, thickness, width, article ID, description, and source.
    - Coating information is standardized as string for downstream analysis.

---

## Scenario B — RFQ Similarity

- **Script**: `rfq_final.py`, `run.py`
- **Purpose**: Enrich RFQs with reference grade properties, compute feature-based similarity, and generate top-3 similar RFQs per request.
- **Inputs**:
    - `rfq.csv`
    - `reference_properties.tsv` (grade-level properties)
- **Outputs**:
    - `outputs/rfq_enriched.csv` — RFQs enriched with numeric and categorical reference data.
    - `outputs/top3.csv` — Top-3 similar RFQs per RFQ, sorted by similarity score.
- **Run the pipeline**:
```
python run.py
```
- **Features considered**:
    - **Dimensions**: thickness, width, length, height, weight, inner/outer diameter (normalized overlap metric).
    - **Categorical**: coating, finish, form, surface type, surface protection (exact match).
    - **Grade Properties**: numeric midpoints of tensile strength, yield strength, elongation, hardness, etc.
- **Similarity aggregation**: Weighted combination (default: 0.4 dimensions, 0.3 categorical, 0.3 grade properties).

---

## Bonus Analysis

### 1. Ablation Analysis

- **Script**: `rfq_ablation.py`
- **Purpose**: ECompare similarity scores when dropping certain feature groups (dimensions-only vs grade-only) or adjusting feature weights.
- **Outputs**: CSV file named with the selected mode.
- **Run**:
```
python rfq_ablation.py
```

### 2. Alternative Similarity Metrics

- **Script**: `rfq_alternative.py`
- **Purpose**: Compute hybrid Cosine + Jaccard similarity, providing a faster, vectorized alternative to interval-based similarity.
- **Run**:
```
python rfq_alternative.py
```

### 3. RFQ Clustering

- **Script**: `rfq_clustering.py`
- **Purpose**: Group RFQs into clusters (families) based on numerical and categorical features. Prints cluster summary for interpretation.
- **Run**:
```
python rfq_clustering.py
```
- **Notes**:
    - Missing numeric data is filtered before clustering.
    - Cluster summary shows average dimensions, grades, coating, and form per cluster.

---

## Process Overview Document

- Refer to `process_documentation.md` for detailed explanations:
    - Data cleaning steps for Scenario A.
    - Enrichment and feature engineering for Scenario B.
    - Similarity calculation methodology and weighting.
    - Bonus analyses and interpretation of results.

---

