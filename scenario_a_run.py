import pandas as pd
import numpy as np
import re

# ---------- helpers ----------
def to_float(x):
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.floating)):
        return float(x)
    s = str(x).strip()
    if not s:
        return np.nan
    s = s.replace(",", ".")  # handle comma decimals
    try:
        return float(s)
    except ValueError:
        return np.nan

def extract_grade_and_coating(material: str):
    if pd.isna(material):
        return (np.nan, np.nan)
    s = str(material).strip().upper()
    # Base grade (DX..., S..., HDC...)
    m = re.search(r"(DX[0-9A-Z]+D?|S[0-9]+JR|HDC)", s)
    base = m.group(1) if m else s.split()[0]
    # Coating (e.g. +Z140, +AZ150)
    plus = re.findall(r"\+[A-Z0-9]+", s)
    coat = plus[0] if plus else np.nan
    return (base, coat)

# ---------- supplier 1 cleaning ----------
def clean_supplier1(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    rename = {
        "Quality/Choice": "quality",
        "Grade": "grade",
        "Finish": "finish",
        "Thickness (mm)": "thickness_mm",
        "Width (mm)": "width_mm",
        "Description": "description",
        "Gross weight (kg)": "weight_kg",
        "Quantity": "quantity",
        "RP02": "rp02",
        "RM": "rm",
        "AG": "ag",
        "AI": "ai",
    }
    df = df.rename(columns={c: rename.get(c, c) for c in df.columns})

    for col in ["thickness_mm", "width_mm", "weight_kg", "rp02", "rm", "ag", "ai", "quantity"]:
        if col in df.columns:
            df[col] = df[col].apply(to_float)

    df["source"] = "supplier1"
    df["article_id"] = np.nan
    df["reserved"] = np.nan
    df["material_full"] = np.nan
    df["coating"] = np.nan

    return df[[
        "grade","quality","finish","thickness_mm","width_mm","description",
        "weight_kg","quantity","rp02","rm","ag","ai","article_id","reserved",
        "material_full","source","coating"
    ]]

# ---------- supplier 2 cleaning ----------
def clean_supplier2(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    rename = {
        "Material": "material_full",
        "Description": "description",
        "Article ID": "article_id",
        "Weight (kg)": "weight_kg",
        "Quantity": "quantity",
        "Reserved": "reserved",
    }
    df = df.rename(columns={c: rename.get(c, c) for c in df.columns})

    for col in ["weight_kg", "quantity"]:
        if col in df.columns:
            df[col] = df[col].apply(to_float)

    if "material_full" in df.columns:
        grade_coat = df["material_full"].apply(extract_grade_and_coating)
        df["grade"] = grade_coat.apply(lambda t: t[0])
        # Replace 0 or np.nan with empty string for Excel readability
        df["coating"] = grade_coat.apply(lambda t: t[1] if pd.notna(t[1]) else "")

    if "reserved" in df.columns:
        df["reserved"] = df["reserved"].astype(str).str.strip().str.lower().map(
            {
                "true": True, "yes": True, "1": True,
                "false": False, "no": False, "0": False,
                "vanilla": True, "not reserved": False
            }
        )

    for col in ["quality","finish","thickness_mm","width_mm","rp02","rm","ag","ai"]:
        if col not in df.columns:
            df[col] = np.nan

    df["source"] = "supplier2"

    return df[[
        "grade","quality","finish","thickness_mm","width_mm","description",
        "weight_kg","quantity","rp02","rm","ag","ai","article_id","reserved",
        "material_full","source","coating"
    ]]

# ---------- main ----------
def build_inventory(file1: str, file2: str, out_path: str):
    s1 = clean_supplier1(file1)
    s2 = clean_supplier2(file2)
    inv = pd.concat([s1, s2], ignore_index=True)

    # Deduplicate conservatively
    key_cols = ["grade","finish","thickness_mm","width_mm","article_id","description","source"]
    inv = inv.drop_duplicates(subset=key_cols)
    # Ensure coating is string and convert NaN/0 to empty string
    # Ensure coating stays as text
    inv["coating"] = inv["coating"].astype("string")

    # Replace any literal "nan" with blank
    inv["coating"] = inv["coating"].fillna("")

    # Save cleanly
    inv.to_csv(out_path.replace(".csv", ".csv"), index=False, encoding="utf-8")
    inv.to_excel(out_path.replace(".csv", ".xlsx"), index=False, engine="openpyxl")


    print(f"[OK] wrote {out_path} with {len(inv)} rows")

# ---------- run ----------
if __name__ == "__main__":
    build_inventory(
        file1="data/supplier_data1.xlsx",
        file2="data/supplier_data2.xlsx",
        out_path="outputs/inventory_dataset.csv"
    )
