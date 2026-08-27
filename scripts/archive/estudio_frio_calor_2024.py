import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import math

def calculate_sine_gdd(t_min, t_max, t_base, t_upper):
    if pd.isna(t_min) or pd.isna(t_max): return 0.0
    if t_min > t_max: t_min, t_max = t_max, t_min
    t_avg = (t_min + t_max) / 2.0
    if t_max <= t_base: return 0.0
    if t_min >= t_base and t_max <= t_upper: return t_avg - t_base
    alpha = (t_max - t_min) / 2.0
    if alpha == 0: return max(0.0, min(t_avg, t_upper) - t_base)
    try: theta1 = math.asin((t_base - t_avg) / alpha)
    except ValueError: theta1 = math.pi / 2 if (t_base - t_avg) / alpha > 1 else -math.pi / 2
    if t_max <= t_upper:
        gdd = (1 / math.pi) * ((t_avg - t_base) * (math.pi / 2 - theta1) + alpha * math.cos(theta1))
    else:
        try: theta2 = math.asin((t_upper - t_avg) / alpha)
        except ValueError: theta2 = math.pi / 2 if (t_upper - t_avg) / alpha > 1 else -math.pi / 2
        gdd = (1 / math.pi) * ((t_avg - t_base) * (theta2 - theta1) + alpha * (math.cos(theta1) - math.cos(theta2)) + (t_upper - t_base) * (math.pi / 2 - theta2))
    return max(0.0, gdd)

def get_climate_data(station_id, provider):
    base_path = r'C:\projects\vendimia_5_0_obj3_clean\data\raw\climate\hourly'
    climate_file = os.path.join(base_path, provider, station_id, 'climate_hourly.csv')
    if not os.path.exists(climate_file):
        return None
        
    df = pd.read_csv(climate_file, sep=None, engine='python')
    
    # Normalize columns
    if 'time' in df.columns:
        df = df.rename(columns={'time': 'fecha'})
    elif 'Fecha Hora' in df.columns:
        df = df.rename(columns={'Fecha Hora': 'fecha'})
        
    if 'temp_air' in df.columns:
        df = df.rename(columns={'temp_air': 'tempMedia'})
    elif 'Temp. promedio aire' in df.columns:
        df = df.rename(columns={'Temp. promedio aire': 'tempMedia', 'Temp. Mínima': 'tempMinima', 'Temp. Máxima': 'tempMaxima'})
        
    # parse dates
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['fecha'])
    
    # clean temps if strings with commas
    for col in ['tempMedia', 'tempMinima', 'tempMaxima']:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(',', '.').astype(float, errors='ignore')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    if 'tempMinima' not in df.columns and 'tempMedia' in df.columns:
         df['tempMinima'] = df['tempMedia']
         df['tempMaxima'] = df['tempMedia']
         
    return df

def main():
    print("Iniciando estudio de Frio vs Calor (2024) con Imputación de ELP4...")
    pheno_path = r'C:\projects\vendimia_5_0_obj3_clean\data\raw\phenology\consolidado_fenologia_multitemporada.xlsx'
    chill_path = r'C:\projects\vendimia_5_0_obj3_clean\data\processed\chill\daily\chill_daily_accumulation_by_fundo.csv'
    
    fundo_station_map = {
        'idahue': ('inia', 'san_vicente_idahue'),
        'ucuquer': ('datavid', 'navidad_ucuquer'),
        'keule': ('inia', 'cauquenes_keule'),
        'qba_seca': ('datavid', 'ovalle_quebrada_seca'),
        'nilahue': ('inia', 'lolol_nilahue'),
        'los_acacios': ('inia', 'pencahue_norte')
    }
    
    df_pheno = pd.read_excel(pheno_path, sheet_name='fenologia_maestra')
    df_chill = pd.read_csv(chill_path)
    df_chill['timestamp'] = pd.to_datetime(df_chill['timestamp']).dt.tz_localize(None)
    
    df_2024 = df_pheno[df_pheno['temporada'] == '2024_2025'].copy()
    df_2024['fecha'] = pd.to_datetime(df_2024['fecha'])
    
    elp4 = df_2024[df_2024['codigo_elp'] == 4].copy()
    elp5 = df_2024[df_2024['codigo_elp'] == 5].copy()
    
    median_deltas = {
        'chardonnay': 6,
        'sauvignon_blanc': 4,
        'cabernet_sauvignon': 4,
        'carmenere': 9,
    }
    
    imputed_rows = []
    
    for (fundo, bloque, variedad), group in elp5.groupby(['fundo', 'bloque', 'variedad']):
        mask_4 = (elp4['fundo'] == fundo) & (elp4['bloque'] == bloque) & (elp4['variedad'] == variedad)
        if not mask_4.any():
            delta = median_deltas.get(variedad, 6)
            f5 = group['fecha'].median()
            f4_imputed = f5 - pd.Timedelta(days=delta)
            
            imputed_rows.append({
                'fundo': fundo,
                'bloque': bloque,
                'variedad': variedad,
                'fecha': f4_imputed,
                'is_imputed': True
            })
            
    df_imputed = pd.DataFrame(imputed_rows)
    elp4['is_imputed'] = False
    
    if not df_imputed.empty:
        df_brot = pd.concat([elp4, df_imputed], ignore_index=True)
    else:
        df_brot = elp4
        
    results = []
    
    for (fundo, variedad), group in df_brot.groupby(['fundo', 'variedad']):
        if pd.isna(fundo) or pd.isna(variedad): continue
        if fundo not in fundo_station_map: continue
        
        provider, station_id = fundo_station_map[fundo]
        fb = pd.to_datetime(group['fecha'].median())
        is_imputed = group['is_imputed'].any()
        
        df_clim = get_climate_data(station_id, provider)
        if df_clim is None or df_clim.empty: continue
            
        daily = df_clim.set_index('fecha').resample('D').agg({
            'tempMinima': 'min',
            'tempMaxima': 'max',
            'tempMedia': 'mean'
        }).reset_index()
        
        # 1. Valle Térmico
        daily['t_mean_14d'] = daily['tempMedia'].rolling(window=14, min_periods=7, center=True).mean()
        mask_winter = (daily['fecha'] >= pd.to_datetime('2024-06-15')) & (daily['fecha'] <= pd.to_datetime('2024-08-31'))
        winter_data = daily[mask_winter]
        
        if winter_data.empty or winter_data['t_mean_14d'].isna().all():
            print(f"[{fundo}] {variedad}: No data invernal para valle termico. Saltando.")
            continue
            
        min_idx = winter_data['t_mean_14d'].idxmin()
        t0 = winter_data.loc[min_idx, 'fecha']
        
        # 2. GDD Valle -> T0
        mask_gdd1 = (daily['fecha'] >= pd.to_datetime('2024-05-01')) & (daily['fecha'] <= t0)
        gdd1_data = daily[mask_gdd1].copy()
        gdd1_data['gdd'] = gdd1_data.apply(lambda row: calculate_sine_gdd(row['tempMinima'], row['tempMaxima'], 10, 30), axis=1)
        gdd_valle_t0 = gdd1_data['gdd'].sum()
        
        # 3. GDD Valle -> Brotacion
        mask_gdd_total = (daily['fecha'] >= pd.to_datetime('2024-05-01')) & (daily['fecha'] <= fb)
        gdd_total_data = daily[mask_gdd_total].copy()
        gdd_total_data['gdd'] = gdd_total_data.apply(lambda row: calculate_sine_gdd(row['tempMinima'], row['tempMaxima'], 10, 30), axis=1)
        gdd_total = gdd_total_data['gdd'].sum()
        
        # 4. Frio
        pf_valle = 0
        pf_brotacion = 0
        
        if station_id in df_chill['fundo'].values:
            chill_st = df_chill[df_chill['fundo'] == station_id].copy()
            if not chill_st.empty:
                valle_ch = chill_st[chill_st['timestamp'] <= t0]
                brot_ch = chill_st[chill_st['timestamp'] <= fb]
                if not valle_ch.empty: pf_valle = valle_ch['dynamic_chill_portions'].max()
                if not brot_ch.empty: pf_brotacion = brot_ch['dynamic_chill_portions'].max()
        
        results.append({
            'fundo': fundo,
            'variedad': variedad,
            't0_latitudinal': t0.strftime('%Y-%m-%d'),
            'fecha_brotacion': fb.strftime('%Y-%m-%d'),
            'porciones_frio_valle': pf_valle,
            'porciones_frio_brotacion': pf_brotacion,
            'gdd_valle_a_t0': gdd_valle_t0,
            'gdd_valle_a_brotacion': gdd_total,
            'imputado': is_imputed
        })
        
        # Grafico
        plt.figure(figsize=(10, 5))
        sns.lineplot(data=daily[(daily['fecha'] >= pd.to_datetime('2024-05-01')) & (daily['fecha'] <= pd.to_datetime('2024-10-31'))], x='fecha', y='tempMedia', label='Temp. Media Diaria', color='blue', alpha=0.5)
        sns.lineplot(data=daily[(daily['fecha'] >= pd.to_datetime('2024-05-01')) & (daily['fecha'] <= pd.to_datetime('2024-10-31'))], x='fecha', y='t_mean_14d', label='Temp. Media Movil (14d)', color='red')
        plt.axvline(t0, color='red', linestyle='--', label=f'T0: {t0.strftime("%Y-%m-%d")}')
        plt.axvline(fb, color='green', linestyle='--', label=f'Brotacion: {fb.strftime("%Y-%m-%d")}')
        
        plt.title(f"{fundo.capitalize()} - {variedad.capitalize()}\nGDD Valle a Brotacion: {gdd_total:.1f} | Frio Valle: {pf_valle:.1f}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        out_img = rf'C:\projects\vendimia_5_0_obj3_clean\valle_termico_{fundo}_{variedad}.png'
        plt.savefig(out_img)
        plt.close()
        print(f"Generado grafico para {fundo} - {variedad}")
        
    if not results:
        print("No se generaron resultados. Verifica las fechas de los archivos.")
        return
        
    df_res = pd.DataFrame(results)
    out_csv = r'C:\projects\vendimia_5_0_obj3_clean\reports\fase6\valles_termicos\estudio_frio_calor_2024_imputado.csv'
    df_res.to_csv(out_csv, index=False)
    
    # Resumen
    resumen = df_res.groupby('variedad').agg({
        'porciones_frio_valle': 'mean',
        'porciones_frio_brotacion': 'mean',
        'gdd_valle_a_brotacion': 'mean'
    })
    
    print("\n--- PROMEDIOS POR VARIEDAD (TEMPORADA 2024-2025) ---")
    print(resumen)
    print("Estudio generado exitosamente.")

if __name__ == '__main__':
    main()
