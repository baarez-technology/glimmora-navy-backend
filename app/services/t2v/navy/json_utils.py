"""
Shared JSON parsing utilities for T2V Navy pipeline.
Uses json-repair for robust handling of LLM JSON output.
"""
import json
import re


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _fix_trailing_commas(text: str) -> str:
    return re.sub(r",(\s*[\]}])", r"\1", text)


def _fix_control_chars(text: str) -> str:
    """Replace literal control chars (tab, newline inside strings) that break JSON."""
    # Replace unescaped newlines within strings
    result = []
    in_string = False
    escape_next = False
    for ch in text:
        if escape_next:
            result.append(ch)
            escape_next = False
            continue
        if ch == '\\':
            escape_next = True
            result.append(ch)
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
            continue
        if in_string and ch == '\n':
            result.append('\\n')
            continue
        if in_string and ch == '\r':
            result.append('\\r')
            continue
        if in_string and ch == '\t':
            result.append('\\t')
            continue
        result.append(ch)
    return ''.join(result)


def safe_parse_json(text: str) -> dict | list:
    """
    Robustly parse a JSON string that may include markdown code fences,
    trailing commas, control characters, or other minor issues from LLM output.
    """
    text = _strip_fences(text)

    # First try: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Second try: fix control chars inside strings
    fixed = _fix_control_chars(text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # Third try: fix trailing commas
    fixed2 = _fix_trailing_commas(fixed)
    try:
        return json.loads(fixed2)
    except json.JSONDecodeError:
        pass

    # Fourth try: use json-repair library if available
    try:
        from json_repair import repair_json
        repaired = repair_json(text, return_objects=True)
        if isinstance(repaired, (dict, list)):
            return repaired
        elif isinstance(repaired, str):
            return json.loads(repaired)
    except (ImportError, Exception):
        pass

    # Fifth try: extract the first JSON object/array via regex
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        candidate = match.group(0)
        for transformer in [
            lambda t: t,
            _fix_control_chars,
            lambda t: _fix_trailing_commas(_fix_control_chars(t)),
        ]:
            try:
                return json.loads(transformer(candidate))
            except json.JSONDecodeError:
                continue
                
        # Sixth try: use json-repair on the extracted regex candidate
        try:
            from json_repair import repair_json
            repaired = repair_json(candidate, return_objects=True)
            if isinstance(repaired, (dict, list)):
                return repaired
            elif isinstance(repaired, str):
                return json.loads(repaired)
        except (ImportError, Exception):
            pass

    # Give up — raise the original error clearly
    return json.loads(text)
