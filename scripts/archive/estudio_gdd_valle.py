import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def analyze():
    print("Iniciando micro estudio...")
    gdd_path = r'C:\projects\vendimia_5_0_obj3_clean\models\indicador_biologico\outputs_multisite_gdd\gdd_acumulado_por_biofix.csv'
    df = pd.read_csv(gdd_path)
    
    results = []
    
    # We only care about biofix 1_agosto to avoid duplicates (since the valley to brotacion is independent of the biofix date chosen, 
    # but the gdd_acumulado is relative to the biofix. Wait! 
    # gdd_acumulado is relative to biofix_fecha in that CSV. 
    # So GDD(Valle to Brotacion) = GDD_diario sum between Valle and Brotacion. 
    # It's better to just sum the gdd_diario between those two dates directly to be safe from any offset.)
    
    for (fundo, temporada, variedad), group in df.groupby(['fundo', 'temporada', 'variedad']):
        group = group.sort_values('fecha')
        
        # Taking the first biofix is enough
        subgroup = group[group['biofix_tipo'] == group['biofix_tipo'].iloc[0]]
        
        fv = subgroup['fecha_fondo_valle'].iloc[0]
        fb = subgroup['fecha_brotacion_ELP4'].iloc[0]
        
        if pd.isna(fv) or pd.isna(fb):
            continue
            
        # Sum GDD between fv and fb
        mask = (subgroup['fecha'] >= fv) & (subgroup['fecha'] <= fb)
        gdd_sum = subgroup.loc[mask, 'gdd_diario'].sum()
        
        # sum GDD from T0 to fb for comparison
        t0 = subgroup['t0_latitudinal'].iloc[0]
        gdd_t0_brot = np.nan
        if pd.notna(t0):
            mask_t0 = (subgroup['fecha'] >= t0) & (subgroup['fecha'] <= fb)
            gdd_t0_brot = subgroup.loc[mask_t0, 'gdd_diario'].sum()
            
        results.append({
            'fundo': fundo,
            'temporada': temporada,
            'variedad': variedad,
            'gdd_valle_a_brotacion': gdd_sum,
            'gdd_t0_a_brotacion': gdd_t0_brot
        })
        
    df_res = pd.DataFrame(results)
    
    # Aggregate statistics
    print("\n--- ESTADÍSTICAS GLOBALES ---")
    print(df_res[['gdd_valle_a_brotacion', 'gdd_t0_a_brotacion']].describe())
    
    print("\n--- ESTADÍSTICAS POR VARIEDAD ---")
    var_stats = df_res.groupby('variedad')['gdd_valle_a_brotacion'].agg(['mean', 'std', 'count'])
    var_stats['cv_%'] = (var_stats['std'] / var_stats['mean']) * 100
    print(var_stats)
    
    # Plotting
    os.makedirs(r'C:\projects\vendimia_5_0_obj3_clean\scratch', exist_ok=True)
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df_res, x='variedad', y='gdd_valle_a_brotacion', hue='temporada')
    plt.title('GDD acumulado (Valle a Brotación) por Variedad y Temporada')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plot_path = r'C:\Users\dnunezs\.gemini\antigravity-ide\brain\0abbf12c-ca84-4d4d-aa4d-09dffbc94848\gdd_valle_brotacion.png'
    plt.savefig(plot_path)
    print(f"Plot saved to {plot_path}")
    
    df_res.to_csv(r'C:\projects\vendimia_5_0_obj3_clean\scratch\estudio_gdd.csv', index=False)

if __name__ == '__main__':
    analyze()
