"""
SmartDocFlow-X — Central Configuration
All tunable parameters centralized for governance maturity.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ──────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o"
OPENAI_TEMPERATURE = 0.1

# ── OCR ─────────────────────────────────────────────────
OCR_CONFIDENCE_THRESHOLD = 60  # avg confidence below this → low_ocr_confidence flag

# ── Per-Unit Tolerance — Domain-Aware Precision ─────────
UNIT_TOLERANCE = {
    "V": 0.01,
    "A": 0.01,
    "°C": 0.1,
    "days": 0,
    "%": 0.1,
    "mm": 0.01,
    "cm": 0.01,
    "kg": 0.01,
    "W": 0.1,
    "kW": 0.01,
    "Hz": 0.1,
    "bar": 0.01,
    "mbar": 0.1,
    "DEFAULT": 0.001,
}

# ── Risk Scoring Weights — Tunable Governance ───────────
RISK_WEIGHTS = {
    "unit_mismatch": 40,
    "value_drift": 40,
    "missing": 20,
    "unexpected": 10,
}

# ── Fuzzy Matching ──────────────────────────────────────
FUZZY_MATCH_THRESHOLD = 80  # rapidfuzz score (0-100) for parameter name matching

# ── Risk Classification Thresholds ──────────────────────
RISK_THRESHOLDS = {
    "low": 95,    # score >= 95 → Low Risk
    "medium": 85, # score >= 85 → Medium Risk
    # score < 85 → High Risk
}

# ── Unit Normalization Map ──────────────────────────────
UNIT_MAP = {
    "Tage": "days",
    "jours": "days",
    "días": "days",
    "Volt": "V",
    "Ampere": "A",
    "Grad": "°C",
    "degrees C": "°C",
}
