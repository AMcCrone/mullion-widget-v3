# custom_profile.py
import tempfile
import os
import streamlit as st
from sectionproperties.pre import Geometry
from sectionproperties.analysis import Section
import matplotlib.pyplot as plt

def get_custom_profile():
    """Process DXF file with manual depth input"""
    custom_data = {"type": "dxf"}
    
    uploaded_file = st.file_uploader("Upload DXF File", type=["dxf"])
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_filename = tmp_file.name
            
        try:
            # Process DXF for basic properties
            geom = Geometry.from_dxf(dxf_filepath=tmp_filename)
            geom.create_mesh(mesh_sizes=[2.0])
            sec = Section(geometry=geom)
            sec.calculate_geometric_properties()

            # Get required properties
            ixx = sec.get_ic()[0]  # Major moment of inertia (Ixx)
            zxx_plus, zxx_minus, *_ = sec.get_z()  # Major axis moduli
            zxx = min(zxx_plus, zxx_minus)  # Conservative value
            
            # Manual depth input
            depth = st.number_input("Section Depth (mm)", 
                                  min_value=50.0, max_value=500.0, 
                                  value=150.0, step=1.0)

            # Create visualization
            fig, ax = plt.subplots(figsize=(6, 4))
            sec.plot_mesh(materials=False, ax=ax)
            ax.set_title("Section Mesh Preview")
            ax.set_aspect("equal")
            ax.invert_xaxis()
            ax.invert_yaxis()

            # Populate custom data
            custom_data["name"] = st.text_input("Profile Name", value="DXF Profile")
            custom_data["depth"] = depth
            custom_data["I"] = ixx / 1e4  # mm⁴ → cm⁴
            custom_data["Z"] = zxx / 1e3  # mm³ → cm³

            # Display results
            st.pyplot(fig)
            st.write("**Calculated Section Properties:**")
            st.metric("Moment of Inertia (Ixx)", f"{custom_data['I']:.1f} cm⁴")
            st.metric("Section Modulus (Zxx)", f"{custom_data['Z']:.1f} cm³")

        except Exception as e:
            st.error(f"DXF Processing Error: {str(e)}")
            st.write("Temporary file path:", tmp_filename)
            custom_data = {}
                
        finally:
            os.remove(tmp_filename)
            
    return custom_data
