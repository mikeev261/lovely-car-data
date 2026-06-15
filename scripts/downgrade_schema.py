import os
import json
import re

def load_jsonc(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Strip comments safely ignoring strings
    content = re.sub(r'("(?:\\"|[^"])*")|//.*', lambda m: m.group(1) if m.group(1) else '', content)
    return json.loads(content)

def downgrade_car_profile(data, base_data=None):
    downgraded = dict(data)
    
    # 1. Apply explicit _downgradeOverrides for v2.0.0
    overrides = downgraded.get("_downgradeOverrides", {}).get("v2.0.0", {})
    for k, v in overrides.items():
        downgraded[k] = v
        
    # 2. Resolve redline aliases in ledColor BEFORE deleting the aliases
    if "ledColor" in downgraded and isinstance(downgraded["ledColor"], list):
        new_led_color = []
        for c in downgraded["ledColor"]:
            if c.startswith("redline"):
                val = downgraded.get(c)
                if val is None and base_data:
                    val = base_data.get(c)
                    
                if isinstance(val, str) and val.startswith("#"):
                    new_led_color.append(val)
                elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], str) and val[0].startswith("#"):
                    new_led_color.append(val[0])
                else:
                    new_led_color.append(c)
            else:
                new_led_color.append(c)
        downgraded["ledColor"] = new_led_color
        
    # 2. Cleanup custom vHH3.0 keys and internal metadata
    keys_to_delete = [
        k for k in downgraded 
        if (k.startswith("_") and k != "_schemaVersion") or k == "statusLeds" or (k.startswith("redline") and k != "redlineBlinkInterval")
    ]
    for k in keys_to_delete:
        del downgraded[k]
        
    downgraded["_schemaVersion"] = "v2.0.0"
        
    # 3. Handle array-based redlineBlinkInterval
    if "redlineBlinkInterval" in downgraded and isinstance(downgraded["redlineBlinkInterval"], list):
        if downgraded["redlineBlinkInterval"]:
            downgraded["redlineBlinkInterval"] = downgraded["redlineBlinkInterval"][-1]
        else:
            downgraded["redlineBlinkInterval"] = 0
            
    # 4. Generic fallback if ledColor still contains aliases
    if "ledColor" in downgraded and len(downgraded["ledColor"]) > 0:
        if not downgraded["ledColor"][0].startswith("#"):
            downgraded["ledColor"][0] = "#FF00FF00"
            
    # 5. Generic fallback for ledRpm string parsing
    if "ledRpm" in downgraded and isinstance(downgraded["ledRpm"], list):
        for i, gear_obj in enumerate(downgraded["ledRpm"]):
            if not isinstance(gear_obj, dict):
                continue
            new_gear_obj = {}
            for gear, rpms in gear_obj.items():
                if not isinstance(rpms, list):
                    new_gear_obj[gear] = rpms
                    continue
                parsed_rpms = []
                for val in rpms:
                    if isinstance(val, str) and "-" in val and not val.startswith("-"):
                        try:
                            first_part = val.split("-")[0].strip()
                            if "." in first_part:
                                parsed_rpms.append(float(first_part))
                            else:
                                parsed_rpms.append(int(first_part))
                        except ValueError:
                            parsed_rpms.append(val)
                    else:
                        parsed_rpms.append(val)
                new_gear_obj[gear] = parsed_rpms
            downgraded["ledRpm"][i] = new_gear_obj

    # 6. Truncate arrays to ledNumber + 1 for v2.0.0 compliance
    # Since stages are at the BEGINNING of the array (vHH3.0 might have multiple stages), 
    # we must keep the 1st stage and the last N base colors.
    expected_len = downgraded.get("ledNumber")
    if expected_len is None and base_data:
        expected_len = base_data.get("ledNumber")
        
    if expected_len is not None:
        expected_len += 1
        num_base_colors = expected_len - 1
        
        if "ledColor" in downgraded and isinstance(downgraded["ledColor"], list):
            arr = downgraded["ledColor"]
            if len(arr) > expected_len:
                downgraded["ledColor"] = [arr[0]] + arr[-num_base_colors:]
                
        if "ledRpm" in downgraded and isinstance(downgraded["ledRpm"], list):
            for gear_obj in downgraded["ledRpm"]:
                if isinstance(gear_obj, dict):
                    for gear, rpms in gear_obj.items():
                        if isinstance(rpms, list) and len(rpms) > expected_len:
                            gear_obj[gear] = [rpms[0]] + rpms[-num_base_colors:]

    # 7. Enforce original key order
    original_key_order = ["carName", "carId", "carClass", "ledNumber", "redlineBlinkInterval", "ledColor", "ledRpm"]
    final_ordered = {}
    for k in original_key_order:
        if k in downgraded:
            final_ordered[k] = downgraded[k]
    for k in downgraded:
        if k not in final_ordered:
            final_ordered[k] = downgraded[k]
            
    return final_ordered

def format_car_profile(data):
    # Enforce original key order
    original_key_order = ["carName", "carId", "carClass", "ledNumber", "redlineBlinkInterval", "ledColor", "ledRpm"]
    ordered_data = {}
    for k in original_key_order:
        if k in data:
            ordered_data[k] = data[k]
    for k in data:
        if k not in ordered_data:
            ordered_data[k] = data[k]

    # First dump with standard indent=2
    json_str = json.dumps(ordered_data, indent=2, ensure_ascii=False)
    
    # Compress ledColor array
    def compress_led_color(match):
        prefix = match.group(1)
        values = re.findall(r'"[^"]*"', match.group(2))
        return prefix + '[' + ','.join(values) + ']'
    
    json_str = re.sub(r'("ledColor":\s*)\[([^\]]*)\]', lambda m: compress_led_color(m), json_str)
    
    # Compress ledRpm gear arrays
    def compress_rpm(match):
        newline = match.group(1)
        spaces = match.group(2)
        key_name = match.group(3)
        inner = match.group(4)
        values = re.findall(r'"[^"]*"|-?\d+\.?\d*', inner)
        return f'{newline}{spaces}"{key_name}": [' + ','.join(values) + ']'
        
    json_str = re.sub(r'(^|\n)(\s*)"([RN1-9])":\s*\[([^\]]*)\]', lambda m: compress_rpm(m), json_str)
    return json_str + "\n"

def process_directory(src_dir, dest_dir):
    for root, dirs, files in os.walk(src_dir):
        # Determine the relative path to maintain directory structure
        rel_path = os.path.relpath(root, src_dir)
        current_dest_dir = os.path.join(dest_dir, rel_path) if rel_path != '.' else dest_dir
        
        os.makedirs(current_dest_dir, exist_ok=True)
        
        for filename in files:
            if not filename.endswith('.json'):
                continue
            src_path = os.path.join(root, filename)
            dest_path = os.path.join(current_dest_dir, filename)
            
            try:
                data = load_jsonc(src_path)
                downgraded = downgrade_car_profile(data)
                json_str = format_car_profile(downgraded)
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python downgrade_schema.py <src_dir> <dest_dir>")
        sys.exit(1)
    process_directory(sys.argv[1], sys.argv[2])
