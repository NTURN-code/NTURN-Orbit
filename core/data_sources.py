"""Data loading helpers: built-in live data, user files, or a public API endpoint."""
import ipaddress
import io
import json
import pathlib
import socket
from urllib.parse import urlparse

import pandas as pd
import requests
import streamlit as st

CELESTRAK = "https://celestrak.org/NORAD/elements/gp.php"
MAX_API_BYTES = 25 * 1024 * 1024

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
    """Accept 2-line or 3-line TLE text; return (name, line1, line2) tuples."""
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    out, i = [], 0
    while i < len(lines):
        if lines[i].startswith("1 ") and i + 1 < len(lines) and lines[i + 1].startswith("2 "):
            out.append((f"SAT-{lines[i][2:7].strip()}", lines[i], lines[i + 1]))
            i += 2
        elif (
            i + 2 < len(lines)
            and lines[i + 1].startswith("1 ")
            and lines[i + 2].startswith("2 ")
        ):
            out.append((lines[i], lines[i + 1], lines[i + 2]))
            i += 3
        else:
            i += 1
    return out


def validate_public_url(url):
    """Validate an HTTP(S) URL and reject hostnames resolving to non-public IPs.

    Redirects are separately disabled in fetch_url so a public URL cannot redirect
    the request to a private address.
    """
    parsed = urlparse(str(url).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        raise ValueError("Enter a valid http:// or https:// URL")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing usernames or passwords are not supported")

    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(
        (".localhost", ".local", ".internal")
    ):
        raise ValueError("Local/private endpoints are not supported")

    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as exc:
        raise ValueError("The URL contains an invalid port") from exc

    try:
        literal_ip = ipaddress.ip_address(host)
        addresses = [literal_ip]
    except ValueError:
        try:
            records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            addresses = [ipaddress.ip_address(record[4][0].split("%")[0]) for record in records]
        except (OSError, ValueError) as exc:
            raise ValueError("The API hostname could not be resolved safely") from exc

    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("The API hostname must resolve only to public IP addresses")
    return parsed


@st.cache_data(ttl=3600, show_spinner="Fetching data...")
def fetch_celestrak(kind, value):
    try:
        response = requests.get(
            CELESTRAK,
            params={kind: value, "FORMAT": "tle"},
            timeout=(5, 20),
        )
        response.raise_for_status()
        return parse_tle_text(response.text)
    except requests.RequestException:
        return []


def fetch_url(url, api_key="", header_name="Authorization"):
    """Fetch a bounded response from a public HTTP(S) endpoint.

    This is a convenience for trusted data sources, not a complete security
    boundary for hosting the app with untrusted users.
    """
    parsed = validate_public_url(url)
    headers = {}
    if api_key:
        if not header_name or any(char in str(header_name) for char in "\r\n:"):
            raise ValueError("Enter a valid API key header name")
        if any(char in str(api_key) for char in "\r\n"):
            raise ValueError("The API key contains invalid line breaks")
        headers[str(header_name)] = str(api_key)

    response = requests.get(
        parsed.geturl(),
        headers=headers,
        timeout=(5, 20),
        allow_redirects=False,
        stream=True,
    )
    if 300 <= response.status_code < 400:
        raise ValueError("API redirects are not followed; enter the final public API URL")
    response.raise_for_status()

    declared_size = response.headers.get("Content-Length")
    if declared_size:
        try:
            if int(declared_size) > MAX_API_BYTES:
                raise ValueError("API response exceeds the 25 MB limit")
        except ValueError as exc:
            if "25 MB limit" in str(exc):
                raise
            # Ignore malformed Content-Length and enforce the limit while streaming.

    chunks, total = [], 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > MAX_API_BYTES:
            raise ValueError("API response exceeds the 25 MB limit")
        chunks.append(chunk)
    encoding = response.encoding or "utf-8"
    return b"".join(chunks).decode(encoding, errors="replace")


def text_to_df(text):
    """Convert JSON or CSV text to a pandas DataFrame."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            lists = [value for value in data.values() if isinstance(value, list)]
            data = lists[0] if lists else [data]
        if not isinstance(data, list):
            raise ValueError("JSON must contain an object or an array of objects")
        return pd.json_normalize(data)
    except (json.JSONDecodeError, ValueError, TypeError):
        return pd.read_csv(io.StringIO(text))


def tle_source_picker(key, builtin_options):
    """UI for built-in live TLE data, a local TLE file, or a public API."""
    mode = st.radio(
        "Data source",
        ["Built-in live (CelesTrak)", "My TLE file", "My API / URL"],
        horizontal=True,
        key=key + "_mode",
    )
    if mode.startswith("Built-in"):
        label = st.selectbox("Dataset", list(builtin_options), key=key + "_ds")
        kind, value = builtin_options[label]
        return fetch_celestrak(kind, value)
    if mode == "My TLE file":
        uploaded = st.file_uploader(
            "Upload TLE file (.txt / .tle)",
            type=["txt", "tle"],
            key=key + "_f",
        )
        return parse_tle_text(uploaded.getvalue().decode("utf-8", "ignore")) if uploaded else []

    url = st.text_input("API URL (must return TLE text)", key=key + "_u")
    api_key = st.text_input("API key (optional)", type="password", key=key + "_k")
    if url and st.button("Fetch data", key=key + "_b"):
        try:
            st.session_state[key + "_api"] = parse_tle_text(fetch_url(url, api_key))
        except Exception as exc:
            st.error(f"API error: {exc}")
    return st.session_state.get(key + "_api", [])


def table_source_picker(key, sample_path=None, extra=None):
    """UI for sample data, uploaded CSV/JSON, or a public API endpoint."""
    extra = extra or {}
    modes = (
        (["Sample data"] if sample_path else [])
        + list(extra)
        + ["My CSV / JSON file", "My API / URL"]
    )
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
        uploaded = st.file_uploader(
            "Upload CSV or JSON",
            type=["csv", "json"],
            key=key + "_f",
        )
        if uploaded:
            try:
                return text_to_df(uploaded.getvalue().decode("utf-8", "replace"))
            except Exception as exc:
                st.error(f"File read error: {exc}")
        return None

    url = st.text_input("API URL (JSON or CSV)", key=key + "_u")
    api_key = st.text_input("API key (optional)", type="password", key=key + "_k")
    header = st.text_input("Key header name", value="Authorization", key=key + "_h")
    if url and st.button("Fetch data", key=key + "_b"):
        try:
            st.session_state[key + "_api"] = text_to_df(fetch_url(url, api_key, header))
        except Exception as exc:
            st.error(f"API error: {exc}")
    return st.session_state.get(key + "_api")
