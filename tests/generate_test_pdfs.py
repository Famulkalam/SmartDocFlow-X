"""
SmartDocFlow-X — Synthetic Test PDF Generator
Creates realistic multilingual manufacturing documents for testing.
"""

import os
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def ensure_fixtures_dir():
    os.makedirs(FIXTURES_DIR, exist_ok=True)


def generate_english_spec():
    """Generate an English manufacturing specification PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Technical Specification - Power Supply Unit PSU-4200", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "Document ID: SPEC-EN-2024-0042", ln=True)
    pdf.cell(0, 8, "Revision: 3.1 | Date: 2024-11-15", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "1. Electrical Parameters", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "The PSU-4200 operates at a nominal voltage of 240.5 V with a maximum "
        "current draw of 12.3 A under full load conditions. The power output is "
        "rated at 2.8 kW continuous. Voltage tolerance is specified at +/-0.25 V "
        "across the operating range. Operating frequency is 50 Hz."
    ))
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. Thermal Specifications", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "Maximum operating temperature: 85.0 degrees C. The thermal protection "
        "circuit activates at 95.5 degrees C. Ambient temperature range: -20.0 degrees C "
        "to 55.0 degrees C. Thermal resistance: 2.4 degrees C per watt."
    ))
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. Maintenance Schedule", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "Preventive maintenance interval: 30 days. Full inspection cycle: 180 days. "
        "Filter replacement: every 90 days. Calibration verification must be performed "
        "within 7 days of any component replacement. Component weight: 4.5 kg."
    ))
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "4. Mechanical Dimensions", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "Unit dimensions: 320 mm x 240 mm x 180 mm. Mounting clearance: 15 mm "
        "on all sides. Cable entry diameter: 12 mm. Internal pressure rating: 2.5 bar."
    ))

    filepath = os.path.join(FIXTURES_DIR, "english_spec.pdf")
    pdf.output(filepath)
    print(f"  Created: {filepath}")
    return filepath


def generate_german_spec():
    """Generate a German manufacturing specification PDF with comma-decimal format."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Technische Spezifikation - Netzteil PSU-4200", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "Dokument-ID: SPEC-DE-2024-0042", ln=True)
    pdf.cell(0, 8, "Revision: 3.1 | Datum: 15.11.2024", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "1. Elektrische Parameter", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "Das PSU-4200 arbeitet bei einer Nennspannung von 240,5 V mit einem "
        "maximalen Strom von 12,3 A unter Volllastbedingungen. Die Ausgangsleistung "
        "betraegt 2,8 kW im Dauerbetrieb. Die Spannungstoleranz betraegt +/-0,25 V. "
        "Betriebsfrequenz: 50 Hz."
    ))
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. Thermische Spezifikationen", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "Maximale Betriebstemperatur: 85,0 Grad. Der thermische Schutzkreis "
        "aktiviert bei 95,5 Grad. Umgebungstemperatur: -20,0 Grad "
        "bis 55,0 Grad."
    ))
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. Wartungsplan", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "Vorbeugende Wartung: alle 30 Tage. Vollinspektion: alle 180 Tage. "
        "Filterwechsel: alle 90 Tage. Kalibrierung innerhalb von 7 Tage "
        "nach Komponentenaustausch. Gewicht: 4,5 kg."
    ))
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "4. Mechanische Abmessungen", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, (
        "Abmessungen: 320 mm x 240 mm x 180 mm. Montageabstand: 15 mm "
        "auf allen Seiten. Kabeleinfuehrung: 12 mm. Innendruck: 2,5 bar."
    ))

    filepath = os.path.join(FIXTURES_DIR, "german_spec.pdf")
    pdf.output(filepath)
    print(f"  Created: {filepath}")
    return filepath


def generate_scanned_spec():
    """
    Generate a scanned/image-based PDF.
    Renders text as an image, then embeds it in a PDF to trigger OCR fallback.
    """
    # Create an image with text
    width, height = 2100, 2970  # A4 at 250 DPI
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Use default font (no external font needed)
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        font_body = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
    except (IOError, OSError):
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    y = 80
    draw.text((80, y), "Technical Specification - Motor Drive MD-7100", fill="black", font=font_title)
    y += 80
    draw.text((80, y), "Document ID: SPEC-SCAN-2024-0099", fill="black", font=font_body)
    y += 50
    draw.text((80, y), "Revision: 1.0 | Date: 2024-12-01", fill="black", font=font_body)
    y += 80

    draw.text((80, y), "1. Electrical Parameters", fill="black", font=font_title)
    y += 70
    lines = [
        "Operating Voltage: 380.0 V",
        "Maximum Current: 25.5 A",
        "Power Rating: 9.5 kW",
        "Frequency: 60 Hz",
    ]
    for line in lines:
        draw.text((100, y), line, fill="black", font=font_body)
        y += 45

    y += 40
    draw.text((80, y), "2. Thermal Specifications", fill="black", font=font_title)
    y += 70
    lines = [
        "Max Operating Temperature: 92.0 degrees C",
        "Coolant Pressure: 3.2 bar",
    ]
    for line in lines:
        draw.text((100, y), line, fill="black", font=font_body)
        y += 45

    y += 40
    draw.text((80, y), "3. Maintenance", fill="black", font=font_title)
    y += 70
    lines = [
        "Service Interval: 60 days",
        "Component Weight: 18.5 kg",
    ]
    for line in lines:
        draw.text((100, y), line, fill="black", font=font_body)
        y += 45

    # Save image as temp file
    img_path = os.path.join(FIXTURES_DIR, "_temp_scan.png")
    img.save(img_path, "PNG")

    # Create PDF from image
    pdf = FPDF()
    pdf.add_page()
    pdf.image(img_path, 0, 0, 210, 297)  # A4 dimensions in mm

    filepath = os.path.join(FIXTURES_DIR, "scanned_spec.pdf")
    pdf.output(filepath)

    # Clean up temp image
    os.remove(img_path)

    print(f"  Created: {filepath}")
    return filepath


if __name__ == "__main__":
    print("Generating synthetic test PDFs...")
    ensure_fixtures_dir()
    generate_english_spec()
    generate_german_spec()
    generate_scanned_spec()
    print("Done! All test PDFs generated in tests/fixtures/")
