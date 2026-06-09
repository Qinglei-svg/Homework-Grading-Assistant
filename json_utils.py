"""JSON parsing helpers with model-output tolerance."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def parse_model_json(raw_output: str) -> Dict[str, Any]:
    """Parse model output as JSON, falling back to extracting the first object."""
    if raw_output is None:
        raw_output = ""

    cleaned = raw_output.strip()
    cleaned = _strip_code_fence(cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            parsed["parse_success"] = True
            return parsed
        return {"parse_success": True, "data": parsed}
    except json.JSONDecodeError:
        pass

    extracted = extract_first_json_object(cleaned)
    if extracted:
        try:
            parsed = json.loads(extracted)
            if isinstance(parsed, dict):
                parsed["parse_success"] = True
                return parsed
            return {"parse_success": True, "data": parsed}
        except json.JSONDecodeError:
            pass

    return {"parse_success": False, "raw_output": raw_output}


def extract_first_json_object(text: str) -> Optional[str]:
    """Extract the first balanced JSON object from a text blob."""
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]

        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return None


def to_pretty_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text
