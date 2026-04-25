import pdfplumber
import os

class PDFProcessor:
    """Extracts text and tables from PDF files."""
    
    def extract_text(self, pdf_path: str) -> str:
        """Extracts all text from a PDF, preserving basic layout."""
        text_content = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            return "\n\n".join(text_content)
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            return ""

    def extract_tables(self, pdf_path: str) -> list:
        """Extracts tables from a PDF as lists of lists."""
        all_tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        all_tables.append(table)
            return all_tables
        except Exception as e:
            print(f"Error extracting tables from {pdf_path}: {e}")
            return []

if __name__ == "__main__":
    # Test with a dummy file
    processor = PDFProcessor()
    # processor.extract_text("example.pdf")
