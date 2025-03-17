import numpy as np
import pandas as pd
import plotly.graph_objects as go
from config import TT_LightBlue, TT_DarkBlue, TT_MidBlue, TT_Grey, TT_Purple, material_props, BARRIER_LENGTH

def generate_plots(
    wind_pressure, bay_width, mullion_length, selected_barrier_load,
    ULS_case, SLS_case, df_selected, plot_material, selected_suppliers,
    use_custom_section=False, custom_section_data=None, view_3d_option="Isometric: Overview"
):
    # Convert wind pressure from kPa to N/mm²
    p = wind_pressure * 0.001
    L = mullion_length
    bay = bay_width
    w = p * bay
    M_WL = (w * L**2) / 8
    M_BL = ((selected_barrier_load * bay) * BARRIER_LENGTH) / 2

    if ULS_case.startswith("ULS 1"):
        M_ULS = 1.5 * M_WL + 0.75 * M_BL
    elif ULS_case.startswith("ULS 2"):
        M_ULS = 0.75 * M_WL + 1.5 * M_BL
    elif ULS_case.startswith("ULS 3"):
        M_ULS = 1.5 * M_WL
    elif ULS_case.startswith("ULS 4"):
        M_ULS = 1.5 * M_BL
    else:
        M_ULS = 0

    fy = material_props[plot_material]["fy"]
    Z_req = M_ULS / fy          # in mm³
    Z_req_cm3 = Z_req / 1000     # in cm³

    # Deflection limit based on mullion length
    if L <= 3000:
        defl_limit = L / 200
    elif L < 7500:
        defl_limit = 5 + L / 300
    else:
        defl_limit = L / 250

    # Filter the dataframe based on material and selected suppliers
    df_mat = df_selected[(df_selected["Material"] == plot_material) & 
                         (df_selected["Supplier"].isin(selected_suppliers))]
    if df_mat.empty:
        raise ValueError("No sections selected.")

    depths = df_mat["Depth"].values
    Wyy_vals = df_mat["Wyy"].values
    Iyy_vals = df_mat["Iyy"].values
    profiles = df_mat["Profile Name"].values
    reinf = df_mat["Reinf"].values
    supps = df_mat["Supplier"].values
    available_cm3 = Wyy_vals / 1000  # Convert to cm³

    # Add custom section if enabled
    if use_custom_section and custom_section_data:
        depths = np.append(depths, custom_section_data["depth"])
        # Use custom_section_data["Z"] instead of "modulus"
        Wyy_vals = np.append(Wyy_vals, custom_section_data["Z"] * 1000)  # cm³ -> mm³
        Iyy_vals = np.append(Iyy_vals, custom_section_data["I"] * 10000)   # cm⁴ -> mm⁴
        profiles = np.append(profiles, custom_section_data["name"])
        # Set a default reinforcement flag (e.g., True) and supplier "Custom"
        reinf = np.append(reinf, True)
        supps = np.append(supps, "Custom")
        available_cm3 = np.append(available_cm3, custom_section_data["Z"])

    # ----- ULS Plot -----
    uls_passed = available_cm3 >= Z_req_cm3
    uls_colors = []
    for i, passed in enumerate(uls_passed):
        if i == len(uls_passed) - 1 and use_custom_section:
            uls_colors.append(TT_Purple if passed else 'darkred')
        else:
            uls_colors.append('seagreen' if passed else 'darkred')
    uls_symbols = ['square' if r else 'circle' for r in reinf]
    uls_hover = [
        f"{profiles[i]}<br>Supplier: {supps[i]}<br>Depth: {depths[i]} mm<br>Z: {available_cm3[i]:.2f} cm³<br>ULS: {'Pass' if uls_passed[i] else 'Fail'}"
        for i in range(len(depths))
    ]
    x_min = np.min(depths) * 0.95
    x_max = np.max(depths) * 1.05
    uls_ymax = 4 * Z_req_cm3

    uls_fig = go.Figure()
    uls_fig.add_shape(
        type="rect",
        x0=x_min, x1=x_max,
        y0=Z_req_cm3, y1=uls_ymax,
        fillcolor=TT_LightBlue, opacity=0.2, line_width=0
    )
    uls_fig.add_shape(
        type="rect",
        x0=x_min, x1=x_max,
        y0=0, y1=Z_req_cm3,
        fillcolor=TT_MidBlue, opacity=0.2, line_width=0
    )
    uls_fig.add_trace(go.Scatter(
        x=depths,
        y=available_cm3,
        mode='markers',
        marker=dict(color=uls_colors, symbol=uls_symbols, size=15, line=dict(color='black', width=1)),
        text=uls_hover,
        hoverinfo='text'
    ))
    uls_fig.update_layout(
        title=(f"{plot_material} ULS Design ({ULS_case})<br>"
               f"WL: {wind_pressure:.2f} kPa, Bay: {bay} mm, L: {L} mm, BL: {selected_barrier_load:.2f} kN/m<br>"
               f"Req. Z: {Z_req_cm3:.1f} cm³"),
        xaxis_title="Section Depth (mm)",
        yaxis_title="Section Modulus (cm³)",
        xaxis=dict(range=[x_min, x_max]),
        yaxis=dict(range=[0, uls_ymax]),
        height=650
    )

    # ----- SLS Plot -----
    E = material_props[plot_material]["E"]
    defl_values = []
    sls_hover = []
    
    # Calculate the required moment of inertia based on the deflection limit
    if SLS_case.startswith("SLS 1"):
        # For wind load case
        I_req = (5 * w * L**4) / (384 * E * defl_limit)
    else:
        # For barrier load case
        F_BL = selected_barrier_load * bay
        I_req = ((F_BL * BARRIER_LENGTH) / (12 * E * defl_limit)) * (0.75 * L**2 - BARRIER_LENGTH**2)
    
    # Convert I_req to cm⁴ for display
    I_req_cm4 = I_req / 10000  # Convert from mm⁴ to cm⁴
    
    for i in range(len(depths)):
        d_wl = (5 * w * L**4) / (384 * E * Iyy_vals[i])
        F_BL = selected_barrier_load * bay
        d_bl = ((F_BL * BARRIER_LENGTH) / (12 * E * Iyy_vals[i])) * (0.75 * L**2 - BARRIER_LENGTH**2)
        defl_total = d_wl if SLS_case.startswith("SLS 1") else d_bl
        defl_values.append(defl_total)
        sls_hover.append(
            f"{profiles[i]}<br>Supplier: {supps[i]}<br>Depth: {depths[i]} mm<br>Defl: {defl_total:.2f} mm<br>"
            f"SLS: {'Pass' if defl_total <= defl_limit else 'Fail'}"
        )
    sls_ymax = 1.33 * defl_limit
    valid = np.where(uls_passed)[0]
    sls_colors = []
    for i in valid:
        if i == len(uls_passed) - 1 and use_custom_section:
            sls_colors.append(TT_Purple if defl_values[i] <= defl_limit else 'darkred')
        else:
            sls_colors.append('seagreen' if defl_values[i] <= defl_limit else 'darkred')
    sls_fig = go.Figure()
    sls_fig.add_shape(
        type="rect",
        x0=x_min, x1=x_max,
        y0=0, y1=defl_limit,
        fillcolor=TT_LightBlue, opacity=0.2, line_width=0
    )
    sls_fig.add_shape(
        type="rect",
        x0=x_min, x1=x_max,
        y0=defl_limit, y1=sls_ymax,
        fillcolor=TT_MidBlue, opacity=0.2, line_width=0
    )
    sls_fig.add_trace(go.Scatter(
        x=depths[valid],
        y=np.array(defl_values)[valid],
        mode='markers',
        marker=dict(
            color=sls_colors,
            symbol=[uls_symbols[i] for i in valid],
            size=15,
            line=dict(color='black', width=1)
        ),
        text=np.array(sls_hover)[valid],
        hoverinfo='text'
    ))
        sls_fig.update_layout(
        title={
            'text': (f"{plot_material} SLS Design ({SLS_case})<br>"
                    f"WL: {wind_pressure:.2f} kPa, Bay: {bay} mm, L: {L} mm, BL: {selected_barrier_load:.2f} kN/m<br>"
                    f"Defl Limit: {defl_limit:.1f} mm, Req. I: {I_req_cm4:.1f} cm⁴"),
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Section Depth (mm)",
        yaxis_title="Deflection (mm)",
        xaxis=dict(range=[x_min, x_max]),
        yaxis=dict(range=[0, sls_ymax]),
        height=650
    )

    # ----- 3D Utilisation Plot -----
    uls_util, sls_util, depths_3d = [], [], []
    safe_suppliers, safe_profiles = [], []
    for i in range(len(depths)):
        if available_cm3[i] == 0:
            continue
        ratio_uls = Z_req_cm3 / available_cm3[i]
        ratio_sls = defl_values[i] / defl_limit if defl_limit != 0 else np.inf
        if ratio_uls <= 1 and ratio_sls <= 1:
            uls_util.append(ratio_uls)
            sls_util.append(ratio_sls)
            depths_3d.append(depths[i])
            safe_suppliers.append(supps[i])
            safe_profiles.append(profiles[i])
    colors_3d = []
    for i in range(len(safe_suppliers)):
        if safe_suppliers[i] == "Custom" and use_custom_section:
            colors_3d.append(TT_Purple)
        else:
            colors_3d.append('#1f77b4')
    if len(uls_util) > 0:
        d_arr = np.sqrt(np.array(uls_util)**2 + np.array(sls_util)**2)
        sizes = 10 + (d_arr / np.sqrt(2)) * 20
    else:
        sizes = 30

    recommended_text = "No suitable profile - choose a custom one!"
    if len(depths_3d) > 0:
        min_depth_val = min(depths_3d)
        indices = [i for i, d in enumerate(depths_3d) if d == min_depth_val]
        if indices:
            d_array = np.sqrt(np.array(uls_util)**2 + np.array(sls_util)**2)
            rec_index = indices[0] if len(indices) == 1 else indices[np.argmax(d_array[indices])]
            recommended_text = f"Recommended Profile: {safe_suppliers[rec_index]}: {safe_profiles[rec_index]}"

    util_fig = go.Figure(data=[go.Scatter3d(
        x=uls_util,
        y=sls_util,
        z=depths_3d,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors_3d if use_custom_section else depths_3d,
            colorscale='Emrld' if not use_custom_section else None,
            colorbar=dict(title="Depth (mm)") if not use_custom_section else None
        ),
        text=[f"{safe_suppliers[i]}: {safe_profiles[i]}<br>Depth: {depths_3d[i]} mm<br>"
              f"ULS Util: {uls_util[i]:.2f}<br>SLS Util: {sls_util[i]:.2f}"
              for i in range(len(depths_3d))],
        hoverinfo='text'
    )])
    util_fig.update_layout(
        height=650,
        title=f"3D Utilisation Plot<br>{recommended_text}",
        scene=dict(
            xaxis=dict(range=[0.0, 1.0]),
            yaxis=dict(range=[0.0, 1.0]),
            zaxis=dict(range=[50, 1.05 * np.max(depths)]),
            xaxis_title="ULS Utilisation",
            yaxis_title="SLS Utilisation",
            zaxis_title="Section Depth (mm)"
        )
    )
    if view_3d_option == "Isometric: Overview":
        camera = dict(eye=dict(x=1.25, y=1.25, z=1.25))
    elif view_3d_option == "XY Plane: Utilisation":
        camera = dict(eye=dict(x=0, y=0, z=2.5), projection=dict(type='orthographic'))
    elif view_3d_option == "XZ Plane: Section Depth":
        camera = dict(eye=dict(x=0, y=2.5, z=0), projection=dict(type='orthographic'))
    util_fig.update_layout(scene_camera=camera)
    
    return uls_fig, sls_fig, util_fig, defl_values, Z_req_cm3, defl_limit


def generate_section_database(
    df_selected, plot_material, selected_suppliers, custom_section_data, use_custom_section,
    wind_pressure, bay_width, mullion_length, selected_barrier_load, SLS_case, defl_limit, Z_req_cm3
):
    from config import BARRIER_LENGTH, material_props, TT_LightBlue, TT_MidBlue, TT_Orange
    import pandas as pd
    import numpy as np
    
    df_mat = df_selected[(df_selected["Material"] == plot_material) &
                         (df_selected["Supplier"].isin(selected_suppliers))].copy()
    df_mat.reset_index(drop=True, inplace=True)

    if use_custom_section and custom_section_data:
        custom_row = pd.DataFrame({
            "Supplier": ["Custom"],
            "Profile Name": [custom_section_data["name"]],
            "Material": [plot_material],
            # Default reinforcement value since it's not used anymore
            "Reinf": [True],
            "Depth": [custom_section_data["depth"]],
            "Iyy": [custom_section_data["I"] * 10000],   # cm⁴ to mm⁴
            "Wyy": [custom_section_data["Z"] * 1000]       # cm³ to mm³
        })
        df_mat = pd.concat([df_mat, custom_row], ignore_index=True)
    
    # Calculate ULS utilisation as the ratio of required section modulus to available modulus.
    df_mat["ULS Utilisation"] = Z_req_cm3 / (df_mat["Wyy"] / 1000)

    # Recompute deflection for each row
    E = material_props[plot_material]["E"]
    defl_values_table = []
    for i, row in df_mat.iterrows():
        Iyy_val = row["Iyy"]
        d_wl = (5 * wind_pressure * 0.001 * bay_width * mullion_length**4) / (384 * E * Iyy_val)
        F_BL = selected_barrier_load * bay_width
        d_bl = ((F_BL * BARRIER_LENGTH) / (12 * E * Iyy_val)) * (0.75 * mullion_length**2 - BARRIER_LENGTH**2)
        defl_total = d_wl if SLS_case.startswith("SLS 1") else d_bl
        defl_values_table.append(defl_total)
    df_mat["SLS Utilisation"] = np.array(defl_values_table) / defl_limit

    # Create a sorting metric and format the dataframe for display
    df_mat["Max Utilisation"] = df_mat[["ULS Utilisation", "SLS Utilisation"]].max(axis=1)
    
    # Separate passing and failing sections
    df_pass = df_mat[df_mat["Max Utilisation"] <= 1.0].copy()
    df_fail = df_mat[df_mat["Max Utilisation"] > 1.0].copy()
    
    # Sort passing sections by SLS Utilisation (highest to lowest)
    df_pass = df_pass.sort_values(by="SLS Utilisation", ascending=False)
    
    # Sort failing sections by Max Utilisation (lowest to highest)
    df_fail = df_fail.sort_values(by="Max Utilisation", ascending=True)
    
    # Concatenate passing and failing dataframes
    df_sorted = pd.concat([df_pass, df_fail], ignore_index=True)
    
    # Create display dataframe with formatted columns
    df_display = df_sorted.copy()
    df_display["Section Modulus (cm³)"] = (df_display["Wyy"] / 1000).round(2)
    df_display["I (cm⁴)"] = (df_display["Iyy"] / 10000).round(2)
    df_display["ULS Util. (%)"] = (df_display["ULS Utilisation"] * 100).round(1)
    df_display["SLS Util. (%)"] = (df_display["SLS Utilisation"] * 100).round(1)
    
    display_columns = ["Supplier", "Profile Name", "Depth", "Section Modulus (cm³)", "I (cm⁴)", 
                       "ULS Util. (%)", "SLS Util. (%)"]
    df_display = df_display[display_columns]
    
    # Create a styled dataframe for display
    def style_dataframe(dataframe):
        # Count passing sections for gradient calculation
        pass_count = len(df_pass)
        
        # Define the style function for each row
        def row_style(row):
            styles = []
            is_custom = row["Supplier"] == "Custom"
            is_passing = row.name < pass_count
            
            # Custom section styling
            if is_custom:
                bg_color = TT_DarkBlue if is_passing else TT_Orange
                styles = [f'background-color: {bg_color}; color: white'] * len(row)
            
            # Non-custom sections
            else:
                if is_passing:
                    # Gradient with consistent opacity
                    light_blue = tuple(int(x) for x in TT_LightBlue.strip("rgb()").split(","))
                    mid_blue = tuple(int(x) for x in TT_MidBlue.strip("rgb()").split(","))
                    
                    ratio = row.name / max(1, pass_count - 1)
                    r = int(light_blue[0] + (mid_blue[0] - light_blue[0]) * ratio)
                    g = int(light_blue[1] + (mid_blue[1] - light_blue[1]) * ratio)
                    b = int(light_blue[2] + (mid_blue[2] - light_blue[2]) * ratio)
                    
                    styles = [f'background-color: rgba({r},{g},{b},0.2)'] * len(row)
                else:
                    # Failing non-custom: consistent styling
                    # Use rgba for background with 0.2 opacity
                    orange_rgba = "rgba(211,69,29,0.2)"
                    styles = [f'background-color: {orange_rgba}; color: {TT_Orange}'] * len(row)
            
            return styles
        
        return dataframe.style.apply(row_style, axis=1)
    
    # Apply styling to the dataframe
    styled_df = style_dataframe(df_display)
    
    return styled_df
