import os

class FileProcessor:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def find_files_to_process(self):
        files_to_sanitize = []
        for filename in os.listdir(self.input_dir):
            file_path = os.path.join(self.input_dir, filename)
            if os.path.isfile(file_path):
                # Check if a sanitized version of this file already exists in the output directory
                base_name, ext = os.path.splitext(filename)
                sanitized_filename_pdf = f"{base_name}-sanitized.pdf"
                sanitized_filename_txt = f"{base_name}-sanitized.txt"
                
                # If the current file is already a sanitized file, skip it.
                if filename.endswith("-sanitized.pdf") or filename.endswith("-sanitized.txt"):
                    continue

                # Check if a sanitized version (either PDF or TXT, regardless of original type) exists
                if os.path.exists(os.path.join(self.output_dir, sanitized_filename_pdf)) or \
                   os.path.exists(os.path.join(self.output_dir, sanitized_filename_txt)):
                    print(f"Skipping {filename}: Sanitized version already exists in output directory.")
                    continue
                
                files_to_sanitize.append(file_path)
        return files_to_sanitize