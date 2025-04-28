from src.tools.clients import openai_client
from src.utils.helper import parse_json_file
import json
import os
import math
from pathlib import Path
import re
# Load JSON1 and JSON2 from files to build the prompt
def build_prompt(json1_chunk, json2):
    return f"""
You are a JSON extraction expert.

You are given two JSONs:

### JSON1 (activities)
It contains a list of activity objects with fields like "activity", "concept", "materials", "description", and "page".

### JSON2 (units)
It is a list of units. Each unit contains one or more activity names under the "activity" key.

---

Your task:

For each unit in JSON2, find activity names that exactly match any "activity" field in JSON1. For each match, return an object with:

- "page": page number from JSON1
- "json1_activity": full activity string from JSON1
- "json2_activity": matching string from JSON2

⚠️ Rules:
- The output must be **strictly valid JSON**.
- Do NOT return any explanations, comments, or code. Only return a JSON array.
- If no matches are found, return an **empty array**: `[]`
- Do NOT wrap the result in markdown or triple backticks.

---

JSON1 chunk:
{json.dumps(json1_chunk, indent=2)}

---

JSON2 full:
{json.dumps(json2, indent=2)}

Return the matched results in an array format.
"""

# tool to match activities in JSON1 and JSON2
def match_activities(master_json_path, users_json_path) -> str:
    """
    Match activities from two JSON files using OpenAI API.
    args:
        master_json_path (str): Path to the master JSON file containing activities.
        users_json_path (str): Path to the users JSON file containing units.
    returns:
        str: A message indicating the result of the operation and path of output json file.
    """
    batch_size = 10  # You can adjust this depending on how long your activities are
    all_matches = []
    
    # Check if the provided paths are valid JSON files
    if not (master_json_path.endswith('.json') and users_json_path.endswith('.json')):
        return "Invalid input. Please provide valid JSON file paths."

    # Checking if the files exist
    if not os.path.exists(master_json_path):
        return f"Master JSON file not found: {master_json_path}"
    if not os.path.exists(users_json_path):
        return f"Users JSON file not found: {users_json_path}"
    
    # Load your JSON data
    with open(master_json_path, "r") as f1:
        json1 = json.load(f1)

    with open(users_json_path, "r") as f2:
        json2 = json.load(f2)

    # Check if the JSON data is loaded correctly
    if json1 is None or json2 is None:
        return "Error loading JSON data. Please check the file contents."
    # Check if the JSON data is in the expected format
    if not isinstance(json1, list) or not isinstance(json2, list):
        return "Invalid JSON format. Expected a list of activities."

    # Chunking logic
    for i in range(0, len(json1), batch_size):
        json1_chunk = json1[i:i + batch_size]
        prompt = build_prompt(json1_chunk, json2)

        print(f"Sending chunk {i // batch_size + 1}/{math.ceil(len(json1) / batch_size)}")

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Extract activities common in both"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            chunk_result_raw = response.choices[0].message.content

            try:
                chunk_matches = json.loads(chunk_result_raw)
                all_matches.extend(chunk_matches)
            except json.JSONDecodeError:
                print(f"Failed to parse chunk {i // batch_size + 1}:")
                print(chunk_result_raw)
                continue
        except Exception as e:
            print(f"Error in chunk {i // batch_size + 1}: {e}")
            continue
        
    if all_matches:
        output_dir = Path(master_json_path).parent.resolve()
        output_path = os.path.join(output_dir, "matched_activities.json")

        try:
            # Save final results to a JSON file
            with open(output_path, "w") as outfile:
                json.dump(all_matches, outfile, indent=2)
            
            return f"Matched activities saved to {output_path}"
        except Exception as e:
            print(f"Error saving matched activities: {e}")
            return f"Error saving matched activities: {e}"
    else:
        return "No matches found in the provided JSON files."


# Wrapper function to parse input string and call the match_activities function
def activity_match_wrapper(input_str: str) -> str:
    """
    Wrapper function to parse input string and call the match_activities function.
    args:
        input_str (str): Input string containing JSON file paths.
    returns:
        str: Result of the match_activities function or error message.
    """
    master_json_path, users_json_path = parse_json_file(input_str)
    
    if not master_json_path or not users_json_path:
        return "Invalid input. Please provide two valid JSON file paths."
    
    return match_activities(master_json_path, users_json_path)


if __name__ == "__main__":
    # Example usage
    master_json_path = r"C:\Users\LPT029\Downloads\CLS_7-1-100_activities.json"
    users_json_path = r"C:\Users\LPT029\Downloads\activities.json"
    result = match_activities(master_json_path, users_json_path)
    print(result)