import streamlit as st
import tempfile
import os
from sectionproperties.analysis import Section
from sectionproperties.pre import Geometry

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
            # Write the uploaded DXF to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_filename = tmp_file.name
            try:
                # Use the updated sectionproperties API
                geom = Geometry.from_dxf(dxf_filepath=tmp_filename)
                geom.create_mesh(mesh_sizes=[2])  # Default mesh size
                sec = Section(geometry=geom)
                
                # Calculate geometric properties
                sec.calculate_geometric_properties()
                
                # Get moment of inertia
                ixx_g, iyy_g, ixy_g = sec.get_ig()
                
                # Calculate section depth from the bounds
                extents = geom.calculate_extents()
                x_min, y_min = extents[0]
                x_max, y_max = extents[1]
                section_depth = y_max - y_min  # in mm
                
                # Calculate section modulus: Z = I / (depth/2)
                Z = iyy_g / (section_depth / 2) if section_depth != 0 else 0
                
                # Let the user give a profile name
                custom_data["name"] = st.text_input("Profile Name", value="DXF Profile")
                custom_data["depth"] = section_depth
                # Convert Iyy from mm^4 to cm^4 (divide by 1e4)
                custom_data["I"] = iyy_g / 1e4  
                # Convert Z from mm^3 to cm^3 (divide by 1e3)
                custom_data["Z"] = Z / 1e3  
                
                st.write("**Calculated Section Properties from DXF:**")
                st.write(f"Section Depth: **{section_depth:.2f} mm**")
                st.write(f"Moment of Inertia (Iyy): **{iyy_g:.2f} mm⁴** (or **{custom_data['I']:.2f} cm⁴**)")
                st.write(f"Section Modulus (Z): **{Z:.2f} mm³** (or **{custom_data['Z']:.2f} cm³**)")
                
                # Optional: Display mesh visualization
                # fig = sec.plot_mesh(materials=False)
                # st.pyplot(fig)
                
            except Exception as e:
                st.error(f"Error processing DXF file: {e}")
                custom_data = {}
            finally:
                os.remove(tmp_filename)
        else:
            # If no file is uploaded, leave custom_data empty
            custom_data = {}
    else:
        custom_data["type"] = "none"
    
    return custom_data

from sectionproperties.pre.library.steel_sections import rectangular_hollow_section

def process_rhs_profile():
    """Process RHS parameters to calculate section properties."""
    custom_data = {"type": "rhs"}
    
    with st.expander("RHS Dimensions", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            d = st.number_input("Depth (mm)", min_value=50.0, max_value=500.0, value=150.0, step=1.0)
        with col2:
            b = st.number_input("Width (mm)", min_value=50.0, max_value=500.0, value=100.0, step=1.0)
        with col3:
            t = st.number_input("Thickness (mm)", min_value=1.0, max_value=25.0, value=5.0, step=0.5)

    try:
        # Create RHS geometry
        geometry = rectangular_hollow_section(
            d=d,
            b=b,
            t=t,
            r_out=2*t,  # Standard outer radius
            n_r=8        # Points on radius
        )
        
        # Create mesh and section
        geometry.create_mesh(mesh_sizes=[1])
        sec = Section(geometry)
        sec.calculate_geometric_properties()
        
        # Calculate section properties
        iyy_g = sec.iyy_g  # mm^4
        cy = sec.cy        # Centroid y-position
        
        # Calculate section modulus (Z = I / y)
        y_extent = max(sec.y_max - cy, cy - sec.y_min)
        zyy = iyy_g / y_extent if y_extent != 0 else 0

        # Populate data (convert to cm units)
        custom_data.update({
            "name": st.text_input("Profile Name", value=f"RHS {d}x{b}x{t}"),
            "depth": d,
            "I": iyy_g / 1e4,  # Convert mm⁴ to cm⁴
            "Z": zyy / 1e3     # Convert mm³ to cm³
        })

        st.write(f"**Calculated Properties:**")
        st.write(f"- Moment of Inertia (Iyy): {custom_data['I']:.1f} cm⁴")
        st.write(f"- Section Modulus (Zyy): {custom_data['Z']:.1f} cm³")

    except Exception as e:
        st.error(f"Invalid dimensions: {e}")
        st.write("Common issues: Wall thickness too large for dimensions")
        custom_data = {"type": "none"}
    
    return custom_data
