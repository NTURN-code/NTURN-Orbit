import pathlib

import plotly.graph_objects as go
import streamlit as st

from core.data_sources import table_source_picker, tle_source_picker, ISRO_OPTIONS
from core.detector import rolling_anomaly
from core.orbit import make_sats, track_dataframe
from core.plugins import plugin_ui

st.set_page_config(page_title="Health AI", page_icon="💓", layout="wide")
st.title("💓 Health AI: Satellite Telemetry Analysis")

SAMPLE = pathlib.Path(__file__).resolve().parent.parent / "sample_data" / "telemetry_sample.csv"


def live_source():
    tles = tle_source_picker("health_live", ISRO_OPTIONS)
    sats = make_sats(tles) if tles else []
    if not sats:
        return None
    names = [s.name for s in sats]
    name = st.selectbox("Satellite", names, key="health_sat")
    return track_dataframe(sats[names.index(name)])


df = table_source_picker("health", SAMPLE, {"Orbit-derived sample (NOT telemetry)": live_source})
if df is None or df.empty:
    st.info("Choose or load telemetry data to begin.")
    st.stop()

num_cols = df.select_dtypes("number").columns.tolist()
if not num_cols:
    st.error("No numeric columns found in this data.")
    st.stop()

st.markdown("**Data preview**")
st.dataframe(df.head(50), width="stretch")

c1, c2 = st.columns(2)
xcol = c1.selectbox("Time / X axis column", ["(row number)"] + list(df.columns))
sensors = c2.multiselect("Sensors to analyse", num_cols, default=num_cols[:4])
window = st.slider("Window size (points)", 5, 100, 20)
z = st.slider("Sensitivity (z-score, lower = more anomalies)", 2.0, 6.0, 3.5, 0.5)

if not sensors:
    st.stop()

x = df.index if xcol == "(row number)" else df[xcol]
flags, rows = {}, []
for col in sensors:
    flag, _ = rolling_anomaly(df[col], window, z)
    flags[col] = flag
    rows.append({
        "Sensor": col,
        "Mean": round(float(df[col].mean()), 3),
        "Min": round(float(df[col].min()), 3),
        "Max": round(float(df[col].max()), 3),
        "Anomalies": int(flag.sum()),
        "Anomaly-free share %": round(100 * (1 - float(flag.mean())), 1),
    })

overall = sum(r["Anomaly-free share %"] for r in rows) / len(rows)
m1, m2 = st.columns(2)
m1.metric("Average anomaly-free share", f"{overall:.1f} %")
m2.metric("Total anomalies", sum(r["Anomalies"] for r in rows))
st.caption("Anomaly-free share is a statistical indicator, not a certified satellite health score. "
           "Orbit-derived samples are position/velocity calculations, not spacecraft sensor telemetry.")
st.dataframe(rows, width="stretch")

for col in sensors:
    f = flags[col]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=df[col], mode="lines", name=col))
    fig.add_trace(go.Scatter(x=x[f], y=df[col][f], mode="markers", name="Anomaly",
                             marker=dict(color="red", size=9)))
    fig.update_layout(title=col, xaxis_title=str(xcol), yaxis_title=col)
    st.plotly_chart(fig, width="stretch", key=f"chart_{col}")

st.divider()
st.markdown("### 🧩 Plugins")
plugin_ui(df, "health")
