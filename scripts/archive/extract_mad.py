import re

with open(r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html', 'r', encoding='utf-8') as f:
    text = f.read()

m1 = re.search(r'(<div id="tab-mad-tec".*?)(?=<div id="tab-)', text, re.DOTALL)
m2 = re.search(r'(<div id="tab-mad-fen".*?)(?=<div id="tab-)', text, re.DOTALL)

with open(r'C:\projects\vendimia_5_0_obj3_clean\mad_divs.txt', 'w', encoding='utf-8') as f:
    f.write(m1.group(1) if m1 else 'NOT FOUND 1\n')
    f.write('\n\n')
    f.write(m2.group(1) if m2 else 'NOT FOUND 2\n')
