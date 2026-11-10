
import streamlit as st
import pandas as pd

from core.data_sources import table_source_picker
from core.plugins import plugin_ui

st.set_page_config(
    page_title="Earth AI",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Earth AI: Satellite Intelligence")

st.info(
    "Research prototype: This workspace supports CSV/JSON data, "
    "basic index visualization and location mapping. "
    "It does not yet process satellite raster imagery."
)

df = table_source_picker("earth")

if df is not None and not df.empty:

    st.success(f"Successfully loaded {len(df)} records.")

    st.subheader("📊 Data Preview")
    st.dataframe(df.head(100), width="stretch")

    st.divider()

    # Prepare numeric columns
    for col in ["latitude", "longitude", "ndvi", "ndwi"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Data summary
    st.subheader("📈 Data Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Records", len(df))

    with col2:
        st.metric(
            "Average NDVI",
            f"{df['ndvi'].mean():.3f}"
            if "ndvi" in df.columns and df["ndvi"].notna().any()
            else "Not available"
        )

    with col3:
        st.metric(
            "Average NDWI",
            f"{df['ndwi'].mean():.3f}"
            if "ndwi" in df.columns and df["ndwi"].notna().any()
            else "Not available"
        )

    st.divider()

    # NDVI chart
    if "ndvi" in df.columns and df["ndvi"].notna().any():
        st.subheader("🌱 NDVI — Vegetation Index")

        chart_data = df[["ndvi"]].dropna().reset_index(drop=True)
        st.line_chart(chart_data)

        st.caption(
            "NDVI values from the uploaded dataset. "
            "These are not independently verified satellite measurements."
        )
    else:
        st.info("NDVI column not found in uploaded data.")

    # NDWI chart
    if "ndwi" in df.columns and df["ndwi"].notna().any():
        st.subheader("💧 NDWI — Water Index")

        chart_data = df[["ndwi"]].dropna().reset_index(drop=True)
        st.line_chart(chart_data)

        st.caption(
            "NDWI values from the uploaded dataset. "
            "Interpretation depends on the index definition and source."
        )
    else:
        st.info("NDWI column not found in uploaded data.")

    st.divider()

    # Geographic map
    st.subheader("🗺️ Geographic Location Map")

    required = {"latitude", "longitude"}

    if required.issubset(df.columns):

        map_data = df[
            ["latitude", "longitude"]
        ].dropna().copy()

        map_data = map_data[
            map_data["latitude"].between(-90, 90)
            & map_data["longitude"].between(-180, 180)
        ]

        if not map_data.empty:
            st.map(
                map_data,
                latitude="latitude",
                longitude="longitude",
                size=10
            )
            st.caption(
                f"Showing {len(map_data)} valid sample locations."
            )
        else:
            st.warning("No valid geographic coordinates found.")
    else:
        st.info("Latitude and longitude columns are required for mapping.")

    st.divider()

    # Land cover summary
    if "land_cover" in df.columns:
        st.subheader("🌍 Land Cover Distribution")

        land_cover_counts = (
            df["land_cover"]
            .fillna("Unknown")
            .astype(str)
            .value_counts()
        )

        st.bar_chart(land_cover_counts)

    st.divider()

    # Existing plugin system
    st.subheader("🔌 Research Plugins")
    plugin_ui(df, "earth")

else:
    st.info("Upload a CSV/JSON dataset or connect a data source to begin.")
