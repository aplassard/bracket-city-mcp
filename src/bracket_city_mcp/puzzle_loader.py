import sys
import json
import re
import requests
from bs4 import BeautifulSoup

def generate_puzzle_structure(html_content: str) -> dict:
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
         # Use sys.stderr for warnings if this function is ever used in a context where stdout is for data
         print("Warning: Could not find the final solution text.", file=sys.stderr)


    # --- Step 3: Recursively parse the string to build the structure ---
    final_clues = {}
    # clue_id_counter = 1 # This was unused, can be removed

    sorted_clues = sorted(clue_text_to_answer.keys(), key=len, reverse=True)
    clue_text_to_id = {text: f"CLUE-C{i+1}" for i, text in enumerate(sorted_clues)}
    
    innermost_bracket_regex = re.compile(r'\[([^\[\]]+)\]')

    processing_string = puzzle_string
    while '[' in processing_string:
        match = innermost_bracket_regex.search(processing_string)
        if not match:
            # Use sys.stderr for warnings
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
            # Use sys.stderr for warnings
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
        # Log to stderr or use proper logging if available
        print(f"Error fetching URL {url}: {e}", file=sys.stderr)
        return {"error": f"Failed to fetch HTML from URL: {url}. Error: {e}"}
    except Exception as e: # Catch any other unexpected errors during parsing
        print(f"Unexpected error processing URL {url}: {e}", file=sys.stderr)
        return {"error": f"An unexpected error occurred while processing URL {url}: {e}"}

# Note: The main() function and if __name__ == '__main__' block from
# scripts/parse_game_html.py are intentionally omitted as this is now a module.


def load_game_data_by_date(date_str: str) -> dict:
    """
    Loads game data for a given date, trying a local JSON file first,
    then falling back to fetching from a URL.

    Args:
        date_str (str): The date of the puzzle in "YYYY-MM-DD" format.

    Returns:
        dict: A dictionary containing the puzzle data, or an error dictionary
              if loading/fetching/parsing fails.
    """
    file_date_str = date_str.replace("-", "")
    filepath = f"games/json/{file_date_str}.json"

    try:
        # Attempt to load from local JSON file first
        with open(filepath, 'r', encoding='utf-8') as f:
            game_data = json.load(f)
        # Optional: print a message if loaded from file
        # print(f"Loaded game data for {date_str} from local file: {filepath}", file=sys.stderr)
        return game_data
    except FileNotFoundError:
        # File not found, fall back to fetching from URL
        # print(f"Local file {filepath} not found for date {date_str}. Attempting to fetch from URL.", file=sys.stderr)
        # The date_str for parse_game_from_url needs to be in YYYY-MM-DD,
        # which is the format of our input date_str.
        # It internally constructs the full URL.
        url = f"https://ladypuzzle.pro/bracket-city-hints-answers-solution/{date_str}"
        return parse_game_from_url(url)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {filepath} for date {date_str}: {e}", file=sys.stderr)
        return {"error": f"Error decoding JSON from {filepath}: {e}"}
    except IOError as e:
        print(f"IOError reading file {filepath} for date {date_str}: {e}", file=sys.stderr)
        return {"error": f"IOError reading file {filepath}: {e}"}
    except Exception as e: # Catch any other unexpected errors during file operations
        print(f"An unexpected error occurred with file {filepath} for date {date_str}: {e}", file=sys.stderr)
        return {"error": f"An unexpected error occurred while trying to load from file {filepath}: {e}"}
