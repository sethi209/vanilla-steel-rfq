# rfq_ablation.py
import pandas as pd
import numpy as np
import os

# ---------- helpers ----------
def interval_overlap(min1, max1, min2, max2):
    if pd.isna(min1) or pd.isna(max1) or pd.isna(min2) or pd.isna(max2):
        return 0
    overlap = max(0, min(max1, max2) - max(min1, min2))
    total = max(max1, max2) - min(min1, min2)
    return overlap / total if total > 0 else 0

# ---------- ablation similarity ----------
def ablation_similarity(rfq_enriched, mode="all", weights=None):
    rfq_ids = rfq_enriched['id'].tolist()
    results = []

    for i, id1 in enumerate(rfq_ids):
        row1 = rfq_enriched.iloc[i]
        similarities = []

        for j, id2 in enumerate(rfq_ids):
            if id1 == id2:
                continue
            row2 = rfq_enriched.iloc[j]

            # --- dimension similarity ---
            dim_sims = [
                interval_overlap(
                    row1.get(f"{dim}_min"), row1.get(f"{dim}_max"),
                    row2.get(f"{dim}_min"), row2.get(f"{dim}_max")
                )
                for dim in ['thickness','width','length','height','weight','inner_diameter','outer_diameter']
            ]
            dim_sim = np.nanmean(dim_sims)

            # --- categorical similarity ---
            cat_sims = [
                int(row1.get(col) == row2.get(col))
                for col in ['coating','finish','form','surface_type','surface_protection']
            ]
            cat_sim = np.mean(cat_sims)

            # --- grade similarity ---
            grade_mid_cols = ['tensile_mid','yield_mid','elongation_mid','reduction_mid','hardness_mid']
            grade_sims = []
            for col in grade_mid_cols:
                v1, v2 = row1.get(col), row2.get(col)
                if pd.notna(v1) and pd.notna(v2) and max(v1,v2) > 0:
                    grade_sims.append(1 - abs(v1-v2)/max(v1,v2))
                else:
                    grade_sims.append(0)
            grade_sim = np.mean(grade_sims)

            # --- total similarity based on mode ---
            if mode == "dimensions":
                total_sim = dim_sim
            elif mode == "grade":
                total_sim = grade_sim
            elif mode == "categorical":
                total_sim = cat_sim
            else:  # weighted
                w = weights if weights else {"dim":0.4,"cat":0.3,"grade":0.3}
                total_sim = w["dim"]*dim_sim + w["cat"]*cat_sim + w["grade"]*grade_sim

            similarities.append((id2, total_sim))

        # keep top-3
        similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:3]
        for match_id, score in similarities:
            results.append({"rfq_id": id1, "match_id": match_id, "similarity_score": score})

    return pd.DataFrame(results)

# ---------- main ----------
if __name__ == "__main__":
    input_path = "outputs/rfq_enriched.csv"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    rfq_enriched = pd.read_csv(input_path)

    modes = ["dimensions", "grade", "categorical", "all"]
    for mode in modes:
        df = ablation_similarity(rfq_enriched, mode=mode)
        out_path = os.path.join(output_dir, f"top3_{mode}.csv")
        df.to_csv(out_path, index=False)
        print(f"[OK] Saved {out_path} with {len(df)} rows")
