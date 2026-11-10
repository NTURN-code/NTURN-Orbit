# NTURN Orbit — Satellite Intelligence Research Prototype

A Streamlit research prototype for experimenting with public orbital data and user-provided CSV/JSON/TLE datasets. It is **not an operational ISRO system**, a certified collision-avoidance tool, or a validated disaster early-warning service.

## Current implementation status

| Module | What works now | Not implemented / limitation |
|---|---|---|
| Earth AI | CSV/JSON table loading and trusted local plugins | Satellite raster ingestion, georeferencing, NDVI, water indices and land-cover change |
| Orbit AI | CelesTrak TLE retrieval, Skyfield/SGP4 propagation, orbit summaries, ground-track positions, statistical outliers and coarse 1-minute proximity screening | Validated unknown-object identification; high-precision conjunction assessment; maneuver prediction |
| Health AI | CSV/JSON numeric-series analysis with rolling statistical anomaly flags | Real spacecraft telemetry ingestion, subsystem models and certified health diagnosis. Orbit-derived samples are not telemetry |
| Disaster AI | CSV/JSON table loading and trusted local plugins | Operational flood, wildfire and earthquake detection, validation and alerting |

## Requirements

- Python 3.10 or newer (3.11 recommended)
- Internet access for CelesTrak live TLE retrieval

## Install and run (Windows PowerShell)

```powershell
cd path\to\isro-framework
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

If PowerShell blocks activation, run without activating:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).

## Tests

```powershell
python -m pytest tests -v
```

## Data and scientific limitations

- TLEs are time-sensitive mean-element sets. Propagation accuracy degrades as a TLE ages; check its epoch and source before interpreting results.
- Orbit proximity is sampled at one-minute intervals. A sampled minimum is not a precise closest-approach solution and may miss a minimum between samples.
- Statistical outlier flags indicate unusual values relative to the selected dataset; they do not identify an unknown object or prove a malfunction.
- The Health AI anomaly-free share is a descriptive statistic, not a satellite health score.
- Never use this prototype alone for spacecraft operations, collision avoidance, emergency response or public safety decisions.

## Plugins and security

Copy `plugins/example_plugin.py` to create a local analysis plugin. Plugins are ordinary Python code and execute with the same operating-system permissions as the app. **Only run plugins you wrote or have reviewed and trust.** Do not expose this development app to the public internet with untrusted users or plugins.

## License

MIT. See `LICENSE`.
