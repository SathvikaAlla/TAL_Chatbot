import json
import gradio as gr
from typing import Dict, Any

JSON_PATH = "/Users/alessiacolumban/TAL_Chatbot/DataPrep/converters_with_links_and_pricelist.json"

def load_json() -> Dict[str, Any]:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data: Dict[str, Any]):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_converter(
    converter_id, converter_type, artnr, description, strain_relief, location, dimmability,
    ccr, size, efficiency, ip, class_, input_voltage, output_voltage, barcode, name,
    price, unit, lifecycle, pdf_link
):
    converter_id = converter_id.strip()
    data = load_json()
    if converter_id in data:
        return f"Converter '{converter_id}' already exists."
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
    # Only update fields that are not blank
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
    save_json(data)
    return f"Updated converter '{converter_id}'."

def delete_converter(converter_id):
    converter_id = converter_id.strip()
    data = load_json()
    if converter_id not in data:
        return f"Converter '{converter_id}' does not exist."
    del data[converter_id]
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
        )

    with gr.Tab("Delete Converter"):
        converter_id_d = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        delete_btn = gr.Button("Delete Converter")
        delete_output = gr.Textbox(label="Result")
        delete_btn.click(delete_converter, inputs=converter_id_d, outputs=delete_output)

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
        )

    with gr.Tab("View Converter"):
        converter_id_v = gr.Textbox(label="Converter ID (e.g. 350mA - 930537)")
        view_btn = gr.Button("View Converter")
        view_output = gr.Textbox(label="Converter Data", lines=10)
        view_btn.click(get_converter, inputs=converter_id_v, outputs=view_output)

if __name__ == "__main__":
    demo.launch()
