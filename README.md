# 📐 SmartDocFlow-X

**Resilient, Multilingual, Risk-Scored AI Document Migration Engine**

SmartDocFlow-X ingests manufacturing PDFs (digital or scanned), extracts structured data with language-aware numeric handling, migrates content via GPT-4o with deterministic numeric guardrails, and scores migration integrity with weighted risk classification.

---

## Architecture

```
┌────────────────────┐
│ Document Ingestion │ ← PDF upload
└─────────┬──────────┘
          ↓
┌─────────────────────────┐
│ Parsing Route Controller │ ← PyMuPDF or Tesseract OCR
└─────────┬───────────────┘
          ↓
┌──────────────────┐
│ Language Detection│ ← langdetect (en, de, fr, es)
└─────────┬────────┘
          ↓
┌──────────────────────────┐
│ Numeric Extraction Engine │ ← Language-agnostic regex
│  + Context Capture        │   European decimals, unit normalization
└─────────┬────────────────┘
          ↓
┌──────────────────────────┐
│ Snapshot Hashing          │ ← SHA-256 order-invariant fingerprint
└─────────┬────────────────┘
          ↓
┌──────────────────────────┐
│ Controlled LLM Migration │ ← GPT-4o (temp=0.1, JSON mode)
└─────────┬────────────────┘
          ↓
┌──────────────────────────┐
│ Numeric Drift Detection   │ ← Fuzzy matching, per-unit tolerance
│ + Risk Scoring Engine     │   Hallucination detection
└─────────┬────────────────┘
          ↓
     Streamlit Interface
```

## Key Features

- **Adaptive Ingestion**: Automatic OCR fallback for scanned PDFs with confidence scoring
- **Multilingual Numeric Extraction**: Handles European formats (`240,5 V`), localized units (`Tage`, `jours`)
- **Deterministic Numeric Guardrails**: Numbers are frozen before LLM migration, never generated
- **Order-Invariant Snapshot Hashing**: SHA-256 fingerprint for audit traceability
- **Position-Aware Drift Detection**: Fuzzy parameter matching prevents value-swapping errors
- **Per-Unit Tolerance**: Domain-aware precision (`V ±0.01`, `°C ±0.1`, `days` exact)
- **Hallucination Detection**: Flags numeric values injected by LLM not in source document
- **Configurable Risk Scoring**: Tunable weights with Low/Medium/High classification
- **OCR Confidence Thresholding**: Auto-caps risk for low-confidence scanned documents

## Setup

```bash
# Clone and enter project
git clone https://github.com/Famulkalam/SmartDocFlow-X.git
cd SmartDocFlow-X

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Tesseract (macOS)
brew install tesseract

# Configure API key
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

```bash
# Generate synthetic test PDFs
python tests/generate_test_pdfs.py

# Run the Streamlit app
streamlit run app.py

# Run the offline test suite (no API key needed)
pytest -q
```

## Testing

`tests/test_core.py` covers the deterministic parts of the pipeline without
calling the OpenAI API: number and unit parsing (European decimals,
thousands separators, negative values, `+/-` tolerances), per-unit
tolerances, drift detection (matched, drifted, missing and injected values),
integrity scoring and snapshot hashing.

Writing these tests found and fixed three bugs in numeric extraction:

- a number like `1200.5 V` was read as `200.5 V`
- values in `%` were never extracted
- negative values lost their sign (`-20.0 degrees C` became `20.0 °C`)

A fourth fix makes drift detection label each value from its own line or
sentence, so a changed value is reported as **drifted** rather than as one
missing value plus one unexpected value.

## Project Structure

```
SmartDocFlow-X/
├── app.py                      # Streamlit interface
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── config.py               # Central configuration
│   ├── ingestion.py            # Adaptive PDF parsing
│   ├── language.py             # Language detection
│   ├── numeric_extraction.py   # Numeric extraction + normalization
│   ├── migration.py            # LLM migration + snapshot hashing
│   └── drift_detection.py      # Drift detection + risk scoring
└── tests/
    ├── test_core.py            # Offline unit tests (pytest)
    ├── generate_test_pdfs.py   # Synthetic test document generator
    └── fixtures/               # Generated test PDFs
```

## Configuration

All tunable parameters are centralized in `src/config.py`:

| Parameter | Default | Description |
|---|---|---|
| `OPENAI_MODEL` | `gpt-4o` | LLM model for migration |
| `OPENAI_TEMPERATURE` | `0.1` | Low temperature for determinism |
| `OCR_CONFIDENCE_THRESHOLD` | `60` | Below this → low confidence flag |
| `FUZZY_MATCH_THRESHOLD` | `80` | Parameter name matching sensitivity |
| `UNIT_TOLERANCE[V]` | `0.01` | Voltage drift tolerance |
| `UNIT_TOLERANCE[°C]` | `0.1` | Temperature drift tolerance |
| `UNIT_TOLERANCE[days]` | `0` | Time values require exact match |

## Known Limitations

- **Thousands separators**: Basic support for `1,200.5 V` and `1.200,5 V`. Full European thousands-format disambiguation (e.g., ambiguity between `1.200` as "one point two hundred" vs "one thousand two hundred") is a documented edge case for future enhancement.
- **Handwritten content**: Low OCR confidence is flagged for manual review; handwriting is not otherwise supported.
- **Test data**: The test PDFs are generated, not real supplier documents, and the end-to-end GPT-4o step has only been checked manually.
- **Document formats**: Currently PDF-only. Extensible to `.docx` via `python-docx` and images via OCR.

## License

MIT, see [LICENSE](LICENSE).

## Author

Famul Kalam, MSc Business Analytics, University of Edinburgh.
