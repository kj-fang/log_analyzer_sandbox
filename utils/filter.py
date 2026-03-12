import re
from typing import List, Union

def read_log_file(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8', errors="replace") as f:
        return f.readlines()

def save_file(output_path: str, filtered_log):
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in filtered_log:
            f.write(line)
    print(f"save to: {output_path}")


def _parse_filter_attributes(line: str) -> dict:
    """Extract key attributes from a single .tat filter XML line."""
    result = {}
    for attr in ('enabled', 'excluding', 'regex', 'case_sensitive', 'text'):
        m = re.search(rf'{attr}="(.*?)"', line, re.IGNORECASE)
        result[attr] = m.group(1) if m else ''
    return result


def _build_keyword_entry(attrs: dict) -> dict:
    """Build a normalized keyword entry dict from parsed .tat attributes."""
    return {
        'text': attrs['text'].strip(),
        'regex': attrs.get('regex', 'n').lower() == 'y',
        'case_sensitive': attrs.get('case_sensitive', 'n').lower() == 'y',
    }


def extract_enabled_keywords_from_filter_file(filter_file_path: str) -> List[dict]:
    """
    Extracts keywords from filter lines where enabled="y" AND excluding="n".
    Returns a list of dicts: {text, regex, case_sensitive}.
    """
    keywords = []
    with open(filter_file_path, "r", encoding="utf-8") as f:
        for line in f:
            attrs = _parse_filter_attributes(line)
            if attrs['enabled'].lower() == 'y' and attrs['excluding'].lower() == 'n' and attrs['text']:
                keywords.append(_build_keyword_entry(attrs))
    print("include_keywords", [k['text'] for k in keywords])
    return keywords


def extract_exclude_keywords_from_filter_file(filter_file_path: str) -> List[dict]:
    """
    Extracts keywords from filter lines where enabled="y" AND excluding="y".
    Returns a list of dicts: {text, regex, case_sensitive}.
    """
    keywords = []
    with open(filter_file_path, "r", encoding="utf-8") as f:
        for line in f:
            attrs = _parse_filter_attributes(line)
            if attrs['enabled'].lower() == 'y' and attrs['excluding'].lower() == 'y' and attrs['text']:
                keywords.append(_build_keyword_entry(attrs))
    print("exclude_keywords", [k['text'] for k in keywords])
    return keywords


def _matches(line: str, kw: Union[dict, str]) -> bool:
    """
    Check if a log line matches a keyword entry.
    kw can be a dict {text, regex, case_sensitive} (from .tat) or a plain string (from UI input).
    """
    if isinstance(kw, str):
        return kw.lower() in line.lower()
    text = kw['text']
    if kw.get('regex', False):
        flags = 0 if kw.get('case_sensitive', False) else re.IGNORECASE
        try:
            return bool(re.search(text, line, flags))
        except re.error:
            return False
    else:
        if kw.get('case_sensitive', False):
            return text in line
        return text.lower() in line.lower()


def filter_log_by_keywords(log_lines: List[str], keywords: List, exclude_keywords: List = None) -> List[str]:
    """
    Filters log lines based on enabled keywords.
    Both keywords and exclude_keywords accept lists of dicts (from .tat) or plain strings (from UI).
    Lines matching any exclude keyword are dropped even if they match an include keyword.
    """
    filtered = []
    exclude_keywords = exclude_keywords or []

    for line in log_lines:
        if any(_matches(line, k) for k in keywords):
            if exclude_keywords and any(_matches(line, e) for e in exclude_keywords):
                continue
            cleaned_line = re.sub(r"^\d+[\t ]", "", line)
            filtered.append(cleaned_line)

    return filtered

