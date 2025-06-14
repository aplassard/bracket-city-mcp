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
    
    processing_string = game_string

    # Loop as long as there are opening brackets in the string
    while '[' in processing_string:
        last_open_bracket_pos = processing_string.rfind('[')
        
        first_close_bracket_pos = processing_string.find(']', last_open_bracket_pos)

        if first_close_bracket_pos == -1:
            print("Error: Mismatched brackets found.")
            break
            
        clue_text = processing_string[last_open_bracket_pos + 1 : first_close_bracket_pos]
        
        clue_id = f"#C{clue_counter}#"
        
        dependencies = sorted([f"#C{num}#" for num in re.findall(r'#C(\d+)#', clue_text)])
        
        clues[clue_id] = {
            "clue": clue_text.strip(),
            "answer": "",
            "depends_on": dependencies
        }
        
        full_clue_substring = processing_string[last_open_bracket_pos : first_close_bracket_pos + 1]
        processing_string = processing_string.replace(full_clue_substring, clue_id, 1)
        
        clue_counter += 1

    sorted_clue_keys = sorted(clues.keys(), key=lambda x: int(re.search(r'(\d+)', x).group(1)))
    
    sorted_clues = {key: clues[key] for key in sorted_clue_keys}
    
    final_json_output = {
        "clues": sorted_clues
    }
    
    return json.dumps(final_json_output, indent=2)

def main():
    """
    Main function to run the script from the command line.
    Handles reading from an input file and writing to an output file.
    """
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

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            raw_game_string = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_file}'")
        return
    except Exception as e:
        print(f"An error occurred while reading the input file: {e}")
        return

    parsed_json = parse_bracket_city(raw_game_string)

    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(parsed_json)
        print(f"Successfully parsed puzzle and saved output to '{args.output_file}'")
    except Exception as e:
        print(f"An error occurred while writing to the output file: {e}")

if __name__ == "__main__":
    main()
