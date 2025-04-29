import streamlit as st

def set_page_config():
    st.set_page_config(page_title="Section Design Tool", layout="wide")

# Define TT Colours
TT_Orange = "rgb(211,69,29)"
TT_Olive = "rgb(139,144,100)"
TT_LightBlue = "rgb(136,219,223)"
TT_MidBlue = "rgb(0,163,173)"
TT_DarkBlue = "rgb(0,48,60)"
TT_Grey = "rgb(99,102,105)"
TT_LightLightBlue = "rgb(207,241,242)"
TT_LightGrey = "rgb(223,224,225)"
TT_Purple = "rgb(128,0,128)"

# Material properties
material_props = {
    "Aluminium": {"fy": 160, "E": 70000},
    "Steel": {"fy": 275, "E": 210000}
}

# Constant: Barrier Length (mm)
BARRIER_LENGTH = 1100
