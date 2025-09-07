import pandas as pd
import numpy as np
import re

# ---------- helpers ----------
def parse_range(value):
    """Parse a string range into min and max numeric values."""
    if pd.isna(value):
        return None, None
    value = re.sub(r'[^\d\.\-–]', '', str(value))
    if '-' in value or '–' in value:
        parts = re.split(r'[-–]', value)
        if len(parts) == 2:
            try:
                return float(parts[0].strip()), float(parts[1].strip())
            except ValueError:
                return None, None
    try:
        f = float(value)
        return f, f
    except ValueError:
        return None, None

def midpoint(min_val, max_val):
    """Return numeric midpoint of min/max, handle NaN."""
    if pd.isna(min_val) and pd.isna(max_val):
        return None
    if pd.isna(min_val):
        return max_val
    if pd.isna(max_val):
        return min_val
    return (min_val + max_val) / 2

def interval_overlap(min1, max1, min2, max2):
    """Normalized overlap ratio between two intervals."""
    if pd.isna(min1) or pd.isna(max1) or pd.isna(min2) or pd.isna(max2):
        return 0
    overlap = max(0, min(max1, max2) - max(min1, min2))
    total = max(max1, max2) - min(min1, min2)
    return overlap / total if total > 0 else 0

# ---------- enrichment ----------
def enrich_rfq(rfq_path, reference_path):
    """Join RFQs with grade reference and parse numeric ranges."""
    rfq = pd.read_csv(rfq_path)
    reference = pd.read_csv(reference_path, sep='\t')

    # Normalize grades
    rfq['grade'] = rfq['grade'].str.upper().str.strip()
    reference['Grade/Material'] = reference['Grade/Material'].str.upper().str.strip()

    # Merge
    rfq_enriched = rfq.merge(reference, how='left', left_on='grade', right_on='Grade/Material')

    # Numeric RFQ ranges: thickness, width, length, height, weight, inner/outer diameters
    dim_cols = [
        'thickness', 'width', 'length', 'height', 'weight', 'inner_diameter', 'outer_diameter'
    ]
    for dim in dim_cols:
        min_col = f"{dim}_min"
        max_col = f"{dim}_max"
        if min_col in rfq_enriched.columns and max_col in rfq_enriched.columns:
            # Already numeric
            continue
        rfq_enriched[min_col] = rfq_enriched.get(min_col, np.nan)
        rfq_enriched[max_col] = rfq_enriched.get(max_col, np.nan)

    # Grade numeric properties
    grade_numeric_cols = [
        ('Tensile strength (Rm)', 'tensile_mid'),
        ('Yield strength (Re or Rp0.2)', 'yield_mid'),
        ('Elongation (A%)', 'elongation_mid'),
        ('Reduction of area (Z%)', 'reduction_mid'),
        ('Hardness (HB, HV, HRC)', 'hardness_mid')
    ]
    for col, mid_col in grade_numeric_cols:
        if col in rfq_enriched.columns:
            rfq_enriched[[f"{col}_min", f"{col}_max"]] = rfq_enriched[col].apply(lambda x: pd.Series(parse_range(x)))
            rfq_enriched[mid_col] = rfq_enriched.apply(lambda row: midpoint(row[f"{col}_min"], row[f"{col}_max"]), axis=1)
        else:
            rfq_enriched[mid_col] = np.nan

    return rfq_enriched

# ---------- similarity ----------
def compute_top3_similarity(rfq_enriched):
    """Compute top-3 similar RFQs for each RFQ."""
    rfq_ids = rfq_enriched['id'].tolist()
    results = []

    for i, id1 in enumerate(rfq_ids):
        row1 = rfq_enriched.iloc[i]
        similarities = []

        for j, id2 in enumerate(rfq_ids):
            if id1 == id2:
                continue
            row2 = rfq_enriched.iloc[j]

            # Dimensions overlap: thickness, width, length, height, weight, inner/outer diameter
            dim_sims = []
            for dim in ['thickness', 'width', 'length', 'height', 'weight', 'inner_diameter', 'outer_diameter']:
                dim_sims.append(interval_overlap(
                    row1.get(f"{dim}_min"), row1.get(f"{dim}_max"),
                    row2.get(f"{dim}_min"), row2.get(f"{dim}_max")
                ))
            dim_sim = np.nanmean(dim_sims)

            # Categorical: coating, finish, form, surface_type, surface_protection
            cat_sims = []
            for col in ['coating', 'finish', 'form', 'surface_type', 'surface_protection']:
                cat_sims.append(int(row1.get(col) == row2.get(col)))
            cat_sim = np.mean(cat_sims)

            # Numeric grade midpoints
            grade_mid_cols = ['tensile_mid','yield_mid','elongation_mid','reduction_mid','hardness_mid']
            grade_sims = []
            for col in grade_mid_cols:
                v1, v2 = row1.get(col), row2.get(col)
                if pd.notna(v1) and pd.notna(v2) and max(v1,v2) > 0:
                    grade_sims.append(1 - abs(v1-v2)/max(v1,v2))
                else:
                    grade_sims.append(0)
            grade_sim = np.mean(grade_sims)

            # Weighted total similarity
            total_sim = 0.4*dim_sim + 0.3*cat_sim + 0.3*grade_sim
            similarities.append((id2, total_sim))

        # Top 3 matches
        similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:3]
        for match_id, score in similarities:
            results.append({'rfq_id': id1, 'match_id': match_id, 'similarity_score': score})

    return pd.DataFrame(results)

# ---------- run ----------
if __name__ == "__main__":
    rfq_enriched = enrich_rfq("data/rfq.csv", "data/reference_properties.tsv")
    top3 = compute_top3_similarity(rfq_enriched)
    top3.to_csv("outputs/rfq_top3.csv", index=False)
    print("[OK] Top3 similarity saved to outputs/rfq_top3.csv")
