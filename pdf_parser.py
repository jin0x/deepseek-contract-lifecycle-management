import json
import re
from pathlib import Path
import pdfplumber
import pytesseract

class PDFParser:
    def __init__(self):
        pass

    def extract_text_pdfplumber(self, file: Path):
        text_list = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_list.append(text.strip())
        return "\n".join(text_list)

    def extract_text_ocr(self, file: Path):
        with pdfplumber.open(file) as pdf:
            text_list = []
            for page in pdf.pages:
                image = page.to_image().original
                text = pytesseract.image_to_string(image, lang="eng")
                text_list.append(text.strip())
        return "\n".join(text_list)

    def clean_text(self, text: str):
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"\s{2,}", " ", text)
        # Remove page nums.
        text = re.sub(r"Page\s\d+|\d+\sPage", "", text)
        # Remove signature
        text = re.sub(r"[-]+\s*Signature\s*[-]+", "", text, flags=re.IGNORECASE)
        return text.strip()

    def organize_clauses(self, text: str):
        lines = text.split("\n")
        clauses = []
        current_heading = None
        current_clause_lines = []

        def save_clause(heading, lines_list):
            clause_text = "\n".join(lines_list).strip()
            if not clause_text:
                return None
            # Extract dates-- amounts 
            related_dates = re.findall(date_pattern, clause_text)
            related_amounts = re.findall(amount_pattern, clause_text)
            return {
                "section": heading if heading else "Unnamed Clause",
                "clause_text": clause_text,
                "related_dates": related_dates if related_dates else [],
                "related_amounts": related_amounts if related_amounts else []
            }

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            match = heading_pattern.match(stripped_line)
            if match:
                clause = save_clause(current_heading, current_clause_lines)
                if clause:
                    clauses.append(clause)
                current_heading = match.group("heading").strip()
                remainder = stripped_line[match.end():].strip()
                current_clause_lines = [remainder] if remainder else []
            else:
                current_clause_lines.append(stripped_line)
        clause = save_clause(current_heading, current_clause_lines)
        if clause:
            clauses.append(clause)
        return clauses

    def organize_into_json(self, text: str, pdf_name: str) -> dict:
        clauses = self.organize_clauses(text)
        structured_data = {"pdf_name": pdf_name, "clauses": clauses}
        return structured_data

    def parse_pdf(self, file: Path, use_ocr=False) -> dict:
        try:
            
            text = self.extract_text_pdfplumber(file)
            ## try OCR.
            if not text and use_ocr:
                text = self.extract_text_ocr(file)
            text = self.clean_text(text)
            structured_data = self.organize_into_json(text, file.name)
            return structured_data
        except Exception as e:
            return {"error": str(e)}

### generic section names
SECTION_NAMES = [
    "EXHIBIT", "Parties", "Purpose", "Scope", "Payment Terms", 
    "Term", "Termination", "Governing Law", "Confidentiality"
]

# patterns for headings, dates, and amounts.
heading_pattern = re.compile(
    r"^(?P<heading>(" + "|".join(SECTION_NAMES) + r")(?:\s+\S+)?)[\s:]+", re.IGNORECASE
)
date_pattern = r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4})\b"
amount_pattern = r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?"


def get_text(file_path):
    parser = PDFParser()
    structured_output = parser.parse_pdf(Path(file_path), use_ocr=True)
    with open("parsed_content.json", "w", encoding="utf-8") as f:
        json.dump(structured_output, f, indent=4, ensure_ascii=False)
    return structured_output

# if __name__ == "__main__":
#     pdf_path = "sample_contracts/FreezeTagInc_20180411_8-K_EX-10.1_11139603_EX-10.1_Sponsorship Agreement.pdf"
#     parsed_data = get_text(pdf_path)
