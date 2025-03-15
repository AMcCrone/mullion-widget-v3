# custom_profile.py
import tempfile
import os
import streamlit as st
from sectionproperties.pre import Geometry
from sectionproperties.analysis import Section
import matplotlib.pyplot as plt

def get_custom_profile():
    """Process DXF file with optimized layout and rotation"""
    custom_data = {
        "type": "dxf",
        "name": "DXF Profile",
        "depth": 150.0,  # Default value
        "Z": 1.0,
        "I": 1.0
    }
    
    # Input fields on one line
    col1, col2 = st.columns(2)
    with col1:
        custom_data["name"] = st.text_input("Profile Name", value="DXF Profile")
    with col2:
        custom_data["depth"] = st.number_input("Section Depth (mm)", 
                                             min_value=50.0, max_value=500.0, 
                                             value=150.0, step=1.0)
    
    uploaded_file = st.file_uploader("Upload DXF File", type=["dxf"])
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_filename = tmp_file.name
            
        try:
            # Process DXF
            geom = Geometry.from_dxf(dxf_filepath=tmp_filename)
            geom.create_mesh(mesh_sizes=[5])
            sec = Section(geometry=geom)
            sec.calculate_geometric_properties()

            # Get properties
            ixx = sec.get_ic()[0]
            zxx_plus, zxx_minus, *_ = sec.get_z()
            zxx = min(zxx_plus, zxx_minus)

            # Update calculated values
            custom_data.update({
                "I": ixx / 1e4,
                "Z": zxx / 1e3
            })

            # Rotated mesh plot
            fig, ax = plt.subplots(figsize=(8, 4))  # Landscape aspect ratio
            sec.plot_mesh(materials=False, ax=ax)
            
            # Rotate 90 degrees
            ax.invert_xaxis()
            ax.invert_yaxis()
            ax.set_aspect("equal")
            ax.set_title("Section Preview (Rotated 90°)")
            
            st.pyplot(fig)

            # Display metrics
            st.write("**Calculated Properties:**")
            st.metric("Moment of Inertia (Ixx)", f"{custom_data['I']:.1f} cm⁴")
            st.metric("Section Modulus (Zxx)", f"{custom_data['Z']:.1f} cm³")

        except Exception as e:
            st.error(f"DXF Processing Error: {str(e)}")
            st.write("Ensure:")
            st.write("- Closed, non-intersecting polylines")
            st.write("- 2D geometry (Z=0)")
            st.write("- Units in millimeters")
                
        finally:
            os.remove(tmp_filename)
            
    return custom_data
