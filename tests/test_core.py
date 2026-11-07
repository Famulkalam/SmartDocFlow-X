"""Offline tests for the deterministic parts of SmartDocFlow-X.
None of these call the OpenAI API.  Run:  pytest -q
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.drift_detection import (  # noqa: E402
    classify_risk,
    compute_integrity_score,
    detect_drift,
    extract_post_migration_numerics,
    is_within_tolerance,
)
from src.migration import create_numeric_snapshot, verify_snapshot_integrity  # noqa: E402
from src.numeric_extraction import extract_numerics, normalize_value  # noqa: E402


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("240.5", 240.5),
        ("240,5", 240.5),      # European decimal comma
        ("1,200.5", 1200.5),   # comma thousands
        ("1.200,5", 1200.5),   # dot thousands, comma decimal
        ("1,200,300", 1200300.0),
        ("±0.25", 0.25),
    ],
)
def test_normalize_value(raw, expected):
    assert normalize_value(raw) == pytest.approx(expected)


@pytest.mark.parametrize(
    "text, value, unit",
    [
        ("Rated voltage: 240.5 V", 240.5, "V"),
        ("Nennspannung: 240,5 V", 240.5, "V"),
        ("Peak load 1200.5 V", 1200.5, "V"),   # regression: was read as 200.5
        ("Efficiency 92.5 % at full load", 92.5, "%"),  # regression: % never matched
        ("Efficiency 92.5%.", 92.5, "%"),
        ("Max temperature 85 °C", 85.0, "°C"),
        ("Max temperature 85 degrees C", 85.0, "°C"),
        ("Garantie 30 Tage", 30.0, "days"),
        ("Supply 230 Volt", 230.0, "V"),
        ("Ambient range: -20.0 degrees C", -20.0, "°C"),  # regression: sign was dropped
        ("Voltage tolerance +/-0.25 V", 0.25, "V"),       # tolerance, not negative
        ("Operating range 20-85 °C", 85.0, "°C"),         # range, not negative
    ],
)
def test_extract_numerics(text, value, unit):
    found = extract_numerics(text)
    assert len(found) == 1
    assert found[0]["value"] == pytest.approx(value)
    assert found[0]["unit"] == unit


def test_labels_stay_on_their_own_line_and_sentence():
    found = extract_numerics("Rated voltage: 240.5 V\nRated current: 12.3 A. Weight is 4.5 kg")
    assert [n["label"] for n in found] == ["Rated voltage", "Rated current", "Weight is"]


def test_unit_must_not_run_into_a_word():
    # "V" at the start of "Version" is not a voltage
    assert extract_numerics("Firmware 2 Version notes") == []


def test_tolerance_per_unit():
    assert is_within_tolerance(240.50, 240.505, "V")
    assert not is_within_tolerance(240.5, 240.6, "V")
    assert is_within_tolerance(30, 30, "days")
    assert not is_within_tolerance(30, 31, "days")


def _post(params):
    return extract_post_migration_numerics({"sections": [{"name": "Spec", "parameters": params}]})


def test_detect_drift_flags_changed_missing_and_injected_values():
    pre = extract_numerics(
        "Rated voltage: 240.5 V\nRated current: 12.3 A\nWarranty period: 30 days"
    )
    post = _post(
        [
            {"name": "Rated voltage", "value": 240.5, "unit": "V"},   # matched
            {"name": "Rated current", "value": 13.2, "unit": "A"},    # drifted
            {"name": "Max power", "value": 2.8, "unit": "kW"},        # injected
        ]
    )
    result = detect_drift(pre, post)
    assert len(result["matched"]) == 1
    assert len(result["drifted"]) == 1
    assert len(result["missing"]) == 1
    assert len(result["unexpected"]) == 1
    assert result["unexpected"][0]["value"] == 2.8


def test_clean_migration_scores_low_risk():
    pre = extract_numerics("Rated voltage: 240.5 V\nRated current: 12.3 A")
    post = _post(
        [
            {"name": "Rated voltage", "value": 240.5, "unit": "V"},
            {"name": "Rated current", "value": 12.3, "unit": "A"},
        ]
    )
    score = compute_integrity_score(detect_drift(pre, post))
    assert score == 100.0
    assert classify_risk(score) == "Low"
    # low OCR confidence caps the score below the Low band
    capped = compute_integrity_score(detect_drift(pre, post), low_ocr_confidence=True)
    assert capped == 94
    assert classify_risk(capped) != "Low"


def test_snapshot_hash_is_order_invariant_and_sensitive_to_values():
    a = extract_numerics("Voltage: 240.5 V\nCurrent: 12.3 A")
    b = list(reversed(a))
    assert verify_snapshot_integrity(create_numeric_snapshot(a), create_numeric_snapshot(b))
    changed = [dict(a[0], value=241.0)] + a[1:]
    assert not verify_snapshot_integrity(create_numeric_snapshot(a), create_numeric_snapshot(changed))
