import json
import os
import re # Though not used in the final version of user's code, re is good for complex patterns

# Attempt to import game_data and id_map
try:
    from temp_data.current_game_data import game_data
except ImportError:
    print("Error: Could not import game_data from temp_data.current_game_data.py. Ensure the file exists and is correct.")
    game_data = None

try:
    from temp_data.id_map_for_descriptions import id_map
except ImportError:
    print("Error: Could not import id_map from temp_data.id_map_for_descriptions.py. Ensure the file exists and is correct.")
    id_map = None

if game_data and 'clues' in game_data and id_map:
    updated_clue_count = 0
    for clue_key, clue_data in game_data['clues'].items():
        if 'clue' in clue_data and isinstance(clue_data['clue'], str):
            original_description = clue_data['clue']
            modified_description = original_description

            # Sort keys by length (descending) to handle #C10# before #C1#
            # This is crucial for correctness, e.g. ensures "#C10#" is not partially replaced by "CLUE-C1" + "0#"
            sorted_old_ids = sorted(id_map.keys(), key=len, reverse=True)

            for old_id_pattern in sorted_old_ids:
                if old_id_pattern in modified_description: # Only replace if pattern exists
                    new_id_replacement = id_map[old_id_pattern]
                    modified_description = modified_description.replace(old_id_pattern, new_id_replacement)

            if original_description != modified_description:
                game_data['clues'][clue_key]['clue'] = modified_description
                print(f"Updated description for clue '{clue_key}':")
                print(f"  Old: {original_description}")
                print(f"  New: {modified_description}")
                updated_clue_count +=1

    if updated_clue_count == 0:
        print("No descriptions were updated.")

    # Save the modified game_data back to temp_data/current_game_data.py
    output_py_file = 'temp_data/current_game_data.py'
    try:
        # Using repr() ensures that strings within the dictionary are properly quoted and escaped.
        with open(output_py_file, 'w', encoding='utf-8') as f:
            f.write(f'game_data = {game_data!r}\n')
        print(f"Successfully saved updated game data to {output_py_file}")
    except Exception as e:
        print(f"Error writing updated game data to {output_py_file}: {e}")
else:
    print("Game data, 'clues' key in game_data, or ID map not found/empty. Skipping description updates.")
    if not game_data:
        print("Reason: game_data is missing.")
    elif 'clues' not in game_data:
        print("Reason: 'clues' key is missing in game_data.")
    elif not id_map:
        print("Reason: id_map is missing.")
