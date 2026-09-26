import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFESTS_DIR = os.path.join(PROJECT_ROOT, "dataset_manifests")
MAPPING_PATH = os.path.join(MANIFESTS_DIR, "impr100_mapping.json")
STATS_PATH = os.path.join(MANIFESTS_DIR, "dataset_stats.json")

def main():
    print(f"Loading IMPR-100 mapping from: {MAPPING_PATH}")
    with open(MAPPING_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    # Index by class_name
    map_by_class = {item["class_name"]: item for item in mapping if item["class_name"]}

    # Update dataset_stats.json
    with open(STATS_PATH, "r", encoding="utf-8") as f:
        stats = json.load(f)

    stats["source_excel"] = "IMPR-100.xlsx"
    stats["total_impr_species"] = len(mapping)
    stats["class_details"] = []
    
    for cls_name in stats["classes"]:
        info = map_by_class.get(cls_name, {})
        stats["class_details"].append({
            "class_name": cls_name,
            "id": info.get("id"),
            "sanskrit_name": info.get("sanskrit_name"),
            "latin_name": info.get("latin_name"),
            "common_name_english": info.get("common_name_english"),
            "family": info.get("family"),
            "habit": info.get("habit"),
            "potency": info.get("potency"),
            "dosage": info.get("dosage")
        })

    with open(STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"Updated {STATS_PATH} with IMPR-100 class metadata.")

    # Enrich train, val, test manifests
    for split_name in ["train", "val", "test"]:
        manifest_file = os.path.join(MANIFESTS_DIR, f"{split_name}_manifest.json")
        if not os.path.exists(manifest_file):
            continue

        print(f"Enriching {manifest_file}...")
        with open(manifest_file, "r", encoding="utf-8") as f:
            records = json.load(f)

        enriched_count = 0
        for rec in records:
            cls_name = rec.get("class_name")
            if cls_name in map_by_class:
                info = map_by_class[cls_name]
                rec["impr_id"] = info.get("id")
                rec["sanskrit_name"] = info.get("sanskrit_name")
                rec["common_name_en"] = info.get("common_name_english")
                rec["family"] = info.get("family")
                rec["habit"] = info.get("habit")
                rec["parts_used"] = info.get("parts_used")
                rec["dosage"] = info.get("dosage")
                enriched_count += 1

        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        print(f"  Enriched {enriched_count}/{len(records)} image records in {split_name}_manifest.json")

    print("[SUCCESS] All dataset manifests enriched with IMPR-100 mapping!")

if __name__ == "__main__":
    main()
