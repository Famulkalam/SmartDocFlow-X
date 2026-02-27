"""
SmartDocFlow-X — Adaptive Document Ingestion
Routes PDFs through PyMuPDF (digital) or Tesseract OCR (scanned) with confidence scoring.
"""

import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from src.config import OCR_CONFIDENCE_THRESHOLD


def extract_text_pymupdf(file_path: str) -> str:
    """Extract text from a digital PDF using PyMuPDF."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_text_tesseract(file_path: str) -> tuple[str, float]:
    """
    Extract text from a scanned/image-based PDF using Tesseract OCR.
    Returns (extracted_text, average_confidence).
    Uses image_to_data() for per-word confidence scoring.
    """
    doc = fitz.open(file_path)
    full_text = ""
    all_confidences = []

    for page in doc:
        # Render page to image at 300 DPI for OCR quality
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Get detailed OCR data with confidence scores
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        page_text_parts = []
        for i, word in enumerate(data["text"]):
            conf = int(data["conf"][i])
            if conf > 0 and word.strip():  # filter noise
                page_text_parts.append(word)
                all_confidences.append(conf)

        full_text += " ".join(page_text_parts) + "\n"

    doc.close()

    avg_confidence = (
        sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
    )
    return full_text.strip(), round(avg_confidence, 1)


def ingest_document(file_path: str) -> dict:
    """
    Adaptive ingestion: routes low-text-density documents to OCR fallback.

    Returns:
        {
            "text": str,
            "method": "pymupdf" | "tesseract",
            "ocr_confidence": float | None,
            "low_ocr_confidence": bool,
            "file_name": str
        }
    """
    file_name = os.path.basename(file_path)

    # Try digital extraction first
    text = extract_text_pymupdf(file_path)

    if len(text.strip()) >= 100:
        return {
            "text": text,
            "method": "pymupdf",
            "ocr_confidence": None,
            "low_ocr_confidence": False,
            "file_name": file_name,
        }

    # Fallback to OCR for scanned documents
    text, confidence = extract_text_tesseract(file_path)
    low_confidence = confidence < OCR_CONFIDENCE_THRESHOLD

    return {
        "text": text,
        "method": "tesseract",
        "ocr_confidence": confidence,
        "low_ocr_confidence": low_confidence,
        "file_name": file_name,
    }
