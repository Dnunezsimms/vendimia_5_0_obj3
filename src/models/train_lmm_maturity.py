import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from pathlib import Path
import sys

# Agregamos la raÃ­z del proyecto al sys.path para importar loaders
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from models.dashboard_obj3_integrado.src.loaders import load_maturity_tables

def train_lmm_lofo():
    print("Loading datasets...")
    
    # Cargamos el consolidado 2025 que ya tiene las variables termicas unidas
    raw_dict = load_maturity_tables()
    df = raw_dict['tintas_historicas'].copy()
    
    # Limpiamos nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Normalizamos fundo
    df['fundo'] = df['fundo'].str.lower().str.strip()
    
    print(f"Dataset shape: {df.shape}")
    
    targets = ['brix', 'pH', 'acidez_tartarica', 'peso_baya']
    predictors = ['GDA', 'BEDD_acum', 'IFN_acum', 'VPD_medio_acum']
    
    results = []
    
    # Run LOFO (Leave-One-Fundo-Out) CV
    fundos = df['fundo'].unique()
    
    for target in targets:
        for predictor in predictors:
            # Quitamos nulos para la dupla (target, predictor)
            df_model = df.dropna(subset=[target, predictor, 'fundo']).copy()
            # Aseguramos formato numÃ©rico
            df_model[target] = pd.to_numeric(df_model[target], errors='coerce')
            df_model[predictor] = pd.to_numeric(df_model[predictor], errors='coerce')
            df_model = df_model.dropna(subset=[target, predictor])
            
            if df_model.empty:
                continue
                
            # LOFO
            y_true_all = []
            y_pred_all = []
            fundo_ids = []
            
            for f in fundos:
                train = df_model[df_model['fundo'] != f]
                test = df_model[df_model['fundo'] == f]
                
                if train.empty or test.empty:
                    continue
                    
                # Estandarizamos el predictor para facilitar convergencia y comparar coeficientes
                mean_p = train[predictor].mean()
                std_p = train[predictor].std()
                
                train_p = (train[predictor] - mean_p) / std_p
                test_p = (test[predictor] - mean_p) / std_p
                
                train_df = pd.DataFrame({'Y': train[target], 'X': train_p, 'Group': train['fundo']})
                test_df = pd.DataFrame({'Y': test[target], 'X': test_p, 'Group': test['fundo']})
                
                try:
                    # LMM: Intercepto aleatorio por Fundo
                    md = smf.mixedlm("Y ~ X", train_df, groups=train_df["Group"])
                    mdf = md.fit(method='cg', maxiter=200) 
                    
                    # Predecimos
                    pred = mdf.predict(exog=test_df)
                    
                    y_true_all.extend(test_df['Y'].tolist())
                    y_pred_all.extend(pred.tolist())
                    fundo_ids.extend(test_df['Group'].tolist())
                except Exception as e:
                    print(f"Error training {target} ~ {predictor} for test fundo {f}: {e}")
            
            # Calcular metricas agregadas (LOFO general)
            if len(y_true_all) > 0:
                y_t = np.array(y_true_all)
                y_p = np.array(y_pred_all)
                
                r2 = np.corrcoef(y_t, y_p)[0, 1]**2 if len(y_t) > 1 else np.nan
                mae = np.mean(np.abs(y_t - y_p))
                rmse = np.sqrt(np.mean((y_t - y_p)**2))
                
                # Global AIC: Entrenar el modelo en TODOS los datos para extraer el AIC real
                global_aic = np.nan
                try:
                    mean_p_full = df_model[predictor].mean()
                    std_p_full = df_model[predictor].std()
                    x_full = (df_model[predictor] - mean_p_full) / std_p_full
                    
                    df_full = pd.DataFrame({'Y': df_model[target], 'X': x_full, 'Group': df_model['fundo']})
                    md_full = smf.mixedlm("Y ~ X", df_full, groups=df_full["Group"])
                    mdf_full = md_full.fit(method='cg', maxiter=200, reml=False)
                    global_aic = mdf_full.aic
                except Exception as e:
                    print(f"Error computing AIC for {target} ~ {predictor}: {e}")

                results.append({
                    'Target': target,
                    'Predictor': predictor,
                    'R2_LOFO': r2,
                    'MAE_LOFO': mae,
                    'RMSE_LOFO': rmse,
                    'AIC_Global': global_aic,
                    'N_Samples': len(y_t)
                })
                print(f"Finished {target} ~ {predictor} | R2 LOFO: {r2:.3f} | AIC: {global_aic:.1f}")
                
                # Opcional: guardar predicciones para plotear luego
                preds_df = pd.DataFrame({
                    'Target': target,
                    'Predictor': predictor,
                    'Fundo': fundo_ids,
                    'Y_true': y_t,
                    'Y_pred': y_p
                })
                preds_path = Path(f"C:/projects/vendimia_5_0_obj3_clean/data/processed/lmm_preds/preds_{target}_{predictor}.csv")
                preds_path.parent.mkdir(parents=True, exist_ok=True)
                preds_df.to_csv(preds_path, index=False)

    res_df = pd.DataFrame(results)
    print("\n--- LOFO Results ---")
    print(res_df.sort_values(by=['Target', 'R2_LOFO'], ascending=[True, False]).to_string(index=False))
    
    out_path = Path("C:/projects/vendimia_5_0_obj3_clean/data/processed/lmm_lofo_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(out_path, index=False)
    print(f"Saved summary metrics to {out_path}")

if __name__ == "__main__":
    train_lmm_lofo()

