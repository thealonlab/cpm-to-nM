import streamlit as st
from datetime import date

# ---------------- Constants ----------------
DPM_PER_CI = 2.22e12  # disintegrations per minute per curie
TRITIUM_HALF_LIFE_YEARS = 12.32

# ---------------- Chemistry presets (EDIT THESE) ----------------
# Put your true SA-at-purchase and purchase dates here.
PRESETS = {
    "DTG (³H)": {
        "sa0_ci_per_mmol": 60.0,
        "purchase_date": date(2025, 2, 16),
        "lot_number" : 250216,

    },
    "Ifenprodil (³H)": {
        "sa0_ci_per_mmol": 37.6,
        "purchase_date": date(2023, 11, 21),
        "lot_number" : 3187761,
    },
    "Pentazocine (³H)": {
        "sa0_ci_per_mmol": 42.4,
        "purchase_date": date(2026, 2, 19),
        "lot_number" : 3463164,
    },
    "Progesterone (³H)": {
        "sa0_ci_per_mmol": 50.0,
        "purchase_date": date(2026, 1, 5),
        "lot_number" : 260105,
    },
    "Custom…": None,
}

# ---------------- Helper functions ----------------
def years_between(d0: date, d1: date) -> float:
    return (d1 - d0).days / 365.2425

def sa_decay_tritium(sa0_ci_per_mmol: float, purchase_date: date, asof: date) -> float:
    """
    Apply radioactive decay for ³H to specific activity:
    SA(t) = SA0 * 2^(-t/T1/2)
    """
    if sa0_ci_per_mmol <= 0:
        raise ValueError("SA at purchase must be > 0.")
    if asof < purchase_date:
        raise ValueError("As-of date cannot be earlier than purchase date.")
    t_years = years_between(purchase_date, asof)
    return sa0_ci_per_mmol * (2 ** (-t_years / TRITIUM_HALF_LIFE_YEARS))

def cpm_to_moles(cpm: float, sa_ci_per_mmol: float, efficiency: float = 0.5) -> float:
    """
    Convert CPM to moles in the counted sample.
    """
    if efficiency <= 0 or efficiency > 1:
        raise ValueError("Efficiency must be in the range (0, 1].")
    if sa_ci_per_mmol <= 0:
        raise ValueError("Specific activity must be > 0.")
    if cpm < 0:
        raise ValueError("CPM must be ≥ 0.")

    # CPM → DPM
    dpm = cpm / efficiency

    # SA: Ci/mmol → Ci/mol
    sa_ci_per_mol = sa_ci_per_mmol * 1e3

    # Activity in Ci
    activity_ci = dpm / DPM_PER_CI

    # Moles
    mol = activity_ci / sa_ci_per_mol
    return mol

def cpm_to_conc_nM(cpm: float, sa_ci_per_mmol: float, aliquot_ul: float, efficiency: float = 0.5) -> float:
    """
    Concentration (nM) in the reaction mixture, assuming the aliquot is representative.
    """
    if aliquot_ul <= 0:
        raise ValueError("Aliquot volume must be > 0.")

    mol_aliquot = cpm_to_moles(cpm, sa_ci_per_mmol, efficiency)
    volume_l = aliquot_ul * 1e-6
    conc_M = mol_aliquot / volume_l
    return conc_M * 1e9

# ---------------- Streamlit UI ----------------
st.title("CPM → Concentration (nM) Calculator (³H decay-corrected SA)")

st.latex(r"""
\textbf{Decay-corrected specific activity (³H):}\qquad
SA(t)=SA_0\cdot 2^{-t/T_{1/2}},\;\; T_{1/2}=12.32\ \text{years}
""")

st.latex(r"""
\textbf{CPM → concentration:}\qquad
C_{\mathrm{nM}} =
\left(\frac{\mathrm{CPM}}{\mathrm{Eff}}\right)
\left(\frac{1}{2.22\times 10^{12}}\right)
\left(\frac{1}{SA_{\mathrm{Ci/mol}}}\right)
\left(\frac{1}{V_{\mathrm{L}}}\right)
\times 10^{9}
""")

# --- Counting inputs ---
st.subheader("Measurement")
cpm = st.number_input("Counts per minute (CPM)", value=25000.0, step=1000.0, min_value=0.0)
eff = st.number_input("Counting efficiency (0-1]", value=0.5, step=0.05, min_value=0.01, max_value=1.0)

aliquot_ul = st.number_input("Measured aliquot volume (µL)", value=10.0, step=1.0, min_value=0.0001)
rxn_ul = st.number_input("Total reaction volume (µL)", value=100.0, step=10.0, min_value=0.0001)

# --- Specific activity inputs ---
st.subheader("Ligand / Specific activity")
choice = st.selectbox("Ligand preset", list(PRESETS.keys()))
asof = st.date_input("Calculate SA as of", value=date.today())

if PRESETS[choice] is None:
    sa0 = st.number_input("SA at purchase (Ci/mmol)", value=60.0, step=0.1, min_value=0.0001)
    purchase_date = st.date_input("Purchase date", value=date.today())
else:
    # Show defaults but allow edits in the UI
    sa0 = st.number_input(
        "SA at purchase (Ci/mmol)",
        value=float(PRESETS[choice]["sa0_ci_per_mmol"]),
        step=0.1,
        min_value=0.0001,
        key=f"sa0_{choice}",
    )
    purchase_date = st.date_input(
        "Purchase date",
        value=PRESETS[choice]["purchase_date"],
        key=f"purchase_{choice}",
    )

# Compute decay-corrected SA
try:
    sa_current = sa_decay_tritium(sa0, purchase_date, asof)
    st.write(f"Decay-corrected SA used: **{sa_current:.3f} Ci/mmol**")
except ValueError as e:
    st.error(str(e))
    st.stop()

# --- Calculation ---
# --- Calculation ---
if st.button("Calculate"):
    try:
        scale = rxn_ul / aliquot_ul
        
        # Calculate concentration based on the aliquot, then correct for the dilution factor
        conc_aliquot_nM = cpm_to_conc_nM(cpm, sa_current, aliquot_ul, eff)
        conc_nM = conc_aliquot_nM / scale

        mol_aliquot = cpm_to_moles(cpm, sa_current, eff)
        mol_total = mol_aliquot * scale

        st.success(f"Concentration in reaction = {conc_nM:.2f} nM")
        st.info(f"Amount in aliquot = {mol_aliquot * 1e12:.3f} pmol")
        st.info(f"Total amount in reaction (scaled by {scale:.2f}×) = {mol_total * 1e12:.3f} pmol")

        st.caption("Note: Aliquot concentration divided by the volume dilution factor yields the reaction concentration.")
    except ValueError as e:
        st.error(str(e))