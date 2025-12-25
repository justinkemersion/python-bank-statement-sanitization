# src/models/txt_handler.py

class TXTHandler:
    def __init__(self):
        pass

    def read_text(self, txt_path):
        print(f"Reading text from TXT: {txt_path}")
        with open(txt_path, 'r') as f:
            content = f.read()
        return content

    def save_sanitized_text(self, sanitized_text, output_path):
        print(f"Saving sanitized TXT to: {output_path}")
        with open(output_path, 'w') as f:
            f.write(sanitized_text)
