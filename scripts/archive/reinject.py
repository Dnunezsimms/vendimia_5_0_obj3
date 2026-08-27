import os
import re

visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Let's find where the <select> for tv are located.
# We know the javascript looks for: document.getElementById('tv-fundo-select').value;
# If the HTML doesn't have 'tv-fundo-select', then the user is looking at something else!
if 'tv-fundo-select' not in text:
    print("WARNING: 'tv-fundo-select' NOT FOUND IN HTML. The user might be looking at a different file or the IDs are different.")
else:
    print("Found 'tv-fundo-select'.")

# 2. Inject container if not present
if 'id="tv-dynamic-container"' not in text:
    # Find the closing div after the select
    # It might be in a flex row or something. Let's just find the last tv-.*-select and insert after its parent div.
    # Alternatively, find the header "B. Valle Térmico y Auditoría de Fecha de Inicio"
    header_pattern = r'(<h[1-6][^>]*>.*?B\.\s*Valle.*?T.rmico.*?<\/h[1-6]>.*?<\/div>)'
    # Or just find the selects container:
    selects_pattern = r'(<select id=\"tv-var-select\"[^>]*>.*?<\/select>\s*<\/div>\s*<\/div>\s*<\/div>)'
    
    match = re.search(selects_pattern, text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        text = text.replace(match.group(1), match.group(1) + '\n<div id="tv-dynamic-container" style="width: 100%; height: 600px; margin-top: 20px;"></div>\n')
        print("Injected container after selects.")
    else:
        # try another approach, just find the end of the row containing tv-var-select
        alt_pattern = r'(<select id=\"tv-var-select\"[^>]*>.*?<\/select>\s*<\/div>\s*<\/div>)'
        match2 = re.search(alt_pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if match2:
            text = text.replace(match2.group(1), match2.group(1) + '\n<div id="tv-dynamic-container" style="width: 100%; height: 600px; margin-top: 20px;"></div>\n')
            print("Injected container after selects (alt pattern).")
        else:
            print("Could not find place to inject container.")

with open(visor_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Done.")
