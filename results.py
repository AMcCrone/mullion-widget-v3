import streamlit as st
import pandas as pd
import numpy as np

def display_results(calc_results, wind_pressure, bay_width, mullion_length, selected_barrier_load, 
                   ULS_case, SLS_case, plot_material, view_3d_option):
    """
    Displays a summary of the structural calculation results.
    
    Args:
        calc_results: Tuple containing results from the generate_plots function
        wind_pressure: Wind pressure in kPa
        bay_width: Width of the bay in mm
        mullion_length: Length of the mullion in mm
        selected_barrier_load: Barrier load in kN/m
        ULS_case: Selected Ultimate Limit State load case
        SLS_case: Selected Serviceability Limit State load case
        plot_material: Selected material (Aluminium or Steel)
        view_3d_option: Selected 3D view option
    """
    # Unpack the calculation results
    uls_fig, sls_fig, util_fig, defl_values, Z_req_cm3, defl_limit = calc_results
    
    # Convert wind pressure from kPa to N/mm²
    p = wind_pressure * 0.001
    L = mullion_length
    bay = bay_width
    w = p * bay
    
    # Calculate moments for each case
    BARRIER_LENGTH = 1100  # Assuming this constant from the calc.py
    M_WL = (w * L**2) / 8
    M_BL = ((selected_barrier_load * bay) * BARRIER_LENGTH) / 2
    
    # Get material properties
    # Assuming these are defined elsewhere, but we'll need them
    material_props = {
        "Aluminium": {"E": 70000, "fy": 260},  # Example values, adjust as needed
        "Steel": {"E": 210000, "fy": 355}      # Example values, adjust as needed
    }
    
    E = material_props[plot_material]["E"]
    fy = material_props[plot_material]["fy"]
    
    # Calculate required second moment of area (Iyy) for SLS
    if SLS_case.startswith("SLS 1"):
        # Wind load deflection
        I_req = (5 * w * L**4) / (384 * E * defl_limit)
    else:
        # Barrier load deflection
        F_BL = selected_barrier_load * bay
        I_req = ((F_BL * BARRIER_LENGTH) / (12 * E * defl_limit)) * (0.75 * L**2 - BARRIER_LENGTH**2)
    
    st.header("Design Results Summary")
    
    # ULS Results
    st.subheader("Ultimate Limit State (ULS) Design")
    
    uls_data = []
    
    if "ULS 1" in ULS_case or "ULS 3" in ULS_case:
        M_case = 1.5 * M_WL if "ULS 3" in ULS_case else 1.5 * M_WL + 0.75 * M_BL
        Z_case = M_case / fy
        uls_data.append(["Wind Load", f"{M_WL:.2f} Nmm", f"{1.5 * M_WL:.2f} Nmm"])
    
    if "ULS 2" in ULS_case or "ULS 4" in ULS_case or "ULS 1" in ULS_case:
        if "ULS 1" in ULS_case:
            pass  # Already covered above
        elif "ULS 2" in ULS_case:
            M_case = 0.75 * M_WL + 1.5 * M_BL
            Z_case = M_case / fy
            uls_data.append(["Wind Load", f"{M_WL:.2f} Nmm", f"{0.75 * M_WL:.2f} Nmm"])
            uls_data.append(["Barrier Load", f"{M_BL:.2f} Nmm", f"{1.5 * M_BL:.2f} Nmm"])
        else:  # ULS 4
            M_case = 1.5 * M_BL
            Z_case = M_case / fy
            uls_data.append(["Barrier Load", f"{M_BL:.2f} Nmm", f"{M_case:.2f} Nmm"])
    
    if "ULS 1" in ULS_case:
        uls_data.append(["Barrier Load", f"{M_BL:.2f} Nmm", f"{0.75 * M_BL:.2f} Nmm"])
    
    # Display ULS results
    if uls_data:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("Load Type")
        with col2:
            st.write("Unfactored Moment")
        with col3:
            st.write("Factored Moment")
            
        for row in uls_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(row[0])
            with col2:
                st.write(row[1])
            with col3:
                st.write(row[2])
    
    st.write(f"**Total Design Moment:** {M_case:.2f} Nmm")
    st.write(f"**Required Section Modulus:** {Z_req_cm3:.2f} cm³")
    
    # SLS Results
    st.subheader("Serviceability Limit State (SLS) Design")
    
    st.write(f"**Deflection Limit:** {defl_limit:.2f} mm")
    st.write(f"**Required Second Moment of Area:** {I_req:.2f} mm⁴")
    
    if SLS_case.startswith("SLS 1"):
        st.write(f"**Load Case:** Wind Load")
        st.write(f"**Load Intensity:** {w:.5f} N/mm")
    else:
        st.write(f"**Load Case:** Barrier Load")
        st.write(f"**Barrier Force:** {selected_barrier_load * bay:.2f} N")
    
    # Display the plotly figures
    st.plotly_chart(uls_fig)
    st.plotly_chart(sls_fig)
    st.plotly_chart(util_fig)
    
    # Return calculated values for PDF export
    return {
        "wind_pressure": wind_pressure,
        "bay_width": bay_width,
        "mullion_length": mullion_length,
        "barrier_load": selected_barrier_load,
        "material": plot_material,
        "ULS_case": ULS_case,
        "SLS_case": SLS_case,
        "M_WL": M_WL,
        "M_BL": M_BL,
        "M_case": M_case,
        "Z_req": Z_req_cm3,
        "defl_limit": defl_limit,
        "I_req": I_req
    }
