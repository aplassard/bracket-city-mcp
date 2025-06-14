import json
import os
import shutil # For removing directory

# Attempt to import game_data
try:
    from temp_data.current_game_data import game_data
    print(f"Successfully imported game_data from temp_data.current_game_data.py")
except ImportError:
    print("Error: Could not import game_data from temp_data.current_game_data.py. Halting.")
    game_data = None

output_json_file_path = 'games/json/20250110.json'
temp_data_dir = 'temp_data'

if game_data: # Proceed only if game_data was successfully imported
    try:
        # Ensure the target directory exists (it should, but good practice)
        # target_dir = os.path.dirname(output_json_file_path)
        # if not os.path.exists(target_dir):
        # os.makedirs(target_dir) # This would create games/json if it didn't exist

        with open(output_json_file_path, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=4, ensure_ascii=False)
        print(f"Successfully wrote fully updated game data to {output_json_file_path}")
    except Exception as e:
        print(f"Error writing updated game data to {output_json_file_path}: {e}")
else:
    print("No game data found to write (likely due to import error). Skipping JSON file update.")

# Clean up temporary data directory
if os.path.exists(temp_data_dir):
    try:
        shutil.rmtree(temp_data_dir)
        print(f"Successfully removed temporary directory: {temp_data_dir}")
    except Exception as e:
        print(f"Error removing temporary directory {temp_data_dir}: {e}")
else:
    print(f"Temporary directory {temp_data_dir} not found. No cleanup needed for it.")

# Verify removal (optional, for sanity check)
# if not os.path.exists(temp_data_dir):
#     print(f"Verified: {temp_data_dir} is gone.")
# else:
#     print(f"Warning: {temp_data_dir} still exists after removal attempt.")
