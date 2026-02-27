"""
SmartDocFlow-X — Controlled LLM Migration
Deterministic + generative hybrid: numbers frozen, narrative migrated via GPT-4o.
Includes order-invariant, context-aware snapshot hashing for audit traceability.
"""

import hashlib
import json
from datetime import datetime, timezone

from openai import OpenAI
from src.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE


def create_numeric_snapshot(numerics: list[dict]) -> dict:
    """
    Create an order-invariant, context-aware SHA-256 fingerprint of numerics.
    Sorting by (value, unit, context) ensures:
      - Stable hash regardless of extraction order
      - Disambiguation of duplicate values in different parameters
    """
    # Build hashable representation
    hashable = [
        {"value": n["value"], "unit": n["unit"], "context": n.get("context", "")}
        for n in numerics
    ]
    sorted_hashable = sorted(
        hashable, key=lambda x: (x["value"], x["unit"], x["context"])
    )
    snapshot_hash = hashlib.sha256(
        json.dumps(sorted_hashable, sort_keys=True).encode()
    ).hexdigest()

    return {
        "values": [
            {"value": n["value"], "unit": n["unit"], "raw": n.get("raw", ""),
             "context": n.get("context", "")}
            for n in numerics
        ],
        "hash": snapshot_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": len(numerics),
    }


def verify_snapshot_integrity(pre_snapshot: dict, post_snapshot: dict) -> bool:
    """Compare pre- and post-migration snapshot hashes."""
    return pre_snapshot["hash"] == post_snapshot["hash"]


def build_migration_prompt(text: str, numerics: list[dict], language: str) -> str:
    """
    Construct a structured prompt that:
    - Instructs GPT-4o to migrate document into structured JSON
    - Embeds numeric snapshot as HARD CONSTRAINT
    - Defines target JSON schema with semantic parameter labels
    """
    # Format numeric constraints
    numeric_constraints = []
    for i, n in enumerate(numerics):
        numeric_constraints.append(
            f"  {i+1}. Value: {n['value']} {n['unit']} "
            f"(original: {n['raw']} {n['original_unit']}, "
            f"context: \"{n.get('context', 'N/A')}\")"
        )
    constraints_str = "\n".join(numeric_constraints)

    prompt = f"""You are a precision document migration engine. Your task is to convert the following document text into a structured JSON format.

CRITICAL CONSTRAINTS:
- The following numeric values MUST appear EXACTLY as specified in the output. Do NOT modify, round, or reinterpret any of these values:

{constraints_str}

- Each numeric parameter MUST retain a meaningful semantic label (e.g., "Operating Voltage", "Max Current", "Maintenance Interval").
- Do NOT invent or hallucinate any numeric values not present in the original document.

SOURCE DOCUMENT LANGUAGE: {language}

OUTPUT FORMAT (strict JSON):
{{
  "title": "Document title",
  "document_id": "Auto-generated or extracted ID",
  "language": "{language}",
  "sections": [
    {{
      "name": "Section name",
      "content": "Narrative content of this section",
      "parameters": [
        {{
          "name": "Semantic parameter label",
          "value": <numeric_value>,
          "unit": "standardized unit"
        }}
      ]
    }}
  ]
}}

SOURCE DOCUMENT TEXT:
{text}

Respond with ONLY the JSON object. No markdown, no explanation."""

    return prompt


def migrate_document(text: str, numerics: list[dict], language: str) -> dict:
    """
    Execute the controlled LLM migration pipeline:
    1. Create pre-migration numeric snapshot (with hash)
    2. Call GPT-4o with structured prompt and hard numeric constraints
    3. Return migrated JSON + both snapshots for drift analysis

    Returns:
        {
            "migrated_json": dict,
            "pre_snapshot": dict,
            "raw_response": str,
            "model": str,
            "temperature": float
        }
    """
    # 1. Freeze numeric snapshot before LLM
    pre_snapshot = create_numeric_snapshot(numerics)

    # 2. Build prompt and call LLM
    prompt = build_migration_prompt(text, numerics, language)

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=OPENAI_TEMPERATURE,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precision document migration engine. "
                    "You convert manufacturing documents into structured JSON. "
                    "You NEVER modify numeric values. "
                    "You NEVER invent data not in the source."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    raw_response = response.choices[0].message.content
    migrated_json = json.loads(raw_response)

    return {
        "migrated_json": migrated_json,
        "pre_snapshot": pre_snapshot,
        "raw_response": raw_response,
        "model": OPENAI_MODEL,
        "temperature": OPENAI_TEMPERATURE,
    }
