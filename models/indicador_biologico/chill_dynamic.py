import argparse
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data/historical_reference/Datos horarios para modelo dinamico/CYT"
OUTPUT_DIR = ROOT_DIR / "models/indicador_biologico/outputs_multisite_gdd"
SUMMARY_PATH = OUTPUT_DIR / "method_pipeline_summary.xlsx"
CLIMATE_PATH = ROOT_DIR / "data/prepared/cabernet_sauvignon_pheno_clima_by_fundo_temporada.xlsx"
PHENOLOGY_PATH = ROOT_DIR / "data/prepared/consolidado_fenologia_ELP_OBJ3_INDICES_BIOCLIMATICOS.csv"

# Mapping from our normalized fundo names to the files
FUNDO_FILES = {
    "idahue": "Idahue_2024_2025_Hora_meteovid.xlsx",
    "keule": "Keule__Zentra_29DIC_2023_18JUN_2025_HORA_meteovid.xlsx",
    "los_acacios": "Los_Acacios_INIA_Ene_Jun_2024_2025_HORA_meteovid.xlsx",
    "lourdes": "Lourdes_2024_2025_HORA.xlsx",
    "nilahue": "Nilahue__2024_2025_HORA.xlsx",
    "qba_seca": "Quebrada_Seca_2024_2025_HORA.xlsx",
    "quebrada_seca": "Quebrada_Seca_2024_2025_HORA.xlsx",
    "ucuquer": "Ucuquer_2024_2025_HORA.xlsx",
}

def calculate_dynamic_chill_portions(temps: np.ndarray) -> np.ndarray:
    """Calculate Chill Portions using the Dynamic Model (Fishman et al., 1987)."""
    temps = np.array(temps, dtype=float)
    # Erez et al constants
    E0 = 4153.5
    E1 = 12888.8
    A0 = 139500.0
    A1 = 2.567e18
    slope = 1.6
    tetmlt = 277.0

    Tk = temps + 273.15
    ftmprt = slope * tetmlt * (Tk - tetmlt) / Tk
    sr = np.exp(ftmprt)

    xi0 = E0 / Tk
    ak1 = A0 * np.exp(-xi0)

    xi1 = E1 / Tk
    ak2 = A1 * np.exp(-xi1)

    inter_e = np.zeros(len(temps))
    portions = np.zeros(len(temps))

    for i in range(1, len(temps)):
        prev_e = inter_e[i-1]
        
        # Transition
        inter_e[i] = prev_e * np.exp(-(ak1[i] + ak2[i])) + (ak1[i] / (ak1[i] + ak2[i])) * (1.0 - np.exp(-(ak1[i] + ak2[i])))
        
        if inter_e[i] >= 1.0:
            # If the intermediate reaches 1, it is irreversibly converted into a chill portion
            inter_e[i] = inter_e[i] * (1.0 - sr[i])
            # prevent negative
            if inter_e[i] < 0:
                inter_e[i] = 0.0
            portions[i] = portions[i-1] + 1.0
        else:
            portions[i] = portions[i-1]

    return portions

def normalize_fundo(f: str) -> str:
    f = str(f).lower().replace(" ", "_")
    if f == "qba_seca": return "quebrada_seca"
    return f

def calculate_gdd_simple(tmin: float, tmax: float, base: float = 10.0) -> float:
    tmean = (tmin + tmax) / 2.0
    return max(tmean - base, 0.0)

def get_season_from_date(date_obj: pd.Timestamp) -> int:
    """Returns the season_year for Southern Hemisphere (e.g., Aug 2025 -> 2025 season)."""
    return date_obj.year

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)
        
    logging.info("Reading diagnostico_cs_reg...")
    diag_df = pd.read_excel(SUMMARY_PATH, sheet_name="diagnostico_cs_reg")
    
    results = []
    
    for _, row in diag_df.iterrows():
        fundo_orig = row["Fundo"]
        fundo_norm = normalize_fundo(fundo_orig)
        file_name = FUNDO_FILES.get(fundo_norm)
        
        if file_name is None and fundo_orig.lower() == "quebrada seca":
            file_name = FUNDO_FILES.get("quebrada_seca")
            fundo_norm = "quebrada_seca"

        t0_cerrado = pd.Timestamp(row["t0_operativo"])
        doy_lat = int(row["doy_t0_pred_reg_lat"])
        # season_year is the year of budbreak
        season_year = get_season_from_date(t0_cerrado)
        t0_lat = pd.Timestamp(f"{season_year}-01-01") + pd.Timedelta(days=doy_lat - 1)
        fecha_brotacion = pd.Timestamp(row["fecha_brotacion"])
        
        may_1 = pd.Timestamp(f"{season_year}-05-01")
        sept_1 = pd.Timestamp(f"{season_year}-09-01")
        
        confidence = "Alta"
        source = "Zentra/Meteovid/INIA" if file_name and ("Zentra" in file_name or "INIA" in file_name or "meteovid" in file_name) else "CII (No metadata)"
        
        chill_lat = chill_cerrado = chill_sept1 = chill_brot = np.nan
        outliers_detected = 0
        
        if file_name and (DATA_DIR / file_name).exists():
            df_hr = pd.read_excel(DATA_DIR / file_name)
            date_col = next((c for c in df_hr.columns if 'fecha' in c.lower() or 'date' in c.lower()), None)
            temp_col = next((c for c in df_hr.columns if 'temp' in c.lower() and 'min' not in c.lower() and 'max' not in c.lower()), None)
            
            if date_col and temp_col:
                df_hr[date_col] = pd.to_datetime(df_hr[date_col], errors='coerce')
                df_hr[temp_col] = pd.to_numeric(df_hr[temp_col], errors='coerce')
                df_hr = df_hr.dropna(subset=[date_col]).sort_values(date_col)
                
                # Outlier detection
                mask_outliers = (df_hr[temp_col] < -15) | (df_hr[temp_col] > 45)
                outliers_detected = mask_outliers.sum()
                if outliers_detected > 0:
                    df_hr.loc[mask_outliers, temp_col] = np.nan
                    confidence = "Baja (Valores extremos filtrados)"
                    
                # Gaps processing
                full_range = pd.date_range(df_hr[date_col].min(), df_hr[date_col].max(), freq='h')
                df_hr = df_hr.set_index(date_col).reindex(full_range)
                
                # Interpolate short gaps (<= 3 hours), leave long gaps as NaN
                df_hr[temp_col] = df_hr[temp_col].interpolate(method='time', limit=3)
                
                if df_hr[temp_col].isna().sum() > 0:
                    confidence = "Baja (Gaps prolongados > 3h)"
                    
                # Reset index for further processing
                df_hr = df_hr.reset_index().rename(columns={"index": date_col})
                
                max_date = df_hr[date_col].max()
                if max_date < fecha_brotacion or max_date < sept_1:
                    confidence = "🔴 INCOMPLETA"
                    
                mask_season = (df_hr[date_col] >= may_1)
                df_season = df_hr[mask_season].copy()
                
                # Only compute chill portions if we have valid contiguous data and reached the milestones
                if not df_season.empty and max_date >= t0_lat:
                    # Drop any remaining NaNs for the chill calculation, or leave them and it will fail.
                    # Since we only interpolated short gaps, long gaps will remain as NaN.
                    if df_season[df_season[date_col] <= fecha_brotacion][temp_col].isna().sum() > 0:
                        confidence = "🔴 INCOMPLETA (Gaps en temporada)"
                    else:
                        df_season["chill_cum"] = calculate_dynamic_chill_portions(df_season[temp_col].values)
                        
                        try: chill_lat = df_season.loc[df_season[date_col] <= t0_lat, "chill_cum"].iloc[-1]
                        except: pass
                        try: chill_cerrado = df_season.loc[df_season[date_col] <= t0_cerrado, "chill_cum"].iloc[-1]
                        except: pass
                        try: chill_sept1 = df_season.loc[df_season[date_col] <= sept_1, "chill_cum"].iloc[-1]
                        except: pass
                        try: chill_brot = df_season.loc[df_season[date_col] <= fecha_brotacion, "chill_cum"].iloc[-1]
                        except: pass
        else:
            confidence = "⚪ SIN DATOS"
            
        # Calor (GDD)
        # Load daily climate to compute GDD
        gdd_pre_lat = gdd_post_lat = np.nan
        gdd_may = gdd_jun = gdd_jul = gdd_aug = gdd_sep = np.nan
        
        try:
            # Reconstruct sheet name
            # Format usually: fundo_yyyy_yyyy where the second yyyy is season_year
            s_name = f"{fundo_norm}_{season_year-1}_{season_year}" if season_year == 2026 else f"{fundo_norm}_{season_year}_{season_year+1}"
            # Actually, the sheets are like: idahue_2025_2026, ucuquer_2025_2026.
            # So season_year + 1 is the second part if season_year is 2025
            s_name = f"{fundo_norm}_{season_year}_{season_year+1}"
            
            xls = pd.ExcelFile(CLIMATE_PATH)
            if s_name not in xls.sheet_names:
                # Fallback to whatever sheet starts with fundo_norm
                valid_sheets = [s for s in xls.sheet_names if s.startswith(fundo_norm)]
                if valid_sheets:
                    s_name = valid_sheets[-1]
            
            if s_name in xls.sheet_names:
                df_daily = pd.read_excel(xls, sheet_name=s_name)
                df_daily["Fecha"] = pd.to_datetime(df_daily["Fecha"], errors="coerce")
                df_daily["gdd"] = df_daily.apply(lambda r: calculate_gdd_simple(r["temp_min_grado_c"], r["temp_max_grado_c"]), axis=1)
                
                # Pre latitudinal: July 1st to t0_lat
                july_1 = pd.Timestamp(f"{season_year}-07-01")
                mask_pre = (df_daily["Fecha"] >= july_1) & (df_daily["Fecha"] <= t0_lat)
                gdd_pre_lat = df_daily.loc[mask_pre, "gdd"].sum()
                
                mask_post = (df_daily["Fecha"] >= t0_lat) & (df_daily["Fecha"] <= fecha_brotacion)
                gdd_post_lat = df_daily.loc[mask_post, "gdd"].sum()
                
                # Monthly GDD
                def get_monthly_gdd(m):
                    m_start = pd.Timestamp(f"{season_year}-0{m}-01")
                    m_end = m_start + pd.offsets.MonthEnd(1)
                    return df_daily.loc[(df_daily["Fecha"] >= m_start) & (df_daily["Fecha"] <= m_end), "gdd"].sum()
                
                gdd_may = get_monthly_gdd(5)
                gdd_jun = get_monthly_gdd(6)
                gdd_jul = get_monthly_gdd(7)
                gdd_aug = get_monthly_gdd(8)
                gdd_sep = get_monthly_gdd(9)
        except Exception as e:
            logging.error(f"Error computing GDD for {fundo_orig}: {e}")
            
        res = {
            "Fundo": fundo_orig,
            "Temporada": f"{season_year}_{season_year+1}",
            "t0_latitudinal": t0_lat.strftime("%Y-%m-%d"),
            "t0_cerrado": t0_cerrado.strftime("%Y-%m-%d"),
            "fecha_brotacion": fecha_brotacion.strftime("%Y-%m-%d"),
            "chill_hasta_t0_lat": round(chill_lat, 1) if pd.notna(chill_lat) else np.nan,
            "chill_hasta_t0_cerrado": round(chill_cerrado, 1) if pd.notna(chill_cerrado) else np.nan,
            "chill_hasta_1_sept": round(chill_sept1, 1) if pd.notna(chill_sept1) else np.nan,
            "chill_hasta_brotacion": round(chill_brot, 1) if pd.notna(chill_brot) else np.nan,
            "gdd_jul1_a_t0_lat": round(gdd_pre_lat, 1) if pd.notna(gdd_pre_lat) else np.nan,
            "gdd_t0_lat_a_brotacion": round(gdd_post_lat, 1) if pd.notna(gdd_post_lat) else np.nan,
            "gdd_may": round(gdd_may, 1),
            "gdd_jun": round(gdd_jun, 1),
            "gdd_jul": round(gdd_jul, 1),
            "gdd_aug": round(gdd_aug, 1),
            "gdd_sep": round(gdd_sep, 1),
            "estado_cobertura_horaria": confidence,
            "fuente_horaria": source,
            "outliers_filtrados": outliers_detected
        }
        results.append(res)
        
    df_out = pd.DataFrame(results)
    out_path = OUTPUT_DIR / "chill_dynamic_diagnostics_by_fundo_temporada.csv"
    df_out.to_csv(out_path, index=False)
    logging.info(f"Saved diagnostics to {out_path}")
    
if __name__ == "__main__":
    main()
