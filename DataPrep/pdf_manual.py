import pdfplumber
import json

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Example usage
pdf_path = '/Users/alessiacolumban/TAL_Chatbot/DataPrep/TAL 11 CATALOGUE 2024-2025.pdf'
extracted_text = extract_text_from_pdf(pdf_path)

# Save as JSON
output_data = {"text": extracted_text}
with open('extracted_text.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)
