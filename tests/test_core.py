"""Small dependency-light regression tests: run with pytest."""
import pandas as pd
import pytest

from core.detector import find_outliers, rolling_anomaly
from core.data_sources import parse_tle_text, text_to_df, fetch_url


def test_parse_tle_two_line_and_three_line():
    text = "ISS (ZARYA)\n1 25544U 98067A   24001.00000000  .00000000  00000-0  00000-0 0  9990\n2 25544  51.6400  10.0000 0005000  20.0000  30.0000 15.50000000123456\n"
    assert len(parse_tle_text(text)) == 1
    assert parse_tle_text(text)[0][0] == "ISS (ZARYA)"


def test_text_to_df_csv_and_json():
    assert list(text_to_df('{"a":1}').columns) == ["a"]
    assert text_to_df("a,b\n1,2").iloc[0].tolist() == [1, 2]


def test_find_outliers_flags_extreme_value():
    result = find_outliers(pd.DataFrame({"x": [1, 1, 1, 1, 100]}), ["x"], z=1)
    assert bool(result.iloc[-1]["is_anomaly"])


def test_rolling_anomaly_detects_jump():
    flags, _ = rolling_anomaly(pd.Series([1, 1, 1, 1, 1, 100]), window=5, z=2)
    assert bool(flags.iloc[-1])


def test_rejects_invalid_url_scheme():
    with pytest.raises(ValueError):
        fetch_url("file:///etc/passwd")


def test_example_plugin_is_discoverable():
    from core.plugins import load_plugins
    plugins = load_plugins()
    assert "Example: basic statistics" in plugins
    assert callable(plugins["Example: basic statistics"].analyze)
