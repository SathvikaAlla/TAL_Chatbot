# import json
# import gradio as gr
# from typing import Dict, Any

# JSON_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"

# def load_json() -> Dict[str, Any]:
#     with open(JSON_PATH, "r", encoding="utf-8") as f:
#         return json.load(f)

# def save_json(data: Dict[str, Any]):
#     with open(JSON_PATH, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)

# def add_converter(
#     converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
#     ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
#     price, unit, lifecycle, pdf_link
# ):
#     converter_id = converter_id.strip()
#     data = load_json()
#     if converter_id in data:
#         return f"Converter '{converter_id}' already exists."
#     info = {}
#     if converter_type: info["TYPE"] = converter_type
#     if artnr: info["ARTNR"] = float(artnr)
#     if description: info["CONVERTER DESCRIPTION:"] = description
#     if strain_relief: info["STRAIN RELIEF"] = strain_relief
#     if location: info["LOCATION"] = location
#     if dimmability: info["DIMMABILITY"] = dimmability
#     if ccr: info["CCR (AMPLITUDE)"] = ccr
#     if size: info["SIZE: L*B*H (mm)"] = size
#     if efficiency: info["EFFICIENCY @full load"] = float(efficiency)
#     if ip: info["IP"] = float(ip)
#     if class_: info["CLASS"] = float(class_)
#     if input_voltage: info["NOM. INPUT VOLTAGE (V)"] = input_voltage
#     if output_voltage: info["OUTPUT VOLTAGE (V)"] = output_voltage
#     if barcode: info["Barcode"] = barcode
#     if name: info["Name"] = name
#     if price: info["Listprice"] = float(price)
#     if unit: info["Unit"] = unit
#     if lifecycle: info["LifeCycle"] = lifecycle
#     if pdf_link: info["pdf_link"] = pdf_link
#     info["lamps"] = {}
#     data[converter_id] = info
#     save_json(data)
#     return f"Added converter '{converter_id}'."

# def update_converter(
#     converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
#     ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
#     price, unit, lifecycle, pdf_link
# ):
#     converter_id = converter_id.strip()
#     data = load_json()
#     if converter_id not in data:
#         return f"Converter '{converter_id}' does not exist."
#     info = data[converter_id]
#     # Update fields if provided
#     if converter_type: info["TYPE"] = converter_type
#     if artnr: info["ARTNR"] = float(artnr)
#     if description: info["CONVERTER DESCRIPTION:"] = description
#     if strain_relief: info["STRAIN RELIEF"] = strain_relief
#     if location: info["LOCATION"] = location
#     if dimmability: info["DIMMABILITY"] = dimmability
#     if ccr: info["CCR (AMPLITUDE)"] = ccr
#     if size: info["SIZE: L*B*H (mm)"] = size
#     if efficiency: info["EFFICIENCY @full load"] = float(efficiency)
#     if ip: info["IP"] = float(ip)
#     if class_: info["CLASS"] = float(class_)
#     if input_voltage: info["NOM. INPUT VOLTAGE (V)"] = input_voltage
#     if output_voltage: info["OUTPUT VOLTAGE (V)"] = output_voltage
#     if barcode: info["Barcode"] = barcode
#     if name: info["Name"] = name
#     if price: info["Listprice"] = float(price)
#     if unit: info["Unit"] = unit
#     if lifecycle: info["LifeCycle"] = lifecycle
#     if pdf_link: info["pdf_link"] = pdf_link

#     # Compute new id
#     new_type = info["TYPE"]
#     new_artnr = int(info["ARTNR"])
#     new_id = f"{new_type}mA - {new_artnr}"

#     # Only update key if it has changed
#     if new_id != converter_id:
#         data[new_id] = info
#         del data[converter_id]
#         save_json(data)
#         return f"Updated converter. ID changed to '{new_id}'."
#     else:
#         data[converter_id] = info
#         save_json(data)
#         return f"Updated converter '{converter_id}'."

# def delete_converter(converter_id):
#     converter_id = converter_id.strip()
#     data = load_json()
#     if converter_id not in data:
#         return f"Converter '{converter_id}' does not exist."
#     del data[converter_id]
#     save_json(data)
#     return f"Deleted converter '{converter_id}'."

# def add_or_update_lamp(converter_id, lamp_name, min_val, max_val):
#     converter_id = converter_id.strip()
#     lamp_name = lamp_name.strip()
#     data = load_json()
#     if converter_id not in data:
#         return f"Converter '{converter_id}' does not exist."
#     if "lamps" not in data[converter_id]:
#         data[converter_id]["lamps"] = {}
#     data[converter_id]["lamps"][lamp_name] = {"min": min_val, "max": max_val}
#     save_json(data)
#     return f"Added/updated lamp '{lamp_name}' in converter '{converter_id}'."

# def delete_lamp(converter_id, lamp_name):
#     converter_id = converter_id.strip()
#     lamp_name = lamp_name.strip()
#     data = load_json()
#     if converter_id not in data:
#         return f"Converter '{converter_id}' does not exist."
#     lamps = data[converter_id].get("lamps", {})
#     if lamp_name not in lamps:
#         return f"Lamp '{lamp_name}' does not exist in converter '{converter_id}'."
#     del lamps[lamp_name]
#     save_json(data)
#     return f"Deleted lamp '{lamp_name}' from converter '{converter_id}'."

# def get_converter(converter_id):
#     converter_id = converter_id.strip()
#     data = load_json()
#     return json.dumps(data.get(converter_id, {}), indent=2, ensure_ascii=False)

# with gr.Blocks(title="TAL Converter JSON Editor") as demo:
#     gr.Markdown("# TAL Converter JSON Editor")

#     with gr.Tab("Add Converter"):
#         converter_id = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
#         converter_type = gr.Textbox(label="TYPE")
#         artnr = gr.Textbox(label="ARTNR")
#         description = gr.Textbox(label="CONVERTER DESCRIPTION:")
#         strain_relief = gr.Textbox(label="STRAIN RELIEF")
#         location = gr.Textbox(label="LOCATION")
#         dimmability = gr.Textbox(label="DIMMABILITY")
#         ccr = gr.Textbox(label="CCR (AMPLITUDE)")
#         size = gr.Textbox(label="SIZE: L*B*H (mm)")
#         efficiency = gr.Textbox(label="EFFICIENCY @full load")
#         ip = gr.Textbox(label="IP")
#         class_ = gr.Textbox(label="CLASS")
#         input_voltage = gr.Textbox(label="NOM. INPUT VOLTAGE (V)")
#         output_voltage = gr.Textbox(label="OUTPUT VOLTAGE (V)")
#         barcode = gr.Textbox(label="Barcode")
#         name = gr.Textbox(label="Name")
#         price = gr.Textbox(label="Listprice")
#         unit = gr.Textbox(label="Unit")
#         lifecycle = gr.Textbox(label="LifeCycle")
#         pdf_link = gr.Textbox(label="pdf_link")
#         add_btn = gr.Button("Add Converter")
#         add_output = gr.Textbox(label="Result")
#         add_btn.click(
#             add_converter,
#             inputs=[
#                 converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
#                 ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
#                 price, unit, lifecycle, pdf_link
#             ],
#             outputs=add_output
#         ).then(
#             lambda *args: [gr.update(value="") for _ in args],
#             inputs=[
#                 converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
#                 ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
#                 price, unit, lifecycle, pdf_link
#             ],
#             outputs=[
#                 converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
#                 ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
#                 price, unit, lifecycle, pdf_link
#             ]
#         )

#     with gr.Tab("Update Converter"):
#         converter_id_u = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
#         converter_type_u = gr.Textbox(label="TYPE")
#         artnr_u = gr.Textbox(label="ARTNR")
#         description_u = gr.Textbox(label="CONVERTER DESCRIPTION:")
#         strain_relief_u = gr.Textbox(label="STRAIN RELIEF")
#         location_u = gr.Textbox(label="LOCATION")
#         dimmability_u = gr.Textbox(label="DIMMABILITY")
#         ccr_u = gr.Textbox(label="CCR (AMPLITUDE)")
#         size_u = gr.Textbox(label="SIZE: L*B*H (mm)")
#         efficiency_u = gr.Textbox(label="EFFICIENCY @full load")
#         ip_u = gr.Textbox(label="IP")
#         class_u = gr.Textbox(label="CLASS")
#         input_voltage_u = gr.Textbox(label="NOM. INPUT VOLTAGE (V)")
#         output_voltage_u = gr.Textbox(label="OUTPUT VOLTAGE (V)")
#         barcode_u = gr.Textbox(label="Barcode")
#         name_u = gr.Textbox(label="Name")
#         price_u = gr.Textbox(label="Listprice")
#         unit_u = gr.Textbox(label="Unit")
#         lifecycle_u = gr.Textbox(label="LifeCycle")
#         pdf_link_u = gr.Textbox(label="pdf_link")
#         update_btn = gr.Button("Update Converter")
#         update_output = gr.Textbox(label="Result")
#         update_btn.click(
#             update_converter,
#             inputs=[
#                 converter_id_u, converter_type_u, artnr_u, description_u, strain_relief_u, location_u, dimmability_u,
#                 ccr_u, size_u, efficiency_u, ip_u, class_u, input_voltage_u, output_voltage_u, barcode_u, name_u,
#                 price_u, unit_u, lifecycle_u, pdf_link_u
#             ],
#             outputs=update_output
#         ).then(
#             lambda *args: [gr.update(value="") for _ in args],
#             inputs=[
#                 converter_id_u, converter_type_u, artnr_u, description_u, strain_relief_u, location_u, dimmability_u,
#                 ccr_u, size_u, efficiency_u, ip_u, class_u, input_voltage_u, output_voltage_u, barcode_u, name_u,
#                 price_u, unit_u, lifecycle_u, pdf_link_u
#             ],
#             outputs=[
#                 converter_id_u, converter_type_u, artnr_u, description_u, strain_relief_u, location_u, dimmability_u,
#                 ccr_u, size_u, efficiency_u, ip_u, class_u, input_voltage_u, output_voltage_u, barcode_u, name_u,
#                 price_u, unit_u, lifecycle_u, pdf_link_u
#             ]
#         )

#     with gr.Tab("Delete Converter"):
#         converter_id_d = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
#         delete_btn = gr.Button("Delete Converter")
#         delete_output = gr.Textbox(label="Result")
#         delete_btn.click(
#             delete_converter, 
#             inputs=converter_id_d, 
#             outputs=delete_output
#         ).then(
#             lambda _: gr.update(value=""),
#             inputs=converter_id_d,
#             outputs=converter_id_d
#         )

#     with gr.Tab("Add/Update Lamp"):
#         converter_id_l = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
#         lamp_name = gr.Textbox(label="Lamp Name")
#         min_val = gr.Textbox(label="Min")
#         max_val = gr.Textbox(label="Max")
#         lamp_btn = gr.Button("Add/Update Lamp")
#         lamp_output = gr.Textbox(label="Result")
#         lamp_btn.click(
#             add_or_update_lamp,
#             inputs=[converter_id_l, lamp_name, min_val, max_val],
#             outputs=lamp_output
#         ).then(
#             lambda *args: [gr.update(value="") for _ in args],
#             inputs=[converter_id_l, lamp_name, min_val, max_val],
#             outputs=[converter_id_l, lamp_name, min_val, max_val]
#         )

#     with gr.Tab("Delete Lamp"):
#         converter_id_ld = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
#         lamp_name_d = gr.Textbox(label="Lamp Name")
#         lamp_delete_btn = gr.Button("Delete Lamp")
#         lamp_delete_output = gr.Textbox(label="Result")
#         lamp_delete_btn.click(
#             delete_lamp,
#             inputs=[converter_id_ld, lamp_name_d],
#             outputs=lamp_delete_output
#         ).then(
#             lambda *args: [gr.update(value="") for _ in args],
#             inputs=[converter_id_ld, lamp_name_d],
#             outputs=[converter_id_ld, lamp_name_d]
#         )

#     with gr.Tab("View Converter"):
#         converter_id_v = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
#         view_btn = gr.Button("View Converter")
#         view_output = gr.Textbox(label="Converter Data", lines=10)
#         view_btn.click(get_converter, inputs=converter_id_v, outputs=view_output)

# if __name__ == "__main__":
#     demo.launch()


import json
import gradio as gr
import pandas as pd
import datetime
from typing import Dict, Any

JSON_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"

def load_json() -> Dict[str, Any]:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: Dict[str, Any]):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
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
    if converter_id in data:
        return f"Converter '{converter_id}' already exists."
    now = get_current_time()
    info = {}
    if converter_type: info["TYPE"] = converter_type
    if artnr: info["ARTNR"] = float(artnr)
    if description: info["CONVERTER DESCRIPTION:"] = description
    if strain_relief: info["STRAIN RELIEF"] = strain_relief
    if location: info["LOCATION"] = location
    if dimmability: info["DIMMABILITY"] = dimmability
    if ccr: info["CCR (AMPLITUDE)"] = ccr
    if size: info["SIZE: L*B*H (mm)"] = size
    if efficiency: info["EFFICIENCY @full load"] = float(efficiency)
    if ip: info["IP"] = float(ip)
    if class_: info["CLASS"] = float(class_)
    if input_voltage: info["NOM. INPUT VOLTAGE (V)"] = input_voltage
    if output_voltage: info["OUTPUT VOLTAGE (V)"] = output_voltage
    if barcode: info["Barcode"] = barcode
    if name: info["Name"] = name
    if price: info["Listprice"] = float(price)
    if unit: info["Unit"] = unit
    if lifecycle: info["LifeCycle"] = lifecycle
    if pdf_link: info["pdf_link"] = pdf_link
    info["lamps"] = {}
    info["created_at"] = now
    info["updated_at"] = now
    info["deleted_at"] = None
    info["price_history"] = [{"timestamp": now, "price": float(price)}] if price else []
    data[converter_id] = info
    save_json(data)
    return f"Added converter '{converter_id}'."

def update_converter(
    converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
    ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
    price, unit, lifecycle, pdf_link
):
    converter_id = converter_id.strip()
    data = load_json()
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    info = data[converter_id]
    now = get_current_time()
    # Update fields if provided
    if converter_type: info["TYPE"] = converter_type
    if artnr: info["ARTNR"] = float(artnr)
    if description: info["CONVERTER DESCRIPTION:"] = description
    if strain_relief: info["STRAIN RELIEF"] = strain_relief
    if location: info["LOCATION"] = location
    if dimmability: info["DIMMABILITY"] = dimmability
    if ccr: info["CCR (AMPLITUDE)"] = ccr
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
            if "price_history" not in info:
                info["price_history"] = []
            info["price_history"].append({"timestamp": now, "price": price})
        info["Listprice"] = price
    if unit: info["Unit"] = unit
    if lifecycle: info["LifeCycle"] = lifecycle
    if pdf_link: info["pdf_link"] = pdf_link
    info["updated_at"] = now

    # Compute new id
    new_type = info["TYPE"]
    new_artnr = int(info["ARTNR"])
    new_id = f"{new_type}mA - {new_artnr}"

    # Only update key if it has changed
    if new_id != converter_id:
        data[new_id] = info
        del data[converter_id]
        save_json(data)
        return f"Updated converter. ID changed to '{new_id}'."
    else:
        data[converter_id] = info
        save_json(data)
        return f"Updated converter '{converter_id}'."

def delete_converter(converter_id):
    converter_id = converter_id.strip()
    data = load_json()
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    now = get_current_time()
    if "deleted_at" in data[converter_id]:
        data[converter_id]["deleted_at"] = now
    else:
        data[converter_id].update({"deleted_at": now})
    save_json(data)
    return f"Deleted converter '{converter_id}'."

def add_or_update_lamp(converter_id, lamp_name, min_val, max_val):
    converter_id = converter_id.strip()
    lamp_name = lamp_name.strip()
    data = load_json()
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    if "lamps" not in data[converter_id]:
        data[converter_id]["lamps"] = {}
    data[converter_id]["lamps"][lamp_name] = {"min": min_val, "max": max_val}
    save_json(data)
    return f"Added/updated lamp '{lamp_name}' in converter '{converter_id}'."

def delete_lamp(converter_id, lamp_name):
    converter_id = converter_id.strip()
    lamp_name = lamp_name.strip()
    data = load_json()
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    lamps = data[converter_id].get("lamps", {})
    if lamp_name not in lamps:
        return f"Lamp '{lamp_name}' does not exist in converter '{converter_id}'."
    del lamps[lamp_name]
    save_json(data)
    return f"Deleted lamp '{lamp_name}' from converter '{converter_id}'."

def get_converter(converter_id):
    converter_id = converter_id.strip()
    data = load_json()
    return json.dumps(data.get(converter_id, {}), indent=2, ensure_ascii=False)

def filter_lamps(filter_type, n_latest):
    data = load_json()
    records = []
    for cid, cinfo in data.items():
        # Handle missing metadata for legacy entries
        created_at = cinfo.get("created_at", "")
        updated_at = cinfo.get("updated_at", "")
        deleted_at = cinfo.get("deleted_at", None)
        price = cinfo.get("Listprice", "")
        lamps = cinfo.get("lamps", {})
        price_history = cinfo.get("price_history", [])
        if filter_type == "Latest Added":
            if not deleted_at:
                records.append({
                    "Converter ID": cid,
                    "Created At": created_at,
                    "Updated At": updated_at,
                    "Price": price,
                    "Lamps": ", ".join(lamps.keys())
                })
        elif filter_type == "Latest Updated":
            if not deleted_at:
                records.append({
                    "Converter ID": cid,
                    "Created At": created_at,
                    "Updated At": updated_at,
                    "Price": price,
                    "Lamps": ", ".join(lamps.keys())
                })
        elif filter_type == "Deleted":
            if deleted_at:
                records.append({
                    "Converter ID": cid,
                    "Deleted At": deleted_at,
                    "Price": price,
                    "Lamps": ", ".join(lamps.keys())
                })
        elif filter_type == "Price Change":
            if len(price_history) > 1:
                records.append({
                    "Converter ID": cid,
                    "Price History": str(price_history),
                    "Current Price": price,
                    "Lamps": ", ".join(lamps.keys())
                })
    # Sort and limit
    if filter_type == "Latest Added":
        records = sorted(records, key=lambda x: x.get("Created At", ""), reverse=True)[:n_latest]
    elif filter_type == "Latest Updated":
        records = sorted(records, key=lambda x: x.get("Updated At", ""), reverse=True)[:n_latest]
    df = pd.DataFrame(records)
    return df

with gr.Blocks(title="TAL Converter JSON Editor") as demo:
    gr.Markdown("# TAL Converter JSON Editor")

    with gr.Tab("Add Converter"):
        converter_id = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        converter_type = gr.Textbox(label="TYPE")
        artnr = gr.Textbox(label="ARTNR")
        description = gr.Textbox(label="CONVERTER DESCRIPTION:")
        strain_relief = gr.Textbox(label="STRAIN RELIEF")
        location = gr.Textbox(label="LOCATION")
        dimmability = gr.Textbox(label="DIMMABILITY")
        ccr = gr.Textbox(label="CCR (AMPLITUDE)")
        size = gr.Textbox(label="SIZE: L*B*H (mm)")
        efficiency = gr.Textbox(label="EFFICIENCY @full load")
        ip = gr.Textbox(label="IP")
        class_ = gr.Textbox(label="CLASS")
        input_voltage = gr.Textbox(label="NOM. INPUT VOLTAGE (V)")
        output_voltage = gr.Textbox(label="OUTPUT VOLTAGE (V)")
        barcode = gr.Textbox(label="Barcode")
        name = gr.Textbox(label="Name")
        price = gr.Textbox(label="Listprice")
        unit = gr.Textbox(label="Unit")
        lifecycle = gr.Textbox(label="LifeCycle")
        pdf_link = gr.Textbox(label="pdf_link")
        add_btn = gr.Button("Add Converter")
        add_output = gr.Textbox(label="Result")
        add_btn.click(
            add_converter,
            inputs=[
                converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
                ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
                price, unit, lifecycle, pdf_link
            ],
            outputs=add_output
        ).then(
            lambda *args: [gr.update(value="") for _ in args],
            inputs=[
                converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
                ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
                price, unit, lifecycle, pdf_link
            ],
            outputs=[
                converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
                ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
                price, unit, lifecycle, pdf_link
            ]
        )

    with gr.Tab("Update Converter"):
        converter_id_u = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        converter_type_u = gr.Textbox(label="TYPE")
        artnr_u = gr.Textbox(label="ARTNR")
        description_u = gr.Textbox(label="CONVERTER DESCRIPTION:")
        strain_relief_u = gr.Textbox(label="STRAIN RELIEF")
        location_u = gr.Textbox(label="LOCATION")
        dimmability_u = gr.Textbox(label="DIMMABILITY")
        ccr_u = gr.Textbox(label="CCR (AMPLITUDE)")
        size_u = gr.Textbox(label="SIZE: L*B*H (mm)")
        efficiency_u = gr.Textbox(label="EFFICIENCY @full load")
        ip_u = gr.Textbox(label="IP")
        class_u = gr.Textbox(label="CLASS")
        input_voltage_u = gr.Textbox(label="NOM. INPUT VOLTAGE (V)")
        output_voltage_u = gr.Textbox(label="OUTPUT VOLTAGE (V)")
        barcode_u = gr.Textbox(label="Barcode")
        name_u = gr.Textbox(label="Name")
        price_u = gr.Textbox(label="Listprice")
        unit_u = gr.Textbox(label="Unit")
        lifecycle_u = gr.Textbox(label="LifeCycle")
        pdf_link_u = gr.Textbox(label="pdf_link")
        update_btn = gr.Button("Update Converter")
        update_output = gr.Textbox(label="Result")
        update_btn.click(
            update_converter,
            inputs=[
                converter_id_u, converter_type_u, artnr_u, description_u, strain_relief_u, location_u, dimmability_u,
                ccr_u, size_u, efficiency_u, ip_u, class_u, input_voltage_u, output_voltage_u, barcode_u, name_u,
                price_u, unit_u, lifecycle_u, pdf_link_u
            ],
            outputs=update_output
        ).then(
            lambda *args: [gr.update(value="") for _ in args],
            inputs=[
                converter_id_u, converter_type_u, artnr_u, description_u, strain_relief_u, location_u, dimmability_u,
                ccr_u, size_u, efficiency_u, ip_u, class_u, input_voltage_u, output_voltage_u, barcode_u, name_u,
                price_u, unit_u, lifecycle_u, pdf_link_u
            ],
            outputs=[
                converter_id_u, converter_type_u, artnr_u, description_u, strain_relief_u, location_u, dimmability_u,
                ccr_u, size_u, efficiency_u, ip_u, class_u, input_voltage_u, output_voltage_u, barcode_u, name_u,
                price_u, unit_u, lifecycle_u, pdf_link_u
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
            choices=["Latest Added", "Latest Updated", "Deleted", "Price Change"],
            value="Latest Added",
            label="Filter Type"
        )
        n_latest = gr.Slider(1, 20, value=5, label="How many (for latest)")
        lamp_table = gr.DataFrame(label="Converters Table", interactive=False, show_search="filter")
        filter_btn = gr.Button("Apply Filter")
        filter_btn.click(
            filter_lamps,
            inputs=[filter_type, n_latest],
            outputs=lamp_table
        )

if __name__ == "__main__":
    demo.launch()
