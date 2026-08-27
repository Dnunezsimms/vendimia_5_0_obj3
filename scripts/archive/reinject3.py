import os
import re

visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Let's ensure updateTVPanel is called on load
if 'setTimeout(updateTVPanel' not in text:
    text = text.replace(
        'function updateTVPanel() {',
        'setTimeout(updateTVPanel, 1000);\nfunction updateTVPanel() {'
    )
    with open(visor_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Added setTimeout trigger.")
else:
    print("Trigger already exists.")
