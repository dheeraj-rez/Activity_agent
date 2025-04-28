import json
import os
from pathlib import Path
from src.utils.helper import parse_json_file

def activity_filter(master_json_path: str, match_json_path: str) -> str:
    """
    Function to filter activities from a master JSON file based on a match JSON file.
    args:
        master_json (str): Path to the master JSON file.
        match_json (str): Path to the match JSON file.
    returns:
        str: Result of the filtering process or error message.
    """
    # Check if the provided paths are valid JSON files
    if not (master_json_path.endswith('.json') and match_json_path.endswith('.json')):
        return "Invalid input. Please provide valid JSON file paths."

    # Check if the files exist
    if not os.path.isfile(master_json_path):
        return f"Master JSON file not found: {master_json_path}"
    
    if not os.path.isfile(match_json_path):
        return f"Match JSON file not found: {match_json_path}"
    
    # Load the master and match JSON files
    with open(master_json_path, "r") as f:
        master_data = json.load(f)
    
    with open(match_json_path, "r") as f:
        match_data = json.load(f)
    
    # Check if the JSON data is in the expected format
    if master_data is None or match_data is None:
        return "Error loading JSON data. Please check the file contents."
    
    if not isinstance(master_data, list) or not isinstance(match_data, list):
        return "Invalid JSON format. Expected a list of activities."
    
    if not all(isinstance(item, dict) for item in master_data) or not all(isinstance(item, dict) for item in match_data):
        return "Invalid JSON structure. Expected list of objects."

    if "activity" not in master_data[0] or "page" not in master_data[0]:
        return "Invalid JSON structure. Expected 'activity' and 'page' keys in the objects."

    filtered_data = [
        item for item in master_data
        if not any(item['page'] == entry['page'] and item['activity'] == entry['json1_activity'] for entry in match_data)
    ]

    output_dir = Path(master_json_path).parent.resolve()
    file_name = os.path.basename(master_json_path).replace(".json", "_filtered.json")
    output_path = os.path.join(output_dir, file_name)

    try:
        # Save final results to a JSON file
        with open(output_path, "w") as outfile:
            json.dump(filtered_data, outfile, indent=2)
    except Exception as e:
        print(f"Error saving filtered activities: {e}")
        return f"Error saving filtered activities: {e}"
    
    return f"Filtered activities saved to {output_path}"

# Wrapper function to parse input string and call the activity_filter function
def activity_filter_wrapper(input_str: str) -> str:
    """
    Wrapper function to parse input string and call the activity_filter function.
    args:
        input_str (str): Input string containing JSON file paths.
    returns:
        str: Result of the activity_filter function or error message.
    """
    master_json_path, match_json_path = parse_json_file(input_str)
    
    if not master_json_path or not match_json_path:
        return "Invalid input. Please provide two valid JSON file paths."
    
    return activity_filter(master_json_path, match_json_path)

