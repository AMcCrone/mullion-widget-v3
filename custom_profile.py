import streamlit as st
import tempfile
import os
from sectionproperties.sections import SectionFromDxf

def get_custom_profile():
    st.subheader("Custom Profile Settings")
    custom_option = st.selectbox("Select Custom Profile Option", ["None", "Manual Input", "Import DXF"])
    custom_data = {}
    
    if custom_option == "Manual Input":
        custom_data["type"] = "manual"
        custom_data["name"] = st.text_input("Profile Name", value="Custom Profile")
        custom_data["depth"] = st.number_input("Section Depth (mm)", min_value=50.0, max_value=500.0, value=150.0, step=1.0)
        custom_data["I"] = st.number_input("Moment of Inertia (cm⁴)", min_value=1.0, max_value=10000.0, value=500.0, step=1.0)
        custom_data["Z"] = st.number_input("Section Modulus (cm³)", min_value=1.0, max_value=1000.0, value=50.0, step=1.0)
    
    elif custom_option == "Import DXF":
        custom_data["type"] = "dxf"
        uploaded_file = st.file_uploader("Upload DXF File", type=["dxf"])
        if uploaded_file is not None:
            # Write the uploaded DXF to a temporary file.
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_filename = tmp_file.name
            try:
                # Use sectionproperties to import and mesh the DXF geometry.
                section = SectionFromDxf(tmp_filename, scale=1.0)
                section.create_meshed_geometry()
                mesh = section.create_mesh(mesh_sizes=1.0)  # Default mesh size
                section_properties = mesh.calculate_section_properties()
                # Access properties like:
                Iyy = section_properties.Iyy
                
                # Calculate section depth from the bounding box.
                # The bounding box returns [x_min, y_min, x_max, y_max]
                bounds = section.get_bounding_box()
                section_depth = bounds[3] - bounds[1]  # y_max - y_min in mm
                
                # Calculate section modulus: Z = Iyy / (depth/2).
                Z = Iyy / (section_depth / 2) if section_depth != 0 else 0
                
                # Let the user give a profile name.
                custom_data["name"] = st.text_input("Profile Name", value="DXF Profile")
                custom_data["depth"] = section_depth
                # Convert Iyy from mm^4 to cm^4 (divide by 1e4)
                custom_data["I"] = Iyy / 1e4  
                # Convert Z from mm^3 to cm^3 (divide by 1e3)
                custom_data["Z"] = Z / 1e3  
                
                st.write("**Calculated Section Properties from DXF:**")
                st.write(f"Section Depth: **{section_depth:.2f} mm**")
                st.write(f"Moment of Inertia (Iyy): **{Iyy:.2f} mm⁴** (or **{custom_data['I']:.2f} cm⁴**)")
                st.write(f"Section Modulus (Z): **{Z:.2f} mm³** (or **{custom_data['Z']:.2f} cm³**)")
            except Exception as e:
                st.error(f"Error processing DXF file: {e}")
                custom_data = {}
            finally:
                os.remove(tmp_filename)
        else:
            # If no file is uploaded, leave custom_data empty.
            custom_data = {}
    else:
        custom_data["type"] = "none"
    
    return custom_data
