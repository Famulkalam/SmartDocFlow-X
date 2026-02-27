"""
SmartDocFlow-X — Language Detection Layer
Detects document language for locale-aware numeric extraction.
"""

from langdetect import detect, LangDetectException


# Human-readable language names
LANGUAGE_NAMES = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
}


def detect_language(text: str) -> str:
    """
    Detect the language of the given text.

    Returns:
        ISO 639-1 language code (e.g., 'en', 'de', 'fr').
        Defaults to 'en' if detection fails.
    """
    try:
        lang = detect(text)
        return lang
    except LangDetectException:
        return "en"


def get_language_name(lang_code: str) -> str:
    """Convert ISO language code to human-readable name."""
    return LANGUAGE_NAMES.get(lang_code, lang_code.upper())
