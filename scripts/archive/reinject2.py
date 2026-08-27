import os
import re

visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Let's see if the container is already there. It shouldn't be based on grep.
if 'id="tv-dynamic-container"' not in text:
    # Inject it right before <div id="sub-feno-f"
    text = text.replace(
        '<div id="sub-feno-f"',
        '<div id="tv-dynamic-container" style="width: 100%; height: 600px; margin-top: 20px;"></div>\n      <div id="sub-feno-f"'
    )
    with open(visor_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Injected tv-dynamic-container.")
else:
    print("Container already exists.")
