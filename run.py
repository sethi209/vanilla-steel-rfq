import os
import rfq_final

def main():
    # Paths
    data_folder = "data"
    outputs_folder = "outputs"
    os.makedirs(outputs_folder, exist_ok=True)

    rfq_file = os.path.join(data_folder, "rfq.csv")
    reference_file = os.path.join(data_folder, "reference_properties.tsv")

    enriched_path = os.path.join(outputs_folder, "rfq_enriched.csv")
    top3_path = os.path.join(outputs_folder, "top3.csv")

    # Step 1: Enrich RFQ
    rfq_enriched = rfq_final.enrich_rfq(rfq_file, reference_file)
    rfq_enriched.to_csv(enriched_path, index=False)
    print(f"Enriched RFQ saved to {enriched_path}")

    # Step 2: Compute top-3 similarity
    top3 = rfq_final.compute_top3_similarity(rfq_enriched)
    top3_df_sorted = top3.sort_values(by=['rfq_id', 'similarity_score'], ascending=[True, False])
    top3_df_sorted.reset_index(drop=True, inplace=True)

    # Save to CSV
    top3_df_sorted.to_csv(top3_path, index=False)
    print(f"Top-3 similarity saved to {top3_path}")

if __name__ == "__main__":
    main()
