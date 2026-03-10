import re
from collections import defaultdict
from typing import List

def preprocess_log_for_llm(log_lines, preserve_timestamps=True):
    processed_lines = []
    
    for line in log_lines:
        if not line.strip():
            continue
            
        # 1. timestamp
        if preserve_timestamps:
            line = re.sub(r'(\d{2}/\d{2}/\d{4})-(\d{2}:\d{2}:\d{2})\.\d{3}', r'<TIME:\2>', line)
        else:
            line = re.sub(r'\d{2}/\d{2}/\d{4}-\d{2}:\d{2}:\d{2}\.\d{3}', '<TIMESTAMP>', line)
        
        # 2. unify 
        # Thread ID
        #line = re.sub(r'\[(\d+)\]', r'[<THREAD_ID>]', line)
        line = re.sub(r'\[(\d+)\]', '', line)
        
        # ETW
        #line = re.sub(r'etwTimeStamp = \d+', 'etwTimeStamp = <ETW_TIMESTAMP>', line)
        line = re.sub(r'etwTimeStamp\s*=\s*\d+', '', line)

        
        # addr
        #line = re.sub(r'etwEvtDataAddress = [0-9A-F]+', 'etwEvtDataAddress = <MEMORY_ADDR>', line)
        line = re.sub(r'etwEvtDataAddress\s*=\s*[0-9A-F]+', '', line)
        
        # hex
        line = re.sub(r'\b[0-9A-F]{8,}\b', '<HEX_VALUE>', line)
        
        # IP
        line = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP_ADDR>', line)
        
        # arg
        #line = re.sub(r'etwLength = \d+', 'etwLength = <LENGTH>', line)
        line = re.sub(r'etwLength\s*=\s*\d+', '', line)
        
        # 3. space remove
        line = re.sub(r'\s+', ' ', line)
        
        processed_lines.append(line.strip())
    
    return processed_lines

def group_similar_logs(processed_lines):
    """
    group similiar logs
    """
    grouped_logs = defaultdict(list)
    
    for line in processed_lines:
        pattern = re.sub(r'\[TIME:[^\]]+\]', '[TIME:*]', line)
        grouped_logs[pattern].append(line)
    
    result = []
    for pattern, lines in grouped_logs.items():
        if len(lines) == 1:
            result.append(lines[0])
        elif len(lines) <= 2:
            result.extend(lines)
        else:
            first_time = re.search(r'\[TIME:([^\]]+)\]', lines[0])
            last_time = re.search(r'\[TIME:([^\]]+)\]', lines[-1])
            
            result.append(lines[0])
            if first_time and last_time:
                result.append(f"... (repeated {len(lines)-2} times between {first_time.group(1)} and {last_time.group(1)}) ...")
            else:
                result.append(f"... (repeated {len(lines)-2} times) ...")
            result.append(lines[-1])
    
    return result

def tokenize_processed_logs(processed_lines):
    """
    Perform simple space-based tokenization after preprocessing.
    Example:
      input: "UEFI STATUS_VARIABLE_NOT_FOUND WLAN-SENSING"
      output: ["UEFI", "STATUS_VARIABLE_NOT_FOUND", "WLAN-SENSING"]
    """
    tokenized_logs = []
    for line in processed_lines:
        tokens = line.split(" ")  # simple space-based split
        tokenized_logs.append(tokens)
    return tokenized_logs

def read_log_file(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8', errors="replace") as f:
        return f.readlines()
    
def save_file(output_path: str, filtered_log):
    with open(output_path, 'w', encoding='utf-8', errors="replace") as f:
        for line in filtered_log:
            line_str = str(line)
            if not line_str.endswith('\n'):
                line_str += '\n'
            f.write(line_str)
    print(f"save to: {output_path}")
