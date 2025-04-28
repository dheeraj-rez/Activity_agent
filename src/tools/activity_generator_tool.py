from src.tools.clients import openai_client
import json
import os
from pathlib import Path
import math

def build_prompt(json_chunk):
        return f"""
    You are a Hands on Activity maker expert means which can be performed in the live class so for the school students.

    You are given one json:
    It contains a list of activity objects with fields like "activity", "concept", "materials", "description", and "page".

    ----
    Your task:
    You have to generate new activities based on activities provided in JSON Chunk (It could be the combination of two or more activities).
    Output format should be same as the json but pageNo will be all page numbers which you are combining (like page : [1,2,3])

    While creating new activity you have to make sure following criteria.

    - The activity should be Hands-on activities
    - Strand coverage – try to include at least one activity from each strand, if possible
    - Ensure the activity can be conducted safely in class.
    - Concepts should have some depth.
    - Material accessibility, It should be of low cost and easily available.
    - Must include as much skills coverage as possible
    - Transdisciplinary coverage is a plus.
    - Description should be well defined keeping in mind that the user who is seeing output of this does not have parent json.
    - Avoid the activities which includes pen, paper or drawing posters, banners, etc..

    ⚠️ Rules:
    - The output must be **strictly valid JSON**.
    - Do NOT return any explanations, comments, or code. Only return a JSON array.
    - Do NOT wrap the result in markdown or triple backticks.
    - Include only four or less than four best activities.

    *** You are free to create new activities based on the activities provided in JSON Chunk. Add extra materials if needed. But make sure that the new activity is not too long and can be performed in a single class.***
    *** Activities created should be able to judge the concepts of students like engage, explore, explain and extend ***

    JSON Chunk:
    {json.dumps(json_chunk, indent=2)}
    """

def generate_activities(filtered_master_json_path:str) -> str:
    """
    Generate activities from the filtered master JSON file using OpenAI's API.

    Args:
        filtered_master_json_path (str): Path to the filtered master JSON file.

    Returns:
        str: Path to the generated activities JSON file.
    """
    # Check if the provided path is a valid JSON file
    if not filtered_master_json_path.endswith('.json'):
        return "Invalid input. Please provide a valid JSON file path."
    
    # Check if the file exists
    if not os.path.isfile(filtered_master_json_path):
        return f"Filtered master JSON file not found: {filtered_master_json_path}"

    # Load the filtered master JSON file
    with open(filtered_master_json_path, "r") as f:
        filered_json = json.load(f)

    # Check if the JSON data is in the expected format
    if filered_json is None:
        return "Error loading JSON data. Please check the file contents."
    
    if not isinstance(filered_json, list):
        return "Invalid JSON format. Expected a list of activities."
    
    if not all(isinstance(item, dict) for item in filered_json):
        return "Invalid JSON structure. Expected list of objects."
    
    batch_size = 20
    all_activities = []

    # Process the JSON data in chunks
    for i in range(0, len(filered_json), batch_size):
        json_chunk = filered_json[i:i + batch_size]
        prompt = build_prompt(json_chunk)
        
        print(f"Sending chunk {i // batch_size + 1}/{math.ceil(len(filered_json) / batch_size)}")
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Combining activities create a new activity"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            chunk_result_raw = response.choices[0].message.content

            try:
                chunk_matches = json.loads(chunk_result_raw)
                all_activities.extend(chunk_matches)
            except json.JSONDecodeError:
                print(f"Failed to parse chunk {i // batch_size + 1}:")
                print(chunk_result_raw)
                continue
        except Exception as e:
            print(f"Error in chunk {i // batch_size + 1}: {e}")
            continue

    output_dir = Path(filtered_master_json_path).parent.resolve()
    output_path = os.path.join(output_dir, "new_activities.json")

    try:
        with open(output_path, "w") as outfile:
            json.dump(all_activities, outfile, indent=2)
    except Exception as e:
        print(f"Error saving generated activities: {e}")
        return f"Error saving generated activities: {e}"
    
    return f"Generated activities saved to {output_path}"
        

    



      