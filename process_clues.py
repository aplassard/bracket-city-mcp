import re
# Ensure parsed_json_data.py is in the same directory or accessible in PYTHONPATH
from parsed_json_data import parsed_data

clue_id_map = {}
if 'clues' in parsed_data:
    for old_id in parsed_data['clues'].keys():
        match = re.fullmatch(r'#C(\d+)#', old_id)
        if match:
            numeric_part = match.group(1)
            new_id = f'CLUE-C{numeric_part}'
            clue_id_map[old_id] = new_id
        else:
            # Handle cases where the old_id doesn't match the pattern, if any
            # For now, we'll just print a warning or skip
            if old_id not in ("C19"): # C19 is a known case from the provided JSON
                print(f"Warning: ID '{old_id}' does not match expected pattern '#C<number>#'. Skipping.")


# Save the map for subsequent steps
try:
    with open('id_mapping.py', 'w') as f:
        f.write(f'clue_id_map = {clue_id_map}\n')
    print(f"Generated ID map: {clue_id_map}")
    print("Saved id_mapping.py successfully.")
except IOError as e:
    print(f"Error saving id_mapping.py: {e}")

# As a verification step, let's also check the content of parsed_data to be sure
# print("\nContent of parsed_data for verification:")
# print(parsed_data)

if not clue_id_map:
    print("Warning: clue_id_map is empty. Check parsed_data and regex logic.")

# Example of how C19 is handled (or not handled by the regex)
if 'C19' in parsed_data['clues']:
    print("\nNote: 'C19' is present in parsed_data['clues'] but does not match '#C<number>#', so it's not in clue_id_map.")
