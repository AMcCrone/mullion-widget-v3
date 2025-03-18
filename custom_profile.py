# custom_profile.py
import tempfile
import os
import streamlit as st
from sectionproperties.pre import Material
from sectionproperties.pre.geometry import Geometry, CompoundGeometry
from sectionproperties.analysis import Section
import matplotlib.pyplot as plt


# def get_custom_profile():
#     """Process DXF with proper 90° rotation for mullion visualization"""
#     custom_data = {
#         "type": "dxf",
#         "name": "DXF Profile",
#         "depth": 150.0,
#         "Z": 1.0,
#         "I": 1.0
#     }

#     # Input row at top
#     col1, col2 = st.columns(2)
#     with col1:
#         custom_data["name"] = st.text_input("Profile Name", value="DXF Profile")
#     with col2:
#         custom_data["depth"] = st.number_input("Section Depth (mm)", 
#                                              min_value=50.0, max_value=500.0, 
#                                              value=150.0, step=1.0)

#     uploaded_file = st.file_uploader("Upload DXF File", type=["dxf"])

#     if uploaded_file is not None:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
#             tmp_file.write(uploaded_file.getbuffer())
#             tmp_filename = tmp_file.name

#         try:
#             # Load and rotate geometry
#             geom = Geometry.from_dxf(dxf_filepath=tmp_filename)
#             geom = geom.rotate_section(angle=-90)  # Clockwise rotation for mullion view
#             geom.create_mesh(mesh_sizes=[5.0])
#             sec = Section(geometry=geom)
#             sec.calculate_geometric_properties()

#             # Get properties for rotated section (-90° rotation swaps axes)
#             iyy = sec.get_ic()[1]  # This is now the MAJOR axis moment of inertia

#             # Get MAJOR axis moduli (first two values after rotation)
#             zxx_plus, zxx_minus, zyy_plus, zyy_minus = sec.get_z()  # First 2 values are now major axis
#             zyy = min(zyy_plus, zyy_minus)  # Conservative value

#             # Update data with converted units
#             custom_data.update({
#                 "I": iyy / 1e4,  # mm⁴ → cm⁴ (major axis)
#                 "Z": zyy / 1e3    # mm³ → cm³ (major axis)
#             })
#             # Create landscape plot
#             fig, ax = plt.subplots(figsize=(10, 5))  # Wider aspect ratio
#             sec.plot_mesh(materials=False, ax=ax)
#             ax.set_title(f"Finite Element Mesh Plot of {custom_data['name']} Cross Section")
#             ax.set_aspect("equal")
#             ax.set_xlabel("Height")
#             ax.set_ylabel("Width")

#             st.pyplot(fig)
#             # Display results
#             st.write("Structural Properties:")
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.metric("Moment of Inertia (Ixx)", f"{custom_data['I']:.2f} cm⁴")
#             with col2:
#                 st.metric("Section Modulus (Zxx)", f"{custom_data['Z']:.2f} cm³")
#         except Exception as e:
#             st.error(f"Processing Error: {str(e)}")
#             st.write("Ensure your DXF:")
#             st.write("- Contains closed polylines")
#             st.write("- Has units in millimeters")
#             st.write("- No 3D elements (Z=0 for all points)")

#         finally:
#             os.remove(tmp_filename)

#     return custom_data

def get_custom_profile():
    """Process DXF without rotation for calculation but rotate for mullion visualization"""
    from sectionproperties.pre import Material
    from sectionproperties.pre.geometry import Geometry, CompoundGeometry
    
    custom_data = {
        "type": "dxf",
        "name": "DXF Profile",
        "depth": 150.0,
        "Z": 1.0,
        "I": 1.0
    }
    
    # Define default materials
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
    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_file = st.file_uploader("Upload Main DXF File", type=["dxf"], key="main_dxf")
    with col2:
        main_material = st.selectbox(
            "Material",
            options=list(DEFAULT_MATERIALS.keys()),
            index=0,
            key="main_material"
        )
    
    # Add reinforcement option
    add_reinforcement = st.checkbox("Add Reinforcement Sections", value=False)
    
    # Initialize for reinforcement sections
    reinforcement_files = []
    reinforcement_materials = []
    
    # Show reinforcement upload options if checkbox is selected
    if add_reinforcement:
        st.subheader("Reinforcement Sections")
        
        # Use headings and horizontal rules to separate sections
        for i in range(5):
            st.markdown(f"#### Reinforcement #{i+1}")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                reinf_file = st.file_uploader(f"Upload Reinforcement DXF #{i+1}", 
                                           type=["dxf"], 
                                           key=f"reinf_dxf_{i}")
            with col2:
                reinf_material = st.selectbox(
                    "Material",
                    options=list(DEFAULT_MATERIALS.keys()),
                    index=1 if "steel" in DEFAULT_MATERIALS else 0,
                    key=f"reinf_material_{i}"
                )
            
            if reinf_file is not None:
                reinforcement_files.append(reinf_file)
                reinforcement_materials.append(reinf_material)
            
            # Add a separator between reinforcement sections
            if i < 4:  # Don't show after the last one
                st.markdown("---")
    
    # Reference material for transformed properties (only shown if reinforcement is added)
    if add_reinforcement:
        st.subheader("Analysis Settings")
        col1, col2 = st.columns(2)
        with col1:
            ref_material = st.selectbox(
                "Reference Material for Transformed Properties",
                options=list(DEFAULT_MATERIALS.keys()),
                index=0
            )
        with col2:
            mesh_size = st.slider("Mesh Size", min_value=0.2, max_value=20.0, value=5.0, 
                                help="Smaller values = finer mesh (slower but more accurate)")
    else:
        # Still need mesh size for single section
        st.subheader("Analysis Settings")
        mesh_size = st.slider("Mesh Size", min_value=0.2, max_value=20.0, value=5.0, 
                            help="Smaller values = finer mesh (slower but more accurate)")
        # Default reference material (not used but needed for variable scope)
        ref_material = main_material
    
    # Only proceed if main file is uploaded
    if uploaded_file is not None:
        try:
            # Create temporary directory to store all files
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Save main DXF to temp file
                main_tmp_path = os.path.join(tmp_dir, "main.dxf")
                with open(main_tmp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # Handle different geometry types based on reinforcement flag
                if add_reinforcement and reinforcement_files:
                    # === COMPOUND SECTION WITH REINFORCEMENT ===
                    # Create main geometry with selected material
                    main_geom = Geometry.from_dxf(dxf_filepath=main_tmp_path)
                    main_geom.material = DEFAULT_MATERIALS[main_material]
                    
                    # Initialize compound geometry with main section
                    compound_geom = CompoundGeometry([main_geom])
                    
                    # Add reinforcement sections if any
                    for i, (reinf_file, reinf_mat) in enumerate(zip(reinforcement_files, reinforcement_materials)):
                        reinf_tmp_path = os.path.join(tmp_dir, f"reinf_{i}.dxf")
                        with open(reinf_tmp_path, 'wb') as f:
                            f.write(reinf_file.getbuffer())
                        
                        reinf_geom = Geometry.from_dxf(dxf_filepath=reinf_tmp_path)
                        reinf_geom.material = DEFAULT_MATERIALS[reinf_mat]
                        
                        # Add to compound geometry
                        compound_geom += reinf_geom
                    
                    # Get reference material object
                    ref_material_obj = DEFAULT_MATERIALS[ref_material]
                    
                    # No rotation for calculation - use original geometry
                    # Create mesh with specified size
                    compound_geom.create_mesh(mesh_sizes=mesh_size)
                    
                    # Create section and calculate properties
                    sec = Section(geometry=compound_geom)
                    sec.calculate_geometric_properties()
                    sec.calculate_plastic_properties()
                    
                    # === COMPOUND SECTION PROPERTIES ===
                    # Get transformed properties using reference material's elastic modulus
                    # Using original orientation - Iyy is the major axis
                    ixx, iyy, ixy = sec.get_eic(e_ref=ref_material_obj)
                    
                    # Get elastic moduli with reference material
                    try:
                        # In original orientation - zyy values are the major axis
                        zxx_plus, zxx_minus, zyy_plus, zyy_minus = sec.get_ez(e_ref=ref_material_obj)
                        section_modulus = min(zyy_plus, zyy_minus)  # Conservative value for MAJOR axis
                    except (ValueError, TypeError) as e:
                        st.warning(f"Could not calculate section moduli: {str(e)}")
                        section_modulus = 0
                    
                    # Display material information
                    material_info = f"Main: {main_material.capitalize()}"
                    if reinforcement_files:
                        material_info += f", Reinforcements: {', '.join(m.capitalize() for m in set(reinforcement_materials))}"
                    st.write(f"Reference Material: {ref_material.capitalize()}")
                    st.write(material_info)
                    
                else:
                    # === SINGLE SECTION WITHOUT REINFORCEMENT ===
                    # Load geometry WITHOUT rotation
                    geom = Geometry.from_dxf(dxf_filepath=main_tmp_path)
                    geom.create_mesh(mesh_sizes=mesh_size)
                    sec = Section(geometry=geom)
                    sec.calculate_geometric_properties()
                    
                    # === STANDARD SECTION PROPERTIES ===
                    # Get properties for original orientation
                    ixx, iyy, ixy = sec.get_ic()  # Standard moment of inertia calculation
                    
                    # Get standard section moduli
                    zxx_plus, zxx_minus, zyy_plus, zyy_minus = sec.get_z()
                    section_modulus = min(zyy_plus, zyy_minus)  # Conservative value for MAJOR axis
                
                # Update data with converted units (mm⁴ → cm⁴, mm³ → cm³)
                # Use iyy for the major axis (vertical axis in original orientation)
                custom_data.update({
                    "I": iyy / 1e4,  # mm⁴ → cm⁴ (major axis)
                    "Z": section_modulus / 1e3  # mm³ → cm³ (major axis)
                })
                
                # Create landscape plot with rotation ONLY for visualization
                fig, ax = plt.subplots(figsize=(10, 5))  # Wider aspect ratio
                
                # Create a copy of the geometry for plotting purposes only
                if add_reinforcement and reinforcement_files:
                    plot_geom = compound_geom.rotate_section(angle=-90)
                else:
                    plot_geom = geom.rotate_section(angle=-90)
                
                # Create a new section with the rotated geometry just for plotting
                plot_sec = Section(geometry=plot_geom)
                plot_sec.calculate_geometric_properties()
                
                # Plot the rotated geometry
                plot_sec.plot_mesh(ax=ax)
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
                
        except Exception as e:
            st.error(f"Processing Error: {str(e)}")
            st.write("Troubleshooting steps:")
            st.write("1. Verify closed, non-intersecting polylines")
            st.write("2. Ensure Z=0 for all vertices (FLATTEN in CAD)")
            st.write("3. Try different mesh size")
            st.write("4. Check units are millimeters")
            st.write("5. Check exception details:", str(e))
    
    return custom_data
