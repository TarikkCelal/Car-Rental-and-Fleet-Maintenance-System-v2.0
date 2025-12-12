import argparse
import sys
import os

# Ensure src is in pythonpath so we can import our modules
sys.path.append(os.path.join(os.getcwd(), 'src'))

from crfms.persistence.json_io import load_from_json, save_to_json
from crfms.persistence.proto_io import load_from_proto, save_to_proto

def main():
    parser = argparse.ArgumentParser(description="CRFMS Format Converter")
    
    # Create a group so user must pick one direction
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--to-proto", action="store_true", help="Convert JSON input to Protocol Buffers output")
    group.add_argument("--to-json", action="store_true", help="Convert Protocol Buffers input to JSON output")
    
    parser.add_argument("input_file", help="Path to input file")
    parser.add_argument("output_file", help="Path to output file")
    
    args = parser.parse_args()
    
    if args.to_proto:
        print(f"Converting JSON ({args.input_file}) -> Proto ({args.output_file})...")
        try:
            # 1. Load from JSON
            db = load_from_json(args.input_file)
            # 2. Save to Proto
            save_to_proto(db, args.output_file)
            print("Conversion successful.")
        except Exception as e:
            print(f"Error converting to Proto: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
    elif args.to_json:
        print(f"Converting Proto ({args.input_file}) -> JSON ({args.output_file})...")
        try:
            # 1. Load from Proto
            db = load_from_proto(args.input_file)
            # 2. Save to JSON
            save_to_json(db, args.output_file)
            print("Conversion successful.")
        except Exception as e:
            print(f"Error converting to JSON: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main()