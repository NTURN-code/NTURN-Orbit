"""Allow pure helper tests to run when optional Streamlit UI deps are absent."""
import importlib.util
import sys
import types

if importlib.util.find_spec("streamlit") is None:
    stub = types.ModuleType("streamlit")
    def _cache_data(*args, **kwargs):
        return lambda function: function
    stub.cache_data = _cache_data
    sys.modules.setdefault("streamlit", stub)
