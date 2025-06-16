import json
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import uuid
from collections import OrderedDict

# === CONFIGURATION ===
EXCEL_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/SALES GEBRUIK_TAL MATRIX LEDCONVERTERS 2024 v10.8.2.xlsx"
PRICELIST_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/Copy of Pricelist 2025_V1.xlsx"
OUTPUT_JSON = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_improved.json"
DOWNLOAD_DIR = "/Users/alessiacolumban/TAL_Chatbot/Backend/pdfs"
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
def rename_and_restructure_item_cosmos(item):
    # Add 'id' field at the top
    item["id"] = str(uuid.uuid4())

    # Key mapping (adjust as needed for your Excel column names)
    key_mapping = {
        "TYPE": "type",
        "ARTNR": "artnr",
        "CONVERTER DESCRIPTION": "converter_description",
        "CONVERTER DESCRIPTION:": "converter_description",
        "DIMLIST TYPE": "dimlist_type",
        "STRAIN RELIEF": "strain_relief",
        "LOCATION": "location",
        "DIMMABILITY": "dimmability",
        "CCR_(AMPLITUDE)": "ccr_amplitude",
        "CCR (AMPLITUDE)": "ccr_amplitude",
        "SIZE: L*B*H (mm)": "size",
        "SIZE L*B*H (MM)": "size",
        "IP": "ip",
        "CLASS": "class",
        "Barcode": "barcode",
        "Name": "name",
        "Listprice": "listprice",
        "Unit": "unit",
        "LifeCycle": "lifecycle",
        "pdf_link": "pdf_link",
        "NOM. INPUT VOLTAGE (V)": "nom_input_voltage",
        "OUTPUT VOLTAGE (V)": "output_voltage",
        "EFFICIENCY @FULL LOAD": "efficiency_full_load",
        "efficiency_@full_load": "efficiency_full_load"
    }

    # Strip colons and normalize keys (optional, if your Excel has weird keys)
    item = {k.rstrip(':'): v for k, v in item.items()}
    normalized_item = {}
    for k, v in item.items():
        normalized_key = k.replace(' ', '_').upper().replace(':', '')
        normalized_item[normalized_key] = v
    renamed_item = {}
    for old_key, value in normalized_item.items():
        new_key = key_mapping.get(old_key, old_key.lower())
        renamed_item[new_key] = value

    if 'size_l*b*h_(mm)' in renamed_item:
        renamed_item['size'] = renamed_item.pop('size_l*b*h_(mm)')
    if 'ccr_(amplitude)' in renamed_item:
        renamed_item['ccr_amplitude'] = renamed_item.pop('ccr_(amplitude)')

    ordered_item = OrderedDict()
    ordered_item['id'] = renamed_item.pop('id')
    for key, value in renamed_item.items():
        ordered_item[key] = value

    return ordered_item

# ======================
# Clean keys (but leave all values untouched, and do not clean keys inside "lamps")
# ======================
def clean_keys(obj):
    """
    Recursively remove all special characters from dictionary keys (except underscores),
    except for keys inside the 'lamps' dictionary, which are preserved as-is.
    Values (including lamp names and all content) are left untouched.
    """
    if isinstance(obj, dict):
        new_obj = OrderedDict()
        for k, v in obj.items():
            if k == "lamps":
                # Do not clean keys inside "lamps" dict
                new_obj[k] = v
            else:
                cleaned_key = re.sub(r'[^a-zA-Z0-9_]', '', k)
                new_obj[cleaned_key] = clean_keys(v)
        return new_obj
    elif isinstance(obj, list):
        return [clean_keys(item) for item in obj]
    else:
        return obj

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
    article_numbers = merged_df["ARTNR"]. dropna().astype(int).astype(str).unique().tolist()
    pdf_mapping = scrape_pdf_links_by_article_numbers(article_numbers)
    print(f"✅ Found {len(pdf_mapping)} PDF links.")

    if DOWNLOAD_DIR:
        print("📥 Downloading PDFs...")
        download_pdfs(pdf_mapping, DOWNLOAD_DIR)
        print("✅ PDFs downloaded.")

    print("🔧 Matching converters with PDF links and pricelist info...")
    converters_list = []

    pricelist_fields = [col for col in pricelist_df.columns if col != "ARTNR"]
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

        info = row.iloc[:GENERAL_INFO_COLUMNS].dropna().to_dict()

        for field in pricelist_fields:
            val = row.get(field)
            if pd.notna(val):
                info[field] = val

        pdf_link = pdf_mapping.get(artnr_str)
        info["pdf_link"] = pdf_link if pdf_link else None
        if not pdf_link:
            print(f"⚠️ No PDF found for converter: {converter_type} - {artnr_str}")

        for field in voltage_fields:
            if field in info:
                info[field] = parse_min_max_as_float(info[field])

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

        info = rename_and_restructure_item_cosmos(info)
        converters_list.append(info)

    # Clean all keys (but do not clean keys inside "lamps" dict)
    cleaned_converters_list = clean_keys(converters_list)

    print(f"💾 Saving output to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(cleaned_converters_list, f, indent=4, ensure_ascii=False)

    print(f"✅ Done! Exported {len(cleaned_converters_list)} converters.")

# ======================
# Run script
# ======================
if __name__ == "__main__":
    main()
