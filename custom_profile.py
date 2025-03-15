# custom_profile.py
import tempfile
import os
import streamlit as st
from sectionproperties.pre import Geometry
from sectionproperties.analysis import Section
import matplotlib.pyplot as plt

def get_custom_profile():
    """Process DXF with proper 90° rotation for mullion visualization"""
    custom_data = {
        "type": "dxf",
        "name": "DXF Profile",
        "depth": 150.0,
        "Z": 1.0,
        "I": 1.0
    }
    
    # Input row at top
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
            # Load and rotate geometry
            geom = Geometry.from_dxf(dxf_filepath=tmp_filename)
            geom = geom.rotate_section(angle=90)  # Physical rotation
            geom.create_mesh(mesh_sizes=[10.0])
            sec = Section(geometry=geom)
            sec.calculate_geometric_properties()

            # Get properties from rotated section
            ixx = sec.get_ic()[0]  # Now corresponds to original vertical axis
            zxx_plus, zxx_minus, *_ = sec.get_z()
            zxx = min(zxx_plus, zxx_minus)

            # Update data with converted units
            custom_data.update({
                "I": ixx / 1e4,  # mm⁴ → cm⁴
                "Z": zxx / 1e3    # mm³ → cm³
            })

            # Create landscape plot
            fig, ax = plt.subplots(figsize=(10, 5))  # Wider aspect ratio
            sec.plot_mesh(materials=False, ax=ax)
            ax.set_title("Mullion Cross-Section (Rotated 90°)")
            ax.set_aspect("equal")
            ax.set_xlabel("Height")
            ax.set_ylabel("Width")
            
            st.pyplot(fig)

            # Display results
            st.write("**Structural Properties:**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Moment of Inertia (Ixx)", f"{custom_data['I']:.1f} cm⁴")
            with col2:
                st.metric("Section Modulus (Zxx)", f"{custom_data['Z']:.1f} cm³")

        except Exception as e:
            st.error(f"Processing Error: {str(e)}")
            st.write("Ensure your DXF:")
            st.write("- Contains closed polylines")
            st.write("- Has units in millimeters")
            st.write("- No 3D elements (Z=0 for all points)")
                
        finally:
            os.remove(tmp_filename)
            
    return custom_data
