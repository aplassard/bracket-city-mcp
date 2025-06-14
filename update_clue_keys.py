import json # Using json for pretty printing the output for verification
from parsed_json_data import parsed_data
from id_mapping import clue_id_map

if 'clues' in parsed_data and clue_id_map:
    original_clues = parsed_data['clues']
    updated_clues = {}
    for old_id, clue_data in original_clues.items():
        new_id = clue_id_map.get(old_id, old_id) # Get new_id if exists, else keep old_id (e.g. for 'C19')
        updated_clues[new_id] = clue_data

    parsed_data['clues'] = updated_clues

    # Save the modified parsed_data back to parsed_json_data.py
    # We need to be careful here. The original parsed_json_data.py stores the raw JSON string
    # and then parses it. If we just write the Python dict back, it's a change in format.
    # The request was to update the parsed_data dictionary.
    # For subsequent Python steps, having parsed_data as a dict is fine.
    # If the goal is to rewrite the original JSON file, that's a different step.
    # The instructions say "Save the modified parsed_data back to parsed_json_data.py"
    # This means the file parsed_json_data.py will now directly contain the dictionary.

    try:
        with open('parsed_json_data.py', 'w') as f:
            # To make it a bit more robust for reading back, especially if it becomes complex,
            # let's import pprint for better formatting if needed, or just str() for simple dicts.
            # For this case, a simple f-string with the dict should work as it did before.
            f.write(f'parsed_data = {parsed_data}\n')
        print("Updated clue keys in parsed_data and overwrote parsed_json_data.py.")
        # For verification, print part of the updated structure
        # print("\nSample of updated parsed_data['clues'] keys:")
        # for i, k in enumerate(parsed_data['clues'].keys()):
        #     if i < 5: # print first 5 keys
        #         print(k)
        #     else:
        #         break
    except IOError as e:
        print(f"Error saving updated parsed_json_data.py: {e}")

else:
    print("No 'clues' data found in parsed_data or clue_id_map is empty. Skipping update of clue keys.")

# print("\nFull updated parsed_data for verification (first level keys):")
# print(parsed_data.keys())
# if 'clues' in parsed_data:
#    print("First few items in parsed_data['clues'] after update:")
#    for i, (k, v) in enumerate(parsed_data['clues'].items()):
#        print(f"Key: {k}, Answer: {v.get('answer', 'N/A')}")
#        if i >= 4:
#            break
