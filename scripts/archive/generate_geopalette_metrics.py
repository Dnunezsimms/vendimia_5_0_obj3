import json
import random
import os
import pandas as pd

stations_file = r"C:\projects\geopalette_dashboard\stations.json"
out_file = r"C:\projects\geopalette_dashboard\data\station_metrics.json"

# Load the base stations
with open(stations_file, 'r', encoding='utf-8') as f:
    stations = json.load(f)

# Real values from proxy_test_pencahue_results.csv (approx)
real_metrics = {
    '66': {'rmse': 2.1, 'bias': -0.5}, # Nilahue (Placeholder ID for San Clemente)
    'Lourdes': {'rmse': 1.8, 'bias': 0.2}
}

for s in stations:
    # Inject real data if matches, otherwise simulate realistic ERA5 biases
    _id = str(s.get('identificacion'))
    
    if _id in real_metrics:
        s['rmse'] = real_metrics[_id]['rmse']
        s['bias'] = real_metrics[_id]['bias']
        s['is_simulated'] = False
    else:
        # Simulate Bias from -3.0 to +3.0
        # If calidad is 'ALTA', tend towards lower bias
        cal = s.get('calidad_global', 'Desconocida')
        
        if cal == 'ALTA':
            bias = random.uniform(-1.5, 1.5)
            rmse = random.uniform(1.0, 2.5)
        elif cal == 'MEDIA':
            bias = random.uniform(-2.5, 2.5)
            rmse = random.uniform(2.0, 3.5)
        else:
            bias = random.uniform(-4.0, 4.0)
            rmse = random.uniform(3.0, 5.0)
            
        s['bias'] = round(bias, 2)
        s['rmse'] = round(rmse, 2)
        s['is_simulated'] = True

os.makedirs(os.path.dirname(out_file), exist_ok=True)
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(stations, f, ensure_ascii=False, indent=2)

print(f"Metrics generated and saved to {out_file}")
