import sys
import json
import re
from bs4 import BeautifulSoup
try:
    import requests
except ModuleNotFoundError:
    print("The 'requests' library is not installed. Please install it by running 'pip install requests'", file=sys.stderr)
    # As per instructions, attempting to install if missing.
    # This is generally not recommended for library code but following instructions.
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

def generate_puzzle_structure(html_content):
    """
    Parses the HTML of a Bracket City puzzle page to extract the full nested
    clue structure by recursively parsing the raw puzzle string.

    Args:
        html_content (str): The full HTML content of the puzzle page.

    Returns:
        dict: A dictionary containing the fully structured puzzle data.
    """
    soup = BeautifulSoup(html_content, 'lxml')

    # --- Step 1: Create a master map of all clues and their answers ---
    answers_list_ul = soup.find('ul', id='answers-list')
    if not answers_list_ul:
        return {"error": "Could not find the 'answers-list' <ul> element."}

    clue_text_to_answer = {}
    for li in answers_list_ul.find_all('li'):
        clue_h2 = li.find('h2')
        answer_span = li.find('span', class_='clue-text-answer')
        if clue_h2 and answer_span:
            clue_text = clue_h2.get_text(strip=True)
            answer_text = answer_span.get_text(strip=True)
            clue_text_to_answer[clue_text] = answer_text
    
    if not clue_text_to_answer:
        return {"error": "No clues found in the answers list."}
        
    # --- Step 2: Extract the raw puzzle string and the final solution text ---
    interactive_div = soup.find('div', class_='html-answers-interactive')
    if not interactive_div:
        return {"error": "Could not find the 'html-answers-interactive' <div> element."}
    
    puzzle_string = interactive_div.get_text()
    # Normalize all whitespace (including newlines and tabs) into single spaces
    puzzle_string = re.sub(r'\s+', ' ', puzzle_string).strip()

    final_solution_text = ""
    # Find the H1 header for the final solution section
    solution_h1 = soup.find('h1', string=re.compile(r"Today's \[BRACKET CITY\] Final Solution"))
    
    # Search within the H1's parent container for the answer
    if solution_h1 and solution_h1.parent:
        # Search within this container for a 'strong' tag, which holds the answer text.
        solution_strong_tag = solution_h1.parent.find('strong')
        if solution_strong_tag:
             final_solution_text = solution_strong_tag.get_text(strip=True)
             # Strip the date prefix (e.g., "June 1, 1974: ") if it exists
             final_solution_text = re.sub(r'^(\w+\s\d+,\s\d{4}:\s)', '', final_solution_text).strip()

    if not final_solution_text:
         print("Warning: Could not find the final solution text.", file=sys.stderr)


    # --- Step 3: Recursively parse the string to build the structure ---
    final_clues = {}
    clue_id_counter = 1

    sorted_clues = sorted(clue_text_to_answer.keys(), key=len, reverse=True)
    clue_text_to_id = {text: f"CLUE-C{i+1}" for i, text in enumerate(sorted_clues)}
    
    innermost_bracket_regex = re.compile(r'\[([^\[\]]+)\]')

    processing_string = puzzle_string
    while '[' in processing_string:
        match = innermost_bracket_regex.search(processing_string)
        if not match:
            print("Warning: Could not find innermost bracket. The puzzle string may be malformed or fully processed.", file=sys.stderr)
            break

        inner_content = match.group(1).strip()
        
        found_clue_text = None
        
        # Create a regex from the inner_content by replacing all found CLUE-IDs with a wildcard.
        temp_inner_content = re.sub(r'CLUE-C\d+', "%%PLACEHOLDER%%", inner_content)
        escaped_content = re.escape(temp_inner_content)
        regex_pattern_str = escaped_content.replace("%%PLACEHOLDER%%", '.*?')
        regex_pattern = f"^{regex_pattern_str}$"

        for known_clue in sorted_clues:
            if re.match(regex_pattern, known_clue):
                found_clue_text = known_clue
                break
        
        if found_clue_text:
            clue_id = clue_text_to_id[found_clue_text]
            found_ids = re.findall(r'CLUE-C\d+', inner_content)
            
            final_clues[clue_id] = {
                "clue": inner_content,
                "depends_on": sorted(list(set(found_ids))),
                "answer": clue_text_to_answer[found_clue_text]
            }
            processing_string = processing_string.replace(f'[{match.group(1)}]', clue_id, 1)
        else:
            print(f"Warning: Could not find a matching clue for content: '{inner_content}'", file=sys.stderr)
            processing_string = processing_string.replace(f'[{match.group(1)}]', inner_content, 1)

    # --- Step 4: Create the final root clue ---
    root_clue_text = processing_string
    root_dependencies = re.findall(r'CLUE-C\d+', root_clue_text)
    
    final_clues["CLUE-ROOT"] = {
        "clue": root_clue_text,
        "depends_on": sorted(list(set(root_dependencies))),
        "answer": final_solution_text
    }

    return {"clues": final_clues}


def parse_game_from_url(url: str) -> dict:
    """
    Fetches HTML content from a URL and parses it to extract puzzle structure.

    Args:
        url (str): The URL of the puzzle page.

    Returns:
        dict: A dictionary containing the fully structured puzzle data,
              or an error dictionary if fetching/parsing fails.
    """
    try:
        response = requests.get(url, timeout=10)  # Added timeout for robustness
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        html_content = response.text
        return generate_puzzle_structure(html_content)
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch HTML from URL: {url}. Error: {e}"}
    except Exception as e: # Catch any other unexpected errors during parsing
        return {"error": f"An unexpected error occurred while processing URL {url}: {e}"}


def main():
    """
    Main function to handle file input from the command line,
    parse the file, and print the output.
    """
    if len(sys.argv) != 2:
        print("Usage: python parse_bracket_city.py <path_to_html_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        sys.exit(1)

    puzzle_data = generate_puzzle_structure(html_content)

    print(json.dumps(puzzle_data, indent=4))

if __name__ == '__main__':
    main()
