import streamlit as st

from core.data_sources import table_source_picker
from core.plugins import plugin_ui

st.set_page_config(page_title="Earth AI", page_icon="🌍", layout="wide")
st.title("🌍 Earth AI: Satellite Intelligence")
st.info("Status: data workspace only. Satellite raster ingestion, georeferencing, NDVI, water indices and land-cover change are not implemented yet. You can load tabular CSV/JSON data and use trusted local plugins.")

df = table_source_picker("earth")
if df is not None and not df.empty:
    st.dataframe(df.head(100), width="stretch")
    st.divider()
    plugin_ui(df, "earth")
