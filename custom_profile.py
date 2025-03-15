# custom_profile.py
import tempfile
import os
import streamlit as st
from sectionproperties.pre import Geometry
from sectionproperties.analysis import Section
import matplotlib.pyplot as plt

def get_custom_profile():
    """Process DXF file and return section properties with visualization"""
    custom_data = {"type": "dxf"}
    
    st.subheader("DXF Profile Import")
    uploaded_file = st.file_uploader("Upload DXF File", type=["dxf"])
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_filename = tmp_file.name
            
        try:
            # Process DXF
            geom = Geometry.from_dxf(dxf_filepath=tmp_filename)
            geom.create_mesh(mesh_sizes=[2.0])
            sec = Section(geometry=geom)
            sec.calculate_geometric_properties()

            # Get required properties
            ixx = sec.get_ic()[0]  # Major moment of inertia (Ixx)
            zxx_plus, zxx_minus, *_ = sec.get_z()  # Major axis moduli
            zxx = min(zxx_plus, zxx_minus)  # Conservative value
            
            # Calculate depth from geometry bounds
            y_min = sec.section_props.y_min
            y_max = sec.section_props.y_max
            depth = y_max - y_min

            # Create visualization
            fig, ax = plt.subplots(figsize=(6, 4))
            sec.plot_mesh(materials=False, ax=ax)
            ax.set_title("Section Mesh Preview")
            ax.set_aspect("equal")
            
            # Rotate 90 degrees for web display
            ax.invert_xaxis()  # Flip to show conventional engineering orientation
            ax.invert_yaxis()

            # Populate custom data
            custom_data["name"] = st.text_input("Profile Name", value="DXF Profile")
            custom_data["depth"] = depth
            custom_data["I"] = ixx / 1e4  # mm⁴ → cm⁴
            custom_data["Z"] = zxx / 1e3  # mm³ → cm³

            # Display results
            st.pyplot(fig)
            st.write("**Calculated Section Properties:**")
            st.metric("Section Depth", f"{depth:.1f} mm")
            st.metric("Moment of Inertia (Ixx)", f"{custom_data['I']:.1f} cm⁴")
            st.metric("Section Modulus (Zxx)", f"{custom_data['Z']:.1f} cm³")

        except Exception as e:
            st.error(f"DXF Processing Error: {str(e)}")
            st.write("Common issues:")
            st.write("- Open or self-intersecting geometry")
            st.write("- Non-planar elements (Z-values present)")
            st.write("- Complex/non-manifold topology")
            custom_data = {}
            
            # Debugging help
            with st.expander("Technical Details"):
                st.write("Temporary file path:", tmp_filename)
                if 'sec' in locals():
                    st.write("Available section methods:", dir(sec))
                
        finally:
            os.remove(tmp_filename)
            
    return custom_data
