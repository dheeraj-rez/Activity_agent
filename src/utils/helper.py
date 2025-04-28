from pathlib import Path
import re

# ---- Helper function ----
def parse_json_file(input_str: str) -> tuple[str | None, str | None]:
    input_str = input_str.strip()
    if not input_str:
        return None, None
    
    # Regex to find JSON file paths in the input string
    paths = re.findall(r"['\"]?([^,'\"\s]+\.json)['\"]?", input_str)

    if len(paths) >= 2:
        path1 = Path(paths[0]).as_posix()
        path2 = Path(paths[1]).as_posix()
        print(f"Parser found two paths: {path1}, {path2}")
        return path1, path2
    else:
        print("Parser did not find two valid JSON file paths.")
        return None, None