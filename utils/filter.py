import re
from typing import List

def read_log_file(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8', errors="replace") as f:
        return f.readlines()

def save_file(output_path: str, filtered_log):
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in filtered_log:
            f.write(line)
    print(f"save to: {output_path}")


def extract_enabled_keywords_from_filter_file(filter_file_path: str) -> List[str]:
    """
    Extracts all `text` attributes from filter lines where `enabled="y"`.
    """
    enabled_keywords = []
    pattern = re.compile(r'enabled="y".*?text="(.*?)"', re.IGNORECASE)

    with open(filter_file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                keyword = match.group(1).strip()
                enabled_keywords.append(keyword)
    print("enabled_keyword", enabled_keywords)
    return enabled_keywords

def filter_log_by_keywords(log_lines: List[str], keywords: List[str]) -> List[str]:
    """
    Filters log lines based on enabled keywords and removes the first character (e.g., line number or symbol).
    """
    filtered = []

    for line in log_lines:
        if any(k.lower() in line.lower() for k in keywords):
            cleaned_line = re.sub(r"^\d+\t", "", line)  # Remove first line number and leading whitespace
            filtered.append(cleaned_line)

    return filtered

