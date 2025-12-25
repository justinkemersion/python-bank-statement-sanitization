import PyPDF2
import os

class PDFHandler:
    def __init__(self):
        pass

    def extract_text(self, pdf_path):
        text_content = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    text_content += reader.pages[page_num].extract_text() or ""
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            return None
        return text_content

    def create_sanitized_pdf(self, original_pdf_path, sanitized_text, output_path):
        # For simplicity, this currently writes the sanitized text to a new TXT file with a .pdf extension.
        # A proper PDF sanitization would involve re-creating the PDF with redacted content,
        # which is significantly more complex and often requires a dedicated library for PDF manipulation (e.g., ReportLab, fpdf2, or commercial solutions).
        # For now, we will save the *text* content as a new file with the sanitized name.
        print(f"Creating (text-based) sanitized 'PDF' at: {output_path}")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(sanitized_text)
            print(f"Sanitized 'PDF' (text content) saved to: {output_path}")
        except Exception as e:
            print(f"Error saving sanitized 'PDF' (text content) to {output_path}: {e}")