import PyPDF2
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT

class PDFHandler:
    def __init__(self):
        pass

    def extract_text(self, pdf_path):
        """Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file to extract text from
            
        Returns:
            str: The extracted text content, or None if an error occurs
        """
        text_content = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    text_content += reader.pages[page_num].extract_text() or ""
        except FileNotFoundError:
            print(f"Error: PDF file not found: {pdf_path}")
            return None
        except PermissionError:
            print(f"Error: Permission denied when reading PDF: {pdf_path}")
            return None
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            return None
        return text_content

    def create_sanitized_pdf(self, original_pdf_path, sanitized_text, output_path):
        """Create a new PDF file with sanitized text content.
        
        This creates a proper PDF document (not just text with a .pdf extension)
        using the reportlab library. The sanitized text is formatted and added
        to the PDF with proper page breaks.
        
        Args:
            original_pdf_path: Path to the original PDF (for reference, not used)
            sanitized_text: The sanitized text content to include in the PDF
            output_path: Path where the sanitized PDF should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Creating sanitized PDF at: {output_path}")
        try:
            # Create a PDF document
            doc = SimpleDocTemplate(output_path, pagesize=letter,
                                    rightMargin=72, leftMargin=72,
                                    topMargin=72, bottomMargin=18)
            
            # Container for the 'Flowable' objects
            story = []
            
            # Define styles
            styles = getSampleStyleSheet()
            normal_style = styles['Normal']
            normal_style.alignment = TA_LEFT
            normal_style.fontSize = 10
            normal_style.leading = 12
            
            # Split text into paragraphs and add to story
            paragraphs = sanitized_text.split('\n')
            for para_text in paragraphs:
                if para_text.strip():  # Skip empty lines
                    para = Paragraph(para_text, normal_style)
                    story.append(para)
                    story.append(Spacer(1, 6))  # Small spacing between paragraphs
                else:
                    story.append(Spacer(1, 6))  # Extra spacing for empty lines
            
            # Build the PDF
            doc.build(story)
            print(f"Sanitized PDF saved to: {output_path}")
            return True
        except PermissionError:
            print(f"Error: Permission denied when writing PDF to: {output_path}")
            return False
        except OSError as e:
            print(f"Error: Unable to write PDF to {output_path}: {e}")
            return False
        except Exception as e:
            print(f"Error creating sanitized PDF at {output_path}: {e}")
            return False