import streamlit as st

def cpm_to_nM(cpm, sa_ciper_mmole, volume_ul, efficiency=0.5):
    """
    Convert CPM to concentration in nM.
    """
    DPM_PER_CI = 2.22e12  # disintegrations per minute per curie
    
    # Convert CPM → DPM
    dpm = cpm / efficiency
    
    # Convert SA (Ci/mmol) → Ci/mol
    sa_ciper_mole = sa_ciper_mmole * 1e3
    
    # Activity in Ci
    activity_ci = dpm / DPM_PER_CI
    
    # Moles of ligand
    mol = activity_ci / sa_ciper_mole
    
    # Convert µL → L
    volume_l = volume_ul * 1e-6
    
    # Concentration in M
    conc_M = mol / volume_l
    
    # Convert to nM
    return conc_M * 1e9

# ---------------- Streamlit UI ----------------

st.title("CPM → Concentration (nM) Calculator")

st.latex(r"""
C \;=\; 
\frac{\text{CPM}}{\text{Eff}} \times 
\frac{10^{6} \; }{SA \;\times\; 2.22 \times 10^{12} \;\times\; V}
\\[12pt]
\textbf{Where:} \\[6pt]
\begin{aligned}
C   &= \text{concentration in nM} \\
SA  &= \text{specific activity (Ci/mmol)} \\
Eff &= \text{counting efficiency (0–1)} \\
CPM &= \text{counts per minute} \\
V   &= \text{volume in } \mu L
\end{aligned}
""")



cpm = st.number_input("Counts per minute (CPM)", value=25000, step=1000)
sa = st.number_input("Specific activity (Ci/mmol)", value=60.0, step=0.1)
vol = st.number_input("Sample volume (µL)", value=10.0, step=1.0)
eff = st.number_input("Counting efficiency (0-1)", value=0.5, step=0.05)

if st.button("Calculate concentration"):
    conc_nM = cpm_to_nM(cpm, sa, vol, eff)
    st.success(f"Concentration = {conc_nM:.2f} nM")
