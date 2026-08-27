import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os

def load_data(filepath):
    """Carga los datos unificados de fenologia y clima."""
    if not os.path.exists(filepath):
        print(f"Error: Archivo no encontrado en {filepath}")
        return None
    df = pd.read_csv(filepath)
    return df

def fit_mixed_model(df):
    """
    Entrena un Modelo Lineal Mixto (MLM).
    
    Y = gdd_valle_a_brotacion (Calor requerido)
    Fixed Effects = porciones_frio_valle (Frio Invernal acumulado) + C(variedad)
    Random Effects = fundo (Microclima / Suelo)
    """
    # Filtrar datos nulos en las variables de interes
    df_clean = df.dropna(subset=['gdd_valle_a_brotacion', 'porciones_frio_valle', 'variedad', 'fundo']).copy()
    
    if df_clean.empty:
        print("No hay datos suficientes para entrenar el modelo.")
        return None
        
    print(f"Entrenando modelo con {len(df_clean)} observaciones...")
    
    # Formula estadistica
    formula = "gdd_valle_a_brotacion ~ porciones_frio_valle + C(variedad)"
    
    # Modelo Mixto: groups = fundo (random intercept per fundo)
    md = smf.mixedlm(formula, df_clean, groups=df_clean["fundo"])
    mdf = md.fit(method='lbfgs')
    
    print("\n--- RESUMEN DEL MODELO LINEAL MIXTO ---")
    print(mdf.summary())
    
    return mdf, df_clean

def plot_residuals(mdf, df_clean):
    """Grafica los residuos del modelo para validar homocedasticidad."""
    df_clean['fitted'] = mdf.fittedvalues
    df_clean['residuals'] = mdf.resid
    
    plt.figure(figsize=(10, 7))
    sns.scatterplot(x='fitted', y='residuals', hue='variedad', style='temporada', data=df_clean, alpha=0.7)
    plt.axhline(0, color='red', linestyle='--')
    plt.title('Residuos vs Valores Ajustados (MLM Multitemporada)')
    plt.xlabel('GDD Predicho')
    plt.ylabel('Residuos')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(r'C:\projects\vendimia_5_0_obj3_clean\reports\fase6\valles_termicos\mixed_model_residuals.png')
    print("Grafico de residuos guardado en reports/fase6/valles_termicos/mixed_model_residuals.png")

def main():
    parser = argparse.ArgumentParser(description="Entrenar Modelo Mixto de Fenologia")
    parser.add_argument('--data', type=str, default=r'C:\projects\vendimia_5_0_obj3_clean\reports\fase6\valles_termicos\estudio_frio_calor_multitemporada.csv',
                        help='Ruta al CSV consolidado de variables bioclimaticas')
    args = parser.parse_args()
    
    df = load_data(args.data)
    if df is not None:
        result = fit_mixed_model(df)
        if result:
            mdf, df_clean = result
            plot_residuals(mdf, df_clean)

if __name__ == '__main__':
    main()

