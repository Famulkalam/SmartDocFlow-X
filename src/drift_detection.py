"""
SmartDocFlow-X — Numeric Drift Detection + Risk Scoring Engine
Position-aware comparison with fuzzy parameter matching, per-unit tolerance,
unexpected value injection detection, and weighted integrity scoring.
"""

from rapidfuzz import fuzz
from src.config import (
    UNIT_TOLERANCE,
    RISK_WEIGHTS,
    FUZZY_MATCH_THRESHOLD,
    RISK_THRESHOLDS,
)


def extract_post_migration_numerics(migrated_json: dict) -> list[dict]:
    """
    Walk the migrated JSON structure and extract all parameter values.

    Returns list of:
        {"name": str, "value": float, "unit": str}
    """
    results = []
    sections = migrated_json.get("sections", [])

    for section in sections:
        section_name = section.get("name", "Unknown")
        parameters = section.get("parameters", [])

        for param in parameters:
            name = param.get("name", "")
            value = param.get("value")
            unit = param.get("unit", "")

            if value is not None:
                try:
                    results.append({
                        "name": name,
                        "value": float(value),
                        "unit": unit,
                        "section": section_name,
                    })
                except (ValueError, TypeError):
                    continue

    return results


def match_parameter_name(pre_name: str, post_name: str) -> bool:
    """
    Fuzzy match parameter names using rapidfuzz.
    Handles LLM renaming like "Operating Voltage" vs "Voltage (Operating)".
    Strict numeric equality is still enforced separately.
    """
    if not pre_name or not post_name:
        return False
    score = fuzz.token_sort_ratio(pre_name.lower(), post_name.lower())
    return score >= FUZZY_MATCH_THRESHOLD


def is_within_tolerance(pre_value: float, post_value: float, unit: str) -> bool:
    """
    Check if two values are within the domain-aware tolerance for their unit.
    Uses UNIT_TOLERANCE config; falls back to DEFAULT tolerance.
    """
    tolerance = UNIT_TOLERANCE.get(unit, UNIT_TOLERANCE["DEFAULT"])
    if tolerance == 0:
        return pre_value == post_value
    return abs(pre_value - post_value) <= tolerance


def _infer_parameter_name(numeric: dict) -> str:
    """
    Infer a parameter name from context for pre-migration numerics.
    Falls back to a value-unit descriptor.
    """
    context = numeric.get("context", "")
    # Try to extract a label from context (text before the number)
    if context:
        # Find the value in context and take text before it
        raw = numeric.get("raw", str(numeric["value"]))
        idx = context.find(raw)
        if idx > 0:
            prefix = context[:idx].strip()
            # Clean up: take last meaningful phrase
            prefix = prefix.rstrip(":").strip()
            if prefix:
                return prefix
    return f"{numeric['value']} {numeric['unit']}"


def detect_drift(pre_numerics: list[dict], post_numerics: list[dict]) -> dict:
    """
    Position-aware drift detection comparing pre- and post-migration numerics.

    Matching strategy:
    1. Match by parameter name (fuzzy) + value + unit
    2. Detect value drift (same name, different value)
    3. Detect missing values (pre-values not found post)
    4. Detect unexpected injected values (post-values not in pre)

    Returns:
        {
            "matched": [...],
            "drifted": [...],
            "missing": [...],
            "unexpected": [...]
        }
    """
    matched = []
    drifted = []
    missing = []

    # Track which post-migration values have been matched
    post_matched_indices = set()

    # Infer parameter names for pre-migration values
    pre_with_names = []
    for n in pre_numerics:
        name = _infer_parameter_name(n)
        pre_with_names.append({**n, "inferred_name": name})

    for pre in pre_with_names:
        best_match = None
        best_score = 0
        best_idx = -1

        for idx, post in enumerate(post_numerics):
            if idx in post_matched_indices:
                continue

            # Try fuzzy name match
            name_match = match_parameter_name(
                pre["inferred_name"], post.get("name", "")
            )

            if name_match:
                score = fuzz.token_sort_ratio(
                    pre["inferred_name"].lower(),
                    post.get("name", "").lower(),
                )
                if score > best_score:
                    best_match = post
                    best_score = score
                    best_idx = idx

        if best_match is not None:
            post_matched_indices.add(best_idx)
            value_ok = is_within_tolerance(
                pre["value"], best_match["value"], pre["unit"]
            )
            unit_ok = pre["unit"] == best_match["unit"]

            if value_ok and unit_ok:
                matched.append({
                    "pre_name": pre["inferred_name"],
                    "post_name": best_match.get("name", ""),
                    "value": pre["value"],
                    "unit": pre["unit"],
                    "status": "matched",
                })
            else:
                drifted.append({
                    "pre_name": pre["inferred_name"],
                    "post_name": best_match.get("name", ""),
                    "pre_value": pre["value"],
                    "post_value": best_match["value"],
                    "pre_unit": pre["unit"],
                    "post_unit": best_match["unit"],
                    "value_drift": abs(pre["value"] - best_match["value"]),
                    "unit_mismatch": not unit_ok,
                    "status": "drifted",
                })
        else:
            # Try direct value+unit match as fallback
            fallback_found = False
            for idx, post in enumerate(post_numerics):
                if idx in post_matched_indices:
                    continue
                if (is_within_tolerance(pre["value"], post["value"], pre["unit"])
                        and pre["unit"] == post["unit"]):
                    post_matched_indices.add(idx)
                    matched.append({
                        "pre_name": pre["inferred_name"],
                        "post_name": post.get("name", ""),
                        "value": pre["value"],
                        "unit": pre["unit"],
                        "status": "matched",
                    })
                    fallback_found = True
                    break

            if not fallback_found:
                missing.append({
                    "name": pre["inferred_name"],
                    "value": pre["value"],
                    "unit": pre["unit"],
                    "status": "missing",
                })

    # Detect unexpected (hallucinated) values
    unexpected = []
    for idx, post in enumerate(post_numerics):
        if idx not in post_matched_indices:
            unexpected.append({
                "name": post.get("name", ""),
                "value": post["value"],
                "unit": post["unit"],
                "section": post.get("section", ""),
                "status": "unexpected",
            })

    return {
        "matched": matched,
        "drifted": drifted,
        "missing": missing,
        "unexpected": unexpected,
    }


def compute_integrity_score(drift_result: dict, low_ocr_confidence: bool = False) -> float:
    """
    Compute weighted integrity score.

    Formula:
        score = 100
              - RISK_WEIGHTS["unit_mismatch"] * unit_mismatch_ratio
              - RISK_WEIGHTS["value_drift"]   * value_drift_ratio
              - RISK_WEIGHTS["missing"]       * missing_value_ratio
              - RISK_WEIGHTS["unexpected"]    * unexpected_value_penalty

    Clamped to [0, 100]. Auto-caps at 94 if low OCR confidence.
    """
    total_pre = (
        len(drift_result["matched"])
        + len(drift_result["drifted"])
        + len(drift_result["missing"])
    )

    if total_pre == 0:
        return 100.0 if not low_ocr_confidence else 94.0

    # Calculate ratios
    unit_mismatches = sum(1 for d in drift_result["drifted"] if d.get("unit_mismatch"))
    value_drifts = sum(1 for d in drift_result["drifted"] if d.get("value_drift", 0) > 0)
    missing_count = len(drift_result["missing"])
    unexpected_count = len(drift_result["unexpected"])

    unit_mismatch_ratio = unit_mismatches / total_pre
    value_drift_ratio = value_drifts / total_pre
    missing_ratio = missing_count / total_pre
    unexpected_penalty = unexpected_count / max(total_pre, 1)

    score = (
        100
        - RISK_WEIGHTS["unit_mismatch"] * unit_mismatch_ratio
        - RISK_WEIGHTS["value_drift"] * value_drift_ratio
        - RISK_WEIGHTS["missing"] * missing_ratio
        - RISK_WEIGHTS["unexpected"] * unexpected_penalty
    )

    if low_ocr_confidence:
        score = min(score, 94)

    # Clamp to [0, 100]
    score = max(0, min(100, score))
    return round(score, 1)


def classify_risk(score: float) -> str:
    """
    Classify risk based on integrity score.
    95-100 → Low, 85-94 → Medium, <85 → High
    """
    if score >= RISK_THRESHOLDS["low"]:
        return "Low"
    elif score >= RISK_THRESHOLDS["medium"]:
        return "Medium"
    else:
        return "High"
