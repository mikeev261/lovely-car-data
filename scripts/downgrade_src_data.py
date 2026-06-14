import os
import json
import re
import downgrade_schema

def downgrade_src_file(data):
    # Process the base profile
    variants = data.pop("variants", [])
    
    # downgrade base template
    downgraded_base = downgrade_schema.downgrade_car_profile(data)
    downgraded_base["_schemaVersion"] = "v2.0.0"
    
    # move _schemaVersion to top
    ordered_base = {"_schemaVersion": "v2.0.0"}
    for k, v in downgraded_base.items():
        if k != "_schemaVersion":
            ordered_base[k] = v
            
    # process variants
    downgraded_variants = []
    for variant in variants:
        dv = downgrade_schema.downgrade_car_profile(variant, base_data=data)
        downgraded_variants.append(dv)
        
    ordered_base["variants"] = downgraded_variants
    return ordered_base

def process_directory(src_dir, dest_dir):
    # Keep track of valid files to clean up orphaned ones
    valid_dest_files = set()
    
    for root, dirs, files in os.walk(src_dir):
        rel_path = os.path.relpath(root, src_dir)
        current_dest_dir = os.path.join(dest_dir, rel_path) if rel_path != '.' else dest_dir
        os.makedirs(current_dest_dir, exist_ok=True)
        
        for filename in files:
            if not filename.endswith('.jsonc'):
                continue
            src_path = os.path.join(root, filename)
            dest_path = os.path.join(current_dest_dir, filename)
            
            try:
                data = downgrade_schema.load_jsonc(src_path)
                downgraded = downgrade_src_file(data)
                
                # Format with standard format_car_profile but preserve variants
                json_str = json.dumps(downgraded, indent=2, ensure_ascii=False)
                
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
                    
                json_str = re.sub(r'(^|\n)(\s*)"([RN0-9]+)":\s*\[([^\]]*)\]', lambda m: compress_rpm(m), json_str)
                
                # Compress generator objects back to single lines
                def compress_generator(match):
                    newline = match.group(1)
                    spaces = match.group(2)
                    key_name = match.group(3)
                    inner = match.group(4)
                    compressed_inner = re.sub(r'\s+', ' ', inner).strip()
                    return f'{newline}{spaces}"{key_name}": {{ {compressed_inner} }}'
                    
                json_str = re.sub(r'(^|\n)(\s*)"([RN0-9]+)":\s*\{\s*([^}]*?)\s*\}', lambda m: compress_generator(m), json_str)
                
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(json_str + "\n")
                valid_dest_files.add(os.path.normpath(dest_path))
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # Clean up orphaned files in dest_dir
    for root, dirs, files in os.walk(dest_dir):
        for filename in files:
            if not filename.endswith('.jsonc'):
                continue
            dest_path = os.path.normpath(os.path.join(root, filename))
            if dest_path not in valid_dest_files:
                try:
                    os.remove(dest_path)
                    print(f"Removed orphaned file: {dest_path}")
                except Exception as e:
                    print(f"Failed to remove {dest_path}: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python downgrade_src_data.py <src_dir> <dest_dir>")
        sys.exit(1)
    process_directory(sys.argv[1], sys.argv[2])
