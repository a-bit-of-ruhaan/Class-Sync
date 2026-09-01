import PyPDF2
import docx  
import io

def extract_text_from_pdf(file_bytes):
    """Extracts raw text content from a PDF file safely."""
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error reading PDF file: {str(e)}"


def extract_text_from_docx(file_bytes):
    """Extracts raw text content from a DOCX file safely."""
    try:
        doc_file = io.BytesIO(file_bytes)
        doc = docx.Document(doc_file)  # Instantiates the document engine
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)
        return "\n".join(text).strip()
    except Exception as e:
        return f"Error reading DOCX file: {str(e)}"
