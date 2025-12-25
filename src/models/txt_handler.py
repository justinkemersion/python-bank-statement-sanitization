# src/models/txt_handler.py

class TXTHandler:
    def __init__(self):
        pass

    def read_text(self, txt_path):
        """Read text content from a TXT file with UTF-8 encoding.
        
        Args:
            txt_path: Path to the text file to read
            
        Returns:
            str: The text content of the file, or None if an error occurs
        """
        print(f"Reading text from TXT: {txt_path}")
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            print(f"Error: File not found: {txt_path}")
            return None
        except PermissionError:
            print(f"Error: Permission denied when reading: {txt_path}")
            return None
        except UnicodeDecodeError as e:
            print(f"Error: Unable to decode file {txt_path} as UTF-8: {e}")
            return None
        except Exception as e:
            print(f"Error reading text from {txt_path}: {e}")
            return None

    def save_sanitized_text(self, sanitized_text, output_path):
        """Save sanitized text to a TXT file with UTF-8 encoding.
        
        Args:
            sanitized_text: The sanitized text content to save
            output_path: Path where the sanitized file should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Saving sanitized TXT to: {output_path}")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(sanitized_text)
            return True
        except PermissionError:
            print(f"Error: Permission denied when writing to: {output_path}")
            return False
        except OSError as e:
            print(f"Error: Unable to write to {output_path}: {e}")
            return False
        except Exception as e:
            print(f"Error saving sanitized text to {output_path}: {e}")
            return False
