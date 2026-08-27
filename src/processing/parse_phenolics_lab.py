import pandas as pd
import numpy as np
import os
import re

files = [
    r'C:\Users\dnunezs\Downloads\180-2026 AQ Informe análisis Uvas - Vendimia 5.0 SVargas.xlsx',
    r'C:\Users\dnunezs\Downloads\182-2026 UV Informe análisis Uvas - Vendimia 5.0 SVargas.xlsx'
]

all_dfs = []

for f in files:
    print(f'Procesando archivo: {os.path.basename(f)}')
    df = pd.read_excel(f, sheet_name='Hoja', header=None)
    
    # 1. Encontrar la cabecera de la tabla de metadatos (donde dice 'Id. original muestra')
    meta_header_idx = -1
    for i in range(200):
        row = df.iloc[i].tolist()
        if any('id. original muestra' in str(x).lower() for x in row):
            meta_header_idx = i
            break
            
    if meta_header_idx == -1:
        continue
        
    # La tabla de metadatos termina cuando encontramos una fila vacia o con 'RESULTADOS'
    meta_end_idx = meta_header_idx + 1
    while meta_end_idx < len(df):
        cell_val = str(df.iloc[meta_end_idx, 1]).lower() if len(df.columns) > 1 else ''
        if 'resultados' in cell_val or cell_val == 'nan' or cell_val.strip() == '':
            break
        meta_end_idx += 1
        
    df_meta = df.iloc[meta_header_idx:meta_end_idx].copy()
    df_meta.columns = [str(x).strip() for x in df_meta.iloc[0].tolist()]
    df_meta = df_meta.iloc[1:].copy()
    
    # 2. Encontrar la cabecera de la tabla de resultados químicos
    res_header_idx = -1
    for i in range(meta_end_idx, len(df)):
        row = df.iloc[i].tolist()
        if any('lab cii' in str(x).lower() for x in row):
            res_header_idx = i
            break
            
    if res_header_idx == -1:
        continue
        
    df_res = df.iloc[res_header_idx:].copy()
    df_res.columns = [str(x).replace('\n', ' ').strip() for x in df_res.iloc[0].tolist()]
    # Saltar la fila de unidades (mg/Kg)
    df_res = df_res.iloc[2:].copy() 
    
    # Identify the ID columns.
    meta_id_col = [c for c in df_meta.columns if 'original muestra' in str(c).lower()][0]
    res_id_col = [c for c in df_res.columns if 'lab cii' in str(c).lower()][0]
    
    df_meta['ID_JOIN'] = df_meta[meta_id_col].astype(str).str.strip()
    df_res['ID_JOIN'] = df_res[res_id_col].astype(str).str.strip()
    
    df_meta = df_meta[df_meta['ID_JOIN'] != 'nan']
    df_res = df_res[df_res['ID_JOIN'] != 'nan']
    
    # Extraer columnas utiles de metadatos
    fundo_col = [c for c in df_meta.columns if 'fundo' in str(c).lower()][0]
    var_col = [c for c in df_meta.columns if 'variedad' in str(c).lower()][0]
    cuartel_col = [c for c in df_meta.columns if 'cuartel' in str(c).lower()][0]
    fecha_col = [c for c in df_meta.columns if 'observaciones' in str(c).lower()][0]
    
    df_meta['Fundo'] = df_meta[fundo_col].astype(str).str.title().str.strip()
    df_meta['Variedad'] = df_meta[var_col].astype(str).str.strip().replace({'C. Sauvignon': 'CS', 'Carmenere': 'CA'})
    df_meta['Cuartel'] = df_meta[cuartel_col].astype(str).str.strip()
    
    # Merge
    merged = pd.merge(df_meta[['ID_JOIN', 'Fundo', 'Variedad', 'Cuartel', fecha_col]], df_res, on='ID_JOIN', how='inner')
    
    # Renombrar columnas químicas (todas las de df_res menos las indeseadas)
    drop_cols = [c for c in merged.columns if str(c).lower() in ['nan', 'n', 'n°'] or 'lab cii' in str(c).lower() or c == 'ID_JOIN']
    merged = merged.drop(columns=drop_cols, errors='ignore')
    
    merged = merged.rename(columns={fecha_col: 'Fecha_Muestra'})
    
    all_dfs.append(merged)

if all_dfs:
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Cleanup columns
    def clean_col(c):
        c = str(c).replace('ó', 'o').replace('í', 'i').replace('á', 'a').replace('é', 'e').replace('ú', 'u')
        c = re.sub(r'[^a-zA-Z0-9_\-]', '_', c)
        c = re.sub(r'__+', '_', c)
        return c.strip('_')
        
    final_df.columns = [clean_col(c) for c in final_df.columns]
    
    output_file = 'datos_fenoles_consolidados_2026.csv'
    final_df.to_csv(output_file, index=False)
    
    print(f'\nProcesado completado! Shape: {final_df.shape}')
    print(final_df.columns.tolist())
    print(final_df.head(2).to_string())
else:
    print('No se extrajo ningun dato.')
