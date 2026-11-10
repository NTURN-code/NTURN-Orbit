"""Local plugin loader.

WARNING: Python plugins execute with the same permissions as this application.
Only load plugin files you wrote or have reviewed and trust.
"""
import importlib.util
import pathlib

import streamlit as st

PLUGIN_DIR = pathlib.Path(__file__).resolve().parent.parent / "plugins"


def load_plugins():
    found = {}
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(PLUGIN_DIR.glob("*.py")):
        if path.name.startswith("_") or path.name == "__init__.py":
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"nturn_plugin_{path.stem}", path)
            if spec is None or spec.loader is None:
                raise ImportError("Could not create plugin loader")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if callable(getattr(module, "analyze", None)):
                name = str(getattr(module, "NAME", path.stem))
                found[name] = module
        except Exception as exc:
            found[f"{path.stem} (load error)"] = (None, str(exc))
    return found


def plugin_ui(df, key):
    st.warning("Security: local Python plugins run with this app's permissions. Only use code you trust.")
    plugins = load_plugins()
    if not plugins:
        st.info("No valid plugins found. See plugins/example_plugin.py.")
        return
    name = st.selectbox("Choose plugin", list(plugins), key=f"{key}_plugin")
    item = plugins[name]
    if isinstance(item, tuple):
        st.error(f"Plugin could not load: {item[1]}")
        return
    if df is None or len(df) == 0:
        st.info("No data loaded yet.")
        return
    try:
        item.analyze(df.copy(), st)
    except Exception as exc:
        st.error(f"Plugin error: {type(exc).__name__}: {exc}")
