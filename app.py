import streamlit as st

st.set_page_config(page_title="NTURN Orbit", page_icon="🛰️", layout="wide")

st.title("🛰️ NTURN Orbit")
st.caption(
    "Space & Earth Intelligence Research Platform — research prototype. "
    "Bring your own data or API. Review scientific limitations and plugin security before use."
)

CARDS = [
    (
        "pages/1_Earth_AI.py",
        "🌍 Earth AI",
        "Satellite Intelligence",
        "CSV/JSON data workspace; satellite raster analysis is not implemented yet.",
    ),
    (
        "pages/2_Orbit_AI.py",
        "🛰️ Orbit AI",
        "Space Debris Research",
        "TLE-based orbital research and coarse proximity screening.",
    ),
    (
        "pages/3_Health_AI.py",
        "💓 Health AI",
        "Satellite Telemetry Analysis",
        "CSV/JSON statistical anomaly analysis; not a certified health diagnosis.",
    ),
    (
        "pages/4_Disaster_AI.py",
        "🌪️ Disaster AI",
        "Disaster Intelligence",
        "CSV/JSON data workspace; operational disaster detection is not implemented yet.",
    ),
]

columns = st.columns(2)
for index, (path, title, subtitle, description) in enumerate(CARDS):
    with columns[index % 2].container(border=True):
        st.subheader(title)
        st.markdown(f"**{subtitle}**")
        st.write(description)
        st.page_link(path, label="Open module", icon="➡️")

st.divider()
st.markdown(
    """
    **How it works**

    1. Open a module.
    2. Choose a source: built-in public data, your own CSV/JSON/TLE file, or a public API.
    3. Analyse the data. Local plugins execute Python code with the app's permissions;
       only use plugins you wrote or have reviewed and trust.

    **Research prototype notice:** Results are exploratory and must not be used alone
    for spacecraft operations, collision avoidance, emergency response, or public-safety decisions.
    """
)
