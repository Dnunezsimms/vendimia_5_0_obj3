import re

text = open(r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html', encoding='utf-8').read()

# Fix openSubTab
old_subtab = """function openSubTab(evt, subtabId) {
            document.querySelectorAll('.subtab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.subtab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(subtabId).classList.add('active');
            evt.currentTarget.classList.add('active');
            triggerPlotlyResize();
            if (tabId === 'tab-fenologia' && typeof updateChartFrio === 'function') { setTimeout(updateChartFrio, 100); }"""

new_subtab = """function openSubTab(evt, subtabId) {
            document.querySelectorAll('.subtab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.subtab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(subtabId).classList.add('active');
            evt.currentTarget.classList.add('active');
            triggerPlotlyResize();
            if (subtabId === 'sub-feno-f' && typeof updateChartFrio === 'function') { setTimeout(updateChartFrio, 100); }"""

if old_subtab in text:
    text = text.replace(old_subtab, new_subtab)
    print("Fixed openSubTab error")
else:
    print("WARNING: openSubTab not matched exactly")

with open(r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html', 'w', encoding='utf-8') as f:
    f.write(text)
