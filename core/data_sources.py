"""Data loading helpers: built-in live data, user files, or any user API."""
import json
import io
import pathlib
from urllib.parse import urlparse

import pandas as pd
import requests
import streamlit as st

CELESTRAK = "https://celestrak.org/NORAD/elements/gp.php"

ISRO_OPTIONS = {
    "ISRO: CARTOSAT": ("NAME", "CARTOSAT"),
    "ISRO: RISAT": ("NAME", "RISAT"),
    "ISRO: RESOURCESAT": ("NAME", "RESOURCESAT"),
    "ISRO: OCEANSAT": ("NAME", "OCEANSAT"),
    "ISRO: INSAT": ("NAME", "INSAT"),
    "ISRO: GSAT": ("NAME", "GSAT"),
    "ISRO: NavIC (IRNSS)": ("NAME", "IRNSS"),
    "ISRO: ASTROSAT": ("NAME", "ASTROSAT"),
    "ISRO: EOS": ("NAME", "EOS"),
}

DEBRIS_OPTIONS = {
    "Debris: Cosmos-2251": ("GROUP", "cosmos-2251-debris"),
    "Debris: Iridium-33": ("GROUP", "iridium-33-debris"),
    "Debris: Fengyun-1C": ("GROUP", "fengyun-1c-debris"),
    "All active satellites": ("GROUP", "active"),
}


def parse_tle_text(text):
    """Accepts 2-line or 3-line TLE text. Returns list of (name, line1, line2)."""
    lines = [l.rstrip() for l in text.strip().splitlines() if l.strip()]
    out, i = [], 0
    while i < len(lines):
        if lines[i].startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 "):
            out.append((f"SAT-{lines[i][2:7].strip()}", lines[i], lines[i + 1]))
            i += 2
        elif i + 2 < len(lines) and lines[i + 1].startswith("1 ") and lines[i + 2].startswith("2 "):
            out.append((lines[i].strip(), lines[i + 1], lines[i + 2]))
            i += 3
        else:
            i += 1
    return out


@st.cache_data(ttl=3600, show_spinner="Fetching data...")
def fetch_celestrak(kind, value):
    try:
        r = requests.get(CELESTRAK, params={kind: value, "FORMAT": "tle"}, timeout=20)
        return parse_tle_text(r.text)
    except Exception:
        return []


def fetch_url(url, api_key="", header_name="Authorization"):
    """Fetch a user-supplied HTTP(S) endpoint. Do not use private/internal URLs."""
    parsed = urlparse(str(url).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a valid http:// or https:// URL")
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise ValueError("Local/private endpoints are not supported")
    headers = {header_name: api_key} if api_key else {}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text


def text_to_df(text):
    """JSON or CSV text -> DataFrame."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            lists = [v for v in data.values() if isinstance(v, list)]
            data = lists[0] if lists else [data]
        if not isinstance(data, list):
            raise ValueError("JSON must contain an object or an array of objects")
        return pd.json_normalize(data)
    except (json.JSONDecodeError, ValueError, TypeError):
        return pd.read_csv(io.StringIO(text))


def tle_source_picker(key, builtin_options):
    """UI: choose where orbit (TLE) data comes from. Returns list of TLEs."""
    mode = st.radio("Data source",
                    ["Built-in live (CelesTrak)", "My TLE file", "My API / URL"],
                    horizontal=True, key=key + "_mode")
    if mode.startswith("Built-in"):
        label = st.selectbox("Dataset", list(builtin_options), key=key + "_ds")
        kind, value = builtin_options[label]
        return fetch_celestrak(kind, value)
    if mode == "My TLE file":
        f = st.file_uploader("Upload TLE file (.txt / .tle)", type=["txt", "tle"], key=key + "_f")
        return parse_tle_text(f.getvalue().decode("utf-8", "ignore")) if f else []
    url = st.text_input("API URL (must return TLE text)", key=key + "_u")
    api_key = st.text_input("API key (optional)", type="password", key=key + "_k")
    if url and st.button("Fetch data", key=key + "_b"):
        try:
            st.session_state[key + "_api"] = parse_tle_text(fetch_url(url, api_key))
        except Exception as e:
            st.error(f"API error: {e}")
    return st.session_state.get(key + "_api", [])


def table_source_picker(key, sample_path=None, extra=None):
    """UI: choose table data (CSV/JSON). `extra` = {label: function returning DataFrame}."""
    extra = extra or {}
    modes = (["Sample data"] if sample_path else []) + list(extra) + ["My CSV / JSON file", "My API / URL"]
    mode = st.radio("Data source", modes, horizontal=True, key=key + "_mode")
    if mode == "Sample data":
        path = pathlib.Path(sample_path)
        if not path.is_file():
            st.error(f"Sample file not found: {path}")
            return None
        return pd.read_csv(path)
    if mode in extra:
        return extra[mode]()
    if mode == "My CSV / JSON file":
        f = st.file_uploader("Upload CSV or JSON", type=["csv", "json"], key=key + "_f")
        if f:
            try:
                return text_to_df(f.getvalue().decode("utf-8", "ignore"))
            except Exception as e:
                st.error(f"File read error: {e}")
        return None
    url = st.text_input("API URL (JSON or CSV)", key=key + "_u")
    api_key = st.text_input("API key (optional)", type="password", key=key + "_k")
    header = st.text_input("Key header name", value="Authorization", key=key + "_h")
    if url and st.button("Fetch data", key=key + "_b"):
        try:
            st.session_state[key + "_api"] = text_to_df(fetch_url(url, api_key, header))
        except Exception as e:
            st.error(f"API error: {e}")
    return st.session_state.get(key + "_api")
