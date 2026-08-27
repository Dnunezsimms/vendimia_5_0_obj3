import os
import re

visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add cache buster to the fetch call
if "fetch('data/valles/' + f + '.json?v='" not in text:
    text = text.replace(
        "fetch('data/valles/' + f + '.json')",
        "fetch('data/valles/' + f + '.json?v=' + new Date().getTime())"
    )
    with open(visor_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Added cache buster to fetch call.")
else:
    print("Cache buster already present.")
