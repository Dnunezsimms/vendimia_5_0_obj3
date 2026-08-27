import os
visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

old_str = "triggerPlotlyResize();\n        }"
new_str = "triggerPlotlyResize();\n            if (tabId === 'tab-fenologia' && typeof updateChartFrio === 'function') { setTimeout(updateChartFrio, 100); }\n        }"

if old_str in text:
    text = text.replace(old_str, new_str)
    with open(visor_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed!")
else:
    print("Not found! trying simpler replace")
    old2 = "triggerPlotlyResize();"
    new2 = "triggerPlotlyResize();\n            if (tabId === 'tab-fenologia' && typeof updateChartFrio === 'function') { setTimeout(updateChartFrio, 100); }"
    text = text.replace(old2, new2)
    with open(visor_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed with simpler replace!")
