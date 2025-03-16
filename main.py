import streamlit as st
import os
import pandas as pd
import io

from auth import authenticate_user
from config import set_page_config, material_props
from calc import generate_plots, generate_section_database
from pdf_export import get_pdf_bytes
from documentation import render_documentation
from custom_profile import get_custom_profile
import matplotlib.pyplot as plt
from sectionproperties.analysis.section import Section

# ---------------------------
# Authentication & Page Config
# ---------------------------
authenticate_user()
set_page_config()

st.title("Mullion Design Widget - *Beta Version*")
st.markdown("Find your one in a mullion ❤️")

# ---------------------------
# Sidebar: Settings & Data Input
# ---------------------------
st.sidebar.header("Settings")
plot_material = st.sidebar.selectbox("Select Material", options=["Aluminium", "Steel"], index=0)

# Read the Excel file (using a relative path)
file_path = "data/Cross_Sections_Database.xlsx"
SHEET = "Alu Mullion Database" if plot_material == "Aluminium" else "Steel Mullion Database"
try:
    df = pd.read_excel(file_path, sheet_name=SHEET, engine="openpyxl")
except Exception as e:
    st.error(f"Error reading Excel file: {e}")
    st.stop()

selected_columns = ["Supplier", "Profile Name", "Material", "Reinf", "Depth", "Iyy", "Wyy"]
df_selected = df[selected_columns].iloc[1:].reset_index(drop=True)

# Sidebar: Calculation Parameters
selected_suppliers = st.sidebar.multiselect(
    "Select Suppliers",
    options=sorted(df_selected["Supplier"].unique()),
    default=sorted(df_selected["Supplier"].unique())
)
barrier_load_option = st.sidebar.radio(
    "Barrier Load (kN/m)", options=["None", "0.74", "1.5", "3"], index=0
)
selected_barrier_load = 0 if barrier_load_option == "None" else float(barrier_load_option)
ULS_case = st.sidebar.radio(
    "ULS Load Case",
    options=[
        "ULS 1: 1.5WL + 0.75BL", 
        "ULS 2: 0.75WL + 1.5BL", 
        "ULS 3: 1.5WL", 
        "ULS 4: 1.5BL"
    ],
    index=0
)
SLS_case = st.sidebar.radio("SLS Load Case", options=["SLS 1: WL", "SLS 2: BL"], index=0)
view_3d_option = st.sidebar.radio(
    "3D View",
    options=["Isometric: Overview", "XY Plane: Utilisation", "XZ Plane: Section Depth"],
    index=0
)
wind_pressure = st.sidebar.slider("Wind Pressure (kPa)", 0.1, 5.0, 1.0, 0.1)
bay_width = st.sidebar.slider("Bay Width (mm)", 500, 10000, 3000, 250)
mullion_length = st.sidebar.slider("Mullion Length (mm)", 2500, 12000, 4000, 250)

# In main.py
with st.expander("Custom Profile?", expanded=False):
    custom_option = st.selectbox(
        "Select Custom Profile Option", 
        ["None", "Manual Input", "Import DXF"]
    )
    
    custom_section_data = {}
    
    if custom_option == "Manual Input":
         col1, col2, col3, col4 = st.columns(4)
         with col1:
             name = st.text_input("Profile Name", value="Custom Profile")
         with col2:
             depth = st.number_input("Section Depth (mm)", min_value=50.0, max_value=500.0, value=150.0, step=1.0)
         with col3:
             Z = st.number_input("Section Modulus (cm³)", min_value=1.0, max_value=1000.0, value=50.0, step=1.0)
         with col4:
             I = st.number_input("Moment of Inertia (cm⁴)", min_value=1.0, max_value=10000.0, value=500.0, step=1.0)
         custom_section_data = {"type": "manual", "name": name, "depth": depth, "Z": Z, "I": I}
    elif custom_option == "Import DXF":
        custom_section_data = get_custom_profile()

use_custom_section = custom_section_data.get("type") in ["manual", "dxf"]


# ---------------------------
# Generate Figures & Calculations
# ---------------------------
# generate_plots returns the three figures plus key calculation values
uls_fig, sls_fig, util_fig, defl_values, Z_req_cm3, defl_limit = generate_plots(
    wind_pressure, bay_width, mullion_length, selected_barrier_load,
    ULS_case, SLS_case, df_selected, plot_material, selected_suppliers,
    use_custom_section, custom_section_data, view_3d_option
)

# ---------------------------
# Layout: Display Figures & PDF Export
# ---------------------------
col1, col2, col3 = st.columns([1, 1, 1.5])
with col1:
    st.plotly_chart(uls_fig, height=650, use_container_width=True)
    pdf_uls = get_pdf_bytes(uls_fig)
    st.download_button("Download ULS PDF", data=pdf_uls, file_name="ULS_Design.pdf", mime="application/pdf")
with col2:
    st.plotly_chart(sls_fig, height=650, use_container_width=True)
    pdf_sls = get_pdf_bytes(sls_fig)
    st.download_button("Download SLS PDF", data=pdf_sls, file_name="SLS_Design.pdf", mime="application/pdf")
with col3:
    st.plotly_chart(util_fig, height=650, use_container_width=True)
    pdf_util = get_pdf_bytes(util_fig)
    st.download_button("Download Utilisation PDF", data=pdf_util, file_name="3D_Utilisation.pdf", mime="application/pdf")

# ---------------------------
# Section Database Table
# ---------------------------
df_display = generate_section_database(
    df_selected, plot_material, selected_suppliers, custom_section_data, use_custom_section,
    wind_pressure, bay_width, mullion_length, selected_barrier_load, SLS_case, defl_limit, Z_req_cm3
)
st.title("Section Database")
st.dataframe(df_display, height=500)

# ---------------------------
# Documentation Section
# ---------------------------
with st.expander("The Boring Stuff...", expanded=False):
    render_documentation()
