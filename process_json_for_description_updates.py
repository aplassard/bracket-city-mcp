import json
import re
import os

# Ensure the directory for temporary files exists
os.makedirs('temp_data', exist_ok=True)

# Path to the JSON file
json_file_path = 'games/json/20250110.json'
current_game_data_py_path = 'temp_data/current_game_data.py'
id_map_for_descriptions_py_path = 'temp_data/id_map_for_descriptions.py'

game_data = None # Initialize game_data

# 1. Read the JSON file
try:
    with open(json_file_path, 'r', encoding='utf-8') as f:
        game_data = json.load(f)
except FileNotFoundError:
    print(f"Error: {json_file_path} not found.")
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {json_file_path}.")

if game_data is not None: # Proceed only if game_data was loaded successfully
    # Save the loaded game data
    try:
        with open(current_game_data_py_path, 'w', encoding='utf-8') as f:
            # Writing a large dict directly might be messy or hit repr limits for huge data.
            # For reasonable dict sizes, this is okay.
            # Consider json.dumps if it needs to be more robustly parseable later as a string
            # or if it's very large, but f.write(f'game_data = {game_data}\n') is what was asked.
            f.write(f'game_data = {game_data}\n')
        print(f"Successfully read {json_file_path} and stored its content in {current_game_data_py_path}")
    except IOError as e:
        print(f"Error writing to {current_game_data_py_path}: {e}")
        game_data = None # Nullify game_data if write failed, to prevent next step

if game_data is not None: # Proceed only if game_data was successfully loaded and saved
    # 2. Generate the clue_id_map for descriptions
    clue_id_map_for_desc = {}
    # The problem implies we are updating #CX# references within clue *descriptions*.
    # The example "a sun#C18# is observed by #C14# dynasty astro#C6#s" is from clue C19's description.
    # The keys in the JSON are already CLUE-CX (or C19).
    # The map should provide the new ID for any old ID found in text.
    for i in range(1, 21): # Create map for #C1# through #C20#
        old_id_format = f'#C{i}#'
        new_id_format = f'CLUE-C{i}' # This is the target format for these IDs
        clue_id_map_for_desc[old_id_format] = new_id_format

    try:
        with open(id_map_for_descriptions_py_path, 'w', encoding='utf-8') as f:
            f.write(f'id_map = {clue_id_map_for_desc}\n')
        print(f"Generated ID map (e.g., '#C1#' -> 'CLUE-C1') and stored in {id_map_for_descriptions_py_path}")
    except IOError as e:
        print(f"Error writing to {id_map_for_descriptions_py_path}: {e}")
else:
    # This message will now only appear if the initial read/parse of json_file_path failed,
    # or if the subsequent write to current_game_data_py_path failed.
    print(f"Skipping map generation due to errors reading/parsing {json_file_path} or saving to {current_game_data_py_path}.")
