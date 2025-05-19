import json
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === CONFIGURATION ===
EXCEL_PATH = "SALES GEBRUIK_TAL MATRIX LEDCONVERTERS 2024 v10.8.2.xlsx"
OUTPUT_JSON = "converters_with_links.json"
HEADER_SKIP_ROWS = 4
GENERAL_INFO_COLUMNS = 14
BASE_URL = "https://www.tal.be"
# Adjust this URL to the correct folder with pagination parameter
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

    print("📥 Reading Excel file...")
    df = pd.read_excel(EXCEL_PATH, skiprows=HEADER_SKIP_ROWS)
    df.dropna(how="all", inplace=True)

    if "TYPE" not in df.columns or "ARTNR" not in df.columns:
        raise KeyError("❌ 'TYPE' or 'ARTNR' column not found in Excel file.")

    print("🔧 Matching converters with PDF links...")

    converters_json = {}
    for _, row in df.iterrows():
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

        # Match PDF link by article number string key
        pdf_link = pdf_mapping.get(artnr_str)
        if pdf_link:
            info["pdf_link"] = pdf_link
        else:
            print(f"⚠️ No PDF found for converter: {converter_id}")

        # Extract lamp info from remaining columns
        lamps = {}
        for col in df.columns[GENERAL_INFO_COLUMNS:]:
            if col in ["ARTNR", "NAME_norm"]:
                continue
            val = row[col]
            if pd.notna(val):
                lamps[str(col).strip()] = {
                    "min": val,
                    "max": val,
                    "avg": val
                }
        info["lamps"] = lamps
        converters_json[converter_id] = info

    print(f"💾 Saving output to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(converters_json, f, indent=4, ensure_ascii=False)

    print(f"✅ Done! Exported {len(converters_json)} converters.")

if __name__ == "__main__":
    main()
