import os
import io
import json
import re
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_PATH = os.path.join(PROJECT_ROOT, "IMPR-100.xlsx")
KB_PATH = os.path.join(PROJECT_ROOT, "backend", "knowledge_base", "plants_kb.json")
CLASS_META_PATH = os.path.join(PROJECT_ROOT, "saved_models", "class_metadata.json")
STATS_PATH = os.path.join(PROJECT_ROOT, "dataset_manifests", "dataset_stats.json")
MAPPING_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "dataset_manifests", "impr100_mapping.json")

def parse_impr_excel(excel_path):
    df_raw = pd.read_excel(excel_path)
    col_name = df_raw.columns[0]
    csv_text = col_name + '\n' + '\n'.join(df_raw[col_name].dropna().astype(str))
    df = pd.read_csv(io.StringIO(csv_text))
    return df

def clean_list(val, delimiters=[',', '/']):
    if pd.isna(val):
        return []
    s = str(val)
    for d in delimiters[1:]:
        s = s.replace(d, delimiters[0])
    items = [x.strip() for x in s.split(delimiters[0]) if x.strip()]
    return items

def infer_body_systems(indications, parts, current_systems=None):
    systems = set(current_systems or [])
    text = " ".join(indications).lower()
    
    mapping = {
        "Respiratory System": ["cough", "asthma", "bronchitis", "respiratory", "cold", "dyspnoea", "chest", "hiccup", "breath"],
        "Musculoskeletal": ["arthritis", "rheumatism", "joint", "swelling", "pain", "gout", "paralysis", "fracture", "muscular", "stiffness"],
        "Digestive System": ["indigestion", "diarrhea", "dysentery", "appetizer", "digestive", "colic", "piles", "hemorrhoids", "worm", "stomach", "liver", "jaundice", "ascites", "spleen", "emesis", "vomiting", "flatulence", "anorexia", "constipation"],
        "Integumentary": ["skin", "leprosy", "wound", "ulcer", "complexion", "eczema", "erysipelas", "boil", "acne", "itching", "pruritus", "leukoderma"],
        "Nervous System": ["insomnia", "memory", "brain", "nervous", "convulsion", "epilepsy", "stress", "anxiety", "headache", "neuralgia", "mania", "intellect"],
        "Cardiovascular System": ["heart", "cardiac", "blood", "hypertension", "cholesterol", "bleeding", "haemorrhage"],
        "Urinary / Kidney": ["urinary", "calculi", "stone", "kidney", "dysuria", "diuretic", "burning micturition", "diabetes", "prameha"],
        "Endocrine / Metabolism": ["diabetes", "anti-aging", "rejuvenative", "strength", "aphrodisiac", "debility", "obesity", "metabolism", "thyroid", "emaciation", "immunity"]
    }
    
    for sys_name, keywords in mapping.items():
        if any(kw in text for kw in keywords):
            systems.add(sys_name)
            
    if not systems:
        systems.add("General / Rasayana")
        
    return sorted(list(systems))

def infer_dosha_karma(potency, vipaka, taste):
    pot_lower = str(potency).lower()
    taste_lower = str(taste).lower()
    vip_lower = str(vipaka).lower()
    
    if "hot" in pot_lower:
        if "bitter" in taste_lower or "astringent" in taste_lower:
            return "Pacifies Kapha and Vata; balances Pitta in moderation"
        return "Pacifies Vata and Kapha; may increase Pitta in excess"
    elif "cold" in pot_lower:
        return "Pacifies Pitta and Vata; cooling Rasayana"
    elif "warm" in pot_lower:
        return "Balances Tridosha (Vata-Pitta-Kapha)"
    return "Balances Vata and Kapha"

def main():
    print(f"Loading IMPR-100 Excel from: {EXCEL_PATH}")
    df = parse_impr_excel(EXCEL_PATH)
    print(f"Total rows in IMPR-100.xlsx: {len(df)}")
    
    with open(STATS_PATH, "r", encoding="utf-8") as f:
        stats = json.load(f)
    classes = stats["classes"]
    
    existing_kb = {}
    if os.path.exists(KB_PATH):
        with open(KB_PATH, "r", encoding="utf-8") as f:
            existing_kb = json.load(f)
            
    existing_meta = {}
    if os.path.exists(CLASS_META_PATH):
        with open(CLASS_META_PATH, "r", encoding="utf-8") as f:
            existing_meta = json.load(f)

    updated_kb = {}
    updated_meta = {}
    full_mapping = []

    for idx, cls_name in enumerate(classes):
        cls_id = int(cls_name.split("_")[0])
        subset = df[df["ID"] == cls_id]
        if len(subset) == 0:
            print(f"WARNING: ID {cls_id} ({cls_name}) not found in IMPR-100.xlsx!")
            continue
            
        row = subset.iloc[0]
        
        # Ground truth fields from IMPR-100
        sanskrit_name = str(row["Sanskrit_Name"]).strip()
        latin_name = str(row["Latin_Name"]).strip()
        common_en = str(row["Common_Name_English"]).strip()
        family = str(row["Family"]).strip()
        habit = str(row["Habit"]).strip()
        dosage = str(row["Dosage"]).strip()
        potency = str(row["Potency"]).strip()
        taste = str(row["Taste"]).strip()
        guna = str(row["Properties_Qualities"]).strip()
        vipaka = str(row["Post_Digestive_Effect"]).strip()
        
        chems = clean_list(row["Chemical_Composition"], delimiters=[','])
        indications = clean_list(row["Therapeutic_Indications"], delimiters=[','])
        parts_used = clean_list(row["Parts_Used"], delimiters=['/', ','])

        # Merge with existing KB entry if present
        cur = existing_kb.get(cls_name, {})
        cur_names = cur.get("common_names", {})
        
        common_names = {
            "english": common_en,
            "sanskrit": sanskrit_name,
            "hindi": cur_names.get("hindi") or sanskrit_name,
            "regional": cur_names.get("regional") or f"{sanskrit_name} ({family})"
        }
        
        # Combine phytochemicals
        all_chems = list(dict.fromkeys(chems + cur.get("active_phytochemicals", [])))
        
        # Inferred systems
        body_systems = infer_body_systems(indications, parts_used, cur.get("body_systems"))
        
        # Dosha karma
        dosha_karma = cur.get("ayurvedic_properties", {}).get("dosha_karma") or infer_dosha_karma(potency, vipaka, taste)
        
        # Derived symptoms for search
        derived_symptoms = list(set([ind.lower() for ind in indications] + cur.get("symptoms", [])))
        
        # Dosage & formulation description
        dosage_and_formulation = cur.get("dosage_and_formulation") or f"Standard classical formulation: Churna / Kwatha. Prescribed Ayurvedic Dosage: {dosage}."
        if dosage not in dosage_and_formulation:
            dosage_and_formulation = f"{dosage_and_formulation} Prescribed Dosage: {dosage}."
            
        # Medicinal uses summary
        medicinal_uses = cur.get("medicinal_uses") or (
            f"{sanskrit_name} ({latin_name}) is a traditional Indian medicinal {habit.lower()} belonging to the family {family}. "
            f"Classical therapeutic indications include: {', '.join(indications[:6])}. "
            f"It possesses {taste} taste (Rasa), {potency} potency (Virya), and {vipaka} post-digestive effect (Vipaka)."
        )

        precautions = cur.get("precautions") or (
            "Administer according to classical Ayurvedic guidelines. Consult an Ayurvedic physician for prolonged therapy."
        )

        # Build comprehensive KB monograph
        updated_kb[cls_name] = {
            "id": cls_id,
            "class_name": cls_name,
            "botanical_name": latin_name,
            "sanskrit_name": sanskrit_name,
            "common_name_en": common_en,
            "family": family,
            "habit": habit,
            "common_names": common_names,
            "parts_used": parts_used if parts_used else ["Whole Plant"],
            "active_phytochemicals": all_chems,
            "dosage": dosage,
            "ayurvedic_properties": {
                "guna": guna,
                "rasa": taste,
                "virya": potency,
                "vipaka": vipaka,
                "dosha_karma": dosha_karma
            },
            "therapeutic_indications": indications,
            "symptoms": derived_symptoms,
            "medicinal_uses": medicinal_uses,
            "dosage_and_formulation": dosage_and_formulation,
            "precautions": precautions,
            "body_systems": body_systems
        }

        # Build class metadata
        updated_meta[cls_name] = {
            "index": idx,
            "id": cls_id,
            "botanical_name": latin_name,
            "sanskrit_name": sanskrit_name,
            "common_name_en": common_en,
            "family": family,
            "habit": habit,
            "dosage": dosage,
            "virya": potency,
            "rasa": taste,
            "parts_used": parts_used
        }

        # Mapping record
        full_mapping.append({
            "class_index": idx,
            "class_name": cls_name,
            "id": cls_id,
            "sanskrit_name": sanskrit_name,
            "latin_name": latin_name,
            "common_name_english": common_en,
            "family": family,
            "habit": habit,
            "chemical_composition": chems,
            "properties_qualities": guna,
            "taste": taste,
            "potency": potency,
            "post_digestive_effect": vipaka,
            "therapeutic_indications": indications,
            "parts_used": parts_used,
            "dosage": dosage
        })

    # Also add the remaining 7 IMPR-100 species to full_mapping and KB for reference
    for _, row in df.iterrows():
        mid = int(row["ID"])
        if any(m["id"] == mid for m in full_mapping):
            continue
        sanskrit_name = str(row["Sanskrit_Name"]).strip()
        latin_name = str(row["Latin_Name"]).strip()
        common_en = str(row["Common_Name_English"]).strip()
        family = str(row["Family"]).strip()
        habit = str(row["Habit"]).strip()
        dosage = str(row["Dosage"]).strip()
        potency = str(row["Potency"]).strip()
        taste = str(row["Taste"]).strip()
        guna = str(row["Properties_Qualities"]).strip()
        vipaka = str(row["Post_Digestive_Effect"]).strip()
        chems = clean_list(row["Chemical_Composition"], delimiters=[','])
        indications = clean_list(row["Therapeutic_Indications"], delimiters=[','])
        parts_used = clean_list(row["Parts_Used"], delimiters=['/', ','])

        full_mapping.append({
            "class_index": None,
            "class_name": f"{mid}_{latin_name.replace(' ', '_')}",
            "id": mid,
            "sanskrit_name": sanskrit_name,
            "latin_name": latin_name,
            "common_name_english": common_en,
            "family": family,
            "habit": habit,
            "chemical_composition": chems,
            "properties_qualities": guna,
            "taste": taste,
            "potency": potency,
            "post_digestive_effect": vipaka,
            "therapeutic_indications": indications,
            "parts_used": parts_used,
            "dosage": dosage
        })

    # Save outputs
    print(f"Writing updated knowledge base ({len(updated_kb)} classes) to: {KB_PATH}")
    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_kb, f, indent=2, ensure_ascii=False)

    print(f"Writing updated class metadata ({len(updated_meta)} classes) to: {CLASS_META_PATH}")
    with open(CLASS_META_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_meta, f, indent=2, ensure_ascii=False)

    print(f"Writing full IMPR-100 mapping ({len(full_mapping)} species) to: {MAPPING_OUTPUT_PATH}")
    with open(MAPPING_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(full_mapping, f, indent=2, ensure_ascii=False)

    print("\n[SUCCESS] IMPR-100 Excel mapping complete!")

if __name__ == "__main__":
    main()
