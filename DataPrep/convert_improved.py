import json
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import uuid

# === CONFIGURATION ===
EXCEL_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/SALES GEBRUIK_TAL MATRIX LEDCONVERTERS 2024 v10.8.2.xlsx"
PRICELIST_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/Copy of Pricelist 2025_V1.xlsx"
OUTPUT_JSON = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_improved.json"
DOWNLOAD_DIR = "/Users/alessiacolumban/TAL_Chatbot/Backend/pdfs"  # Directory to save PDFs (optional)
HEADER_SKIP_ROWS = 4
GENERAL_INFO_COLUMNS = 14
BASE_URL = "https://www.tal.be"

# ======================
# PDF Lookup Function by Article Numbers
# ======================
def scrape_pdf_links_by_article_numbers(article_numbers):
    pdf_links = {}
    for artnr in article_numbers:
        url = f"https://www.tal.be/en/downloads?field_download_category_target_id=All&name={artnr}&field_file_type_target_id=All"
        print(f"🔍 Searching PDF for: {artnr}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            found = False
            for link in soup.find_all("a", href=True):
                href = link["href"].strip()
                if href.lower().endswith(".pdf") and (artnr in href or artnr in link.get_text()):
                    pdf_links[str(artnr)] = urljoin(BASE_URL, href)
                    found = True
                    print(f"✅ Found PDF for {artnr}")
                    break
            if not found:
                print(f"⚠️ No PDF found for {artnr}")
        except Exception as e:
            print(f"❌ Error for {artnr}: {e}")
    return pdf_links

# ======================
# Download PDFs (optional)
# ======================
def download_pdfs(pdf_mapping, download_dir):
    os.makedirs(download_dir, exist_ok=True)
    for key, url in pdf_mapping.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            filename = os.path.join(download_dir, f"{key}.pdf")
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"📥 Downloaded: {filename}")
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")

# ======================
# Min/Max Value Parser (with float conversion)
# ======================
def parse_min_max_as_float(value):
    if pd.isna(value):
        return None
    val_str = str(value).strip()
    if '-' in val_str:
        parts = val_str.split('-', 1)
        min_val = parts[0].strip()
        max_val = parts[1].strip()
    else:
        min_val = max_val = val_str.strip()
    try:
        min_val = float(min_val)
        max_val = float(max_val)
    except ValueError:
        return None
    return {'min': min_val, 'max': max_val}

# ======================
# Rename and Restructure Item for Cosmos DB
# ======================
def rename_and_restructure_item(item):
    # Assign a UUID as id (required for Cosmos DB)
    item["id"] = str(uuid.uuid4())
    # Rename and move voltage fields
    item["output_voltage"] = item.get("OUTPUT VOLTAGE (V)")
    item["nom_input_voltage"] = item.get("NOM. INPUT VOLTAGE (V)")
    # Handle efficiency and size (use any existing key, case-insensitive)
    item["efficiency_full_load"] = item.get("EFFICIENCY @FULL LOAD", item.get("efficiency_@full_load", None))
    item["size"] = item.get("SIZE L*B*H (MM)", item.get("size_l*b*h_(mm)", None))
    # Remove old keys
    old_keys = [
        "OUTPUT VOLTAGE (V)", "output_voltage_(v)",
        "NOM. INPUT VOLTAGE (V)", "nom._input_voltage_(v)",
        "EFFICIENCY @FULL LOAD", "efficiency_@full_load",
        "SIZE L*B*H (MM)", "size_l*b*h_(mm)"
    ]
    for key in old_keys:
        if key in item:
            item.pop(key, None)
    return item

# ======================
# Main Function
# ======================
def main():
    print("📥 Reading main Excel file...")
    df = pd.read_excel(EXCEL_PATH, skiprows=HEADER_SKIP_ROWS)
    df.dropna(how="all", inplace=True)

    if "TYPE" not in df.columns or "ARTNR" not in df.columns:
        raise KeyError("❌ 'TYPE' or 'ARTNR' column not found in main Excel file.")

    print("📥 Reading pricelist Excel file...")
    pricelist_df = pd.read_excel(PRICELIST_PATH)
    if "ARTNR" not in pricelist_df.columns:
        raise KeyError("❌ 'ARTNR' column not found in pricelist Excel file.")

    print("🔧 Merging main data with pricelist data...")
    merged_df = df.merge(pricelist_df, on="ARTNR", how="left", suffixes=('', '_pricelist'))

    print("🔎 Scraping PDFs by article number...")
    article_numbers = merged_df["ARTNR"].dropna().astype(int).astype(str).unique().tolist()
    pdf_mapping = scrape_pdf_links_by_article_numbers(article_numbers)
    print(f"✅ Found {len(pdf_mapping)} PDF links.")

    # Optional: Download PDFs
    if DOWNLOAD_DIR:
        print("📥 Downloading PDFs...")
        download_pdfs(pdf_mapping, DOWNLOAD_DIR)
        print("✅ PDFs downloaded.")

    print("🔧 Matching converters with PDF links and pricelist info...")
    converters_json = {}

    # Pricelist fields (everything except ARTNR)
    pricelist_fields = [col for col in pricelist_df.columns if col != "ARTNR"]

    # Fields to parse as min/max (match the EXACT column names from your Excel)
    voltage_fields = ["NOM. INPUT VOLTAGE (V)", "OUTPUT VOLTAGE (V)"]

    for _, row in merged_df.iterrows():
        converter_type = str(row.get("TYPE", "")).strip()
        artnr_raw = row.get("ARTNR")

        if pd.isna(artnr_raw):
            continue

        try:
            artnr_int = int(artnr_raw)
            artnr_str = str(artnr_int)
        except ValueError:
            continue

        if not converter_type or not artnr_str:
            continue

        converter_id = f"{converter_type} - {artnr_str}"
        info = row.iloc[:GENERAL_INFO_COLUMNS].dropna().to_dict()

        # Add extra pricelist info
        for field in pricelist_fields:
            val = row.get(field)
            if pd.notna(val):
                info[field] = val

        # Match PDF link by article number
        pdf_link = pdf_mapping.get(artnr_str)
        info["pdf_link"] = pdf_link if pdf_link else None
        if not pdf_link:
            print(f"⚠️ No PDF found for converter: {converter_id}")

        # Process voltage fields as min/max float
        for field in voltage_fields:
            if field in info:
                info[field] = parse_min_max_as_float(info[field])

        # Extract lamp fields
        lamps = {}
        for col in merged_df.columns[GENERAL_INFO_COLUMNS:]:
            if col in ["ARTNR", "NAME_norm"] or col in pricelist_fields:
                continue
            val = str(row.get(col))
            if pd.notna(row.get(col)) and val.strip():
                lamp_minmax = parse_min_max_as_float(val)
                if lamp_minmax:
                    lamps[str(col).strip()] = lamp_minmax

        info["lamps"] = lamps

        # Rename and restructure the item for Cosmos DB
        info = rename_and_restructure_item(info)
        converters_json[converter_id] = info

    print(f"💾 Saving output to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(converters_json, f, indent=4, ensure_ascii=False)

    print(f"✅ Done! Exported {len(converters_json)} converters.")

# ======================
# Run script
# ======================
if __name__ == "__main__":
    main()
