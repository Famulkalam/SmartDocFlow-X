"""
SmartDocFlow-X: Language-Agnostic Numeric Extraction Engine
Extracts, normalizes, and standardizes numeric values with units across languages.
Handles European decimal formats and localized units.
"""

import re
from src.config import UNIT_MAP


# ── Regex — supports thousands separators and European formats ──
# Matches: 240.5 V, 240,5 V, 1,200.5 V, 1.200,5 V, ±0.25 A, 85 °C
NUMERIC_PATTERN = re.compile(
    # value: digits with optional "." / "," groups, e.g. 240.5, 240,5, 1200.5,
    # 1,200.5, 1.200,5. The look-behind stops a match starting in the middle
    # of a longer number (previously "1200.5 V" was read as 200.5 V).
    # A leading minus is kept ("-20.0 degrees C" was read as +20), except in
    # "+/-0.25", where the "-" belongs to the tolerance sign.
    r'(?<![\d.,])((?:(?<!/)[-−])?[±]?\d+(?:[.,]\d+)*)'
    r'\s*'
    r'(degrees\s*C|°C|V|A|%|mm|cm|kg|Tage|days|jours|días'  # units (degrees C before single letters)
    r'|Volt|Ampere|Grad|kW|W|Hz|Ω|bar|mbar|µm|nm)'
    # unit must not run into a letter or digit ("V" in "Voltage", "A" in "Amps").
    # A plain \b failed after non-word units such as "%", so percentages were never matched.
    r'(?!\w)',
    re.UNICODE
)

# Context window: chars before/after match for position-aware tracking
CONTEXT_WINDOW = 40


def normalize_value(raw: str) -> float:
    """
    Normalize a numeric string to float.
    Handles European comma-decimal format (240,5 → 240.5).
    Handles thousands separators (1,200.5 or 1.200,5).
    """
    cleaned = raw.replace("±", "")
    sign = 1.0
    if cleaned[:1] in ("-", "−"):
        sign, cleaned = -1.0, cleaned[1:]

    # Determine format:
    # If both . and , exist, the last one is the decimal separator
    dot_pos = cleaned.rfind(".")
    comma_pos = cleaned.rfind(",")

    # A separator that appears more than once can only be a thousands
    # separator: 1,200,300 or 1.200.300
    if cleaned.count(",") > 1 and dot_pos == -1:
        return sign * float(cleaned.replace(",", ""))
    if cleaned.count(".") > 1 and comma_pos == -1:
        return sign * float(cleaned.replace(".", ""))

    if dot_pos > -1 and comma_pos > -1:
        if dot_pos > comma_pos:
            # Format: 1,200.5 → comma is thousands
            cleaned = cleaned.replace(",", "")
        else:
            # Format: 1.200,5 → dot is thousands, comma is decimal
            cleaned = cleaned.replace(".", "").replace(",", ".")
    elif comma_pos > -1:
        # Only comma → European decimal (240,5 → 240.5)
        cleaned = cleaned.replace(",", ".")

    return sign * float(cleaned)


def normalize_unit(unit: str) -> str:
    """Normalize localized units to standard form using UNIT_MAP."""
    unit = " ".join(unit.split())  # "degrees   C" -> "degrees C"
    return UNIT_MAP.get(unit, unit)


def extract_numerics(text: str) -> list[dict]:
    """
    Extract all numeric values with units from text.

    Returns list of:
        {
            "raw": str,           # original matched value string
            "value": float,       # normalized numeric value
            "unit": str,          # standardized unit
            "original_unit": str, # unit as it appeared in text
            "context": str,       # surrounding text for position-aware matching
            "label": str          # text before the value on the same line
        }
    """
    results = []
    prev_end = 0

    for match in NUMERIC_PATTERN.finditer(text):
        raw_value = match.group(1)
        raw_unit = match.group(2)

        # Capture surrounding context
        start = max(0, match.start() - CONTEXT_WINDOW)
        end = min(len(text), match.end() + CONTEXT_WINDOW)
        context = text[start:end].strip()

        # Label = text on the same line before the number ("Rated current:").
        # Used to match the value to the migrated parameter of the same name.
        # Starts after the previous value on the line and after the last
        # sentence break, so prose like "rated at 2.8 kW. Voltage tolerance is"
        # gives "Voltage tolerance is" rather than the whole sentence.
        line_start = text.rfind("\n", 0, match.start()) + 1
        label = text[max(line_start, prev_end):match.start()]
        label = re.split(r"[;|\t]|\.\s", label)[-1]
        label = re.sub(r"\s*(\+/-|±)\s*$", "", label).strip().rstrip(":").strip()
        prev_end = match.end()

        try:
            value = normalize_value(raw_value)
        except ValueError:
            continue  # skip unparseable values

        results.append({
            "raw": raw_value,
            "value": value,
            "unit": normalize_unit(raw_unit),
            "original_unit": raw_unit,
            "context": context,
            "label": label,
        })

    return results
