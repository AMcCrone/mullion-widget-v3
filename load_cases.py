from config import material_props, BARRIER_LENGTH
import pandas as pd
import streamlit as st

def generate_load_case_tables(wind_pressure, bay_width, mullion_length, selected_barrier_load):
    """
    Generate dataframes for ULS and SLS load cases.
    
    Parameters:
    -----------
    wind_pressure : float
        Wind pressure in kPa
    bay_width : float
        Width of the bay in mm
    mullion_length : float
        Length of the mullion in mm
    selected_barrier_load : float
        Barrier load in kN/m
    
    Returns:
    --------
    tuple
        (uls_df, sls_df) - DataFrames containing ULS and SLS load case information
    """
    
    
    # Convert wind pressure from kPa to N/mm²
    p = wind_pressure * 0.001
    L = mullion_length
    bay = bay_width
    w = p * bay
    M_WL = (w * L**2) / 8
    M_BL = ((selected_barrier_load * bay) * BARRIER_LENGTH) / 2
    
    # ULS calculations
    uls_data = []
    
    # ULS 1: 1.5 WL + 0.75 BL
    M_ULS1 = 1.5 * M_WL + 0.75 * M_BL
    Z_req1 = M_ULS1 / material_props["Aluminium"]["fy"]  # Using Aluminium as default for calculation
    Z_req1_cm3 = Z_req1 / 1000  # Convert to cm³
    uls_data.append({
        "Load Case": "ULS 1",
        "Loading": f"1.5 WL + 0.75 BL",
        "Required Z (cm³)": f"{Z_req1_cm3:.2f}"
    })
    
    # ULS 2: 0.75 WL + 1.5 BL
    M_ULS2 = 0.75 * M_WL + 1.5 * M_BL
    Z_req2 = M_ULS2 / material_props["Aluminium"]["fy"]
    Z_req2_cm3 = Z_req2 / 1000
    uls_data.append({
        "Load Case": "ULS 2",
        "Loading": f"0.75 WL + 1.5 BL",
        "Required Z (cm³)": f"{Z_req2_cm3:.2f}"
    })
    
    # ULS 3: 1.5 WL
    M_ULS3 = 1.5 * M_WL
    Z_req3 = M_ULS3 / material_props["Aluminium"]["fy"]
    Z_req3_cm3 = Z_req3 / 1000
    uls_data.append({
        "Load Case": "ULS 3",
        "Loading": f"1.5 WL",
        "Required Z (cm³)": f"{Z_req3_cm3:.2f}"
    })
    
    # ULS 4: 1.5 BL
    M_ULS4 = 1.5 * M_BL
    Z_req4 = M_ULS4 / material_props["Aluminium"]["fy"]
    Z_req4_cm3 = Z_req4 / 1000
    uls_data.append({
        "Load Case": "ULS 4",
        "Loading": f"1.5 BL",
        "Required Z (cm³)": f"{Z_req4_cm3:.2f}"
    })
    
    # Create ULS dataframe
    uls_df = pd.DataFrame(uls_data)
    
    # SLS calculations
    sls_data = []
    
    # Deflection limit based on mullion length
    if L <= 3000:
        defl_limit = L / 200
    elif L < 7500:
        defl_limit = 5 + L / 300
    else:
        defl_limit = L / 250
    
    E = material_props["Aluminium"]["E"]  # Using Aluminium as default
    
    # SLS 1: Wind Load
    I_req_wl = (5 * w * L**4) / (384 * E * defl_limit)
    I_req_wl_cm4 = I_req_wl / 10000  # Convert from mm⁴ to cm⁴
    sls_data.append({
        "Load Case": "SLS 1",
        "Loading": "Wind Load",
        "Required I (cm⁴)": f"{I_req_wl_cm4:.2f}"
    })
    
    # SLS 2: Barrier Load
    F_BL = selected_barrier_load * bay
    I_req_bl = ((F_BL * BARRIER_LENGTH) / (12 * E * defl_limit)) * (0.75 * L**2 - BARRIER_LENGTH**2)
    I_req_bl_cm4 = I_req_bl / 10000  # Convert from mm⁴ to cm⁴
    sls_data.append({
        "Load Case": "SLS 2",
        "Loading": "Barrier Load",
        "Required I (cm⁴)": f"{I_req_bl_cm4:.2f}"
    })
    
    # Create SLS dataframe
    sls_df = pd.DataFrame(sls_data)
    
    return uls_df, sls_df

def display_load_case_tables(wind_pressure, bay_width, mullion_length, selected_barrier_load):
    """
    Display Streamlit dataframes for ULS and SLS load cases.
    
    Parameters:
    -----------
    wind_pressure : float
        Wind pressure in kPa
    bay_width : float
        Width of the bay in mm
    mullion_length : float
        Length of the mullion in mm
    selected_barrier_load : float
        Barrier load in kN/m
    """
    
    uls_df, sls_df = generate_load_case_tables(
        wind_pressure, bay_width, mullion_length, selected_barrier_load
    )
    
    st.subheader("Ultimate Limit State (ULS) Load Cases")
    st.dataframe(uls_df)
    
    st.subheader("Serviceability Limit State (SLS) Load Cases")
    st.dataframe(sls_df)
