import pandas as pd
import json
import os
import math

def build():
    gdd_path = r'C:\projects\vendimia_5_0_obj3_clean\models\indicador_biologico\outputs_multisite_gdd\gdd_acumulado_por_biofix.csv'
    sinusoidal_path = r'C:\projects\vendimia_5_0_obj3_clean\reports\fase6\valles_termicos\resumen_valles_termicos_2025.csv'
    out_dir = r'C:\projects\vendimia_5_0_obj3_clean\reports\dashboards_html\data\valles'
    
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Loading {gdd_path}...")
    df = pd.read_csv(gdd_path)
    
    valles_math = {}
    if os.path.exists(sinusoidal_path):
        df_sin = pd.read_csv(sinusoidal_path)
        valles_math = dict(zip(df_sin['fundo'], df_sin['fecha_valle_matematico']))
        
    fundos = df['fundo'].unique()
    for f in fundos:
        d_fundo = df[df['fundo'] == f]
        fundo_dict = {}
        for (temporada, variedad, biofix), group in d_fundo.groupby(['temporada', 'variedad', 'biofix_tipo']):
            first_row = group.iloc[0]
            
            def safe_list(s):
                return s.tolist()
            
            series_data = {
                'temporada': str(temporada),
                'variedad': str(variedad),
                'biofix_tipo': str(biofix),
                'threshold_GDD_usado': first_row.get('threshold_GDD_usado'),
                'fecha_fondo_valle': first_row.get('fecha_fondo_valle') if pd.notnull(first_row.get('fecha_fondo_valle')) else None,
                'biofix_fecha': first_row.get('biofix_fecha') if pd.notnull(first_row.get('biofix_fecha')) else None,
                't0_operativo': first_row.get('t0_operativo') if pd.notnull(first_row.get('t0_operativo')) else None,
                't0_latitudinal': first_row.get('t0_latitudinal') if pd.notnull(first_row.get('t0_latitudinal')) else None,
                'fecha_brotacion_ELP4': first_row.get('fecha_brotacion_ELP4') if pd.notnull(first_row.get('fecha_brotacion_ELP4')) else None,
                
                'fechas': safe_list(group['fecha']),
                'gdd_diario': safe_list(group['gdd_diario']),
                'gdd_acumulado': safe_list(group['gdd_acumulado']),
                'rolling_gdd_14': safe_list(group['rolling_gdd_14']),
                'rolling_tmean_14': safe_list(group['rolling_tmean_14'])
            }
            
            if temporada not in fundo_dict:
                fundo_dict[temporada] = {}
            if variedad not in fundo_dict[temporada]:
                fundo_dict[temporada][variedad] = {}
                
            fundo_dict[temporada][variedad][biofix] = series_data
            
        final_json = {
            'fundo': str(f),
            'valle_sinusoidal': valles_math.get(f, valles_math.get(f.capitalize(), None)),
            'data': fundo_dict
        }
        
        out_file = os.path.join(out_dir, f"{f}.json")
        
        # Dump to string, and force replace any NaN with null
        # json.dumps writes NaN and Infinity by default if they are floats
        json_str = json.dumps(final_json)
        json_str = json_str.replace("NaN", "null")
        json_str = json_str.replace("Infinity", "null")
        json_str = json_str.replace("-Infinity", "null")
        
        with open(out_file, 'w', encoding='utf-8') as fh:
            fh.write(json_str)
        print(f"Saved {out_file}")

if __name__ == "__main__":
    build()
