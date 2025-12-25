import os

class FileProcessor:
    # Supported file extensions
    SUPPORTED_EXTENSIONS = {'.pdf', '.txt', '.csv', '.xlsx', '.xls'}
    
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def find_files_to_process(self):
        """Find all supported files in the input directory that need to be processed.
        
        Returns:
            list: List of file paths to sanitize
        """
        files_to_sanitize = []
        try:
            for filename in os.listdir(self.input_dir):
                file_path = os.path.join(self.input_dir, filename)
                if not os.path.isfile(file_path):
                    continue
                
                # Get file extension
                base_name, ext = os.path.splitext(filename)
                ext_lower = ext.lower()
                
                # Only process supported file types
                if ext_lower not in self.SUPPORTED_EXTENSIONS:
                    continue
                
                # If the current file is already a sanitized file, skip it.
                if filename.endswith("-sanitized.pdf") or filename.endswith("-sanitized.txt"):
                    continue

                # Check if a sanitized version of the SAME file type exists
                sanitized_filename = f"{base_name}-sanitized{ext_lower}"
                sanitized_file_path = os.path.join(self.output_dir, sanitized_filename)
                if os.path.exists(sanitized_file_path):
                    print(f"Skipping {filename}: Sanitized version already exists in output directory.")
                    continue
                
                files_to_sanitize.append(file_path)
        except PermissionError:
            print(f"Error: Permission denied when accessing directory: {self.input_dir}")
        except Exception as e:
            print(f"Error scanning directory {self.input_dir}: {e}")
        
        return files_to_sanitize