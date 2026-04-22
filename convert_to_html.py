import markdown
import codecs

with codecs.open("RESEARCH_PAPER.md", mode="r", encoding="utf-8") as input_file:
    text = input_file.read()

# Convert markdown to html with tables extension
try:
    html = markdown.markdown(text, extensions=['tables'])
except Exception as e:
    # fallback if tables extension isn't installed
    html = markdown.markdown(text)

# Add basic styling for a clean, academic look
css = """
<style>
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; max-width: 850px; margin: 0 auto; padding: 40px; color: #333; }
h1, h2, h3 { color: #2c3e50; margin-top: 1.5em; }
table { border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 0.95em; }
th, td { border: 1px solid #dddddd; padding: 12px; text-align: left; }
th { background-color: #f8f9fa; font-weight: bold; }
tr:nth-child(even) { background-color: #fcfcfc; }
img { max-width: 100%; height: auto; display: block; margin: 25px auto; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 4px; }
em { color: #555; display: block; text-align: center; margin-top: -15px; margin-bottom: 30px; font-size: 0.9em; }
code { background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-family: monospace; }
</style>
"""

full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Research Paper</title>{css}</head><body>{html}</body></html>"

with codecs.open("RESEARCH_PAPER.html", "w", encoding="utf-8", errors="xmlcharrefreplace") as output_file:
    output_file.write(full_html)

print("Successfully generated RESEARCH_PAPER.html!")
