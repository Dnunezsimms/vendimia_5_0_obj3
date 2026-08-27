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

def get_climate_data(station_id):
    base_path = r'C:\projects\vendimia_5_0_obj3_clean\data\processed\climate\hourly\consolidated'
    climate_file = os.path.join(base_path, f"{station_id}_climate_hourly_consolidated.csv")
    if not os.path.exists(climate_file):
        return None
        
    df = pd.read_csv(climate_file)
    
    # Normalize columns to the ones expected by the rest of the script
    df = df.rename(columns={'timestamp': 'fecha', 'temperature_c': 'tempMedia'})
    
    df['fecha'] = pd.to_datetime(df['fecha']).dt.tz_localize(None)
    df = df.dropna(subset=['fecha'])
    
    # We only have tempMedia (temperature_c) in consolidated, so map it to min/max too
    df['tempMinima'] = df['tempMedia']
    df['tempMaxima'] = df['tempMedia']
         
    return df

def main():
    print("Iniciando estudio Multitemporada de Frio vs Calor (2024 y 2025)...")
    pheno_path = r'C:\projects\vendimia_5_0_obj3_clean\data\raw\phenology\consolidado_fenologia_multitemporada.xlsx'
    chill_path = r'C:\projects\vendimia_5_0_obj3_clean\data\processed\chill\daily\chill_daily_accumulation_by_fundo.csv'
    
    fundo_station_map = {
        'idahue': 'san_vicente_idahue',
        'ucuquer': 'navidad_ucuquer',
        'keule': 'cauquenes_keule',
        'qba_seca': 'ovalle_quebrada_seca',
        'nilahue': 'lolol_nilahue',
        'los_acacios': 'pencahue_norte',
        'lourdes': 'pencahue_sur'
    }
    
    df_pheno = pd.read_excel(pheno_path, sheet_name='fenologia_maestra')
    df_chill = pd.read_csv(chill_path)
    df_chill['timestamp'] = pd.to_datetime(df_chill['timestamp'], format='mixed', utc=True).dt.tz_localize(None)
    
    temporadas = ['2024_2025', '2025_2026']
    
    median_deltas = {
        'chardonnay': 6,
        'sauvignon_blanc': 4,
        'cabernet_sauvignon': 4,
        'carmenere': 9,
    }
    
    results = []
    
    for temporada in temporadas:
        print(f"\n--- Procesando Temporada: {temporada} ---")
        df_temp = df_pheno[df_pheno['temporada'] == temporada].copy()
        df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
        
        elp4 = df_temp[df_temp['codigo_elp'] == 4].copy()
        elp5 = df_temp[df_temp['codigo_elp'] == 5].copy()
        
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
            
        base_year = int(temporada.split('_')[0])
        may_1 = pd.to_datetime(f"{base_year}-05-01")
        oct_31 = pd.to_datetime(f"{base_year}-10-31")
        winter_start = pd.to_datetime(f"{base_year}-06-15")
        winter_end = pd.to_datetime(f"{base_year}-08-31")
        
        for (fundo, variedad), group in df_brot.groupby(['fundo', 'variedad']):
            if pd.isna(fundo) or pd.isna(variedad): continue
            if fundo not in fundo_station_map: continue
            
            station_id = fundo_station_map[fundo]
            fb = pd.to_datetime(group['fecha'].median())
            is_imputed = group['is_imputed'].any()
            
            df_clim = get_climate_data(station_id)
            if df_clim is None or df_clim.empty: continue
                
            daily = df_clim.set_index('fecha').resample('D').agg({
                'tempMinima': 'min',
                'tempMaxima': 'max',
                'tempMedia': 'mean'
            }).reset_index()
            
            daily['t_mean_14d'] = daily['tempMedia'].rolling(window=14, min_periods=7, center=True).mean()
            mask_winter = (daily['fecha'] >= winter_start) & (daily['fecha'] <= winter_end)
            winter_data = daily[mask_winter]
            
            if winter_data.empty or winter_data['t_mean_14d'].isna().all():
                print(f"[{fundo}] {variedad}: No data invernal para valle termico.")
                continue
                
            min_idx = winter_data['t_mean_14d'].idxmin()
            t0 = winter_data.loc[min_idx, 'fecha']
            
            mask_gdd1 = (daily['fecha'] >= may_1) & (daily['fecha'] <= t0)
            gdd1_data = daily[mask_gdd1].copy()
            gdd1_data['gdd'] = gdd1_data.apply(lambda row: calculate_sine_gdd(row['tempMinima'], row['tempMaxima'], 10, 30), axis=1)
            gdd_valle_t0 = gdd1_data['gdd'].sum()
            
            mask_gdd_total = (daily['fecha'] >= may_1) & (daily['fecha'] <= fb)
            gdd_total_data = daily[mask_gdd_total].copy()
            gdd_total_data['gdd'] = gdd_total_data.apply(lambda row: calculate_sine_gdd(row['tempMinima'], row['tempMaxima'], 10, 30), axis=1)
            gdd_total = gdd_total_data['gdd'].sum()
            
            pf_valle = 0
            pf_brotacion = 0
            
            if station_id in df_chill['fundo'].values:
                chill_st = df_chill[df_chill['fundo'] == station_id].copy()
                if not chill_st.empty:
                    valle_ch = chill_st[chill_st['timestamp'] <= t0]
                    brot_ch = chill_st[chill_st['timestamp'] <= fb]
                    # Filter chill array to strictly current season
                    valle_ch = valle_ch[valle_ch['timestamp'] >= may_1]
                    brot_ch = brot_ch[brot_ch['timestamp'] >= may_1]
                    if not valle_ch.empty: pf_valle = valle_ch['dynamic_chill_portions'].sum()
                    if not brot_ch.empty: pf_brotacion = brot_ch['dynamic_chill_portions'].sum()
            
            results.append({
                'temporada': temporada,
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
            
            plt.figure(figsize=(10, 5))
            sns.lineplot(data=daily[(daily['fecha'] >= may_1) & (daily['fecha'] <= oct_31)], x='fecha', y='tempMedia', label='Temp. Media Diaria', color='blue', alpha=0.5)
            sns.lineplot(data=daily[(daily['fecha'] >= may_1) & (daily['fecha'] <= oct_31)], x='fecha', y='t_mean_14d', label='Temp. Media Movil (14d)', color='red')
            plt.axvline(t0, color='red', linestyle='--', label=f'T0: {t0.strftime("%Y-%m-%d")}')
            plt.axvline(fb, color='green', linestyle='--', label=f'Brotacion: {fb.strftime("%Y-%m-%d")}')
            
            plt.title(f"{fundo.capitalize()} - {variedad.capitalize()} ({temporada})\nGDD Valle a Brotacion: {gdd_total:.1f} | Frio Valle: {pf_valle:.1f}")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            out_img = rf'C:\projects\vendimia_5_0_obj3_clean\valle_termico_{fundo}_{variedad}_{temporada}.png'
            plt.savefig(out_img)
            plt.close()
            print(f"Generado grafico para {fundo} - {variedad} ({temporada})")
            
    if not results:
        print("No se generaron resultados.")
        return
        
    df_res = pd.DataFrame(results)
    out_csv = r'C:\projects\vendimia_5_0_obj3_clean\reports\fase6\valles_termicos\estudio_frio_calor_multitemporada.csv'
    df_res.to_csv(out_csv, index=False)
    
    print("\n--- PROMEDIOS POR TEMPORADA Y VARIEDAD ---")
    resumen = df_res.groupby(['temporada', 'variedad']).agg({
        'fundo': 'count',
        'porciones_frio_valle': 'mean',
        'gdd_valle_a_brotacion': 'mean'
    }).rename(columns={'fundo': 'n_fundos'})
    print(resumen)
    print(f"\nEstudio multitemporada generado en {out_csv}")

if __name__ == '__main__':
    main()
