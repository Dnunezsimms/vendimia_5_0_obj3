import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from pathlib import Path
import json

def sine_model(t, A, omega, phi, D):
    return A * np.sin(omega * t + phi) + D

def sine_derivative(t, A, omega, phi):
    return A * omega * np.cos(omega * t + phi)

def detect_valleys():
    print("Iniciando detecciÃ³n de valles tÃ©rmicos con modelo sinusoidal...")
    base_dir = Path(__file__).resolve().parent.parent
    csv_path = base_dir / "reports" / "fase6" / "frio_diario_2025.csv"
    out_dir = base_dir / "reports" / "fase6" / "valles_termicos"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(csv_path)
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    fundos = df['fundo_canonical'].unique()
    resultados = []
    
    # La frecuencia astronÃ³mica esperada de un ciclo anual es 2*pi / 365
    omega_guess = 2 * np.pi / 365.25
    
    for fundo in fundos:
        df_fundo = df[df['fundo_canonical'] == fundo].copy()
        df_fundo = df_fundo.sort_values('fecha').reset_index(drop=True)
        df_fundo = df_fundo.dropna(subset=['temp_media'])
        
        if len(df_fundo) < 30:
            continue
            
        x = np.arange(len(df_fundo))
        y = df_fundo['temp_media'].values
        
        # ParÃ¡metros iniciales: (A: amplitud, omega, phi: fase, D: media)
        A_guess = (np.max(y) - np.min(y)) / 2.0
        D_guess = np.mean(y)
        # Buscar el punto mÃ¡s frÃ­o aproximado para alinear la fase
        min_idx_approx = np.argmin(y)
        # Queremos que A*sin(omega*t + phi) sea mÃ­nimo (-A)
        # sin(theta) = -1 => theta = 3*pi/2 => omega*t_min + phi = 3*pi/2 => phi = 3*pi/2 - omega*t_min
        phi_guess = 3 * np.pi / 2 - omega_guess * min_idx_approx
        
        # Limites (bounds) para forzar un ciclo anual (evitar que ajuste frecuencias ridÃ­culas)
        # omega puede variar ligeramente pero cerca de 1 aÃ±o.
        bounds = (
            [0, omega_guess * 0.8, -np.inf, -10],
            [100, omega_guess * 1.2, np.inf, 40]
        )
        
        try:
            popt, _ = curve_fit(sine_model, x, y, p0=[A_guess, omega_guess, phi_guess, D_guess], bounds=bounds)
        except RuntimeError:
            print(f"Error ajustando curva para {fundo}")
            continue
            
        A, omega, phi, D = popt
        
        # Generar curva continua (y su derivada)
        x_dense = np.linspace(0, len(x)-1, 1000)
        y_fit = sine_model(x_dense, A, omega, phi, D)
        y_deriv = sine_derivative(x_dense, A, omega, phi)
        
        # Encontrar donde la derivada es exactamente cero y la curva estÃ¡ en el mÃ­nimo
        # MatemÃ¡ticamente: A*sin(wt + phi) es mÃ­nimo cuando wt + phi = 3*pi/2 + 2*k*pi
        # Resolviendo para t: t = (3*pi/2 - phi) / omega
        # Buscamos el k que ponga a t dentro de nuestro rango [0, len(x)]
        t_valle_exacto = None
        for k in range(-5, 5):
            t_cand = (3 * np.pi / 2 + 2 * k * np.pi - phi) / omega
            if 0 <= t_cand <= len(x):
                t_valle_exacto = t_cand
                break
        
        if t_valle_exacto is None:
            # Fallback en caso de que la curva quede fuera
            t_valle_exacto = x_dense[np.argmin(y_fit)]
        
        t_valle_dense = t_valle_exacto
        min_idx = np.argmin(np.abs(x_dense - t_valle_exacto))
        
        # Interpolar para encontrar la fecha exacta
        fecha_start = df_fundo['fecha'].iloc[0]
        # x representa "dÃ­as", asÃ­ que t_valle_dense lo podemos sumar como timedelta
        fecha_valle_exacta = fecha_start + pd.Timedelta(days=t_valle_dense)
        # Redondear a la fecha entera mÃ¡s cercana
        fecha_valle_str = fecha_valle_exacta.round('d').strftime('%Y-%m-%d')
        valle_temp = y_fit[min_idx]
        
        eq_text = f"T(t) = {A:.2f} * sin({omega:.4f}t + {phi:.2f}) + {D:.2f}"
        
        resultados.append({
            'fundo': fundo,
            'fecha_valle_matematico': fecha_valle_str,
            'temperatura_valle_suavizada': round(valle_temp, 2),
            'ecuacion': eq_text
        })
        
        # Inject equation into JSON for the HTML dashboard
        json_path = base_dir / "reports" / "dashboards_html" / "data" / "valles" / f"{fundo.lower().replace(' ', '_')}.json"
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
                data['ecuacion_sinusoidal'] = eq_text
                with open(json_path, 'w', encoding='utf-8') as jf:
                    json.dump(data, jf, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"No se pudo inyectar ecuacion en {json_path}: {e}")
                
        # Generar grfico
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(df_fundo['fecha'], y, label="Temp Media Observada", color='gray', alpha=0.5)
        
        fechas_dense = pd.date_range(start=fecha_start, periods=len(x_dense), freq=f"{(x[-1]/1000)*24}h")
        # Ajustamos el array de fechas denso a algo simple para plotear:
        fechas_dense_plot = [fecha_start + pd.Timedelta(days=d) for d in x_dense]
        
        ax1.plot(fechas_dense_plot, y_fit, label="Ajuste Sinusoidal (TeÃ³rico)", color='blue', linewidth=2.5)
        ax1.axvline(x=pd.to_datetime(fecha_valle_str), color='red', linestyle='--', label=f'Fondo de Valle: {fecha_valle_str}')
        
        # Anotar la curva sinusoidal en el grÃ¡fico (sin usar caracteres especiales que rompan python o matplotlib)
        eq_text = f"Curva Sinusoidal:\n$T(t) = {A:.2f} * sin({omega:.4f}t + {phi:.2f}) + {D:.2f}$"
        ax1.text(0.02, 0.05, eq_text, transform=ax1.transAxes, fontsize=10, 
                 bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray'), 
                 verticalalignment='bottom')
                 
        ax1.set_ylabel("Temperatura Media Diaria (Â°C)")
        ax1.set_title(f"Ajuste Sinusoidal de Temperatura Anual - {fundo.capitalize()}")
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="upper left")
        
        ax2 = ax1.twinx()
        ax2.plot(fechas_dense_plot, y_deriv, label="1ra Derivada (Pendiente)", color='green', linestyle=':', alpha=0.7)
        ax2.axhline(y=0, color='green', alpha=0.3)
        ax2.set_ylabel("Derivada (Â°C/dÃ­a)", color='green')
        ax2.tick_params(axis='y', labelcolor='green')
        
        fig.tight_layout()
        plt.savefig(out_dir / f"valle_termico_{fundo}.png", dpi=150)
        plt.close(fig)
        
    df_res = pd.DataFrame(resultados)
    df_res.to_csv(out_dir / "resumen_valles_termicos_2025.csv", index=False)
    print("\nResultados calculados con modelo sinusoidal:")
    print(df_res)
    print(f"\nGrÃ¡ficos guardados en: {out_dir}")

if __name__ == "__main__":
    detect_valleys()

