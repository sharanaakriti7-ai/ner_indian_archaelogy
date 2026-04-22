import base64
import re
import os

with open("RESEARCH_PAPER.md", "r", encoding="utf-8") as f:
    text = f.read()

# Regex to find markdown images with relative paths
pattern = r'!\[([^\]]*)\]\(([^)]+\.png)\)'

def replace_with_base64(match):
    alt_text = match.group(1)
    filepath = match.group(2)
    # Remove file:/// if present
    if filepath.startswith("file:///"):
        # On Windows it might look like file:///c:/...
        filepath = filepath.replace("file:///", "")
    
    try:
        with open(filepath, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
        return f"![{alt_text}](data:image/png;base64,{encoded_string})"
    except Exception as e:
        print(f"Failed to load {filepath}: {e}")
        return match.group(0) # return original if failed

new_text = re.sub(pattern, replace_with_base64, text)

with open("RESEARCH_PAPER_BASE64.md", "w", encoding="utf-8") as f:
    f.write(new_text)

print("Created RESEARCH_PAPER_BASE64.md with embedded images.")
