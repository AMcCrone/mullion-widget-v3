import streamlit as st

def render_documentation():
    st.markdown("The following text describes the documentation, limitations, and formulae used in the creation of this **Mullion Check Widget**")

    st.header("Material Properties")
    st.subheader("Steel")
    st.subheader("Aluminium")
    
    st.header("Stress Calculations")
    st.subheader("Wind Load (WL)")
    st.latex(r'''
        w_{WL} = q_{WL}W_{bay}
        ''')
    st.markdown("Where $w_{WL}$ is the effective UDL on the mullion for a given wind load, $q_{WL}$, and bay width, $W_{bay}$. The maximum bending moment - at midspan - is calculated through:")
    st.latex(r'''
        M_{WL,max} = \frac{w_{WL}L^2}{8}
        ''')
    st.markdown("Where $L$ is the total span of the mullion.")
    
    st.subheader("Barrier Load (WL)")
    st.latex(r'''
        P_{BL} = w_{WL}W_{bay}
        ''')
    st.markdown("Where $P_{BL}$ is the effective point load on the mullion at 1100mm from its base for a given barrier load, $w_{BL}$, and bay width, $W_{bay}$. The maximum bending moment - at midspan - is calculated through:")
    st.latex(r'''
        M_{BL,max} = \frac{P_{BL}Lx}{2} = \frac{P_{BL}L^2}{4}
        ''')
    
    st.subheader("Stress Limit")
    st.markdown("The required section modulus is calculated through:")
    st.latex(r'''
        \sigma_{y} = \frac{My}{I} = \frac{M}{Z_{req}} 
        ''')
    st.latex(r'''
        Z_{req} = \frac{M}{\sigma_{y}} 
        ''')
    st.markdown("Where $\sigma_{y}$ is the yield stress of the material (aluminium or steel), $y$ is the distance of a section’s extreme fibre from its centroid, and $Z_{req}$ is the required section modulus given bending moment $M$. With:")
    st.latex(r'''
        M = \alpha M_{WL,max} + \beta M_{BL,max}
        ''')
    st.markdown("With combination factors α and β depending on the load case.")
    
    st.header("Deflection Calculations")
    st.subheader("Wind Load (WL)")
    st.markdown("For the UDL $w_{WL}$, the maximum deflection, $\delta_{WL}$, is at midspan with a magnitude of:")
    st.latex(r'''
        \delta_{WL}=\frac{5w_{WL}L^4}{384EI}
        ''')
    st.markdown("Where $E$ is the elastic modulus of the material (aluminium or steel) and $I$ is the section's second moment of area.")
    
    st.subheader("Barrier Load (WL)")
    st.markdown("For the point load $P_{BL}$ at barrier height $L_{BL}$, the deflection, $\delta_{BL}$, is calculated through:")
    st.latex(r'''
        \delta_{BL}=\frac{P_{BL}}{12EI}\left(L^2-x^2-L_{BL}^2\right)
        ''')
    st.markdown("Where $L_{BL}$ has been assumed to be 1100mm from the base of the mullion and the deflection taken at midspan ($x = L/2$) for superposition with $\delta_{WL}$. Thus:")
    st.latex(r'''
        \delta_{BL}=\frac{P_{BL}}{12EI}\left(\frac{3}{4}L^2-L_{BL}^2\right)
        ''')
    
    st.subheader("Deflection Limits")
    st.markdown("The deflection limits are as set out in CWCT doc XX...")
    st.latex(r'''
        \delta_{lim} = \begin{cases}
                           L/200 &\text{if } L \leq 3000 \text{mm} \\
                           5 + L/300 &\text{if } 3000 < L \leq 7500 \text{mm} \\
                           L/250 &\text{if } L > 7500 \text{mm}
                       \end{cases}
                       ''')
    
    st.header("Load Cases")
    st.markdown("The following load cases have been selected following guidance from *CWCT Guidance on non-loadbearing building envelopes*")
    st.latex(r'''
        \text{Load Case 1 (ULS 1):} 1.35DL + 1.5WL + 0.5*1.5BL
        ''')
    st.latex(r'''
        \text{Load Case 2 (ULS 2):} 1.35DL + 0.5*1.5WL + 1.5BL
        ''')
    st.latex(r'''
        \text{Load Case 3 (ULS 3):} 1.35DL + 1.5WL
        ''')
    st.latex(r'''
        \text{Load Case 4 (ULS 4):} 1.35DL + 1.5BL
        ''')
    st.latex(r'''
        \text{Load Case 5 (SLS 1):} 1.00DL + 1.00WL
        ''')
    st.latex(r'''
        \text{Load Case 6 (SLS 2):} 1.00DL + 1.00BL
        ''')
    
    st.header("Utilisation")
    st.markdown("Utilisation is calculated as described above.")
