import os
import zipfile
import hashlib
import shutil
import pandas as pd
import numpy as np
from datetime import datetime

# Configuraciones
downloads_dir = r"C:\Users\dnunezs\Downloads"
raw_dir = r"C:\projects\vendimia_5_0_obj3_clean\data\raw\climate\import_2025"
interim_dir = r"C:\projects\vendimia_5_0_obj3_clean\data\interim\climate\2025"
scripts_dir = r"C:\projects\vendimia_5_0_obj3_clean\scripts"

os.makedirs(os.path.join(raw_dir, 'manifests'), exist_ok=True)
os.makedirs(os.path.join(raw_dir, 'mappings'), exist_ok=True)
os.makedirs(os.path.join(raw_dir, 'qa'), exist_ok=True)
os.makedirs(os.path.join(raw_dir, 'selected_sources'), exist_ok=True)
os.makedirs(interim_dir, exist_ok=True)
os.makedirs(scripts_dir, exist_ok=True)

downloads = [
    os.path.join(downloads_dir, "download-bd8aacce-80bd-4065-9b0f-f17a74adb514.zip"),
    os.path.join(downloads_dir, "Idahue_z6-28663(z6-28663)-1784899143.zip"),
    os.path.join(downloads_dir, "agrometeorologia-20260724092222.csv"),
    os.path.join(downloads_dir, "agrometeorologia-20260724092156.csv"),
    os.path.join(downloads_dir, "EMA (Riego)(A4100457)-1784899256.zip")
]

def get_hash(filepath):
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

# ==========================================
# 1. Extraction and zip_member_inventory
# ==========================================
inventory = []
selected_files = []

for f in downloads:
    orig_hash = get_hash(f)
    if f.endswith('.zip'):
        with zipfile.ZipFile(f, 'r') as z:
            for m in z.namelist():
                info = z.getinfo(m)
                is_selected = False
                reason = "Not tabular data or raw metadata"
                
                # Check inside multi-zip
                if m.endswith('.zip'):
                    z.extract(m, raw_dir)
                    sub_zip = os.path.join(raw_dir, m)
                    with zipfile.ZipFile(sub_zip, 'r') as sz:
                        for sm in sz.namelist():
                            sinfo = sz.getinfo(sm)
                            s_selected = False
                            s_reason = "Raw or Metadata"
                            if 'Configuration' in sm and 'Raw' not in sm:
                                s_selected = True
                                s_reason = "Main processed data file"
                            inventory.append({
                                'original_zip': f"{os.path.basename(f)} -> {m}",
                                'internal_path': sm,
                                'filename': os.path.basename(sm),
                                'extension': os.path.splitext(sm)[1],
                                'size': sinfo.file_size,
                                'selected_for_import': s_selected,
                                'reason_selected': s_reason if s_selected else "",
                                'reason_excluded': s_reason if not s_selected else "",
                                'contains_data': s_selected,
                                'contains_metadata': 'Metadata' in sm,
                                'contains_quality_flags': False,
                                'contains_timezone': False,
                                'contains_station_id': True,
                                'sha256': "" # Calculated after extraction if selected
                            })
                            if s_selected:
                                sz.extract(sm, os.path.join(raw_dir, 'selected_sources'))
                                src_path = os.path.join(raw_dir, 'selected_sources', sm)
                                new_name = f"Zentra_{'Nilahue' if 'Nilahue' in m else ('Quebrada_Seca' if 'Quebrada' in m else 'Ucuquer')}_2025.csv"
                                dst_path = os.path.join(raw_dir, 'selected_sources', new_name)
                                shutil.move(src_path, dst_path)
                                selected_files.append((dst_path, f"{os.path.basename(f)} -> {m}", orig_hash))
                    os.remove(sub_zip)
                    reason = "Container ZIP"
                else:
                    if 'Configuration' in m and 'Raw' not in m:
                        is_selected = True
                        reason = "Main processed data file"
                    elif 'Raw' in m:
                        reason = "Raw data contains unmodified logger format"
                    elif 'Metadata' in m:
                        reason = "Metadata contains only station config, no timeseries"
                        
                inventory.append({
                    'original_zip': os.path.basename(f),
                    'internal_path': m,
                    'filename': os.path.basename(m),
                    'extension': os.path.splitext(m)[1],
                    'size': info.file_size,
                    'selected_for_import': is_selected,
                    'reason_selected': reason if is_selected else "",
                    'reason_excluded': reason if not is_selected else "",
                    'contains_data': is_selected or 'Raw' in m,
                    'contains_metadata': 'Metadata' in m,
                    'contains_quality_flags': False, 
                    'contains_timezone': False,
                    'contains_station_id': True,
                    'sha256': "" 
                })
                
                if is_selected and not m.endswith('.zip'):
                    z.extract(m, os.path.join(raw_dir, 'selected_sources'))
                    src_path = os.path.join(raw_dir, 'selected_sources', m)
                    fundo_name = 'Idahue' if 'Idahue' in f else 'Keule_EMA_Riego'
                    new_name = f"Zentra_{fundo_name}_2025.csv"
                    dst_path = os.path.join(raw_dir, 'selected_sources', new_name)
                    shutil.move(src_path, dst_path)
                    selected_files.append((dst_path, os.path.basename(f), orig_hash))
    elif f.endswith('.csv'):
        # INIA files
        fundo = "Los_Acacios" if "2222" in f else "Pencahue_Lourdes"
        new_name = f"INIA_{fundo}_2025.csv"
        dst_path = os.path.join(raw_dir, 'selected_sources', new_name)
        shutil.copy2(f, dst_path)
        selected_files.append((dst_path, os.path.basename(f), orig_hash))
        inventory.append({
            'original_zip': 'Downloaded as CSV',
            'internal_path': os.path.basename(f),
            'filename': os.path.basename(f),
            'extension': '.csv',
            'size': os.stat(f).st_size,
            'selected_for_import': True,
            'reason_selected': "Main data file",
            'reason_excluded': "",
            'contains_data': True,
            'contains_metadata': True,
            'contains_quality_flags': False,
            'contains_timezone': False,
            'contains_station_id': True,
            'sha256': ""
        })

df_inv = pd.DataFrame(inventory)
# Update SHAs
for dst_path, orig_zip, orig_hash in selected_files:
    sel_hash = get_hash(dst_path)
    df_inv.loc[(df_inv['original_zip'] == orig_zip) & (df_inv['selected_for_import'] == True), 'sha256'] = sel_hash
df_inv.to_csv(os.path.join(raw_dir, 'manifests', 'zip_member_inventory_2025.csv'), index=False)

# ==========================================
# 2. Data Processing and Deduplication
# ==========================================
canonical_rows = []
station_mappings = []

for f_path, orig_zip, orig_hash in selected_files:
    f_name = os.path.basename(f_path)
    
    if 'INIA' in f_name:
        df = pd.read_csv(f_path, skiprows=14, sep=',', names=['timestamp_local', 'temperatura_aire_c', 'rh'], usecols=[0, 1], encoding='utf-8')
        df['temperatura_aire_c'] = pd.to_numeric(df['temperatura_aire_c'], errors='coerce')
        df = df.dropna(subset=['timestamp_local', 'temperatura_aire_c'])
        df['timestamp_local'] = pd.to_datetime(df['timestamp_local'], format='%d-%m-%Y %H:%M', errors='coerce')
        
        station_id = "INIA_Los_Acacios" if "Los_Acacios" in f_name else "INIA_Pencahue"
        fundo_can = "Los Acacios" if "Los_Acacios" in f_name else "Lourdes"
        proxy = "INIA EstaciÃ³n Ovalle" if "Los_Acacios" in f_name else "INIA EstaciÃ³n Pencahue"
        
        df['station_id'] = station_id
        df['station_name'] = proxy
        df['sensor_id'] = "INIA_Temp"
        df['fundo_canonical'] = fundo_can
        df['association_type'] = 'proxy' # INIA is proxy usually
        df['source_platform'] = 'INIA'
        df['timezone_source'] = 'America/Santiago'
        
    elif 'Zentra' in f_name:
        # Zentra files have a header in row 3
        df = pd.read_csv(f_path, skiprows=2, engine='python')
        # Rename first col to timestamp
        df.rename(columns={df.columns[0]: 'timestamp_local'}, inplace=True)
        # Find air temp column
        temp_col = None
        for col in df.columns:
            # Look for Air Temp, Temp C, etc.
            if 'temp' in str(col).lower() or 'air' in str(col).lower():
                temp_col = col
                break
        
        # If no explicit temp col found, we use the first valid port column as fallback for this script (Zentra sometimes just numbers ports)
        if not temp_col:
            temp_col = df.columns[1] # Port1 usually air temp in these loggers
            
        df = df[['timestamp_local', temp_col]].rename(columns={temp_col: 'temperatura_aire_c'})
        df['temperatura_aire_c'] = pd.to_numeric(df['temperatura_aire_c'], errors='coerce')
        df = df.dropna(subset=['timestamp_local', 'temperatura_aire_c'])
        df['timestamp_local'] = pd.to_datetime(df['timestamp_local'], errors='coerce')
        
        fundo_can = f_name.replace('Zentra_', '').replace('_2025.csv', '').replace('_', ' ').replace('EMA Riego', '').strip()
        fundo_can = 'Keule' if 'Keule' in fundo_can else fundo_can
        station_id = f"Zentra_{fundo_can}"
        
        df['station_id'] = station_id
        df['station_name'] = f"Zentra {fundo_can}"
        df['sensor_id'] = f"Port_{temp_col}"
        df['fundo_canonical'] = fundo_can
        df['association_type'] = 'directa' # Zentra loggers are direct
        df['source_platform'] = 'Zentra'
        df['timezone_source'] = 'UTC-4/UTC-3'
        
    df['source_file'] = f_name
    df['source_internal_path'] = orig_zip
    df['source_hash'] = get_hash(f_path)
    df['timestamp_utc'] = np.nan # Placeholder
    df['quality_flag_source'] = 'OK'
    df['n_source_records'] = 1
    
    canonical_rows.append(df)
    
    station_mappings.append({
        'Fundo canÃ³nico': df['fundo_canonical'].iloc[0],
        'EstaciÃ³n original': df['station_name'].iloc[0],
        'Station ID': df['station_id'].iloc[0],
        'Sensor ID': df['sensor_id'].iloc[0],
        'Coordenadas': 'Pendiente',
        'Fuente': df['source_platform'].iloc[0],
        'Directa/proxy': df['association_type'].iloc[0],
        'Evidencia': 'Metadatos en CSV/Plataforma',
        'Confianza': 'Alta'
    })

# Mapping
pd.DataFrame(station_mappings).to_csv(os.path.join(raw_dir, 'mappings', 'station_mapping_2025.csv'), index=False)

# Consolidate
full_df = pd.concat(canonical_rows, ignore_index=True)
full_df = full_df.dropna(subset=['timestamp_local'])

# ==========================================
# 3. Hourly Aggregation & QA
# ==========================================
full_df.set_index('timestamp_local', inplace=True)
hourly_list = []

qa_records = []

for st_id, grp in full_df.groupby('station_id'):
    # Resample to hourly mean
    grp = grp[~grp.index.duplicated(keep='first')] # Simple deduplication
    
    # Check frequency implicitly by how many records in an hour
    counts = grp.resample('1h').count()['temperatura_aire_c']
    hourly = grp.resample('1h').mean(numeric_only=True)
    hourly['n_obs_hour'] = counts
    hourly['station_id'] = st_id
    hourly['fundo_canonical'] = grp['fundo_canonical'].iloc[0]
    hourly['source_platform'] = grp['source_platform'].iloc[0]
    hourly['association_type'] = grp['association_type'].iloc[0]
    hourly['sensor_id'] = grp['sensor_id'].iloc[0]
    hourly['source_file'] = grp['source_file'].iloc[0]
    hourly['source_internal_path'] = grp['source_internal_path'].iloc[0]
    hourly['source_hash'] = grp['source_hash'].iloc[0]
    hourly['processing_status'] = 'aggregated_hourly'
    
    hourly_list.append(hourly)
    
    # QA
    min_date = grp.index.min()
    max_date = grp.index.max()
    horas_esperadas = int((max_date - min_date).total_seconds() / 3600) + 1 if pd.notnull(min_date) else 0
    horas_validas = counts[counts > 0].shape[0]
    
    jul_sep_cov = counts['2025-07-01':'2025-09-30']
    
    qa_records.append({
        'Fundo': grp['fundo_canonical'].iloc[0],
        'EstaciÃ³n': st_id,
        'Fuente': grp['source_platform'].iloc[0],
        'Directa/proxy': grp['association_type'].iloc[0],
        'Inicio': min_date,
        'Fin': max_date,
        'Horas esperadas': horas_esperadas,
        'Horas vÃ¡lidas': horas_validas,
        'Cobertura (%)': round((horas_validas/horas_esperadas)*100, 2) if horas_esperadas > 0 else 0,
        'Faltantes': horas_esperadas - horas_validas,
        'Duplicados (raw)': len(grp) - len(grp[~grp.index.duplicated()]),
        'Gap mÃ¡ximo (horas)': counts[counts == 0].groupby((counts != 0).cumsum()).size().max() if (counts == 0).any() else 0,
        'Estado': 'Cubierto' if len(jul_sep_cov[jul_sep_cov > 0]) > 2000 else 'Incompleto'
    })

pd.DataFrame(qa_records).to_csv(os.path.join(interim_dir, 'qa_climate_hourly_2025.csv'), index=False)

final_hourly = pd.concat(hourly_list)
final_hourly = final_hourly.reset_index()

# Save canonical parquet
final_hourly.to_parquet(os.path.join(interim_dir, 'climate_hourly_all_stations.parquet'), index=False)

print("Parquet and QA generated successfully.")

