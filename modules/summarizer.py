from core.models_hf import summarize_text

def summarize_any(text: str, min_len=50, max_len=220) -> str:
    text = (text or "").strip()
    if not text:
        return "Please provide text to summarize."
    # Use the correct keyword names; models_hf also accepts min_length for safety.
    return summarize_text(text, max_len=max_len, min_len=min_len)

# -------- File extraction for Doc Summarizer --------
import os, tempfile
from io import BytesIO

def extract_text_from_file(uploaded_file) -> str:
    """
    Supports: .txt, .pdf, .docx
    Returns raw text or an error message string.
    """
    try:
        name = (uploaded_file.name or "").lower()
        data = uploaded_file.read()
        if not data:
            return "Error: Empty file."

        if name.endswith(".txt"):
            try:
                return data.decode("utf-8", errors="ignore")
            finally:
                try: uploaded_file.seek(0)
                except Exception: pass

        elif name.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(BytesIO(data))
                text = "".join([(p.extract_text() or "") for p in reader.pages])
                try: uploaded_file.seek(0)
                except Exception: pass
                return text.strip() or "Error: No extractable text in PDF."
            except Exception as e:
                return f"Error reading PDF: {e}"

        elif name.endswith(".docx"):
            try:
                import docx2txt
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                text = docx2txt.process(tmp_path) or ""
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                try: uploaded_file.seek(0)
                except Exception: pass
                return text.strip() or "Error: No extractable text in DOCX."
            except Exception as e:
                return f"Error reading DOCX: {e}"

        else:
            return f"Unsupported file type: {name}"
    except Exception as e:
        return f"Error: {e}"
