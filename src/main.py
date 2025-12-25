import argparse
import os
from src.controllers.file_processor import FileProcessor
from src.models.sanitizer import Sanitizer
from src.models.pdf_handler import PDFHandler
from src.models.txt_handler import TXTHandler

def main():
    parser = argparse.ArgumentParser(description="Sanitize bank statements to remove sensitive information.")
    parser.add_argument("input_dir", help="Path to the directory containing bank statements.")
    parser.add_argument("-o", "--output_dir", help="Optional: Path to the output directory for sanitized files. Defaults to input directory.", default=None)
    args = parser.parse_args()

    input_directory = args.input_dir
    output_directory = args.output_dir if args.output_dir else input_directory

    if not os.path.isdir(input_directory):
        print(f"Error: Input directory '{input_directory}' not found or is not a directory.")
        return

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created output directory: {output_directory}")

    print(f"Processing files in directory: {input_directory}")
    print(f"Sanitized files will be saved to: {output_directory}")

    file_processor = FileProcessor(input_directory, output_directory)
    sanitizer = Sanitizer()
    pdf_handler = PDFHandler()
    txt_handler = TXTHandler()

    files_to_sanitize = file_processor.find_files_to_process()

    if not files_to_sanitize:
        print("No new files to sanitize found.")
        return

    for file_path in files_to_sanitize:
        print(f"\nProcessing file: {file_path}")
        base_name, ext = os.path.splitext(file_path)
        sanitized_filename = f"{os.path.basename(base_name)}-sanitized{ext}"
        sanitized_file_path = os.path.join(output_directory, sanitized_filename)

        if ext.lower() == '.pdf':
            text_content = pdf_handler.extract_text(file_path)
            if text_content is None:
                print(f"Error: Failed to extract text from {file_path}. Skipping.")
                continue
            sanitized_text = sanitizer.sanitize_text(text_content)
            if not pdf_handler.create_sanitized_pdf(file_path, sanitized_text, sanitized_file_path):
                print(f"Error: Failed to create sanitized PDF: {sanitized_file_path}")
                continue
        elif ext.lower() == '.txt':
            text_content = txt_handler.read_text(file_path)
            if text_content is None:
                print(f"Error: Failed to read text from {file_path}. Skipping.")
                continue
            sanitized_text = sanitizer.sanitize_text(text_content)
            if not txt_handler.save_sanitized_text(sanitized_text, sanitized_file_path):
                print(f"Error: Failed to save sanitized file: {sanitized_file_path}")
                continue
        else:
            print(f"Skipping unsupported file type: {file_path}")

    print("\nSanitization process complete.")

if __name__ == "__main__":
    main()