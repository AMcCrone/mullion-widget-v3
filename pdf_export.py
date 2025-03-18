import io
import pandas as pd
import plotly.io as pio
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib.pyplot as plt
import base64
from PIL import Image as PILImage

def get_pdf_bytes(fig):
    """Convert a plotly figure to PDF bytes"""
    img_bytes = fig.to_image(format="png", width=1000, height=600)
    return io.BytesIO(img_bytes)

def create_pdf_report(
    wind_pressure, bay_width, mullion_length, selected_barrier_load,
    ULS_case, SLS_case, plot_material, Z_req_cm3, I_req_cm4, defl_limit,
    selected_df, selected_indices=None, uls_df=None, sls_df=None
):
    """
    Create a PDF report with the design inputs, requirements, load cases, and selected sections
    
    Parameters:
    -----------
    wind_pressure : float
        The wind pressure in kPa
    bay_width : float
        Bay width in mm
    mullion_length : float
        Mullion length in mm
    selected_barrier_load : float
        Barrier load in kN/m
    ULS_case : str
        The ULS load case used
    SLS_case : str
        The SLS load case used
    plot_material : str
        Material used (Aluminium or Steel)
    Z_req_cm3 : float
        Required section modulus in cm³
    I_req_cm4 : float
        Required moment of inertia in cm⁴
    defl_limit : float
        Deflection limit in mm
    selected_df : pandas.DataFrame
        Dataframe containing section data
    selected_indices : list, optional
        List of indices for selected sections from the dataframe
    uls_df : pandas.DataFrame, optional
        DataFrame with ULS load case information
    sls_df : pandas.DataFrame, optional
        DataFrame with SLS load case information
        
    Returns:
    --------
    BytesIO
        PDF document as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=20*mm, 
        leftMargin=20*mm, 
        topMargin=20*mm, 
        bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    # Build the PDF content
    elements = []
    
    # Title
    elements.append(Paragraph("Mullion Design Results Report", title_style))
    elements.append(Spacer(1, 10*mm))
    
    # Input parameters table
    elements.append(Paragraph("Design Input Parameters", heading_style))
    
    data = [
        ["Parameter", "Value"],
        ["Material", plot_material],
        ["Wind Pressure", f"{wind_pressure:.2f} kPa"],
        ["Bay Width", f"{bay_width} mm"],
        ["Mullion Length", f"{mullion_length} mm"],
        ["Barrier Load", f"{selected_barrier_load:.2f} kN/m"],
        ["Current ULS Load Case", ULS_case],
        ["Current SLS Load Case", SLS_case]
    ]
    
    t = Table(data, colWidths=[doc.width/2.5, doc.width/2.5])
    t.setStyle(table_style)
    elements.append(t)
    elements.append(Spacer(1, 10*mm))
    
    # ULS Load cases table 
    if uls_df is not None:
        elements.append(Paragraph("Ultimate Limit State (ULS) Load Cases", heading_style))
        
        # Prepare ULS table data
        uls_table_data = [uls_df.columns.tolist()]
        for _, row in uls_df.iterrows():
            uls_table_data.append(row.tolist())
        
        uls_table = Table(uls_table_data, colWidths=[doc.width/4, doc.width/4, doc.width/4])
        uls_table.setStyle(table_style)
        elements.append(uls_table)
        elements.append(Spacer(1, 10*mm))
    
    # SLS Load cases table
    if sls_df is not None:
        elements.append(Paragraph("Serviceability Limit State (SLS) Load Cases", heading_style))
        
        # Prepare SLS table data
        sls_table_data = [sls_df.columns.tolist()]
        for _, row in sls_df.iterrows():
            sls_table_data.append(row.tolist())
        
        sls_table = Table(sls_table_data, colWidths=[doc.width/4, doc.width/4, doc.width/4])
        sls_table.setStyle(table_style)
        elements.append(sls_table)
        elements.append(Spacer(1, 10*mm))
    
    # Design requirements table
    elements.append(Paragraph("Design Requirements", heading_style))
    
    data = [
        ["Parameter", "Value"],
        ["Required Section Modulus", f"{Z_req_cm3:.2f} cm³"],
        ["Required Moment of Inertia", f"{I_req_cm4:.2f} cm⁴"],
        ["Deflection Limit", f"{defl_limit:.2f} mm"]
    ]
    
    t = Table(data, colWidths=[doc.width/2.5, doc.width/2.5])
    t.setStyle(table_style)
    elements.append(t)
    elements.append(Spacer(1, 10*mm))
    
    # Selected sections
    elements.append(Paragraph("Selected Sections", heading_style))
    
    if selected_indices is None or len(selected_indices) == 0:
        # If no specific sections are selected, use the top passing sections
        df_passing = selected_df[
            (selected_df["ULS Util. (%)"] <= 100) & 
            (selected_df["SLS Util. (%)"] <= 100)
        ]
        
        if len(df_passing) > 0:
            # Take up to 5 passing sections with the highest utilization
            df_to_show = df_passing.sort_values(by="SLS Util. (%)", ascending=False).head(5)
        else:
            # If no passing sections, take 5 with lowest maximum utilization
            df_to_show = selected_df.sort_values(
                by=["ULS Util. (%)", "SLS Util. (%)"]
            ).head(5)
    else:
        # Use specific selected indices
        df_to_show = selected_df.iloc[selected_indices]
    
    # Create table header
    headers = ["Supplier", "Profile Name", "Depth (mm)", "Z (cm³)", 
               "I (cm⁴)", "ULS Util. (%)", "SLS Util. (%)"]
    
    data = [headers]
    
    # Add rows for each selected section
    for _, row in df_to_show.iterrows():
        data.append([
            row["Supplier"],
            row["Profile Name"],
            f"{row['Depth']:.1f}",
            f"{row['Z (cm³)']:.2f}",
            f"{row['I (cm⁴)']:.2f}",
            f"{row['ULS Util. (%)']:.1f}",
            f"{row['SLS Util. (%)']:.1f}"
        ])
    
    # Alternate row colors
    for i in range(len(df_to_show)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i+1), (-1, i+1), colors.lightgrey)
    
    # Create the table
    col_widths = [doc.width/8, doc.width/6, doc.width/10, doc.width/7, doc.width/7, doc.width/8, doc.width/8]
    t = Table(data, colWidths=col_widths)
    t.setStyle(table_style)
    elements.append(t)
    
    # Add notes section
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("Notes:", heading_style))
    elements.append(Paragraph("1. This report was generated using the Mullion Design Widget.", normal_style))
    elements.append(Paragraph(f"2. ULS requirements: Section modulus ≥ {Z_req_cm3:.2f} cm³", normal_style))
    elements.append(Paragraph(f"3. SLS requirements: Moment of inertia ≥ {I_req_cm4:.2f} cm⁴, " + 
                               f"deflection ≤ {defl_limit:.2f} mm", normal_style))
    elements.append(Paragraph("4. Sections are listed in descending order of SLS utilization for passing sections.", normal_style))
    
    # Build the PDF document
    doc.build(elements)
    buffer.seek(0)
    return buffer

def export_section_report(
    wind_pressure, bay_width, mullion_length, selected_barrier_load,
    ULS_case, SLS_case, plot_material, Z_req_cm3, defl_limit,
    df_display, selected_indices=None
):
    """
    Generate section report PDF and return as bytes
    
    This function wraps the create_pdf_report function and calculates the required 
    moment of inertia before calling it.
    
    Parameters:
    -----------
    Same as create_pdf_report, plus:
    df_display : pandas.DataFrame
        The dataframe displayed in the UI with all sections
        
    Returns:
    --------
    BytesIO
        PDF document as bytes
    """
    from config import material_props
    
    # Calculate the required moment of inertia
    E = material_props[plot_material]["E"]
    p = wind_pressure * 0.001  # Convert kPa to N/mm²
    L = mullion_length
    bay = bay_width
    w = p * bay
    
    # Calculate required I based on SLS case
    if SLS_case.startswith("SLS 1"):
        # For wind load case
        I_req = (5 * w * L**4) / (384 * E * defl_limit)
    else:
        # For barrier load case
        from config import BARRIER_LENGTH
        F_BL = selected_barrier_load * bay
        I_req = ((F_BL * BARRIER_LENGTH) / (12 * E * defl_limit)) * (0.75 * L**2 - BARRIER_LENGTH**2)
    
    # Convert to cm⁴
    I_req_cm4 = I_req / 10000
    
    # Generate load case tables
    from load_cases import generate_load_case_tables
    uls_df, sls_df = generate_load_case_tables(
        wind_pressure, bay_width, mullion_length, selected_barrier_load
    )
    
    # Generate PDF report
    return create_pdf_report(
        wind_pressure, bay_width, mullion_length, selected_barrier_load,
        ULS_case, SLS_case, plot_material, Z_req_cm3, I_req_cm4, defl_limit,
        df_display, selected_indices, uls_df, sls_df
    )

def generate_pdf_download_button(
    wind_pressure, bay_width, mullion_length, selected_barrier_load,
    ULS_case, SLS_case, plot_material, Z_req_cm3, defl_limit,
    df_display, selected_sections=None
):
    """
    Generate a Streamlit download button for PDF report export
    
    Parameters:
    -----------
    Same as export_section_report
    selected_sections : list or None
        The indices of sections selected by the user
    
    Returns:
    --------
    Streamlit download button
    """
    import streamlit as st
    
    # Create section selection multi-select
    section_options = []
    for idx, row in df_display.iterrows():
        uls_status = "✅" if row["ULS Util. (%)"] <= 100 else "❌"
        sls_status = "✅" if row["SLS Util. (%)"] <= 100 else "❌"
        label = f"{row['Supplier']}: {row['Profile Name']} - {row['Depth']} mm (ULS: {uls_status}, SLS: {sls_status})"
        section_options.append((idx, label))
    
    # Default to selecting passing sections
    default_indices = []
    for idx, row in df_display.iterrows():
        if row["ULS Util. (%)"] <= 100 and row["SLS Util. (%)"] <= 100:
            default_indices.append(idx)
    
    if len(default_indices) > 5:
        default_indices = default_indices[:5]
    
    # Allow user to select sections for the report
    st.subheader("Select Sections for Report")
    selected_indices = st.multiselect(
        "Choose sections to include in the PDF report:",
        options=[idx for idx, _ in section_options],
        default=default_indices,
        format_func=lambda x: next((label for idx, label in section_options if idx == x), "Unknown")
    )
    
    # Create the PDF bytes
    pdf_bytes = export_section_report(
        wind_pressure, bay_width, mullion_length, selected_barrier_load,
        ULS_case, SLS_case, plot_material, Z_req_cm3, defl_limit,
        df_display, selected_indices
    )
    
    # Create download button
    return st.download_button(
        label="Download Design Report PDF",
        data=pdf_bytes,
        file_name="mullion_design_report.pdf",
        mime="application/pdf",
        help="Download a design report in PDF format"
    )
