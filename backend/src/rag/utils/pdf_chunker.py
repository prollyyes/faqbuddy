import os
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
import re

# Optional: for OCR fallback
try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None


def extract_text_from_pdf(pdf_path: str, ocr: bool = False) -> List[Dict[str, Any]]:
    """
    Extract text from a PDF, page by page. If ocr=True, use OCR for image-based pages.
    Returns a list of dicts: [{page_num, text, image (if OCR)}]
    """
    doc = fitz.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        if not text.strip() and ocr and pytesseract:
            # OCR fallback for image-based pages
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img)
        pages.append({
            "page_num": page_num + 1,
            "text": text,
        })
    return pages


def split_by_headings(text: str) -> List[Dict[str, Any]]:
    """
    Split text into sections by headings (simple regex for now).
    Returns list of dicts: [{section_title, section_text}]
    """
    # Example: headings start with numbers or all-caps
    heading_regex = re.compile(r"(^\d+\.\s+.+|^[A-Z][A-Z\s]{5,}$)", re.MULTILINE)
    matches = list(heading_regex.finditer(text))
    sections = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_title = match.group().strip()
        section_text = text[start:end].strip()
        sections.append({
            "section_title": section_title,
            "section_text": section_text,
        })
    if not sections:
        # fallback: treat whole text as one section
        sections = [{"section_title": "", "section_text": text.strip()}]
    return sections


def sliding_window_chunks(text: str, window_tokens: int = 200, overlap_tokens: int = 50) -> List[str]:
    """
    Split text into overlapping chunks by token count
    """
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + window_tokens]
        chunks.append(" ".join(chunk)) # approximate by whitespace
        if i + window_tokens >= len(words):
            break
        i += window_tokens - overlap_tokens
    return chunks


def summarize_text(text: str, max_words: int = 20) -> str:
    """
    Simple summary: return the first max_words words of the text as a pseudo-title.
    """
    words = text.strip().split()
    if not words:
        return "(empty)"
    summary = " ".join(words[:max_words])
    if len(words) > max_words:
        summary += "..."
    return summary


def chunk_pdf(
    pdf_path: str,
    ocr: bool = False,
    window_tokens: int = 200,
    overlap_tokens: int = 50,
    doc_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Main entry: extract, split, and chunk PDF. Returns list of chunks with metadata.
    """
    pages = extract_text_from_pdf(pdf_path, ocr=ocr)
    all_chunks = []
    source = os.path.basename(pdf_path)
    for page in pages:
        page_num = page["page_num"]
        sections = split_by_headings(page["text"])
        for section in sections:
            # If section_title is missing or empty, generate a summary from the section text
            section_title = section["section_title"].strip()
            if not section_title:
                section_title = summarize_text(section["section_text"])
            for chunk_text in sliding_window_chunks(section["section_text"], window_tokens, overlap_tokens):
                chunk = {
                    "text": chunk_text,
                    "metadata": {
                        "source": source,
                        "doc_id": doc_id or source,
                        "page": page_num,
                        "section_title": section_title,
                    }
                }
                all_chunks.append(chunk)
    return all_chunks

# Example usage:
# chunks = chunk_pdf("/path/to/file.pdf", ocr=True) 