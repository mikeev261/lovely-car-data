import os
import json
import re

src_dir = r'C:\Code\lovely-car-data-mgmt\lovely_data_to_simhub\lovely-car-data\src_data\lmu'

for filename in os.listdir(src_dir):
    if not filename.endswith('.jsonc'): continue
    
    with open(os.path.join(src_dir, filename), 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'("(?:\\"|[^"])*")|//.*', lambda m: m.group(1) if m.group(1) else '', content)
    
    try:
        data = json.loads(content)
    except Exception as e:
        print(f'Error reading {filename}: {e}')
        continue
        
    years_in_filename = [int(y) for y in re.findall(r'(202\d)', filename)]
    min_year = min(years_in_filename) if years_in_filename else None
    max_year = max(years_in_filename) if years_in_filename else None
    
    for var in data.get('variants', []):
        texts_to_check = [var.get('carId', ''), var.get('carName', ''), var.get('fileName', '')]
        
        for text in texts_to_check:
            years_in_text = [int(y) for y in re.findall(r'(202\d)', text)]
            for y in years_in_text:
                if not years_in_filename:
                    print(f'Anomaly: {filename} has NO year, but variant "{text}" has {y}')
                elif y < min_year or y > max_year:
                    print(f'Anomaly: {filename} range is {min_year}-{max_year}, but variant "{text}" has {y}')
