import fitz  # PyMuPDF
import pdfplumber
import pytesseract
import re
from pathlib import Path

class PDFParser:
    def __init__(self):
        pass

    def extract_text_pymupdf(self, file: Path) -> str:
        """Extract text using PyMuPDF"""
        doc = fitz.open(file)
        return "\n".join([page.get_text("text") for page in doc]).strip()

    def extract_text_pdfplumber(self, file: Path) -> str:
        """Extract text using pdfplumber"""
        text_list = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_list.append(text.strip())
        return "\n".join(text_list)

    def extract_text_ocr(self, file: Path) -> str:
        """Extract text using OCR"""
        with pdfplumber.open(file) as pdf:
            text_list = []
            for page in pdf.pages:
                image = page.to_image().original
                text = pytesseract.image_to_string(image, lang="eng")
                text_list.append(text.strip())
        return "\n".join(text_list)

    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"Page\s\d+|\d+\sPage", "", text)
        text = re.sub(r"[-]+\s*Signature\s*[-]+", "", text, flags=re.IGNORECASE)
        return text.strip()

    def parse_pdf(self, file: Path, use_ocr: bool = True) -> str:
        """Main method to parse PDF with fallback to OCR if needed"""
        try:
            # Try regular text extraction first
            text = self.extract_text_pdfplumber(file) or self.extract_text_pymupdf(file)

            # If no text found and OCR is enabled, try OCR
            if not text.strip() and use_ocr:
                text = self.extract_text_ocr(file)

            return self.clean_text(text)
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")