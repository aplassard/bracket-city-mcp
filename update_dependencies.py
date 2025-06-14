from parsed_json_data import parsed_data
from id_mapping import clue_id_map

if 'clues' in parsed_data and clue_id_map:
    updated_count = 0
    for clue_id, clue_data in parsed_data['clues'].items(): # Iterate with clue_id for better logging if needed
        if 'depends_on' in clue_data and isinstance(clue_data['depends_on'], list):
            original_dependencies = clue_data['depends_on']
            updated_dependencies = []
            changed_in_this_clue = False
            for dep_id in original_dependencies:
                new_dep_id = clue_id_map.get(dep_id, dep_id)
                updated_dependencies.append(new_dep_id)
                if new_dep_id != dep_id:
                    changed_in_this_clue = True

            if changed_in_this_clue:
                clue_data['depends_on'] = updated_dependencies
                updated_count += 1

    # Save the modified parsed_data back to parsed_json_data.py
    try:
        with open('parsed_json_data.py', 'w') as f:
            f.write(f'parsed_data = {parsed_data}\n')
        print(f"Updated 'depends_on' references for {updated_count} clue(s).")
        # For verification, print a specific clue that had dependencies
        # Example: CLUE-C3 depends on #C2# (now CLUE-C2)
        # if 'CLUE-C3' in parsed_data['clues']:
        #    print("\nVerification: CLUE-C3 dependencies:")
        #    print(parsed_data['clues']['CLUE-C3']['depends_on'])
        # if 'C19' in parsed_data['clues'] and parsed_data['clues']['C19']['depends_on']:
        #    print("\nVerification: C19 dependencies:")
        #    print(parsed_data['clues']['C19']['depends_on'])


    except IOError as e:
        print(f"Error saving updated parsed_json_data.py: {e}")
else:
    print("No 'clues' data found in parsed_data or clue_id_map is empty. Skipping update of 'depends_on' references.")

# print("\nFull updated parsed_data for verification (first level keys):")
# print(parsed_data.keys())
# if 'clues' in parsed_data and 'CLUE-C6' in parsed_data['clues']: # CLUE-C6 has multiple dependencies
#    print("Dependencies for CLUE-C6 after update:")
#    print(parsed_data['clues']['CLUE-C6']['depends_on'])

# Check C19, which has dependencies that should be updated
# if 'clues' in parsed_data and 'C19' in parsed_data['clues']:
#    print("Dependencies for C19 after update:")
#    print(parsed_data['clues']['C19']['depends_on'])
