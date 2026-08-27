import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
import argparse
from pathlib import Path

def forward_selected(data, response):
    """Linear model designed by forward selection.
    Parameters:
    -----------
    data : pandas DataFrame with all possible predictors and response
    response: string, name of response column in data

    Returns:
    --------
    model: an "optimal" fitted statsmodels linear model
           with an intercept selected by forward selection
           evaluated by adjusted R-squared
    """
    remaining = set(data.columns)
    remaining.remove(response)
    selected = []
    current_score, best_new_score = 0.0, 0.0
    while remaining and current_score == best_new_score:
        scores_with_candidates = []
        for candidate in remaining:
            formula = "{} ~ {} + 1".format(response,
                                           ' + '.join(selected + [candidate]))
            score = smf.ols(formula, data).fit().rsquared_adj
            scores_with_candidates.append((score, candidate))
        scores_with_candidates.sort()
        best_new_score, best_candidate = scores_with_candidates[-1]
        if current_score < best_new_score:
            remaining.remove(best_candidate)
            selected.append(best_candidate)
            current_score = best_new_score
    formula = "{} ~ {} + 1".format(response,
                                   ' + '.join(selected))
    model = smf.ols(formula, data).fit()
    return model

def main():
    print("Iniciando Selección Stepwise de variables agronómicas...")
    
    # Intentamos cargar un dataset de prueba. En la realidad esto apuntará
    # al dataset canónico cuando incluya suelo, rendimiento, etc.
    # Por ahora armamos un mock si no existe, o usamos madurez si existe.
    
    try:
        # Ejemplo: df = pd.read_csv("ruta_al_dataset.csv")
        # Aquí simularíamos un dataset con estas variables para probar el script
        import numpy as np
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'brix': np.random.normal(24, 2, n),
            'rendimiento_ton_ha': np.random.normal(12, 3, n),
            'ano_plantacion': np.random.randint(1995, 2020, n),
            'profundidad_suelo_cm': np.random.normal(80, 20, n),
            'gdd_acumulado': np.random.normal(1500, 200, n),
            'arcilla_pct': np.random.normal(20, 5, n)
        })
        
        # Agregamos una relación real para que el stepwise la encuentre
        df['brix'] += 0.5 * df['gdd_acumulado'] / 100 - 0.2 * df['rendimiento_ton_ha']
        
        print("Dataset cargado con las columnas:", list(df.columns))
        print("\nEjecutando Forward Stepwise Selection para predecir 'brix'...")
        
        model = forward_selected(df, 'brix')
        
        print("\n--- MODELO FINAL SELECCIONADO ---")
        print(model.model.formula)
        print(model.summary())
        print("\nR2 Ajustado del mejor modelo:", round(model.rsquared_adj, 4))
        
        print("\nEl script de Stepwise está listo para ser integrado al flujo principal")
        print("cuando los datos reales de suelo y rendimiento estén disponibles.")
        
    except Exception as e:
        print(f"Error ejecutando stepwise: {e}")

if __name__ == "__main__":
    main()
