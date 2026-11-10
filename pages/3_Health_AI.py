
import pathlib

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data_sources import table_source_picker, tle_source_picker, ISRO_OPTIONS
from core.detector import rolling_anomaly
from core.orbit import make_sats, track_dataframe
from core.plugins import plugin_ui

st.set_page_config(page_title="Health AI", page_icon="💓", layout="wide")

st.title("💓 Health AI: Satellite Health Monitoring")
st.caption("Satellite telemetry analysis, sensor monitoring and statistical anomaly detection.")

SAMPLE = (
    pathlib.Path(__file__).resolve().parent.parent
    / "sample_data"
    / "telemetry_sample.csv"
)


def live_source():
    tles = tle_source_picker("health_live", ISRO_OPTIONS)
    sats = make_sats(tles) if tles else []

    if not sats:
        return None

    names = [s.name for s in sats]
    name = st.selectbox("Satellite", names, key="health_sat")

    # Orbit-derived data is not actual spacecraft telemetry.
    return track_dataframe(sats[names.index(name)])


df = table_source_picker(
    "health",
    SAMPLE,
    {"Orbit-derived sample (NOT telemetry)": live_source},
)

if df is None or df.empty:
    st.info("Choose a data source or upload a telemetry CSV/JSON file to begin.")
    st.stop()

data = df.copy()
data.columns = [str(col).strip() for col in data.columns]

# Detect commonly used columns.
def find_column(candidates):
    lookup = {
        str(col).lower().replace(" ", "_"): col
        for col in data.columns
    }
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


satellite_col = find_column(["satellite_id", "satellite", "object_name", "name"])
time_col = find_column(["timestamp", "datetime", "date", "time"])
status_col = find_column(["status", "health_status", "condition"])

# Satellite filter.
st.divider()
st.subheader("🛰️ Satellite Selection")

if satellite_col:
    satellite_options = sorted(
        data[satellite_col].dropna().astype(str).unique().tolist()
    )
    selected_satellite = st.selectbox(
        "Select satellite",
        ["All satellites"] + satellite_options,
    )

    if selected_satellite != "All satellites":
        data = data[
            data[satellite_col].astype(str) == selected_satellite
        ].copy()
else:
    st.caption("No satellite ID column found. Showing all records.")

if data.empty:
    st.warning("No records available for this selection.")
    st.stop()

# Identify numeric sensor columns.
numeric_candidates = data.select_dtypes(include="number").columns.tolist()

# Also recognize numeric readings stored as text.
for col in data.columns:
    if col not in numeric_candidates:
        converted = pd.to_numeric(data[col], errors="coerce")
        if converted.notna().sum() > 0 and converted.notna().mean() >= 0.8:
            data[col] = converted
            numeric_candidates.append(col)

num_cols = numeric_candidates

st.divider()
st.subheader("📋 Telemetry Data Preview")
st.dataframe(data.head(100), width="stretch")

if not num_cols:
    st.error("No numeric sensor columns found in this dataset.")
    st.stop()

# Overview metrics.
st.divider()
st.subheader("📊 Satellite Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Telemetry records", f"{len(data):,}")
c2.metric("Sensors detected", f"{len(num_cols):,}")

if satellite_col:
    c3.metric(
        "Satellites",
        f"{data[satellite_col].nunique(dropna=True):,}",
    )
else:
    c3.metric("Satellites", "Not available")

if time_col:
    parsed_dates = pd.to_datetime(data[time_col], errors="coerce")
    valid_dates = parsed_dates.dropna()

    if not valid_dates.empty:
        c4.metric("Latest reading", valid_dates.max().strftime("%Y-%m-%d"))
    else:
        c4.metric("Latest reading", "Invalid dates")
else:
    c4.metric("Latest reading", "Not available")

# Status monitoring.
st.divider()
st.subheader("🚦 Telemetry Status")

if status_col:
    status_values = data[status_col].fillna("UNKNOWN").astype(str).str.upper()
    status_counts = status_values.value_counts()

    normal = int(status_counts.get("NORMAL", 0))
    warning = int(status_counts.get("WARNING", 0))
    critical = int(status_counts.get("CRITICAL", 0))
    unknown = len(data) - normal - warning - critical

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("NORMAL", normal)
    s2.metric("WARNING", warning)
    s3.metric("CRITICAL", critical)
    s4.metric("Other / Unknown", unknown)

    st.bar_chart(status_counts)
    st.caption("Status counts reflect labels supplied by the uploaded dataset.")
else:
    st.info(
        "No status column found. Add a column named status with "
        "NORMAL, WARNING or CRITICAL values to enable status monitoring."
    )

# Sensor monitoring.
st.divider()
st.subheader("🔬 Sensor Monitoring")

default_sensors = [
    col for col in num_cols
    if any(word in col.lower() for word in [
        "temperature", "voltage", "battery", "power",
        "signal", "cpu", "memory"
    ])
]

if not default_sensors:
    default_sensors = num_cols[:4]

selected_sensors = st.multiselect(
    "Select sensors to analyse",
    num_cols,
    default=default_sensors,
)

window = st.slider(
    "Anomaly detection window size (points)",
    min_value=5,
    max_value=100,
    value=20,
)

z = st.slider(
    "Anomaly sensitivity (z-score)",
    min_value=2.0,
    max_value=6.0,
    value=3.5,
    step=0.5,
)

if not selected_sensors:
    st.warning("Select at least one numeric sensor to continue.")
    st.stop()

# Prepare X-axis.
if time_col:
    x = data[time_col]
    x_label = time_col
else:
    x = data.index
    x_label = "Record number"

flags = {}
summary_rows = []
report = data.copy()

# Run anomaly detection.
for col in selected_sensors:
    values = pd.to_numeric(data[col], errors="coerce")
    valid = values.notna()

    if valid.sum() < window:
        st.warning(
            f"{col}: Not enough valid readings for the selected "
            f"window size of {window}."
        )
        continue

    flag = pd.Series(False, index=data.index)
    detected, _ = rolling_anomaly(values.loc[valid], window, z)
    flag.loc[valid] = detected.astype(bool).to_numpy()

    flags[col] = flag
    report[f"{col}_anomaly"] = flag

    clean_values = values.dropna()

    summary_rows.append({
        "Sensor": col,
        "Mean": round(float(clean_values.mean()), 3),
        "Minimum": round(float(clean_values.min()), 3),
        "Maximum": round(float(clean_values.max()), 3),
        "Anomalies": int(flag.sum()),
        "Anomaly-free share (%)": round(
            100 * (1 - float(flag.loc[valid].mean())), 1
        ),
    })

if not summary_rows:
    st.error("Not enough valid numeric readings to perform anomaly analysis.")
    st.stop()

summary = pd.DataFrame(summary_rows)

total_anomalies = sum(row["Anomalies"] for row in summary_rows)
average_clean_share = summary["Anomaly-free share (%)"].mean()

st.divider()
st.subheader("⚠️ Anomaly Detection Results")

m1, m2, m3 = st.columns(3)
m1.metric("Average anomaly-free share", f"{average_clean_share:.1f}%")
m2.metric("Total sensor anomalies", f"{total_anomalies:,}")
m3.metric("Sensors analysed", len(summary_rows))

st.dataframe(summary, width="stretch")

# Sensor graphs.
st.divider()
st.subheader("📈 Sensor Telemetry Graphs")

for col in flags:
    values = pd.to_numeric(data[col], errors="coerce")
    flag = flags[col]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=values,
            mode="lines",
            name=col,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x[flag],
            y=values[flag],
            mode="markers",
            name="Detected anomaly",
            marker=dict(color="red", size=9),
        )
    )

    fig.update_layout(
        title=f"{col} — Telemetry Analysis",
        xaxis_title=x_label,
        yaxis_title=col,
        hovermode="x unified",
    )

    st.plotly_chart(fig, width="stretch", key=f"health_chart_{col}")

# Detailed anomaly records.
st.divider()
st.subheader("🔎 Detected Anomaly Records")

anomaly_masks = list(flags.values())
any_anomaly = pd.concat(anomaly_masks, axis=1).any(axis=1)

anomaly_records = report.loc[any_anomaly].copy()

st.metric("Records with at least one anomaly", len(anomaly_records))

if not anomaly_records.empty:
    st.dataframe(anomaly_records, width="stretch")
else:
    st.success("No anomalies were detected with the current settings.")

# Export.
st.divider()
st.subheader("📥 Download Analysis Report")

csv_data = report.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download telemetry analysis CSV",
    data=csv_data,
    file_name="health_ai_analysis_report.csv",
    mime="text/csv",
)

# Research plugins.
st.divider()
st.subheader("🧩 Research Plugins")
st.caption("Only use plugins you wrote or have reviewed and trust.")
plugin_ui(data, "health")

st.divider()
st.caption(
    "Research prototype: statistical anomalies do not automatically mean "
    "spacecraft faults. This dashboard does not provide certified satellite "
    "health assessments. Orbit-derived samples are orbital calculations, "
    "not actual spacecraft sensor telemetry."
)
