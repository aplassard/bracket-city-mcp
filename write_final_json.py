import json
from parsed_json_data import parsed_data # This now directly contains the Python dict

output_file_path = './games/json/20250110.json'

try:
    # Ensure the directory exists - though in this case, it should.
    # import os
    # os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=4, ensure_ascii=False)
    print(f"Successfully wrote modified game data to {output_file_path}")

    # For quick verification, print a small part of what was written (or would be written)
    # This is just a local print, the actual file content is the true test.
    # if 'clues' in parsed_data and 'CLUE-C3' in parsed_data['clues']:
    #     print("\nSample of data written (CLUE-C3):")
    #     print(json.dumps({'CLUE-C3': parsed_data['clues']['CLUE-C3']}, indent=4, ensure_ascii=False))
    # if 'clues' in parsed_data and 'C19' in parsed_data['clues']:
    #     print("\nSample of data written (C19):")
    #     print(json.dumps({'C19': parsed_data['clues']['C19']}, indent=4, ensure_ascii=False))


except Exception as e:
    print(f"Error writing modified game data to {output_file_path}: {e}")
    # To aid debugging if something goes wrong, print the type of parsed_data
    print(f"Type of parsed_data: {type(parsed_data)}")
    if isinstance(parsed_data, str):
        print("parsed_data is a string. It should be a dictionary for json.dump().")
        print("Content of string (first 500 chars):", parsed_data[:500])
