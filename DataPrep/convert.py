import pandas as pd
import json

# === CONFIGURATION ===
excel_path = "SALES GEBRUIK_TAL MATRIX LEDCONVERTERS 2024 v10.8.2.xlsx"
output_json_path = "converters.json"
header_skip_rows = 4
general_info_columns = 14  # First 14 columns contain general converter info

# === LOAD EXCEL ===
df = pd.read_excel(excel_path, skiprows=header_skip_rows)
df.dropna(how="all", inplace=True)

# === BUILD JSON STRUCTURE ===
converters_json = {}

for _, row in df.iterrows():
    # Create a unique name from TYPE and ARTNR
    converter_type = str(row.get('TYPE', '')).strip()
    converter_artnr = str(row.get('ARTNR', '')).strip()
    if not converter_type or not converter_artnr or converter_type == 'nan' or converter_artnr == 'nan':
        continue

    converter_name = f"{converter_type} - {converter_artnr}"

    # Extract general converter info
    general_info = row.iloc[:general_info_columns].dropna().to_dict()

    # Extract lamp data
    lamp_data = {}
    for col in df.columns[general_info_columns:]:
        value = row[col]
        if pd.notna(value):
            lamp_data[str(col).strip()] = {
                "min": value,
                "max": value,
            }

    general_info["lamps"] = lamp_data
    converters_json[converter_name] = general_info

# === SAVE TO JSON ===
with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump(converters_json, f, indent=4, ensure_ascii=False)

print(f"✅ Exported {len(converters_json)} converters to '{output_json_path}'")
