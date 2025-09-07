import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def jaccard_similarity(set1, set2):
    """Compute Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def compute_top3_cosine_jaccard(rfq_enriched, numeric_cols, cat_cols, weight_cosine=0.6, weight_jacc=0.4):
    """Compute top-3 similar RFQs using cosine+jaccard hybrid metric."""
    rfq_ids = rfq_enriched['id'].tolist()
    results = []

    # Prepare numeric matrix for cosine similarity
    numeric_data = rfq_enriched[numeric_cols].fillna(0).to_numpy()
    cos_sim_matrix = cosine_similarity(numeric_data)

    # Pre-extract categorical sets
    cat_sets = []
    for _, row in rfq_enriched.iterrows():
        features = set()
        for col in cat_cols:
            val = row.get(col)
            if pd.notna(val):
                features.add(f"{col}:{val}")
        cat_sets.append(features)

    # Compute similarities
    for i, id1 in enumerate(rfq_ids):
        similarities = []
        for j, id2 in enumerate(rfq_ids):
            if id1 == id2:
                continue

            # Cosine similarity
            cos_sim = cos_sim_matrix[i, j]

            # Jaccard similarity
            jacc_sim = jaccard_similarity(cat_sets[i], cat_sets[j])

            # Weighted hybrid
            total_sim = weight_cosine * cos_sim + weight_jacc * jacc_sim
            similarities.append((id2, total_sim))

        # Top 3 matches
        similarities = sorted(similarities, key=lambda x: x[1], reverse=True)[:3]
        for match_id, score in similarities:
            results.append({'rfq_id': id1, 'match_id': match_id, 'similarity_score': score})

    return pd.DataFrame(results)

if __name__ == "__main__":
    # Paths
    enriched_path = "outputs/rfq_enriched.csv"
    output_path = "outputs/top3_cosine_jaccard.csv"

    # Load enriched RFQ
    rfq_enriched = pd.read_csv(enriched_path)

    # Numeric and categorical columns
    numeric_cols = [
        "thickness_min", "thickness_max",
        "width_min", "width_max",
        "length_min", "length_max",
        "height_min", "height_max",
        "weight_min", "weight_max",
        "inner_diameter_min", "inner_diameter_max",
        "outer_diameter_min", "outer_diameter_max",
        "tensile_mid", "yield_mid", "elongation_mid",
        "reduction_mid", "hardness_mid"
    ]
    numeric_cols = [col for col in numeric_cols if col in rfq_enriched.columns]

    cat_cols = ["coating", "finish", "form", "surface_type", "surface_protection"]
    cat_cols = [col for col in cat_cols if col in rfq_enriched.columns]

    # Compute similarities
    top3 = compute_top3_cosine_jaccard(rfq_enriched, numeric_cols, cat_cols)

    # Save
    top3.to_csv(output_path, index=False)
    print(f"Top-3 cosine+jaccard similarity saved to {output_path}")
