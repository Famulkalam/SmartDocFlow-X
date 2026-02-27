"""
SmartDocFlow-X — Streamlit Interface
Upload → Migrate → Score → Flagged values in red.
"""

import json
import tempfile
import os
from datetime import datetime, timezone

import streamlit as st

from src.ingestion import ingest_document
from src.language import detect_language, get_language_name
from src.numeric_extraction import extract_numerics
from src.migration import migrate_document, create_numeric_snapshot
from src.drift_detection import (
    extract_post_migration_numerics,
    detect_drift,
    compute_integrity_score,
    classify_risk,
)


# ── Page Config ─────────────────────────────────────────
st.set_page_config(
    page_title="SmartDocFlow-X",
    page_icon="📐",
    layout="wide",
)

# ── Custom CSS ──────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
    }
    .main-header h1 {
        color: #1a1a2e;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .main-header p {
        color: #6c757d;
        font-size: 1.1rem;
    }
    .risk-badge {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 1.1rem;
    }
    .risk-low { background: #d4edda; color: #155724; }
    .risk-medium { background: #fff3cd; color: #856404; }
    .risk-high { background: #f8d7da; color: #721c24; }
    .score-big {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        line-height: 1;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .matched-row { background-color: #d4edda !important; }
    .drifted-row { background-color: #f8d7da !important; }
    .missing-row { background-color: #fff3cd !important; }
    .unexpected-row { background-color: #ffeaa7 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📐 SmartDocFlow-X</h1>
    <p>Resilient, Multilingual, Risk-Scored AI Document Migration Engine</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Upload ──────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload a PDF document for migration",
    type=["pdf"],
    help="Supports digital PDFs and scanned documents (OCR fallback)",
)

if uploaded_file is not None:
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # ── Pipeline Button ─────────────────────────────────
    if st.button("🚀 Run Migration Pipeline", type="primary", use_container_width=True):
        try:
            # ── STEP 1: Ingestion ───────────────────────
            with st.spinner("📄 Ingesting document..."):
                ingestion_result = ingest_document(tmp_path)

            # ── STEP 2: Language Detection ──────────────
            with st.spinner("🌐 Detecting language..."):
                language = detect_language(ingestion_result["text"])
                language_name = get_language_name(language)

            # ── STEP 3: Numeric Extraction ──────────────
            with st.spinner("🔢 Extracting numerics..."):
                pre_numerics = extract_numerics(ingestion_result["text"])
                pre_snapshot = create_numeric_snapshot(pre_numerics)

            # ── STEP 4: LLM Migration ──────────────────
            with st.spinner("🤖 Migrating via GPT-4o..."):
                migration_result = migrate_document(
                    ingestion_result["text"], pre_numerics, language
                )

            # ── STEP 5: Post-Migration Analysis ────────
            with st.spinner("🔍 Analyzing migration integrity..."):
                migrated_json = migration_result["migrated_json"]
                post_numerics = extract_post_migration_numerics(migrated_json)
                drift_result = detect_drift(pre_numerics, post_numerics)
                integrity_score = compute_integrity_score(
                    drift_result, ingestion_result["low_ocr_confidence"]
                )
                risk_level = classify_risk(integrity_score)
                post_snapshot = create_numeric_snapshot(
                    [{"value": n["value"], "unit": n["unit"], "context": n.get("name", "")}
                     for n in post_numerics]
                )

            # ── Results Display ─────────────────────────
            st.success("✅ Migration pipeline completed!")
            st.markdown("---")

            # ── Metadata Row ────────────────────────────
            meta_cols = st.columns(4)
            with meta_cols[0]:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Parsing Method", ingestion_result["method"].upper())
                st.markdown('</div>', unsafe_allow_html=True)
            with meta_cols[1]:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                ocr_conf = ingestion_result["ocr_confidence"]
                st.metric("OCR Confidence", f"{ocr_conf}%" if ocr_conf else "N/A")
                st.markdown('</div>', unsafe_allow_html=True)
            with meta_cols[2]:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Language", f"{language_name} ({language})")
                st.markdown('</div>', unsafe_allow_html=True)
            with meta_cols[3]:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Numerics Found", len(pre_numerics))
                st.markdown('</div>', unsafe_allow_html=True)

            if ingestion_result["low_ocr_confidence"]:
                st.warning(
                    f"⚠️ Low OCR confidence ({ocr_conf}%). "
                    "Risk auto-capped at Medium. Manual review recommended."
                )

            st.markdown("---")

            # ── Score + Risk Badge ──────────────────────
            score_cols = st.columns([1, 2, 1])
            with score_cols[1]:
                risk_color = {"Low": "low", "Medium": "medium", "High": "high"}[risk_level]
                risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}[risk_level]

                st.markdown(
                    f'<div class="score-big" style="color: '
                    f'{"#155724" if risk_level == "Low" else "#856404" if risk_level == "Medium" else "#721c24"}'
                    f'">{integrity_score}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="text-align:center; margin-top:0.5rem;">'
                    f'<span class="risk-badge risk-{risk_color}">'
                    f'{risk_emoji} {risk_level} Risk</span></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<p style="text-align:center; color:#6c757d; font-size:0.85rem; margin-top:0.5rem;">'
                    f'Snapshot Hash: <code>{pre_snapshot["hash"][:16]}...</code></p>',
                    unsafe_allow_html=True,
                )

            st.markdown("---")

            # ── Side-by-Side JSON ───────────────────────
            st.subheader("📋 Side-by-Side Comparison")
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("**Pre-Migration Numerics**")
                pre_display = [
                    {"value": n["value"], "unit": n["unit"], "original": f"{n['raw']} {n['original_unit']}"}
                    for n in pre_numerics
                ]
                st.json(pre_display)

            with col_right:
                st.markdown("**Migrated Structured JSON**")
                st.json(migrated_json)

            st.markdown("---")

            # ── Drift Comparison Table ──────────────────
            st.subheader("🔍 Drift Analysis")

            # Matched
            if drift_result["matched"]:
                st.markdown("**✅ Matched Parameters**")
                for m in drift_result["matched"]:
                    st.markdown(
                        f'<div style="background:#d4edda; padding:0.5rem 1rem; '
                        f'border-radius:6px; margin:0.2rem 0;">'
                        f'✅ <b>{m["pre_name"]}</b> → {m["post_name"]}: '
                        f'{m["value"]} {m["unit"]}</div>',
                        unsafe_allow_html=True,
                    )

            # Drifted
            if drift_result["drifted"]:
                st.markdown("**🔴 Drifted Parameters**")
                for d in drift_result["drifted"]:
                    drift_info = f'Value: {d["pre_value"]} → {d["post_value"]}'
                    if d.get("unit_mismatch"):
                        drift_info += f' | Unit: {d["pre_unit"]} → {d["post_unit"]}'
                    st.markdown(
                        f'<div style="background:#f8d7da; padding:0.5rem 1rem; '
                        f'border-radius:6px; margin:0.2rem 0;">'
                        f'🔴 <b>{d["pre_name"]}</b> → {d["post_name"]}: '
                        f'{drift_info} (drift: {d["value_drift"]:.4f})</div>',
                        unsafe_allow_html=True,
                    )

            # Missing
            if drift_result["missing"]:
                st.markdown("**🟠 Missing Parameters**")
                for m in drift_result["missing"]:
                    st.markdown(
                        f'<div style="background:#fff3cd; padding:0.5rem 1rem; '
                        f'border-radius:6px; margin:0.2rem 0;">'
                        f'🟠 <b>{m["name"]}</b>: {m["value"]} {m["unit"]} — '
                        f'not found in migrated output</div>',
                        unsafe_allow_html=True,
                    )

            # Unexpected (hallucination)
            if drift_result["unexpected"]:
                st.markdown("**⚠️ Unexpected Values (Potential Hallucination)**")
                for u in drift_result["unexpected"]:
                    st.markdown(
                        f'<div style="background:#ffeaa7; padding:0.5rem 1rem; '
                        f'border-radius:6px; margin:0.2rem 0;">'
                        f'⚠️ <b>{u["name"]}</b>: {u["value"]} {u["unit"]} '
                        f'(section: {u.get("section", "N/A")}) — '
                        f'not in pre-migration snapshot</div>',
                        unsafe_allow_html=True,
                    )

            if not any([drift_result["drifted"], drift_result["missing"],
                       drift_result["unexpected"]]):
                st.success("🎯 Perfect migration — all numeric values preserved!")

            st.markdown("---")

            # ── Downloadable Report ─────────────────────
            st.subheader("📥 Migration Report")

            report = {
                "metadata": {
                    "file_name": ingestion_result["file_name"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "parsing_method": ingestion_result["method"],
                    "ocr_confidence": ingestion_result["ocr_confidence"],
                    "low_ocr_confidence": ingestion_result["low_ocr_confidence"],
                    "language": language,
                    "language_name": language_name,
                    "model": migration_result["model"],
                    "temperature": migration_result["temperature"],
                },
                "pre_migration_snapshot": migration_result["pre_snapshot"],
                "post_migration_snapshot": {
                    "hash": post_snapshot["hash"],
                    "count": len(post_numerics),
                },
                "integrity": {
                    "score": integrity_score,
                    "risk_level": risk_level,
                    "snapshot_match": migration_result["pre_snapshot"]["hash"] == post_snapshot["hash"],
                },
                "drift_analysis": {
                    "matched": drift_result["matched"],
                    "drifted": drift_result["drifted"],
                    "missing": drift_result["missing"],
                    "unexpected": drift_result["unexpected"],
                    "summary": {
                        "total_pre": len(pre_numerics),
                        "total_post": len(post_numerics),
                        "matched_count": len(drift_result["matched"]),
                        "drifted_count": len(drift_result["drifted"]),
                        "missing_count": len(drift_result["missing"]),
                        "unexpected_count": len(drift_result["unexpected"]),
                    },
                },
                "migrated_document": migrated_json,
            }

            report_json = json.dumps(report, indent=2, ensure_ascii=False)

            st.download_button(
                label="📥 Download Full Migration Report (.json)",
                data=report_json,
                file_name=f"migration_report_{ingestion_result['file_name'].replace('.pdf', '')}.json",
                mime="application/json",
                use_container_width=True,
            )

            # Show raw report in expander
            with st.expander("View raw report JSON"):
                st.json(report)

        except Exception as e:
            st.error(f"❌ Pipeline error: {str(e)}")
            st.exception(e)

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

else:
    # ── Landing State ───────────────────────────────────
    st.info("👆 Upload a PDF to begin the migration pipeline.")

    with st.expander("ℹ️ How it works"):
        st.markdown("""
        **SmartDocFlow-X** processes documents through a 6-stage pipeline:

        1. **Adaptive Ingestion** — Routes digital PDFs through PyMuPDF; scanned
           documents automatically fall back to Tesseract OCR with confidence scoring.
        2. **Language Detection** — Identifies document language for locale-aware processing.
        3. **Numeric Extraction** — Language-agnostic regex extracts values with units,
           handles European decimal formats (`240,5 V`), and captures context.
        4. **Snapshot & Migration** — Freezes a SHA-256 numeric fingerprint, then migrates
           via GPT-4o with hard numeric constraints into structured JSON.
        5. **Drift Detection** — Position-aware comparison with fuzzy parameter matching,
           per-unit tolerance, and hallucination detection.
        6. **Risk Scoring** — Weighted integrity score with configurable risk classification.
        """)

    with st.expander("⚙️ Configuration"):
        st.markdown("""
        | Parameter | Value |
        |---|---|
        | LLM Model | GPT-4o |
        | Temperature | 0.1 |
        | OCR Confidence Threshold | 60% |
        | Fuzzy Match Threshold | 80/100 |
        | Voltage Tolerance | ±0.01 V |
        | Temperature Tolerance | ±0.1 °C |
        | Days Tolerance | Exact match |
        """)
