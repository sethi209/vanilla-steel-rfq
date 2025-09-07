# rfq_clustering.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans

def cluster_rfq(rfq_enriched, n_clusters=5):
    """Cluster RFQs using numeric + categorical features."""

    # -------------------------
    # 1. Select features
    # -------------------------
    numeric_features = [
        "thickness_min", "thickness_max",
        "width_min", "width_max",
        "length_min", "length_max",
        "height_min", "height_max",
        "weight_min", "weight_max",
        "inner_diameter_min", "inner_diameter_max",
        "outer_diameter_min", "outer_diameter_max",
        "tensile_mid", "yield_mid",
        "elongation_mid", "reduction_mid", "hardness_mid"
    ]

    categorical_features = [
        "coating", "finish", "form",
        "surface_type", "surface_protection"
    ]

    # Keep only relevant columns
    rfq_filtered = rfq_enriched[numeric_features + categorical_features].copy()

    # -------------------------
    # 2. Preprocessing pipelines
    # -------------------------
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="mean")),
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="Not specified")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features)
        ]
    )

    # -------------------------
    # 3. Fit KMeans clustering
    # -------------------------
    model = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("clusterer", KMeans(n_clusters=n_clusters, random_state=42, n_init=10))
    ])

    rfq_filtered["cluster"] = model.fit_predict(rfq_filtered)

    return rfq_filtered, model


def cluster_summary(rfq_filtered):
    """Summarize clusters by numeric means and categorical modes."""
    summary = {}
    for cluster_id, group in rfq_filtered.groupby("cluster"):
        numeric_means = group.select_dtypes(include=[np.number]).mean()
        categorical_modes = group.select_dtypes(exclude=[np.number]).mode().iloc[0]
        summary[cluster_id] = pd.concat([numeric_means, categorical_modes])
    return pd.DataFrame(summary).T


if __name__ == "__main__":
    # Paths
    rfq_path = "outputs/rfq_enriched.csv"
    clustered_path = "outputs/rfq_clustered.csv"

    # Load enriched data
    rfq_enriched = pd.read_csv(rfq_path)

    # Cluster
    clustered, model = cluster_rfq(rfq_enriched, n_clusters=5)

    # Save clustered RFQs with cluster labels
    clustered.to_csv(clustered_path, index=False)
    print(f"Clustered RFQs saved to {clustered_path}")

    # Print cluster interpretation
    summary = cluster_summary(clustered)
    print("\n=== Cluster Interpretation ===")
    print(summary)
