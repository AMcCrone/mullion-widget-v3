# custom_profile.py
import tempfile
import os
import streamlit as st
from sectionproperties.pre import Material
from sectionproperties.pre.geometry import Geometry, CompoundGeometry
from sectionproperties.analysis import Section
import matplotlib.pyplot as plt

def get_custom_profile(material):
    """Process DXF with proper 90° rotation for mullion visualization and compound geometry support
    
    Parameters:
    material (str): Material name ('Aluminium' or 'Steel') to use for all sections
    """
    from sectionproperties.pre import Material
    from sectionproperties.pre.geometry import Geometry, CompoundGeometry
    
    # Convert material name to lowercase for dictionary lookup
    material_name = material.lower()
    
    # Define materials
    DEFAULT_MATERIALS = {
        "aluminium": Material(
            name="Aluminium",
            elastic_modulus=70e3,
            poissons_ratio=0.33,
            density=2.7e-6,
            yield_strength=160,
            color="lightgrey",
        ),
        "steel": Material(
            name="Steel",
            elastic_modulus=210e3,
            poissons_ratio=0.3,
            density=7.85e-6,
            yield_strength=355,
            color="grey",
        )
    }
    
    # Create custom data dictionary
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
    
    # Main section upload
    st.subheader("Main Section")
    uploaded_file = st.file_uploader("Upload Main DXF File", type=["dxf"], key="main_dxf")
    
    # Add reinforcement option
    add_reinforcement = st.checkbox("Add Reinforcement Sections", value=False)
    
    # Initialize for reinforcement sections
    reinforcement_files = []
    
    # Show reinforcement upload options if checkbox is selected
    if add_reinforcement:
        st.subheader("Reinforcement Sections")
        # Allow up to 5 reinforcement sections without using expanders
        col1, col2 = st.columns(2)
        
        with col1:
            reinf_file1 = st.file_uploader("Upload Reinforcement #1", type=["dxf"], key="reinf_dxf_1")
            if reinf_file1 is not None:
                reinforcement_files.append(reinf_file1)
                
            reinf_file3 = st.file_uploader("Upload Reinforcement #3", type=["dxf"], key="reinf_dxf_3")
            if reinf_file3 is not None:
                reinforcement_files.append(reinf_file3)
                
            reinf_file5 = st.file_uploader("Upload Reinforcement #5", type=["dxf"], key="reinf_dxf_5")
            if reinf_file5 is not None:
                reinforcement_files.append(reinf_file5)
        
        with col2:
            reinf_file2 = st.file_uploader("Upload Reinforcement #2", type=["dxf"], key="reinf_dxf_2")
            if reinf_file2 is not None:
                reinforcement_files.append(reinf_file2)
                
            reinf_file4 = st.file_uploader("Upload Reinforcement #4", type=["dxf"], key="reinf_dxf_4")
            if reinf_file4 is not None:
                reinforcement_files.append(reinf_file4)
    
    # Analysis settings
    st.subheader("Analysis Settings")
    mesh_size = st.slider("Mesh Size", min_value=0.2, max_value=20.0, value=5.0, 
                        help="Smaller values = finer mesh (slower but more accurate)")
    
    # Only proceed if main file is uploaded
    if uploaded_file is not None:
        try:
            # Create temporary directory to store all files
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Save main DXF to temp file
                main_tmp_path = os.path.join(tmp_dir, "main.dxf")
                with open(main_tmp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # Create main geometry with selected material
                main_geom = Geometry.from_dxf(dxf_filepath=main_tmp_path)
                main_geom.material = DEFAULT_MATERIALS[material_name]
                
                # Initialize compound geometry with main section
                compound_geom = CompoundGeometry([main_geom])
                
                # Add reinforcement sections if any
                for i, reinf_file in enumerate(reinforcement_files):
                    reinf_tmp_path = os.path.join(tmp_dir, f"reinf_{i}.dxf")
                    with open(reinf_tmp_path, 'wb') as f:
                        f.write(reinf_file.getbuffer())
                    
                    reinf_geom = Geometry.from_dxf(dxf_filepath=reinf_tmp_path)
                    # Use the same material for reinforcements as the main material
                    reinf_geom.material = DEFAULT_MATERIALS[material_name]
                    
                    # Add to compound geometry
                    compound_geom += reinf_geom
                
                # Rotate compound geometry 90 degrees clockwise for mullion view
                compound_geom = compound_geom.rotate_section(angle=-90)
                
                # Create mesh with specified size
                compound_geom.create_mesh(mesh_sizes=mesh_size)
                
                # Create section and calculate properties
                sec = Section(geometry=compound_geom)
                sec.calculate_geometric_properties()
                sec.calculate_plastic_properties()
                
                # Get transformed properties using the same material
                # After 90° rotation, what was Iyy is now the major axis (Ixx)
                ixx, iyy, ixy = sec.get_eic(e_ref=DEFAULT_MATERIALS[material_name])
                
                # Get elastic moduli with reference material
                try:
                    # After rotation, zxx values are now major axis
                    zxx_plus, zxx_minus, zyy_plus, zyy_minus = sec.get_ez(e_ref=DEFAULT_MATERIALS[material_name])
                    section_modulus = min(zxx_plus, zxx_minus)  # Conservative value
                except (ValueError, TypeError) as e:
                    st.warning(f"Could not calculate section moduli: {str(e)}")
                    section_modulus = 0
                
                # Update data with converted units (mm⁴ → cm⁴, mm³ → cm³)
                custom_data.update({
                    "I": ixx / 1e4,  # mm⁴ → cm⁴ (major axis after rotation)
                    "Z": section_modulus / 1e3  # mm³ → cm³ (major axis after rotation)
                })
                
                # Create landscape plot
                fig, ax = plt.subplots(figsize=(10, 5))  # Wider aspect ratio
                sec.plot_mesh(ax=ax)
                ax.set_title(f"Finite Element Mesh Plot of {custom_data['name']} Cross Section")
                ax.set_aspect("equal")
                ax.set_xlabel("Height")
                ax.set_ylabel("Width")
                
                st.pyplot(fig)
                
                # Display results
                st.write("**Structural Properties:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Moment of Inertia (Ixx)", f"{custom_data['I']:.2f} cm⁴")
                with col2:
                    st.metric("Section Modulus (Zxx)", f"{custom_data['Z']:.2f} cm³")
                
                # Display material information
                st.write(f"**Material:** {material}")
                st.write(f"**Number of reinforcement sections:** {len(reinforcement_files)}")
                
        except Exception as e:
            st.error(f"Processing Error: {str(e)}")
            st.write("Troubleshooting steps:")
            st.write("1. Verify closed, non-intersecting polylines")
            st.write("2. Ensure Z=0 for all vertices (FLATTEN in CAD)")
            st.write("3. Try different mesh size")
            st.write("4. Check units are millimeters")
            st.write("5. Check exception details:", str(e))
    
    return custom_data
