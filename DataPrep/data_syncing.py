
import json
import gradio as gr
import pandas as pd
import datetime
import uuid
import re
from typing import Dict, Any
from collections import OrderedDict

# ======================
# Configuration
# ======================
MAIN_JSON_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"
METADATA_JSON_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_metadata.json"
SECONDARY_JSON_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_improved.json"

# ======================
# Data Transformation Functions
# ======================
def rename_and_restructure_item_cosmos(item):
    if "id" not in item:
        item["id"] = str(uuid.uuid4())
    
    key_mapping = {
        "TYPE": "type",
        "ARTNR": "artnr",
        "CONVERTER DESCRIPTION": "converter_description",
        "STRAIN RELIEF": "strain_relief",
        "LOCATION": "location",
        "DIMMABILITY": "dimmability",
        "CCR (AMPLITUDE)": "ccr_amplitude",
        "SIZE: L*B*H (mm)": "size",
        "EFFICIENCY @full load": "efficiency_full_load",
        "IP": "ip",
        "CLASS": "class",
        "NOM. INPUT VOLTAGE (V)": "nom_input_voltage_v",
        "OUTPUT VOLTAGE (V)": "output_voltage_v",
        "Barcode": "barcode",
        "Name": "name",
        "Listprice": "listprice",
        "Unit": "unit",
        "LifeCycle": "lifecycle",
        "pdf_link": "pdf_link"
    }
    
    renamed_item = {}
    for old_key, value in item.items():
        new_key = key_mapping.get(old_key, old_key.lower())
        renamed_item[new_key] = value
    
    return renamed_item

def clean_keys(obj):
    if isinstance(obj, dict):
        new_obj = OrderedDict()
        for k, v in obj.items():
            if k == "lamps":
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
# Core Sync Functionality
# ======================
def sync_secondary_json():
    """Transforms and saves data to secondary JSON format"""
    try:
        with open(MAIN_JSON_PATH, "r", encoding="utf-8") as f:
            main_data = json.load(f)
        with open(METADATA_JSON_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        transformed_list = []
        for converter_id, value in main_data.items():
            # Skip deleted items using metadata
            if metadata.get(converter_id, {}).get("deleted_at"):
                continue
            
            # Apply transformations
            item = rename_and_restructure_item_cosmos(value)
            cleaned_item = clean_keys(item)
            
            # Ensure required fields
            if "id" not in cleaned_item:
                cleaned_item["id"] = str(uuid.uuid4())
            transformed_list.append(cleaned_item)
        
        with open(SECONDARY_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(transformed_list, f, indent=4, ensure_ascii=False)
            
        print("✅ Successfully synced secondary JSON")
    except Exception as e:
        print(f"❌ Sync failed: {str(e)}")

# ======================
# CRUD Functions with Metadata Management
# ======================
def load_json() -> Dict[str, Any]:
    with open(MAIN_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: Dict[str, Any]):
    with open(MAIN_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    sync_secondary_json()

def load_metadata() -> Dict[str, Any]:
    try:
        with open(METADATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_metadata(data: Dict[str, Any]):
    with open(METADATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_current_time():
    return datetime.datetime.now().isoformat()

def add_converter(
    converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
    ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
    price, unit, lifecycle, pdf_link
):
    converter_id = converter_id.strip()
    data = load_json()
    metadata = load_metadata()
    
    if converter_id in data:
        return f"Converter '{converter_id}' already exists."
    
    now = get_current_time()
    
    # Main data entry
    data[converter_id] = {
        "TYPE": converter_type,
        "ARTNR": float(artnr) if artnr else None,
        "CONVERTER DESCRIPTION:": description,
        "STRAIN RELIEF": strain_relief,
        "LOCATION": location,
        "DIMMABILITY": dimmability,
        "CCR (AMPLITUDE)": ccr,
        "SIZE: L*B*H (mm)": size,
        "EFFICIENCY @full load": float(efficiency) if efficiency else None,
        "IP": float(ip) if ip else None,
        "CLASS": float(class_) if class_ else None,
        "NOM. INPUT VOLTAGE (V)": input_voltage,
        "OUTPUT VOLTAGE (V)": output_voltage,
        "Barcode": barcode,
        "Name": name,
        "Listprice": float(price) if price else None,
        "Unit": unit,
        "LifeCycle": lifecycle,
        "pdf_link": pdf_link,
        "lamps": {}
    }
    
    # Metadata entry
    metadata[converter_id] = {
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
        "price_history": [{"timestamp": now, "price": float(price)}] if price else []
    }
    
    save_json(data)
    save_metadata(metadata)
    return f"Added converter '{converter_id}'."

def update_converter(
    converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
    ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
    price, unit, lifecycle, pdf_link
):
    converter_id = converter_id.strip()
    data = load_json()
    metadata = load_metadata()
    
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    
    now = get_current_time()
    
    # Update main data
    info = data[converter_id]
    update_fields = {
        "TYPE": converter_type,
        "ARTNR": float(artnr) if artnr else None,
        "CONVERTER DESCRIPTION:": description,
        "STRAIN RELIEF": strain_relief,
        "LOCATION": location,
        "DIMMABILITY": dimmability,
        "CCR (AMPLITUDE)": ccr,
        "SIZE: L*B*H (mm)": size,
        "EFFICIENCY @full load": float(efficiency) if efficiency else None,
        "IP": float(ip) if ip else None,
        "CLASS": float(class_) if class_ else None,
        "NOM. INPUT VOLTAGE (V)": input_voltage,
        "OUTPUT VOLTAGE (V)": output_voltage,
        "Barcode": barcode,
        "Name": name,
        "Unit": unit,
        "LifeCycle": lifecycle,
        "pdf_link": pdf_link
    }
    
    for key, value in update_fields.items():
        if value:
            info[key] = value
    
    # Handle price changes in metadata
    current_price = float(price) if price else None
    if current_price:
        if "Listprice" not in info or current_price != info.get("Listprice"):
            metadata[converter_id]["price_history"].append({
                "timestamp": now,
                "price": current_price
            })
        info["Listprice"] = current_price
    
    # Update metadata
    metadata[converter_id]["updated_at"] = now
    
    # Handle ID change
    new_type = info.get("TYPE", "")
    new_artnr = info.get("ARTNR", 0)
    new_id = f"{new_type}mA - {int(new_artnr)}"
    
    if new_id != converter_id:
        data[new_id] = info
        del data[converter_id]
        metadata[new_id] = metadata.pop(converter_id)
        save_json(data)
        save_metadata(metadata)
        return f"Updated converter. ID changed to '{new_id}'."
    else:
        save_json(data)
        save_metadata(metadata)
        return f"Updated converter '{converter_id}'."

def delete_converter(converter_id):
    converter_id = converter_id.strip()
    data = load_json()
    metadata = load_metadata()
    
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    
    metadata[converter_id]["deleted_at"] = get_current_time()
    save_metadata(metadata)
    return f"Deleted converter '{converter_id}'."

def add_or_update_lamp(converter_id, lamp_name, min_val, max_val):
    converter_id = converter_id.strip()
    data = load_json()
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    
    lamps = data[converter_id].setdefault("lamps", {})
    lamps[lamp_name.strip()] = {
        "min": float(min_val),
        "max": float(max_val)
    }
    save_json(data)
    return f"Added/updated lamp '{lamp_name}' in converter '{converter_id}'."

def delete_lamp(converter_id, lamp_name):
    converter_id = converter_id.strip()
    data = load_json()
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    
    lamps = data[converter_id].get("lamps", {})
    if lamp_name.strip() not in lamps:
        return f"Lamp '{lamp_name}' not found."
    
    del lamps[lamp_name.strip()]
    save_json(data)
    return f"Deleted lamp '{lamp_name}' from converter '{converter_id}'."

def get_converter(converter_id):
    data = load_json()
    return json.dumps(data.get(converter_id.strip(), {}), indent=2, ensure_ascii=False)

def filter_lamps(filter_type, n_latest):
    data = load_json()
    records = []
    
    for cid, cinfo in data.items():
        if cinfo.get("deleted_at") and filter_type != "Deleted":
            continue
            
        record = {
            "Converter ID": cid,
            "Created At": cinfo.get("created_at", ""),
            "Updated At": cinfo.get("updated_at", ""),
            "Price": cinfo.get("Listprice", ""),
            "Lamps": ", ".join(cinfo.get("lamps", {}).keys())
        }
        
        if filter_type == "Deleted":
            if cinfo.get("deleted_at"):
                record["Deleted At"] = cinfo["deleted_at"]
                records.append(record)
        elif filter_type == "Price Change" and len(cinfo.get("price_history", [])) > 1:
            record["Price History"] = str(cinfo["price_history"])
            records.append(record)
        else:
            records.append(record)
    
    if filter_type == "Latest Added":
        records.sort(key=lambda x: x["Created At"], reverse=True)
    elif filter_type == "Latest Updated":
        records.sort(key=lambda x: x["Updated At"], reverse=True)
    
    return pd.DataFrame(records[:n_latest])

# ======================
# Gradio Interface
# ======================
with gr.Blocks(title="TAL Converter JSON Editor") as demo:
    gr.Markdown("# TAL Converter JSON Editor")
    
    with gr.Tab("Add Converter"):
        inputs = [
            gr.Textbox(label=label) for label in [
                "Converter ID (e.g. 350mA - 930537)", "TYPE", "ARTNR", "CONVERTER DESCRIPTION:",
                "STRAIN RELIEF", "LOCATION", "DIMMABILITY", "CCR (AMPLITUDE)", "SIZE: L*B*H (mm)",
                "EFFICIENCY @full load", "IP", "CLASS", "NOM. INPUT VOLTAGE (V)", "OUTPUT VOLTAGE (V)",
                "Barcode", "Name", "Listprice", "Unit", "LifeCycle", "pdf_link"
            ]
        ]
        add_btn = gr.Button("Add Converter")
        add_output = gr.Textbox(label="Result")
        add_btn.click(
            add_converter,
            inputs=inputs,
            outputs=add_output
        ).then(lambda: [gr.update(value="") for _ in inputs], outputs=inputs)
    
    with gr.Tab("Update Converter"):
        update_inputs = [gr.Textbox(label=f"{label} (update)") for label in [
            "Converter ID", "TYPE", "ARTNR", "CONVERTER DESCRIPTION:", "STRAIN RELIEF",
            "LOCATION", "DIMMABILITY", "CCR (AMPLITUDE)", "SIZE: L*B*H (mm)",
            "EFFICIENCY @full load", "IP", "CLASS", "NOM. INPUT VOLTAGE (V)",
            "OUTPUT VOLTAGE (V)", "Barcode", "Name", "Listprice", "Unit", "LifeCycle", "pdf_link"
        ]]
        update_btn = gr.Button("Update Converter")
        update_output = gr.Textbox(label="Result")
        update_btn.click(
            update_converter,
            inputs=update_inputs,
            outputs=update_output
        ).then(lambda: [gr.update(value="") for _ in update_inputs], outputs=update_inputs)
    
    with gr.Tab("Delete Converter"):
        converter_id_d = gr.Textbox(label="Converter ID")
        delete_btn = gr.Button("Delete Converter")
        delete_output = gr.Textbox(label="Result")
        delete_btn.click(
            delete_converter,
            inputs=converter_id_d,
            outputs=delete_output
        ).then(lambda: gr.update(value=""), outputs=converter_id_d)
    
    with gr.Tab("Lamp Management"):
        lamp_inputs = [
            gr.Textbox(label=label) for label in [
                "Converter ID", "Lamp Name", "Min Value", "Max Value"
            ]
        ]
        lamp_btns = [
            gr.Button("Add/Update Lamp"),
            gr.Button("Delete Lamp")
        ]
        lamp_output = gr.Textbox(label="Result")
        lamp_btns[0].click(
            add_or_update_lamp,
            inputs=lamp_inputs,
            outputs=lamp_output
        ).then(lambda: [gr.update(value="") for _ in lamp_inputs], outputs=lamp_inputs)
        lamp_btns[1].click(
            delete_lamp,
            inputs=lamp_inputs[:2],
            outputs=lamp_output
        ).then(lambda: [gr.update(value="") for _ in lamp_inputs[:2]], outputs=lamp_inputs[:2])
    
    with gr.Tab("View Converter"):
        converter_id_v = gr.Textbox(label="Converter ID")
        view_btn = gr.Button("View Converter")
        view_output = gr.Textbox(label="Converter Data", lines=10)
        view_btn.click(get_converter, inputs=converter_id_v, outputs=view_output)
    
    with gr.Tab("Converters Table"):
        filter_type = gr.Dropdown(
            choices=["Latest Added", "Latest Updated", "Deleted", "Price Change"],
            value="Latest Added",
            label="Filter Type"
        )
        n_latest = gr.Slider(1, 200, value=5, label="Number of Results")
        filter_btn = gr.Button("Apply Filter")
        lamp_table = gr.DataFrame(label="Converters")
        filter_btn.click(filter_lamps, inputs=[filter_type, n_latest], outputs=lamp_table)

if __name__ == "__main__":
    demo.launch()
