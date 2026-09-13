import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.src.triage import ASTRATriageEngine

def main():
    print("=" * 70)
    print("ASTRA STEP 9: LOCAL TRIAGE ENGINE REPRODUCIBILITY TEST")
    print("=" * 70)

    project_root = os.getcwd()
    img_dir = os.path.join(project_root, "ml/data/processed/galaxy_zoo/images")
    audit_csv = os.path.join(project_root, "ml/artifacts/model_audit_examples.csv")

    if not os.path.exists(audit_csv):
        print(f"Error: Audit examples CSV not found at {audit_csv}")
        return

    df_audit = pd.read_csv(audit_csv)
    print(f"Loaded {len(df_audit)} representative audit examples.")

    engine = ASTRATriageEngine()

    results = []
    for idx, row in df_audit.iterrows():
        asset_id = int(row['asset_id'])
        cat = row['category']
        img_path = os.path.join(img_dir, f"{asset_id}.jpg")

        if not os.path.exists(img_path):
            print(f"Warning: Image file not found for asset_id {asset_id}: {img_path}")
            continue

        res = engine.triage_single_image(img_path)

        print(f"\n--- Example {idx+1}: {cat} (Asset ID: {asset_id}) ---")
        print(f"  True Class:         {row['true_class']}")
        print(f"  Predicted Class:    {res['predicted_class']} (Conf: {res['class_confidence']:.4f})")
        print(f"  Novelty Score:      {res['novelty_score']:.4f} (Dist: {res['raw_embedding_distance']:.4f})")
        print(f"  Uncertainty Score:  {res['uncertainty_score']:.4f}")
        print(f"  Oddity Score:       {res['oddity_score']:.4f}")
        print(f"  Triage Score:       {res['experimental_triage_score']:.4f}")
        print(f"  Priority Level:     {res['priority_level']}")
        print(f"  Explanation:        {res['explanation']}")

        results.append({
            "category": cat,
            "asset_id": asset_id,
            "true_class": row['true_class'],
            "predicted_class": res['predicted_class'],
            "confidence": res['class_confidence'],
            "novelty_score": res['novelty_score'],
            "uncertainty_score": res['uncertainty_score'],
            "oddity_score": res['oddity_score'],
            "experimental_triage_score": res['experimental_triage_score'],
            "priority_level": res['priority_level'],
            "explanation": res['explanation']
        })

    print("\n" + "=" * 70)
    print("REPRODUCIBILITY SUMMARY TABLE")
    print("=" * 70)
    df_res = pd.DataFrame(results)
    print(df_res[['category', 'asset_id', 'predicted_class', 'confidence', 'experimental_triage_score', 'priority_level']].to_string())

if __name__ == "__main__":
    main()
