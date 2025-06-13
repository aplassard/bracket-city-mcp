import json
import re
import argparse

def parse_bracket_city(game_string: str) -> str:
    """
    Parses a 'bracket city' game string into a structured JSON format.

    The function works by repeatedly finding the innermost bracketed clue,
    extracting its content, assigning it a unique ID (e.g., #C1#), and
    then replacing the original bracketed text with this ID in the main string.
    This process continues until no brackets are left.

    Args:
        game_string: The string containing the nested bracket puzzle.

    Returns:
        A JSON formatted string representing the parsed clues, their
        dependencies, and an empty placeholder for the answer.
    """
    clues = {}
    clue_counter = 1
    
    # Use a working copy of the string that we can modify
    processing_string = game_string

    # Loop as long as there are opening brackets in the string
    while '[' in processing_string:
        # Find the position of the *last* opening bracket. This ensures
        # we are always starting with the most deeply nested clue.
        last_open_bracket_pos = processing_string.rfind('[')
        
        # From that position, find the *first* closing bracket. This
        # pair will define the innermost clue.
        first_close_bracket_pos = processing_string.find(']', last_open_bracket_pos)

        if first_close_bracket_pos == -1:
            # Error case: Mismatched brackets. Stop processing.
            print("Error: Mismatched brackets found.")
            break
            
        # Extract the raw clue text from between the brackets
        clue_text = processing_string[last_open_bracket_pos + 1 : first_close_bracket_pos]
        
        # Generate the unique ID for this new clue
        clue_id = f"#C{clue_counter}#"
        
        # Find all dependency placeholders (e.g., #C1#, #C2#) already in the clue text
        # The re.findall will return a list like ['1', '7'], which we format.
        dependencies = sorted([f"#C{num}#" for num in re.findall(r'#C(\d+)#', clue_text)])
        
        # Store the extracted clue information
        clues[clue_id] = {
            "clue": clue_text.strip(),
            "answer": "",
            "depends_on": dependencies
        }
        
        # Replace the entire bracketed clue in the main string with its new ID
        # This simplifies the string for the next iteration.
        full_clue_substring = processing_string[last_open_bracket_pos : first_close_bracket_pos + 1]
        processing_string = processing_string.replace(full_clue_substring, clue_id, 1)
        
        # Increment the counter for the next clue
        clue_counter += 1

    # Create the final JSON structure, sorting clues by their number for readability
    sorted_clue_keys = sorted(clues.keys(), key=lambda x: int(re.search(r'(\d+)', x).group(1)))
    
    sorted_clues = {key: clues[key] for key in sorted_clue_keys}
    
    final_json_output = {
        "clues": sorted_clues
    }
    
    # Return the final result as a formatted JSON string
    return json.dumps(final_json_output, indent=2)

def main():
    """
    Main function to run the script from the command line.
    Handles reading from an input file and writing to an output file.
    """
    # Set up the argument parser to handle command-line arguments
    parser = argparse.ArgumentParser(
        description="Parse a 'bracket city' puzzle from a text file and save it as JSON."
    )
    parser.add_argument(
        "input_file", 
        help="The path to the input text file containing the puzzle string."
    )
    parser.add_argument(
        "output_file", 
        help="The path to the output JSON file where the result will be saved."
    )
    
    args = parser.parse_args()

    # Read the input file with error handling
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            raw_game_string = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_file}'")
        return
    except Exception as e:
        print(f"An error occurred while reading the input file: {e}")
        return

    # Parse the string and get the JSON output
    parsed_json = parse_bracket_city(raw_game_string)

    # Write the output to the specified JSON file with error handling
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(parsed_json)
        print(f"Successfully parsed puzzle and saved output to '{args.output_file}'")
    except Exception as e:
        print(f"An error occurred while writing to the output file: {e}")

if __name__ == "__main__":
    main()
