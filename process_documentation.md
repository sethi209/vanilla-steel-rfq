# Process Documentation — Vanilla Steel RFQ Analysis

This document explains the full workflow and methodology for **Scenario A (Supplier Data Cleaning)** and **Scenario B (RFQ Similarity)**, including the bonus stretch goals. It describes how the data was processed, the reasoning behind each step, and how to interpret the outputs.

---

## Scenario A — Supplier Data Cleaning

### Goal
To clean and unify two supplier datasets (`supplier_data1.xlsx`, `supplier_data2.xlsx`) into a single standardized inventory table.

### Steps
1. **Column normalization**
   - Renamed inconsistent columns to standardized names (e.g., `Thickness (mm)` → `thickness_mm`).
   - Ensured consistent casing for grades, finishes, and coatings.

2. **Data type conversion**
   - Converted thickness, width, weight, and mechanical properties to floats.
   - Handled European-style decimals (`,` → `.`).
   - Empty or invalid entries were set to `NaN`.

3. **Supplier-specific handling**
   - Supplier 1: already structured (grade, finish, quality, thickness, etc.).
   - Supplier 2: parsed `Material` into **grade** and **coating** using regex.
   - Normalized `Reserved` column into booleans.

4. **Deduplication**
   - Dropped duplicates based on key attributes (`grade`, `finish`, `thickness_mm`, `width_mm`, `article_id`, `description`, `source`).

5. **Outputs**
   - `inventory_dataset.csv` and `inventory_dataset.xlsx` in the `outputs/` folder.

### Assumptions
- Missing numeric values are preserved as `NaN` (not imputed).
- Coating values not present were replaced with empty strings.
- Supplier 2’s `Material` field sometimes contains extra descriptors; only standardized **grade** and **coating** were extracted.

---

## Scenario B — RFQ Similarity

### Goal
To compute similarity scores between RFQs based on their requirements, enriched with grade-level reference properties.

### Inputs
- `rfq.csv` — RFQ requests.
- `reference_properties.tsv` — grade-level mechanical and chemical properties.

### Step 1: Enrichment
- **Grade normalization**: converted to uppercase, stripped whitespace.
- **Reference join**: merged RFQs with grade reference table on `Grade/Material`.
- **Numeric parsing**: properties like tensile/yield strength often appear as ranges (e.g., `400–550`). These were split into `min`, `max`, and `midpoint` values.
- **Dimensions**: ensured min/max values exist for thickness, width, length, height, weight, and diameters.

### Step 2: Feature Engineering
- **Dimensions (intervals)**  
  - Represented as `[min, max]` ranges.  
  - Similarity metric: *overlap ratio* (intersection ÷ union of ranges).  
- **Categorical features**  
  - `coating`, `finish`, `form`, `surface_type`, `surface_protection`.  
  - Similarity metric: exact match (1 if same, 0 otherwise).  
- **Grade properties**  
  - Numeric midpoints: tensile strength, yield strength, elongation, hardness, etc.  
  - Similarity metric: normalized difference (closer midpoints → higher similarity).

### Step 3: Similarity Calculation
- For each pair of RFQs, compute:
  - **Dimension similarity** = average overlap across all dimensions.  
  - **Categorical similarity** = average match score.  
  - **Grade similarity** = average similarity of numeric midpoints.  
- Aggregate with weighted average:  
``` 
total_similarity = 0.4 * dimension + 0.3 * categorical + 0.3 * grade
```


### Step 4: Top-3 Ranking
- For each RFQ, exclude self-matches.  
- Rank by similarity score.  
- Save **top-3 matches** in `outputs/top3.csv`.

---

## Bonus Analyses

### 1. Ablation Analysis
- Purpose: evaluate the effect of feature groups by computing similarity with:
- **Dimensions only**  
- **Grade properties only**  
- **Categorical only**  
- Method: re-ran similarity pipeline with adjusted weights.
- Output: CSVs named according to mode (e.g., `top3_dimensions.csv`).

### 2. Alternative Metrics (Cosine + Jaccard)
- Vectorized features into numeric (standardized dimensions/grade midpoints) and binary (categorical matches).
- Applied:
- **Cosine similarity** for numeric features.  
- **Jaccard similarity** for categorical features.  
- Hybrid score = weighted average of both.
- Advantage: much faster, more scalable for large datasets.

### 3. RFQ Clustering
- Used **KMeans** to group RFQs into families based on enriched features.
- Preprocessing:
- Dropped rows with too many missing values.
- Standardized numeric features.
- Output:
- Cluster assignments per RFQ.
- Printed cluster summaries with average dimensions, coatings, and forms.
- Interpretation: clusters represent “families” of RFQs with similar requirements (e.g., structural coils, coated sheets, tubes).

---

## Interpretation of Outputs

- **inventory_dataset.csv**: unified supplier inventory for Scenario A.  
- **rfq_enriched.csv**: enriched RFQs with reference properties.  
- **top3.csv**: top-3 similar RFQs for each RFQ with similarity scores.  
- **Bonus scripts**: additional perspectives for analyzing robustness and grouping.  

---

## Key Takeaways

- RFQ similarity is **multi-faceted**: dimensions, categories, and grade-level mechanics all matter.  
- **Ablation** shows the importance of each feature group.  
- **Alternative metrics** (cosine+jaccard) provide scalable similarity calculation.  
- **Clustering** offers insight into natural groupings of RFQs, supporting business use cases like family-based pricing or sourcing.  

---
