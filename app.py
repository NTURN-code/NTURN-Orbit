import streamlit as st

st.set_page_config(page_title="Satellite Intelligence Framework", page_icon="🚀", layout="wide")

st.title("🚀 Satellite Intelligence Framework")
st.caption("Research prototype. Bring your own data or API. Review scientific limitations and plugin security before use.")

CARDS = [
    ("pages/1_Earth_AI.py", "🌍 Earth AI", "Satellite Intelligence",
     "Data workspace; raster indices are not implemented yet."),
    ("pages/2_Orbit_AI.py", "🛰️ Orbit AI", "Space Debris Research",
     "TLE-based orbital research and coarse proximity screening."),
    ("pages/3_Health_AI.py", "💓 Health AI", "Satellite Telemetry Analysis",
     "CSV telemetry anomaly analysis; not certified health diagnosis."),
    ("pages/4_Disaster_AI.py", "🔥 Disaster AI", "Disaster Intelligence",
     "Data workspace; operational disaster detection is not implemented yet."),
]

cols = st.columns(2)
for i, (path, title, subtitle, desc) in enumerate(CARDS):
    with cols[i % 2].container(border=True):
        st.subheader(title)
        st.markdown(f"**{subtitle}**")
        st.write(desc)
        st.page_link(path, label="Open module", icon="➡️")

st.divider()
st.markdown("""
**How it works**
1. Open a module.
2. Choose a data source: built-in live data, your own file (CSV / JSON / TLE), or any API with your own key.
3. Analyse. Local plugins run as Python code with app permissions; only use trusted files.
""")
