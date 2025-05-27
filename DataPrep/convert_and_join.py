import pdfplumber
import json
import re

# 1. Extract text and tables from PDF
def extract_text_and_tables(file_path):
    text = ""
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
            tables.extend(page.extract_tables())
    return {"text": text, "tables": tables}

# 2. Filter and organize sections by "converter" or "lamp"
def filter_sections(text, keywords=["converter", "lamp"]):
    # Compile regex to find section headers (adjust pattern as needed)
    # Example: "Converter XYZ" or "Lamp ABC"
    pattern = re.compile(r'^(Converter|Lamp)\s+[A-Za-z0-9]+', re.MULTILINE | re.IGNORECASE)
    matches = list(re.finditer(pattern, text))
    sections = []
    for i, match in enumerate(matches):
        start = match.start()
        if i + 1 < len(matches):
            end = matches[i+1].start()
        else:
            end = len(text)
        content = text[start:end].strip()
        sections.append({
            "type": match.group(0),
            "content": content
        })
    # Filter out sections not containing any keyword (optional, but already matched by pattern)
    # But if you want to be sure, uncomment:
    # filtered_sections = [
    #     s for s in sections
    #     if any(kw.lower() in s["type"].lower() or kw.lower() in s["content"].lower()
    #            for kw in keywords)
    # ]
    # return filtered_sections
    return sections

# 3. Main execution
pdf_path = '/Users/alessiacolumban/TAL_Chatbot/DataPrep/TAL 11 CATALOGUE 2024-2025.pdf'
extracted = extract_text_and_tables(pdf_path)

# Save raw text as JSON
with open('extracted_text.json', 'w', encoding='utf-8') as f:
    json.dump({"text": extracted["text"], "tables": extracted["tables"]}, f, ensure_ascii=False, indent=4)

# Filter and organize sections
filtered_sections = filter_sections(extracted["text"])

# Save filtered sections as JSON
with open('filtered_sections.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_sections, f, ensure_ascii=False, indent=4)

print("Raw text and tables saved to extracted_text.json")
print("Filtered and organized sections saved to filtered_sections.json")
