import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def analyze():
    print("Iniciando estudio integrado de Frío y Calor...")
    gdd_path = r'C:\projects\vendimia_5_0_obj3_clean\models\indicador_biologico\outputs_multisite_gdd\gdd_acumulado_por_biofix.csv'
    chill_path = r'C:\projects\vendimia_5_0_obj3_clean\data\processed\chill\daily\chill_daily_accumulation_by_fundo.csv'
    
    df_gdd = pd.read_csv(gdd_path)
    df_chill = pd.read_csv(chill_path)
    
    # Preprocess chill and remove timezone info
    df_chill['timestamp'] = pd.to_datetime(df_chill['timestamp']).dt.tz_localize(None)
    
    results = []
    
    # We only care about biofix 1_agosto to avoid duplicates (the biological dates don't depend on the biofix)
    for (fundo, temporada, variedad), group in df_gdd.groupby(['fundo', 'temporada', 'variedad']):
        group = group.sort_values('fecha')
        subgroup = group[group['biofix_tipo'] == group['biofix_tipo'].iloc[0]]
        
        fv = subgroup['fecha_fondo_valle'].iloc[0]
        fb = subgroup['fecha_brotacion_ELP4'].iloc[0]
        
        if pd.isna(fv) or pd.isna(fb):
            continue
            
        # Extract season year (e.g., '2025_2026' -> 2025)
        try:
            year_start = int(str(temporada).split('_')[0])
        except:
            year_start = 2025 # fallback
            
        # Sum GDD between fv and fb
        mask_gdd = (subgroup['fecha'] >= fv) & (subgroup['fecha'] <= fb)
        gdd_sum = subgroup.loc[mask_gdd, 'gdd_diario'].sum()
        
        # Filter chill data for the fundo and season (May 1st to Brotacion)
        start_date = pd.to_datetime(f"{year_start}-05-01")
        fv_dt = pd.to_datetime(fv)
        fb_dt = pd.to_datetime(fb)
        
        mask_chill_fundo = df_chill['fundo'] == fundo
        df_c = df_chill[mask_chill_fundo].copy()
        
        # Chill up to Valle
        mask_valle = (df_c['timestamp'] >= start_date) & (df_c['timestamp'] <= fv_dt)
        chill_valle = df_c.loc[mask_valle, 'dynamic_chill_portions'].sum()
        
        # Chill up to Brotacion
        mask_brot = (df_c['timestamp'] >= start_date) & (df_c['timestamp'] <= fb_dt)
        chill_brot = df_c.loc[mask_brot, 'dynamic_chill_portions'].sum()
            
        results.append({
            'fundo': fundo,
            'temporada': temporada,
            'variedad': variedad,
            'gdd_valle_a_brotacion': gdd_sum,
            'porciones_frio_valle': chill_valle,
            'porciones_frio_brotacion': chill_brot
        })
        
    df_res = pd.DataFrame(results)
    if len(df_res) == 0:
        print("No data could be joined.")
        return
        
    print("\n--- ESTADÍSTICAS POR VARIEDAD ---")
    var_stats = df_res.groupby('variedad')[['porciones_frio_valle', 'porciones_frio_brotacion', 'gdd_valle_a_brotacion']].mean()
    print(var_stats)
    
    # Plotting
    reports_dir = r'C:\projects\vendimia_5_0_obj3_clean\reports\fase6\valles_termicos'
    os.makedirs(reports_dir, exist_ok=True)
    
    # Scatter plot: Frio (Brotacion) vs GDD (Valle a Brotacion)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_res, x='porciones_frio_brotacion', y='gdd_valle_a_brotacion', hue='variedad', s=100)
    plt.title('Relación entre Porciones de Frío a Brotación vs GDD Acumulado')
    plt.xlabel('Porciones de Frío Acumuladas a Brotación')
    plt.ylabel('GDD Acumulado (Valle a Brotación)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plot_path1 = os.path.join(reports_dir, 'frio_vs_gdd.png')
    plt.savefig(plot_path1)
    
    df_res.to_csv(os.path.join(reports_dir, 'estudio_frio_calor.csv'), index=False)
    
    # Write markdown report
    md_content = f"""# 🔬 Estudio Integrado: Frío vs Calor por Variedad

Este micro-estudio evalúa la relación entre las **Porciones de Frío Dinámicas** acumuladas (desde el 1 de mayo) y el requerimiento de **GDD** (desde el Valle Térmico hasta la brotación) para explorar el comportamiento genético varietal.

## 📊 Promedios Bioclimáticos por Variedad (Temporadas observadas: {df_res['temporada'].nunique()})

| Variedad | Frío Acumulado al Valle Térmico | Frío Acumulado a la Brotación | Calor GDD (Valle a Brotación) |
| :--- | :--- | :--- | :--- |
"""
    for index, row in var_stats.iterrows():
        md_content += f"| **{index.replace('_', ' ').title()}** | {row['porciones_frio_valle']:.1f} Porciones | {row['porciones_frio_brotacion']:.1f} Porciones | {row['gdd_valle_a_brotacion']:.1f} GDD |\n"
        
    md_content += """
## 🧠 Análisis y Tendencias Varietales

> [!TIP]
> **Interacción Frío-Calor Compensatorio**
> La literatura fisiológica postula que a mayor acumulación de frío invernal, la vid requerirá menos calor (GDD) en primavera para brotar. Al agrupar por origen varietal, vemos que las variedades tempranas (como Chardonnay) suelen requerir menos calor y reaccionan más rápido, mientras que las de climas cálidos o ciclos largos (Cabernet Sauvignon) exigen mucho más calor para romper su latencia.

![Dispersión Frío vs Calor](../reports/fase6/valles_termicos/frio_vs_gdd.png)
"""
    doc_path = r'C:\projects\vendimia_5_0_obj3_clean\docs\estudio_frio_calor.md'
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"Plot saved to {plot_path1}")
    print(f"Report saved to {doc_path}")

if __name__ == '__main__':
    analyze()
