"""Orbit maths using real TLE data (skyfield / SGP4)."""
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
from skyfield.api import EarthSatellite, load

ts = load.timescale()
MU = 398600.4418   # km^3/s^2
RE = 6378.137      # km


def make_sats(tles):
    out = []
    for name, l1, l2 in tles:
        try:
            out.append(EarthSatellite(l1, l2, name, ts))
        except Exception:
            pass
    return out


def orbit_table(sats):
    rows = []
    for s in sats:
        m = s.model
        if m.no_kozai <= 0:
            continue
        n = m.no_kozai / 60.0                       # rad/s
        a = (MU / n ** 2) ** (1 / 3)                # semi-major axis km
        rows.append({
            "Name": s.name,
            "Inclination": float(np.degrees(m.inclo)),
            "Eccentricity": float(m.ecco),
            "Period_min": float(2 * np.pi / m.no_kozai),
            "Altitude_km": a - RE,
            "Perigee_km": a * (1 - m.ecco) - RE,
            "Apogee_km": a * (1 + m.ecco) - RE,
        })
    return pd.DataFrame(rows)


def positions_now(sats):
    t = ts.now()
    rows = []
    for s in sats:
        try:
            sp = s.at(t).subpoint()
            la, lo = sp.latitude.degrees, sp.longitude.degrees
            if np.isnan(la) or np.isnan(lo):
                continue
            rows.append({"Name": s.name, "lat": la, "lon": lo, "alt": sp.elevation.km})
        except Exception:
            pass
    return pd.DataFrame(rows)


def track_dataframe(sat, minutes=180, step=2):
    now = datetime.now(timezone.utc)
    mins = list(range(0, minutes, step))
    t = ts.from_datetimes([now + timedelta(minutes=m) for m in mins])
    g = sat.at(t)
    sp = g.subpoint()
    return pd.DataFrame({
        "minute": mins,
        "height_km": sp.elevation.km,
        "speed_km_s": np.linalg.norm(g.velocity.km_per_s, axis=0),
        "lat": sp.latitude.degrees,
        "lon": sp.longitude.degrees,
    })


def closest_approach(target, others, minutes=90):
    """Minimum distance between target and every other object in the next N minutes."""
    now = datetime.now(timezone.utc)
    t = ts.from_datetimes([now + timedelta(minutes=m) for m in range(0, minutes + 1)])
    tp = target.at(t).position.km
    rows = []
    for s in others:
        if s is target:
            continue
        try:
            d = np.linalg.norm(s.at(t).position.km - tp, axis=0)
            if np.all(np.isnan(d)):
                continue
            i = int(np.nanargmin(d))
            rows.append({"Object": s.name,
                         "Min distance (km)": round(float(d[i]), 1),
                         "After (minutes)": i})
        except Exception:
            pass
    if not rows:
        return pd.DataFrame(columns=["Object", "Min distance (km)", "After (minutes)"])
    return pd.DataFrame(rows).sort_values("Min distance (km)").reset_index(drop=True)
