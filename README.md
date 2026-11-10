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

- Python 3.10 or newer (Python 3.11 recommended)
- Internet access for CelesTrak live TLE retrieval

## Install and run (Windows PowerShell)

Clone or download this repository, then open PowerShell in the repository folder:

```powershell
cd path\to\NTURN-Orbit
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If PowerShell blocks virtual-environment activation, use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).

## Tests

Run from the repository root:

```powershell
python -m pytest tests -v
```

When using the virtual environment without activation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

## Data and scientific limitations

- TLEs are time-sensitive mean-element sets. Propagation accuracy degrades as a TLE ages; check its epoch and source before interpreting results.
- Orbit proximity is sampled at one-minute intervals. A sampled minimum is not a precise closest-approach solution and may miss a minimum between samples.
- Statistical outlier flags indicate unusual values relative to the selected dataset; they do not identify an unknown object or prove a malfunction.
- The Health AI anomaly-free share is a descriptive statistic, not a satellite health score.
- The included telemetry CSV is synthetic demonstration data, not data from a real spacecraft.
- Never use this prototype alone for spacecraft operations, collision avoidance, emergency response or public safety decisions.

## Plugins and security

Copy `plugins/example_plugin.py` to create a local analysis plugin. Plugins are ordinary Python code and execute with the same operating-system permissions as the app. **Only run plugins you wrote or have reviewed and trust.**

The optional API/URL data source is intended for public HTTP(S) endpoints. The app rejects local/private IP destinations, does not follow redirects, and limits API response bodies to 25 MB. These checks are defense-in-depth, not a complete security boundary. Do not expose this development app to the public internet with untrusted users or plugins, and never paste API keys into public code or screenshots.

## License

MIT. See `LICENSE`.
