"""
SmartDocFlow-X — Language-Agnostic Numeric Extraction Engine
Extracts, normalizes, and standardizes numeric values with units across languages.
Handles European decimal formats and localized units.
"""

import re
from src.config import UNIT_MAP


# ── Regex — supports thousands separators and European formats ──
# Matches: 240.5 V, 240,5 V, 1,200.5 V, 1.200,5 V, ±0.25 A, 85 °C
NUMERIC_PATTERN = re.compile(
    r'([±]?\d{1,3}(?:[.,]\d{3})*[.,]\d+|[±]?\d+)'  # value: decimal required if dot/comma present
    r'\s*'
    r'(degrees\s*C|°C|V|A|%|mm|cm|kg|Tage|days|jours|días'  # units (degrees C before single letters)
    r'|Volt|Ampere|Grad|kW|W|Hz|Ω|bar|mbar|µm|nm)'
    r'\b',                                               # word boundary to prevent false positives
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

    # Determine format:
    # If both . and , exist, the last one is the decimal separator
    dot_pos = cleaned.rfind(".")
    comma_pos = cleaned.rfind(",")

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

    return float(cleaned)


def normalize_unit(unit: str) -> str:
    """Normalize localized units to standard form using UNIT_MAP."""
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
            "context": str        # surrounding text for position-aware matching
        }
    """
    results = []

    for match in NUMERIC_PATTERN.finditer(text):
        raw_value = match.group(1)
        raw_unit = match.group(2)

        # Capture surrounding context
        start = max(0, match.start() - CONTEXT_WINDOW)
        end = min(len(text), match.end() + CONTEXT_WINDOW)
        context = text[start:end].strip()

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
        })

    return results
