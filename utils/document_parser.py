"""Document parsing utilities for extracting key messages."""
import io
from typing import List, Tuple
from pathlib import Path

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except ImportError:
        raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from Word document."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except ImportError:
        raise ImportError("python-docx is required for Word parsing. Install with: pip install python-docx")
    except Exception as e:
        raise Exception(f"Error extracting Word document text: {str(e)}")

def extract_text_from_file(uploaded_file) -> Tuple[bool, str]:
    """
    Extract text from uploaded file.

    Returns:
        Tuple of (success, text_or_error_message)
    """
    filename = uploaded_file.name.lower()
    content = uploaded_file.read()

    try:
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(content)
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(content)
        elif filename.endswith('.doc'):
            return False, "Legacy .doc format not supported. Please convert to .docx or PDF."
        elif filename.endswith('.txt'):
            text = content.decode('utf-8')
        else:
            return False, f"Unsupported file format: {Path(filename).suffix}"

        if not text.strip():
            return False, "No text could be extracted from the file."

        return True, text
    except Exception as e:
        return False, str(e)

def parse_extracted_messages(raw_messages: str) -> List[dict]:
    """
    Parse raw extracted messages from Claude into structured format.

    Expected format from Claude:
    - Message 1 text
    - Message 2 text
    etc.

    Returns list of dicts with 'message' and 'priority' keys.
    """
    messages = []
    lines = raw_messages.strip().split('\n')

    for line in lines:
        # Clean up the line
        line = line.strip()
        if not line:
            continue

        # Remove common prefixes
        for prefix in ['- ', '• ', '* ', '– ', '— ']:
            if line.startswith(prefix):
                line = line[len(prefix):]
                break

        # Remove numbering like "1. " or "1) "
        import re
        line = re.sub(r'^\d+[\.\)]\s*', '', line)

        if line:
            messages.append({
                'message': line,
                'priority': 'medium'  # Default priority
            })

    return messages
