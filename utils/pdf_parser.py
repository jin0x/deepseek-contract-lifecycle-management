import fitz  # PyMuPDF
import pdfplumber
import pytesseract
import re
from pathlib import Path
from utils.helpers import get_logger

logger = get_logger(__name__)

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
            logger.info(f"Starting PDF parsing for file: {file}")
            text = self.extract_text_pdfplumber(file) or self.extract_text_pymupdf(file)
            logger.info(f"Initial text extraction length: {len(text) if text else 0} characters")

            # If no text found and OCR is enabled, try OCR
            if not text.strip() and use_ocr:
                logger.info("No text found, attempting OCR extraction")
                text = self.extract_text_ocr(file)
                logger.info(f"OCR extraction length: {len(text) if text else 0} characters")


            cleaned_text = self.clean_text(text)
            logger.info(f"Final cleaned text length: {len(cleaned_text)} characters")

            # Log a sample to understand content structure
            logger.debug(f"First 500 characters of cleaned text: {cleaned_text[:500]}")

            return cleaned_text
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}", exc_info=True)
            raise Exception(f"Error parsing PDF: {str(e)}")