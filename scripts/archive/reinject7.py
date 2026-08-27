import os
import re

visor_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\visor_obj3.html'
with open(visor_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the GDD calculation block in JS
old_block = """let val1 = 0; let val2 = 0;
                let v_idx = dataset.fechas.indexOf(dataset.fecha_fondo_valle);
                let t0_idx = dataset.fechas.indexOf(dataset.t0_latitudinal);
                if(v_idx !== -1 && t0_idx !== -1) {
                    val1 = dataset.gdd_acumulado[v_idx];
                    val2 = dataset.gdd_acumulado[t0_idx];
                    let diff = (val2 - val1).toFixed(1);
                    html += `<div style="padding: 10px; background: #fef3c7; border-radius: 5px;">🔥 GDD (Valle a T0): <br><span style="color: #b45309; font-size: 1.1em;">${diff} GDD</span></div>`;
                }"""

new_block = """let v_idx = dataset.fechas.indexOf(dataset.fecha_fondo_valle);
                let t0_idx = dataset.fechas.indexOf(dataset.t0_latitudinal);
                let b_idx = dataset.fechas.indexOf(dataset.fecha_brotacion_ELP4);
                
                if (v_idx !== -1 && t0_idx !== -1) {
                    let gdd_v = dataset.gdd_acumulado[v_idx];
                    let gdd_t0 = dataset.gdd_acumulado[t0_idx];
                    let diff = (gdd_t0 - gdd_v).toFixed(1);
                    html += `<div style="padding: 10px; background: #fef3c7; border-radius: 5px;">🔥 GDD (Valle a T0): <br><span style="color: #b45309; font-size: 1.1em;">${diff} GDD</span></div>`;
                }
                if (v_idx !== -1 && b_idx !== -1) {
                    let gdd_v = dataset.gdd_acumulado[v_idx];
                    let gdd_b = dataset.gdd_acumulado[b_idx];
                    let diff = (gdd_b - gdd_v).toFixed(1);
                    html += `<div style="padding: 10px; background: #fee2e2; border-radius: 5px;">🔥 GDD (Valle a Brotación): <br><span style="color: #b91c1c; font-size: 1.1em;">${diff} GDD</span></div>`;
                }
                if (t0_idx !== -1 && b_idx !== -1) {
                    let gdd_t0 = dataset.gdd_acumulado[t0_idx];
                    let gdd_b = dataset.gdd_acumulado[b_idx];
                    let diff = (gdd_b - gdd_t0).toFixed(1);
                    html += `<div style="padding: 10px; background: #ffedd5; border-radius: 5px;">🔥 GDD (T0 a Brotación): <br><span style="color: #c2410c; font-size: 1.1em;">${diff} GDD</span></div>`;
                }"""

if old_block in text:
    text = text.replace(old_block, new_block)
    with open(visor_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated metrics.")
else:
    print("Could not find the old block to replace.")
