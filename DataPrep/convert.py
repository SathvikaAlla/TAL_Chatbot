import json
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# === CONFIGURATION ===
CONVERTERS_EXCEL = "SALES GEBRUIK_TAL MATRIX LEDCONVERTERS 2024 v10.8.2.xlsx"
LUMINAIRES_EXCEL = "Copy of Pricelist 2025_V1.xlsx"
OUTPUT_JSON = "combined_luminaires_converters.json"

HEADER_SKIP_ROWS = 4
GENERAL_INFO_COLUMNS = 14
BASE_URL = "https://www.tal.be"
DOWNLOADS_FOLDER_URL = "https://www.tal.be/en/downloads?folder=3-Brochures-Brochures-Brochures-Brosch%C3%BCren&page={}"
NUM_PAGES = 24

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

    print("📥 Reading converters Excel file...")
    df_converters = pd.read_excel(CONVERTERS_EXCEL, skiprows=HEADER_SKIP_ROWS)
    df_converters.dropna(how="all", inplace=True)

    print("📥 Reading luminaires Excel file...")
    df_luminaires = pd.read_excel(LUMINAIRES_EXCEL)
    df_luminaires.dropna(how="all", inplace=True)

    # Build a dict: luminaire name -> price
    luminaire_price_map = {}
    for _, row in df_luminaires.iterrows():
        name = str(row['Name']).strip()
        price = row['Listprice']
        luminaire_price_map[name] = price

    converters_json = {}
    for _, row in df_converters.iterrows():
        converter_type = str(row.get("TYPE", "")).strip()
        artnr_raw = row.get("ARTNR")
        if pd.isna(artnr_raw):
            continue
        artnr_int = int(artnr_raw)
        artnr_str = str(artnr_int)

        if not converter_type or not artnr_str:
            continue

        converter_id = f"{converter_type} - {artnr_str}"
        info = row.iloc[:GENERAL_INFO_COLUMNS].dropna().to_dict()

        # Add PDF link if available
        pdf_link = pdf_mapping.get(artnr_str)
        if pdf_link:
            info["pdf_link"] = pdf_link
        else:
            print(f"⚠️ No PDF found for converter: {converter_id}")

        # Add price from luminaires if matching by converter_type == luminaire name
        price = luminaire_price_map.get(converter_type)
        if price is not None:
            info["price"] = price
        else:
            print(f"⚠️ No price found for luminaire: {converter_type}")

        # Extract lamp info
        lamps = {}
        for col in df_converters.columns[GENERAL_INFO_COLUMNS:]:
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

    print(f"💾 Saving combined output to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(converters_json, f, indent=4, ensure_ascii=False)

    print(f"✅ Done! Exported {len(converters_json)} combined converters with prices.")

if __name__ == "__main__":
    main()
