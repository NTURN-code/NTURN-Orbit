
import pandas as pd
import streamlit as st

from core.data_sources import table_source_picker
from core.plugins import plugin_ui

st.set_page_config(page_title="Disaster AI", page_icon="🌪️", layout="wide")

st.title("🌪️ Disaster AI: Disaster Intelligence")
st.caption(
    "Explore disaster-related datasets, identify patterns and visualize "
    "reported impacts. Research prototype — not an operational warning system."
)

st.info(
    "Upload CSV/JSON data or connect a supported API. Results depend on "
    "the quality and meaning of your source data."
)

df = table_source_picker("disaster")

if df is None or df.empty:
    st.info("Choose a data source and load a dataset to begin.")
    st.stop()

# Work on a copy so the original uploaded data remains unchanged.
data = df.copy()
data.columns = [str(col).strip() for col in data.columns]

st.subheader("📋 Dataset Preview")
st.dataframe(data.head(100), width="stretch")

# Find common column names without assuming every dataset uses the same schema.
def find_column(candidates):
    lookup = {str(col).lower().replace(" ", "_"): col for col in data.columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


date_col = find_column([
    "date", "datetime", "timestamp", "event_date", "reported_date"
])
type_col = find_column([
    "disaster_type", "event_type", "hazard_type", "disaster",
    "event", "category", "type"
])
severity_col = find_column([
    "severity", "severity_level", "risk_level", "impact_level"
])
latitude_col = find_column(["latitude", "lat"])
longitude_col = find_column(["longitude", "lon", "lng"])
affected_col = find_column([
    "affected_population", "people_affected", "affected_people",
    "population_affected", "affected", "affected_count"
])
damage_col = find_column([
    "economic_damage", "estimated_damage", "damage", "loss",
    "damage_usd", "damage_inr"
])

st.divider()
st.subheader("📊 Disaster Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total records", f"{len(data):,}")
c2.metric("Data columns", f"{len(data.columns):,}")

if type_col:
    c3.metric("Disaster categories", f"{data[type_col].nunique(dropna=True):,}")
else:
    c3.metric("Disaster categories", "Not available")

if severity_col:
    c4.metric("Severity levels", f"{data[severity_col].nunique(dropna=True):,}")
else:
    c4.metric("Severity levels", "Not available")

# Disaster category analysis
st.divider()
st.subheader("🔥 Disaster Category Analysis")

if type_col:
    category_counts = (
        data[type_col].fillna("Unknown").astype(str)
        .value_counts()
        .head(15)
    )
    st.bar_chart(category_counts)
else:
    st.warning(
        "No recognized disaster-type column found. "
        "Try a column named disaster_type, event_type, category or type."
    )

# Severity analysis
st.divider()
st.subheader("⚠️ Severity Analysis")

if severity_col:
    severity_counts = (
        data[severity_col].fillna("Unknown").astype(str)
        .value_counts()
    )
    st.bar_chart(severity_counts)
    st.caption("Severity categories are shown as provided by the dataset.")
else:
    st.info("Severity analysis requires a severity or risk_level column.")

# Date-wise trend
st.divider()
st.subheader("📅 Disaster Timeline")

if date_col:
    timeline = data[[date_col]].copy()
    timeline[date_col] = pd.to_datetime(timeline[date_col], errors="coerce")
    timeline = timeline.dropna(subset=[date_col])

    if not timeline.empty:
        timeline["Date"] = timeline[date_col].dt.date
        daily_counts = timeline.groupby("Date").size()
        st.line_chart(daily_counts)
    else:
        st.warning("The date column was found, but no valid dates could be parsed.")
else:
    st.info("Date-wise analysis requires a date, datetime or timestamp column.")

# Geographic visualization
st.divider()
st.subheader("🗺️ Geographic Impact Map")

if latitude_col and longitude_col:
    locations = data[[latitude_col, longitude_col]].copy()
    locations[latitude_col] = pd.to_numeric(
        locations[latitude_col], errors="coerce"
    )
    locations[longitude_col] = pd.to_numeric(
        locations[longitude_col], errors="coerce"
    )
    locations = locations.dropna()

    valid = (
        locations[latitude_col].between(-90, 90)
        & locations[longitude_col].between(-180, 180)
    )
    locations = locations[valid]

    if not locations.empty:
        map_data = locations.rename(
            columns={latitude_col: "latitude", longitude_col: "longitude"}
        )
        st.map(map_data)
        st.caption(
            f"Showing {len(map_data):,} valid coordinate records. "
            "These are dataset locations, not independently verified impact boundaries."
        )
    else:
        st.warning("Latitude and longitude columns were found, but no valid coordinates exist.")
else:
    st.info(
        "Map visualization requires latitude and longitude columns "
        "(for example, latitude and longitude)."
    )

# Impact statistics
st.divider()
st.subheader("📉 Reported Impact Statistics")

impact_found = False

if affected_col:
    affected = pd.to_numeric(data[affected_col], errors="coerce").dropna()
    if not affected.empty:
        impact_found = True
        a, b = st.columns(2)
        a.metric("Total reported affected", f"{affected.sum():,.0f}")
        b.metric("Average per record", f"{affected.mean():,.1f}")

if damage_col:
    damage = pd.to_numeric(data[damage_col], errors="coerce").dropna()
    if not damage.empty:
        impact_found = True
        a, b = st.columns(2)
        a.metric("Total reported damage", f"{damage.sum():,.2f}")
        b.metric("Average damage per record", f"{damage.mean():,.2f}")

if not impact_found:
    st.info(
        "Impact statistics require numeric columns such as "
        "affected_population or economic_damage."
    )

# Research plugins
st.divider()
st.subheader("🧩 Research Plugins")
st.caption("Only run plugins that you wrote or have reviewed and trust.")
plugin_ui(data, "disaster")

st.divider()
st.caption(
    "Research prototype: this dashboard summarizes uploaded records. "
    "It does not independently confirm disasters, predict their occurrence, "
    "or replace official emergency services and authoritative data."
)
