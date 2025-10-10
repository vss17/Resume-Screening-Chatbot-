import os
from PyPDF2 import PdfReader

def load_resumes_from_path(path):
    path = path.strip().strip('"').replace("\\", "/")

    # Handle single file
    if os.path.isfile(path) and path.lower().endswith(".pdf"):
        try:
            with open(path, "rb") as f:
                reader = PdfReader(f)
                text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                if text.strip():
                    return [{"name": os.path.basename(path), "text": text}]
        except Exception as e:
            print(f"Error reading file {path}: {e}")
        return []

    # Handle folder with PDFs
    elif os.path.isdir(path):
        pdf_files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(".pdf")]
        resumes = []
        for pdf_path in pdf_files:
            try:
                with open(pdf_path, "rb") as f:
                    reader = PdfReader(f)
                    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                    if text.strip():
                        resumes.append({"name": os.path.basename(pdf_path), "text": text})
            except Exception as e:
                print(f"Error reading {pdf_path}: {e}")
        return resumes

    else:
        print(f"Invalid path: {path}")
        return []
