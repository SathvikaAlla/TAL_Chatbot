import json
import gradio as gr
import pandas as pd
import datetime
import os
import uuid
from typing import Dict, Any
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# File paths
DATA_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"
META_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_metadata.json"

# Cosmos DB configuration from environment variables
COSMOS_ENDPOINT = os.getenv("AZURE_COSMOS_DB_ENDPOINT")
COSMOS_KEY = os.getenv("AZURE_COSMOS_DB_KEY")
DATABASE_NAME = os.getenv("AZURE_COSMOS_DB_DATABASE", "TAL")  # Default to TAL_DB
print(DATABASE_NAME)
CONTAINER_NAME = os.getenv("AZURE_COSMOS_DB_CONTAINER", "Converters")  # Default to Converters_with_embeddings

# Indexing policy
INDEXING_POLICY = {
    "indexingMode": "consistent",
    "includedPaths": [{"path": "/*"}],
    "excludedPaths": [
        {"path": "/\"_etag\"/?",
         "path": "/embedding/*"}
    ]
}

# Validate environment variables
if not all([COSMOS_ENDPOINT, COSMOS_KEY, DATABASE_NAME]):
    raise ValueError("Missing required Cosmos DB environment variables (AZURE_COSMOS_DB_ENDPOINT, AZURE_COSMOS_DB_KEY, AZURE_COSMOS_DB_DATABASE). Check .env file.")

# Initialize Cosmos DB client
try:
    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.create_database_if_not_exists(id=DATABASE_NAME)
    container = database.create_container_if_not_exists(
        id=CONTAINER_NAME,
        partition_key=PartitionKey(path="/artnr"),
        indexing_policy=INDEXING_POLICY,
        default_ttl=-1
    )
except exceptions.CosmosHttpResponseError as e:
    raise ValueError(f"Failed to initialize Cosmos DB client or create database/container: {str(e)}")

def load_json(path) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(data: Dict[str, Any], path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_current_time():
    return datetime.datetime.now().isoformat()

def transform_to_cosmos_format(converter_id: str, converter_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform converter data to match Cosmos DB document structure."""
    return {
        "id": str(uuid.uuid4()),  # Generate UUID for Cosmos DB
        "type": converter_data.get("TYPE", ""),
        "artnr": int(converter_data.get("ARTNR", 0)),
        "converter_description": converter_data.get("CONVERTER DESCRIPTION:", ""),
        "dimlist_type": converter_data.get("dimlist_type", ""),
        "strain_relief": converter_data.get("STRAIN RELIEF", ""),
        "location": converter_data.get("LOCATION", ""),
        "dimmability": converter_data.get("DIMMABILITY", ""),
        "ccr_(amplitude)": converter_data.get("CCR (AMPLITUDE)", ""),
        "size_l*b*h_(mm)": converter_data.get("SIZE: L*B*H (mm)", ""),
        "ip": float(converter_data.get("IP", 0)),
        "class": float(converter_data.get("CLASS", 0)),
        "barcode": converter_data.get("Barcode", ""),
        "name": converter_data.get("Name", ""),
        "listprice": float(converter_data.get("Listprice", 0)),
        "unit": converter_data.get("Unit", ""),
        "gross_weight": float(converter_data.get("gross_weight", 0)),
        "lifecycle": converter_data.get("LifeCycle", ""),
        "pdf_link": converter_data.get("pdf_link", ""),
        "lamps": converter_data.get("lamps", {}),
        "output_voltage": converter_data.get("OUTPUT VOLTAGE (V)", ""),
        "nom_input_voltage": converter_data.get("NOM. INPUT VOLTAGE (V)", ""),
        "efficiency_full_load": float(converter_data.get("EFFICIENCY @full load", 0))
    }

def sync_to_cosmos_db(converter_id: str, converter_data: Dict[str, Any], meta_data: Dict[str, Any], operation="upsert"):
    """Sync converter data to Cosmos DB with UUID and transformed format."""
    if operation == "delete":
        cosmos_id = meta_data.get("cosmos_id")
        if cosmos_id:
            try:
                # Use artnr as partition key value
                artnr = int(converter_data.get("ARTNR", 0)) if converter_data else 0
                container.delete_item(item=cosmos_id, partition_key=artnr)
            except CosmosResourceNotFoundError:
                print(f"Document with ID {cosmos_id} not found in Cosmos DB. Continuing deletion.")
            except exceptions.CosmosHttpResponseError as e:
                print(f"Error deleting document {cosmos_id}: {str(e)}")
                return False
        return True
    
    # Transform data to Cosmos DB format
    document = transform_to_cosmos_format(converter_id, converter_data)
    
    # Store the UUID in metadata
    meta_data["cosmos_id"] = document["id"]
    
    try:
        # Use artnr as partition key value
        doc = container.create_item(document)
        if doc:
            print(doc)
            print(container.read_item(item=doc["id"], partition_key=doc["artnr"]))
            return True
    except exceptions.CosmosHttpResponseError as e:
        print(f"Error syncing to Cosmos DB: {str(e)}")
        return False

def add_converter(
    converter_id, type_, artnr, converter_description, dimlist_type, strain_relief, location, dimmability,
    ccr_amplitude, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
    price, unit, gross_weight, lifecycle, pdf_link
):
    converter_id = converter_id.strip()
    data = load_json(DATA_PATH)
    meta = load_json(META_PATH)
    if converter_id in data:
        return f"Converter '{converter_id}' already exists."
    
    info = {
        "TYPE": type_ or "",
        "ARTNR": float(artnr) if artnr else 0,
        "CONVERTER DESCRIPTION:": converter_description or "",
        "dimlist_type": dimlist_type or "",
        "STRAIN RELIEF": strain_relief or "",
        "LOCATION": location or "",
        "DIMMABILITY": dimmability or "",
        "CCR (AMPLITUDE)": ccr_amplitude or "",
        "SIZE: L*B*H (mm)": size or "",
        "EFFICIENCY @full load": float(efficiency) if efficiency else 0,
        "IP": float(ip) if ip else 0,
        "CLASS": float(class_) if class_ else 0,
        "NOM. INPUT VOLTAGE (V)": input_voltage or "",
        "OUTPUT VOLTAGE (V)": output_voltage or "",
        "Barcode": barcode or "",
        "Name": name or "",
        "Listprice": float(price) if price else 0,
        "Unit": unit or "",
        "gross_weight": float(gross_weight) if gross_weight else 0,
        "LifeCycle": lifecycle or "",
        "pdf_link": pdf_link or "",
        "lamps": {}
    }
    
    data[converter_id] = info
    now = get_current_time()
    meta[converter_id] = {
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
        "price_history": [{"timestamp": now, "price": float(price)}] if price else [],
        "cosmos_id": None  # Will be updated after syncing
    }
    
    # Sync to Cosmos DB and update metadata with cosmos_id
    if sync_to_cosmos_db(converter_id, info, meta[converter_id]):
        # Save to JSON files
        save_json(data, DATA_PATH)
        save_json(meta, META_PATH)
        return f"Added converter '{converter_id}' and synced to Cosmos DB."
    else:
        return f"Failed to add converter '{converter_id}' to Cosmos DB."

def update_converter(
    converter_id, type_, artnr, converter_description, dimlist_type, strain_relief, location, dimmability,
    ccr_amplitude, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
    price, unit, gross_weight, lifecycle, pdf_link
):
    converter_id = converter_id.strip()
    data = load_json(DATA_PATH)
    meta = load_json(META_PATH)
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    
    info = data[converter_id]
    now = get_current_time()
    
    # Update fields if provided
    if type_: info["TYPE"] = type_
    if artnr: info["ARTNR"] = float(artnr)
    if converter_description: info["CONVERTER DESCRIPTION:"] = converter_description
    if dimlist_type: info["dimlist_type"] = dimlist_type
    if strain_relief: info["STRAIN RELIEF"] = strain_relief
    if location: info["LOCATION"] = location
    if dimmability: info["DIMMABILITY"] = dimmability
    if ccr_amplitude: info["CCR (AMPLITUDE)"] = ccr_amplitude
    if size: info["SIZE: L*B*H (mm)"] = size
    if efficiency: info["EFFICIENCY @full load"] = float(efficiency)
    if ip: info["IP"] = float(ip)
    if class_: info["CLASS"] = float(class_)
    if input_voltage: info["NOM. INPUT VOLTAGE (V)"] = input_voltage
    if output_voltage: info["OUTPUT VOLTAGE (V)"] = output_voltage
    if barcode: info["Barcode"] = barcode
    if name: info["Name"] = name
    if price:
        price = float(price)
        if "Listprice" not in info or price != info.get("Listprice"):
            if converter_id not in meta:
                meta[converter_id] = {
                    "created_at": now,
                    "updated_at": now,
                    "deleted_at": None,
                    "price_history": [],
                    "cosmos_id": None
                }
            if "price_history" not in meta[converter_id]:
                meta[converter_id]["price_history"] = []
            meta[converter_id]["price_history"].append({"timestamp": now, "price": price})
        info["Listprice"] = price
    if unit: info["Unit"] = unit
    if gross_weight: info["gross_weight"] = float(gross_weight)
    if lifecycle: info["LifeCycle"] = lifecycle
    if pdf_link: info["pdf_link"] = pdf_link
    
    # Update metadata
    if converter_id not in meta:
        meta[converter_id] = {
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
            "price_history": [],
            "cosmos_id": None
        }
    meta[converter_id]["updated_at"] = now
    
    # Compute new id
    new_type = info["TYPE"]
    new_artnr = int(info["ARTNR"])
    new_id = f"{new_type}mA - {new_artnr}"
    
    if new_id != converter_id:
        # Delete old Cosmos DB document
        sync_to_cosmos_db(converter_id, data[converter_id], meta[converter_id], operation="delete")
        data[new_id] = info
        meta[new_id] = meta.pop(converter_id)
        del data[converter_id]
        # Sync new document
        if sync_to_cosmos_db(new_id, info, meta[new_id]):
            save_json(data, DATA_PATH)
            save_json(meta, META_PATH)
            return f"Updated converter. ID changed to '{new_id}' and synced to Cosmos DB."
        else:
            return f"Failed to update converter to '{new_id}' in Cosmos DB."
    else:
        if sync_to_cosmos_db(converter_id, info, meta[converter_id]):
            data[converter_id] = info
            save_json(data, DATA_PATH)
            save_json(meta, META_PATH)
            return f"Updated converter '{converter_id}' and synced to Cosmos DB."
        else:
            return f"Failed to update converter '{converter_id}' in Cosmos DB."

def delete_converter(converter_id):
    converter_id = converter_id.strip()
    data = load_json(DATA_PATH)
    meta = load_json(META_PATH)
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    
    now = get_current_time()
    if converter_id not in meta:
        meta[converter_id] = {
            "created_at": None,
            "updated_at": now,
            "deleted_at": now,
            "price_history": [],
            "cosmos_id": None
        }
    else:
        meta[converter_id]["deleted_at"] = now
    
    # Delete from Cosmos DB
    sync_to_cosmos_db(converter_id, data[converter_id], meta[converter_id], operation="delete")
    
    del data[converter_id]
    save_json(data, DATA_PATH)
    save_json(meta, META_PATH)
    return f"Deleted converter '{converter_id}' and removed from Cosmos DB."

def add_or_update_lamp(converter_id, lamp_name, min_val, max_val):
    converter_id = converter_id.strip()
    lamp_name = lamp_name.strip()
    data = load_json(DATA_PATH)
    meta = load_json(META_PATH)
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    
    if "lamps" not in data[converter_id]:
        data[converter_id]["lamps"] = {}
    data[converter_id]["lamps"][lamp_name] = {"min": min_val, "max": max_val}
    
    # Update metadata
    now = get_current_time()
    if converter_id not in meta:
        meta[converter_id] = {
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
            "price_history": [],
            "cosmos_id": None
        }
    meta[converter_id]["updated_at"] = now
    
    # Sync to Cosmos DB
    if sync_to_cosmos_db(converter_id, data[converter_id], meta[converter_id]):
        save_json(data, DATA_PATH)
        save_json(meta, META_PATH)
        return f"Added/updated lamp '{lamp_name}' in converter '{converter_id}' and synced to Cosmos DB."
    else:
        return f"Failed to add/update lamp '{lamp_name}' in Cosmos DB."

def delete_lamp(converter_id, lamp_name):
    converter_id = converter_id.strip()
    lamp_name = lamp_name.strip()
    data = load_json(DATA_PATH)
    meta = load_json(META_PATH)
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    
    lamps = data[converter_id].get("lamps", {})
    if lamp_name not in lamps:
        return f"Lamp '{lamp_name}' does not exist in converter '{converter_id}'."
    
    del lamps[lamp_name]
    
    # Update metadata
    now = get_current_time()
    if converter_id not in meta:
        meta[converter_id] = {
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
            "price_history": [],
            "cosmos_id": None
        }
    meta[converter_id]["updated_at"] = now
    
    # Sync to Cosmos DB
    if sync_to_cosmos_db(converter_id, data[converter_id], meta[converter_id]):
        save_json(data, DATA_PATH)
        save_json(meta, META_PATH)
        return f"Deleted lamp '{lamp_name}' from converter '{converter_id}' and synced to Cosmos DB."
    else:
        return f"Failed to delete lamp '{lamp_name}' in Cosmos DB."

def get_converter(converter_id):
    converter_id = converter_id.strip()
    meta = load_json(META_PATH)
    cosmos_id = meta.get(converter_id, {}).get("cosmos_id")
    
    if cosmos_id:
        try:
            # Fetch from Cosmos DB using artnr as partition key
            data = load_json(DATA_PATH)
            artnr = int(data.get(converter_id, {}).get("ARTNR", 0))
            item = container.read_item(item=cosmos_id, partition_key=artnr)
            # Add metadata from local file
            item["metadata"] = meta.get(converter_id, {})
            return json.dumps(item, indent=2, ensure_ascii=False)
        except CosmosResourceNotFoundError:
            print(f"Document with ID {cosmos_id} not found in Cosmos DB. Falling back to local JSON.")
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error reading document {cosmos_id}: {str(e)}")
    
    # Fallback to local JSON
    data = load_json(DATA_PATH)
    item = data.get(converter_id, {})
    if item:
        item["metadata"] = meta.get(converter_id, {})
    return json.dumps(item, indent=2, ensure_ascii=False)

def filter_lamps(filter_type, n_latest):
    # Load local JSON files
    data = load_json(DATA_PATH)
    meta = load_json(META_PATH)
    records = []
    for cid, cinfo in data.items():
        m = meta.get(cid, {})
        created_at = m.get("created_at", "")
        updated_at = m.get("updated_at", "")
        deleted_at = m.get("deleted_at", None)
        price_history = m.get("price_history", [])
        price = cinfo.get("Listprice", "")
        lamps = cinfo.get("lamps", {})
        record = {
            "Converter ID": cid,
            "Created At": created_at,
            "Updated At": updated_at,
            "Deleted At": deleted_at,
            "Price": price,
            "Lamps": ", ".join(lamps.keys())
        }
        if filter_type == "Show All":
            records.append(record)
        elif filter_type == "Latest Added":
            if not deleted_at:
                records.append(record)
        elif filter_type == "Latest Updated":
            if not deleted_at:
                records.append(record)
        elif filter_type == "Deleted":
            if deleted_at:
                records.append(record)
        elif filter_type == "Price Change":
            if len(price_history) > 1:
                record["Price History"] = str(price_history)
                records.append(record)
    
    # Apply sorting and slicing
    if filter_type == "Latest Added":
        records = sorted(records, key=lambda x: x.get("Created At", ""), reverse=True)[:n_latest]
    elif filter_type == "Latest Updated":
        records = sorted(records, key=lambda x: x.get("Updated At", ""), reverse=True)[:n_latest]
    
    return pd.DataFrame(records)

# Gradio interface
with gr.Blocks(title="TAL Converter JSON Editor") as demo:
    gr.Markdown("# TAL Converter JSON Editor")

    with gr.Tab("Add Converter"):
        converter_id = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        type_ = gr.Textbox(label="Type")
        artnr = gr.Textbox(label="Article Number")
        converter_description = gr.Textbox(label="Converter Description")
        dimlist_type = gr.Textbox(label="Dimlist Type")
        strain_relief = gr.Textbox(label="Strain Relief")
        location = gr.Textbox(label="Location")
        dimmability = gr.Textbox(label="Dimmability")
        ccr_amplitude = gr.Textbox(label="CCR (Amplitude)")
        size = gr.Textbox(label="Size: L*B*H (mm)")
        efficiency = gr.Textbox(label="Efficiency @ Full Load")
        ip = gr.Textbox(label="IP")
        class_ = gr.Textbox(label="Class")
        input_voltage = gr.Textbox(label="Nominal Input Voltage (V)")
        output_voltage = gr.Textbox(label="Output Voltage (V)")
        barcode = gr.Textbox(label="Barcode")
        name = gr.Textbox(label="Name")
        price = gr.Textbox(label="List Price")
        unit = gr.Textbox(label="Unit")
        gross_weight = gr.Textbox(label="Gross Weight")
        lifecycle = gr.Textbox(label="Lifecycle")
        pdf_link = gr.Textbox(label="PDF Link")
        add_btn = gr.Button("Add Converter")
        add_output = gr.Textbox(label="Result")
        add_btn.click(
            add_converter,
            inputs=[
                converter_id, type_, artnr, converter_description, dimlist_type, strain_relief, location, dimmability,
                ccr_amplitude, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
                price, unit, gross_weight, lifecycle, pdf_link
            ],
            outputs=add_output
        ).then(
            lambda *args: [gr.update(value="") for _ in args],
            inputs=[
                converter_id, type_, artnr, converter_description, dimlist_type, strain_relief, location, dimmability,
                ccr_amplitude, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
                price, unit, gross_weight, lifecycle, pdf_link
            ],
            outputs=[
                converter_id, type_, artnr, converter_description, dimlist_type, strain_relief, location, dimmability,
                ccr_amplitude, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
                price, unit, gross_weight, lifecycle, pdf_link
            ]
        )

    with gr.Tab("Update Converter"):
        converter_id_u = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        type_u = gr.Textbox(label="Type")
        artnr_u = gr.Textbox(label="Article Number")
        converter_description_u = gr.Textbox(label="Converter Description")
        dimlist_type_u = gr.Textbox(label="Dimlist Type")
        strain_relief_u = gr.Textbox(label="Strain Relief")
        location_u = gr.Textbox(label="Location")
        dimmability_u = gr.Textbox(label="Dimmability")
        ccr_amplitude_u = gr.Textbox(label="CCR (Amplitude)")
        size_u = gr.Textbox(label="Size: L*B*H (mm)")
        efficiency_u = gr.Textbox(label="Efficiency @ Full Load")
        ip_u = gr.Textbox(label="IP")
        class_u = gr.Textbox(label="Class")
        input_voltage_u = gr.Textbox(label="Nominal Input Voltage (V)")
        output_voltage_u = gr.Textbox(label="Output Voltage (V)")
        barcode_u = gr.Textbox(label="Barcode")
        name_u = gr.Textbox(label="Name")
        price_u = gr.Textbox(label="List Price")
        unit_u = gr.Textbox(label="Unit")
        gross_weight_u = gr.Textbox(label="Gross Weight")
        lifecycle_u = gr.Textbox(label="Lifecycle")
        pdf_link_u = gr.Textbox(label="PDF Link")
        update_btn = gr.Button("Update Converter")
        update_output = gr.Textbox(label="Result")
        update_btn.click(
            update_converter,
            inputs=[
                converter_id_u, type_u, artnr_u, converter_description_u, dimlist_type_u, strain_relief_u, location_u, dimmability_u,
                ccr_amplitude_u, size_u, efficiency_u, ip_u, class_u, input_voltage_u, output_voltage_u, barcode_u, name_u,
                price_u, unit_u, gross_weight_u, lifecycle_u, pdf_link_u
            ],
            outputs=update_output
        ).then(
            lambda *args: [gr.update(value="") for _ in args],
            inputs=[
                converter_id_u, type_u, artnr_u, converter_description_u, dimlist_type_u, strain_relief_u, location_u, dimmability_u,
                ccr_amplitude_u, size_u, efficiency_u, ip_u, class_u, input_voltage_u, output_voltage_u, barcode_u, name_u,
                price_u, unit_u, gross_weight_u, lifecycle_u, pdf_link_u
            ],
            outputs=[
                converter_id_u, type_u, artnr_u, converter_description_u, dimlist_type_u, strain_relief_u, location_u, dimmability_u,
                ccr_amplitude_u, size_u, efficiency_u, ip_u, class_u, input_voltage_u, output_voltage_u, barcode_u, name_u,
                price_u, unit_u, gross_weight_u, lifecycle_u, pdf_link_u
            ]
        )

    with gr.Tab("Delete Converter"):
        converter_id_d = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        delete_btn = gr.Button("Delete Converter")
        delete_output = gr.Textbox(label="Result")
        delete_btn.click(
            delete_converter, 
            inputs=converter_id_d, 
            outputs=delete_output
        ).then(
            lambda _: gr.update(value=""),
            inputs=converter_id_d,
            outputs=converter_id_d
        )

    with gr.Tab("Add/Update Lamp"):
        converter_id_l = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        lamp_name = gr.Textbox(label="Lamp Name")
        min_val = gr.Textbox(label="Min")
        max_val = gr.Textbox(label="Max")
        lamp_btn = gr.Button("Add/Update Lamp")
        lamp_output = gr.Textbox(label="Result")
        lamp_btn.click(
            add_or_update_lamp,
            inputs=[converter_id_l, lamp_name, min_val, max_val],
            outputs=lamp_output
        ).then(
            lambda *args: [gr.update(value="") for _ in args],
            inputs=[converter_id_l, lamp_name, min_val, max_val],
            outputs=[converter_id_l, lamp_name, min_val, max_val]
        )

    with gr.Tab("Delete Lamp"):
        converter_id_ld = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        lamp_name_d = gr.Textbox(label="Lamp Name")
        lamp_delete_btn = gr.Button("Delete Lamp")
        lamp_delete_output = gr.Textbox(label="Result")
        lamp_delete_btn.click(
            delete_lamp,
            inputs=[converter_id_ld, lamp_name_d],
            outputs=lamp_delete_output
        ).then(
            lambda *args: [gr.update(value="") for _ in args],
            inputs=[converter_id_ld, lamp_name_d],
            outputs=[converter_id_ld, lamp_name_d]
        )

    with gr.Tab("View Converter"):
        converter_id_v = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        view_btn = gr.Button("View Converter")
        view_output = gr.Textbox(label="Converter Data", lines=10)
        view_btn.click(get_converter, inputs=converter_id_v, outputs=view_output)

    with gr.Tab("Converters Table & Filters"):
        filter_type = gr.Dropdown(
            choices=["Show All", "Latest Added", "Latest Updated", "Price Change"],
            value="Show All",
            label="Filter Type"
        )
        n_latest = gr.Slider(1, 20, value=5, step=1, label="How many (for latest)")
        lamp_table = gr.DataFrame(label="Converters Table", interactive=False, show_search="filter")
        filter_btn = gr.Button("Apply Filter")
        filter_btn.click(
            filter_lamps,
            inputs=[filter_type, n_latest],
            outputs=lamp_table
        )

if __name__ == "__main__":
    demo.launch()  # Run locally without sharing