import json
import re
from typing import Any


def repair_and_parse_json(raw_text: str) -> dict[str, Any]:
    """
    Robustly parses JSON emitted by LLMs, repairing common syntax anomalies
    such as unescaped inner quotes, markdown code fences, trailing commas,
    unescaped control characters, and truncated closing braces.
    """
    if not isinstance(raw_text, str):
        raise ValueError("Input must be a string")

    text = raw_text.strip()

    # 1. Strip markdown code fences if present
    if text.startswith("```"):
        # Match ```json or ``` at beginning and ``` at end
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # 2. Try standard json.loads directly
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return data[0]
    except json.JSONDecodeError:
        pass

    # 3. Clean control characters and trailing commas
    cleaned = re.sub(r",\s*([\}\]])", r"\1", text)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 4. Repair unescaped newlines inside strings
    # Replace literal unescaped newlines between quotes with \n
    fixed_chars = []
    in_string = False
    escape = False

    for i, ch in enumerate(cleaned):
        if ch == "\\" and not escape:
            escape = True
            fixed_chars.append(ch)
            continue

        if ch == '"' and not escape:
            in_string = not in_string
            fixed_chars.append(ch)
        elif in_string and ch == "\n":
            fixed_chars.append("\\n")
        elif in_string and ch == "\r":
            fixed_chars.append("\\r")
        elif in_string and ch == "\t":
            fixed_chars.append("\\t")
        else:
            fixed_chars.append(ch)

        if escape:
            escape = False

    newline_fixed = "".join(fixed_chars)
    newline_fixed = re.sub(r",\s*([\}\]])", r"\1", newline_fixed)

    try:
        data = json.loads(newline_fixed)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 5. Extract JSON object substring if model added preamble or postamble
    match = re.search(r"(\{.*\})", newline_fixed, re.DOTALL)
    if match:
        candidate = match.group(1).strip()
        candidate = re.sub(r",\s*([\}\]])", r"\1", candidate)
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    # 6. Fallback line-by-line / regex key-value extraction for 20 fields if syntax is heavily malformed
    try:
        # Check for unescaped inner quotes by replacing internal quotes
        # Pattern matching: "key": "value" where value might contain unescaped "
        return _fallback_object_extract(cleaned)
    except Exception:
        pass

    # Final attempt with the standard parser so original error trace is preserved if impossible
    return json.loads(text)


def _fallback_object_extract(text: str) -> dict[str, Any]:
    """
    Fallback parser that extracts top-level string and list fields using regex
    when quote escaping is broken by the LLM.
    """
    result: dict[str, Any] = {}
    
    # Extract list fields: "field_name": [ ... ]
    list_matches = re.findall(r'"([a-zA-Z0-9_]+)"\s*:\s*\[(.*?)\](?=\s*,\s*"|\s*\})', text, re.DOTALL)
    for key, raw_list in list_matches:
        # Extract items inside brackets
        items = re.findall(r'"(.*?)"(?=\s*,\s*"|\s*\]|\s*$)', raw_list, re.DOTALL)
        if not items:
            items = [item.strip().strip('"') for item in raw_list.split(",") if item.strip()]
        result[key] = [item.replace('\\"', '"').replace("\\n", "\n").strip() for item in items if item.strip()]

    # Extract string fields: "field_name": "..."
    str_matches = re.findall(r'"([a-zA-Z0-9_]+)"\s*:\s*"(.*?)"(?=\s*,\s*"[a-zA-Z0-9_]+"\s*:|\s*\})', text, re.DOTALL)
    for key, val in str_matches:
        if key not in result:
            result[key] = val.replace('\\"', '"').replace("\\n", "\n").strip()

    if result and ("research_objective" in result or "working_title" in result or "primary_research_question" in result):
        return result

    raise ValueError("Fallback extraction could not find valid research plan fields")
