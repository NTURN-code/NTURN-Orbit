import streamlit as st

from core.data_sources import table_source_picker
from core.plugins import plugin_ui

st.set_page_config(page_title="Disaster AI", page_icon="🔥", layout="wide")
st.title("🔥 Disaster AI: Disaster Intelligence")
st.info("Status: data workspace only. Operational flood, wildfire and earthquake detection/alerts are not implemented yet. You can load tabular CSV/JSON data and use trusted local plugins.")

df = table_source_picker("disaster")
if df is not None and not df.empty:
    st.dataframe(df.head(100), width="stretch")
    st.divider()
    plugin_ui(df, "disaster")
