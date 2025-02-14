import json
import re
from pathlib import Path
import fitz  # PyMuPDF
import pdfplumber
import pytesseract

class PDFParser:
    def __init__(self):
        pass

    def extract_text_pymupdf(self, file: Path) -> str:
        doc = fitz.open(file)
        return "\n".join([page.get_text("text") for page in doc]).strip()

    def extract_text_pdfplumber(self, file: Path) -> str:
        text_list = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_list.append(text.strip())
        return "\n".join(text_list)

    def extract_text_ocr(self, file: Path) -> str:
        with pdfplumber.open(file) as pdf:
            text_list = []
            for page in pdf.pages:
                image = page.to_image().original
                text = pytesseract.image_to_string(image, lang="eng")
                text_list.append(text.strip())
        return "\n".join(text_list)

    def clean_text(self, text: str) -> str:
        text = re.sub(r"\n{2,}", "\n", text)  # Remove excessive new lines
        text = re.sub(r"\s{2,}", " ", text)   # Remove extra spaces
        text = re.sub(r"Page\s\d+|\d+\sPage", "", text)  # Remove page numbers
        text = re.sub(r"[-]+\s*Signature\s*[-]+", "", text, flags=re.IGNORECASE)  # Remove signature labels
        return text.strip()

    def organize_into_clauses(self, text: str) -> list:
        clauses = re.split(r"\n(?=\d+\.)", text)  # Split on numbered clauses
        return [{"id": i + 1, "text": clause.strip()} for i, clause in enumerate(clauses) if clause.strip()]

    def parse_pdf(self, file: Path, use_ocr=False) -> dict:
        try:
            text = self.extract_text_pdfplumber(file) or self.extract_text_pymupdf(file)
            if not text and use_ocr:
                text = self.extract_text_ocr(file)

            text = self.clean_text(text)
            clauses = self.organize_into_clauses(text)
            
            return {"pdf_name": file.name, "clauses": clauses}
        except Exception as e:
            return {"error": str(e)}


def get_text(file_path):
    parser = PDFParser()
    structured_output = parser.parse_pdf(Path(file_path), use_ocr=True)
    
    with open("parsed_output.json", "w", encoding="utf-8") as f:
        json.dump(structured_output, f, indent=4, ensure_ascii=False)

    return structured_output


if __name__ == "__main__":
    pdf_path = "EmmisCommunicationsCorp_20191125_8-K_EX-10.6_11906433_EX-10.6_Marketing Agreement.pdf"
    parsed_data = get_text(pdf_path)
    print(json.dumps(parsed_data, indent=4))
