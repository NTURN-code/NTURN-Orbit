import plotly.graph_objects as go
import streamlit as st

from core.data_sources import tle_source_picker, ISRO_OPTIONS, DEBRIS_OPTIONS
from core.detector import find_outliers
from core.orbit import make_sats, orbit_table, positions_now, closest_approach
from core.plugins import plugin_ui

st.set_page_config(page_title="Orbit AI", page_icon="🛰️", layout="wide")
st.title("🛰️ Orbit AI: Space Debris Research")

tles = tle_source_picker("orbit", {**ISRO_OPTIONS, **DEBRIS_OPTIONS})
if not tles:
    st.info("Choose or load data to begin. Built-in data needs internet.")
    st.stop()

max_n = st.slider("Max objects to analyse (more = slower)", 50, 3000, 500, step=50)
sats = make_sats(tles[:max_n])
table = orbit_table(sats)
if table.empty:
    st.error("Could not read any valid orbit from this data.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Objects loaded", len(table))
c2.metric("Average altitude (km)", f"{table['Altitude_km'].mean():.0f}")
c3.metric("Average inclination (deg)", f"{table['Inclination'].mean():.1f}")

tab_map, tab_data, tab_unk, tab_col, tab_plug = st.tabs(
    ["🗺️ Live map", "📋 Orbit data", "❓ Unknown objects", "⚠️ Collision screening", "🧩 Plugins"])

with tab_map:
    pos = positions_now(sats)
    if pos.empty:
        st.warning("No positions could be calculated.")
    else:
        fig = go.Figure(go.Scattergeo(
            lat=pos["lat"], lon=pos["lon"], mode="markers", text=pos["Name"],
            marker=dict(size=5, color=pos["alt"], colorscale="Viridis",
                        showscale=True, colorbar=dict(title="Height km"))))
        st.plotly_chart(fig, width="stretch")

with tab_data:
    st.dataframe(table.round(3), width="stretch")
    h = go.Figure(go.Histogram(x=table["Altitude_km"], nbinsx=40))
    h.update_layout(title="Altitude distribution", xaxis_title="Altitude (km)")
    st.plotly_chart(h, width="stretch")

with tab_unk:
    st.write("Finds objects whose orbit is very different from the rest of the group.")
    z = st.slider("Sensitivity (z-score, lower = more objects flagged)", 1.5, 6.0, 3.0, 0.5)
    result = find_outliers(table, ["Inclination", "Eccentricity", "Period_min", "Altitude_km"], z)
    unusual = result[result["is_anomaly"]].sort_values("anomaly_score", ascending=False)
    st.metric("Unusual objects", len(unusual))
    st.dataframe(unusual.round(3), width="stretch")

with tab_col:
    st.write("Coarse closest-approach screening between one object and the others. Samples are evaluated at one-minute intervals; this is not a certified conjunction assessment.")
    names = [s.name for s in sats]
    target_name = st.selectbox("Target object", names)
    limit = st.slider("Alert distance (km)", 1, 500, 50)
    window = st.slider("Look ahead (minutes)", 10, 360, 90, step=10)
    if st.button("Run screening"):
        target = sats[names.index(target_name)]
        with st.spinner("Calculating..."):
            res = closest_approach(target, sats, window)
        close = res[res["Min distance (km)"] < limit] if not res.empty else res
        if len(close):
            st.error(f"{len(close)} object(s) come within {limit} km of {target_name}")
            st.dataframe(close, width="stretch")
        else:
            st.success(f"No object within {limit} km in the next {window} minutes.")
        st.markdown("**10 closest objects**")
        st.dataframe(res.head(10), width="stretch")
        st.caption("TLE data is approximate. This is a screening tool, not a final "
                   "collision-avoidance decision. One-minute sampling can miss a shorter-lived minimum; use authoritative conjunction data and specialist tools for operational decisions.")

with tab_plug:
    plugin_ui(table, "orbit")
