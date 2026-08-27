import pandas as pd
import numpy as np
import xarray as xr
from xclim.indices import chill_portions

def test_against_xclim():
    print("--- 3. Results vs reference (xclim) ---")
    
    # Create test series
    # 1. Constant 6C for 300 hours
    temp_const = np.full(300, 6.0)
    
    # 2. Day/night cycle (0C to 15C)
    time = np.arange(300)
    temp_cycle = 7.5 + 7.5 * np.sin(2 * np.pi * time / 24)
    
    # 3. Warm pulses (5C base, pulses of 25C)
    temp_pulse = np.full(300, 5.0)
    temp_pulse[50:60] = 25.0
    temp_pulse[150:160] = 25.0
    
    # 4. Real series chunk (random walk)
    np.random.seed(42)
    temp_real = 10 + np.cumsum(np.random.normal(0, 1, 300))
    
    scenarios = {
        'Constant 6C': temp_const,
        'Day/Night Cycle': temp_cycle,
        'Warm Pulses': temp_pulse,
        'Random Walk': temp_real
    }
    
    for name, temps in scenarios.items():
        # Our implementation
        s_temps = pd.Series(temps)
        res_ours = calculate_dynamic_model(s_temps)
        cp_ours = res_ours['CP_acum'].values
        
        # xclim implementation
        # xclim expects xarray with time dimension
        dates = pd.date_range('2024-01-01', periods=len(temps), freq='h')
        da_tas = xr.DataArray(temps, coords=[dates], dims=['time'])
        da_tas.attrs['units'] = 'degC'
        
        # xclim chill_portions computes the total per season by default, 
        # but if we pass it directly it might resample. 
        # To get the hourly accumulation, we can use the internal function:
        from xclim.indices._agro import _chill_portion_one_season
        da_tas_k = da_tas + 273.15
        delta_xclim = _chill_portion_one_season(da_tas_k.values)
        cp_xclim = np.cumsum(delta_xclim)
        
        # Compare
        max_diff = np.max(np.abs(cp_ours - cp_xclim))
        print(f"Scenario '{name}': Max Diff = {max_diff:.6e} CP")
        print(f"  Our total: {cp_ours[-1]:.6f}, xclim total: {cp_xclim[-1]:.6f}")
        if max_diff > 1e-5:
            print(f"Mismatch in {name}!")

def check_boundary_behavior():
    print("\n--- 4. Boundary behavior at CP generation ---")
    temp_const = pd.Series(np.full(100, 6.0))
    res = calculate_dynamic_model(temp_const)
    
    # Find where CP increases
    cp_increases = res[res['CP_hourly'] > 0].index
    if len(cp_increases) > 0:
        idx = cp_increases[0]
        print(f"First CP generation at hour {idx}")
        print("State previous hour: " + str(res.loc[idx-1].to_dict()))
        print("State generation hour: " + str(res.loc[idx].to_dict()))
        print("State next hour: " + str(res.loc[idx+1].to_dict()))
    else:
        print("No CP generated.")

def check_chunking():
    print("\n--- 5. Chunking conservation ---")
    temp_const = pd.Series(np.full(300, 6.0))
    res_full = calculate_dynamic_model(temp_const)
    
    # Split into 3 chunks
    c1 = temp_const.iloc[:100]
    c2 = temp_const.iloc[100:200]
    c3 = temp_const.iloc[200:]
    
    r1 = calculate_dynamic_model(c1)
    state1 = {'x': r1['x_state'].iloc[-1], 'y': r1['CP_acum'].iloc[-1], 'prev_xi': r1['prev_xi'].iloc[-1]}
    
    r2 = calculate_dynamic_model(c2, initial_state=state1)
    state2 = {'x': r2['x_state'].iloc[-1], 'y': r2['CP_acum'].iloc[-1], 'prev_xi': r2['prev_xi'].iloc[-1]}
    
    r3 = calculate_dynamic_model(c3, initial_state=state2)
    
    chunked_acum = r3['CP_acum'].iloc[-1]
    full_acum = res_full['CP_acum'].iloc[-1]
    diff = abs(chunked_acum - full_acum)
    
    print(f"Full accumulation: {full_acum:.6f}")
    print(f"Chunked accumulation: {chunked_acum:.6f}")
    print(f"Difference: {diff:.6e}")
    if diff > 1e-5:
        print("CHUNK STATE IS NOT PERFECTLY CONSERVED (Missing prev_xi?)")

if __name__ == '__main__':
    from build_chill_indicators import calculate_dynamic_model
    test_against_xclim()
    check_boundary_behavior()
    check_chunking()
