import json
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === CONFIGURATION ===
EXCEL_PATH = "SALES GEBRUIK_TAL MATRIX LEDCONVERTERS 2024 v10.8.2.xlsx"
PRICELIST_PATH = "Copy of Pricelist 2025_V1.xlsx"
OUTPUT_JSON = "converters_with_links_and_pricelist.json"
HEADER_SKIP_ROWS = 4
GENERAL_INFO_COLUMNS = 14
BASE_URL = "https://www.tal.be"
DOWNLOADS_FOLDER_URL = "https://www.tal.be/en/downloads?folder=3-Brochures-Brochures-Brochures-Brosch%C3%BCren&page={}"
NUM_PAGES = 24  # Number of pages to scrape

def scrape_all_pdf_links(num_pages):
    pdf_links = {}
    for page in range(1, num_pages + 1):
        url = DOWNLOADS_FOLDER_URL.format(page)
        print(f"Scraping page {page}: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"].strip()
                if href.lower().endswith(".pdf"):
                    full_url = urljoin(BASE_URL, href)
                    filename = href.split("/")[-1]
                    name_part = filename.rsplit(".", 1)[0]
                    digits_match = re.match(r'(\d{6})', name_part)
                    if digits_match:
                        key = digits_match.group(1)
                        pdf_links[key] = full_url
                        print(f"Found PDF: {key} -> {full_url}")
        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e}")
    return pdf_links

def main():
    print("🔎 Scraping all PDF links from TAL website...")
    pdf_mapping = scrape_all_pdf_links(NUM_PAGES)
    print(f"✅ Found {len(pdf_mapping)} PDF links.")

    print("📥 Reading main Excel file...")
    df = pd.read_excel(EXCEL_PATH, skiprows=HEADER_SKIP_ROWS)
    df.dropna(how="all", inplace=True)

    if "TYPE" not in df.columns or "ARTNR" not in df.columns:
        raise KeyError("❌ 'TYPE' or 'ARTNR' column not found in main Excel file.")

    print("📥 Reading pricelist Excel file...")
    pricelist_df = pd.read_excel(PRICELIST_PATH)
    # Ensure 'ARTNR' column exists in pricelist for merging
    if "ARTNR" not in pricelist_df.columns:
        # You may need to rename the column here if different, e.g.:
        # pricelist_df.rename(columns={"Reference": "ARTNR"}, inplace=True)
        raise KeyError("❌ 'ARTNR' column not found in pricelist Excel file.")

    print("🔧 Merging main data with pricelist data...")
    # Merge on 'ARTNR' column, left join to keep all converters
    merged_df = df.merge(pricelist_df, on="ARTNR", how="left", suffixes=('', '_pricelist'))

    print("🔧 Matching converters with PDF links and merging pricelist info...")

    converters_json = {}

    # Define pricelist fields you want to add from the pricelist file
    # Replace these with actual column names from your pricelist Excel
    pricelist_fields = [col for col in pricelist_df.columns if col != "ARTNR"]

    for _, row in merged_df.iterrows():
        converter_type = str(row.get("TYPE", "")).strip()
        artnr_raw = row.get("ARTNR")
        if pd.isna(artnr_raw):
            continue
        # Convert float article number to int string (e.g., 40082.0 -> "40082")
        artnr_int = int(artnr_raw)
        artnr_str = str(artnr_int)

        if not converter_type or not artnr_str:
            continue

        converter_id = f"{converter_type} - {artnr_str}"
        info = row.iloc[:GENERAL_INFO_COLUMNS].dropna().to_dict()

        # Add pricelist fields to info dictionary
        for field in pricelist_fields:
            val = row.get(field)
            if pd.notna(val):
                info[field] = val

        # Match PDF link by article number string key
        pdf_link = pdf_mapping.get(artnr_str)
        if pdf_link:
            info["pdf_link"] = pdf_link
        else:
            print(f"⚠️ No PDF found for converter: {converter_id}")

        # Extract lamp info from remaining columns (after GENERAL_INFO_COLUMNS)
        lamps = {}
        for col in merged_df.columns[GENERAL_INFO_COLUMNS:]:
            if col in ["ARTNR", "NAME_norm"] or col in pricelist_fields:
                continue
            val = row[col]
            if pd.notna(val):
                lamps[str(col).strip()] = {
                    "min": val,
                    "max": val,
                }
        info["lamps"] = lamps

        converters_json[converter_id] = info

    print(f"💾 Saving output to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(converters_json, f, indent=4, ensure_ascii=False)

    print(f"✅ Done! Exported {len(converters_json)} converters.")

if __name__ == "__main__":
    main()
