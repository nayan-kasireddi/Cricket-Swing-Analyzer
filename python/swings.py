"""Find swings in a recording and summarize each one.

detect_swings() is a stand-in: a threshold with hysteresis on acceleration magnitude.
It uses the signature agreed (proposed) with Nayan, so his version can replace it later:
    detect_swings(df, threshold) -> list of (start_time, end_time) in seconds
"""
import numpy as np
import pandas as pd

from python.analyze import acceleration_magnitude, rotation_magnitude

DEFAULT_THRESHOLD_G = 2.5    # a swing starts when magnitude rises above this
RELEASE_FRACTION = 0.8       # ...and ends when it falls below 80% of the threshold
MIN_DURATION_S = 0.05        # ignore spikes shorter than this (noise)


def detect_swings(df, threshold=DEFAULT_THRESHOLD_G):
    """Return a list of (start_time, end_time) pairs, one per swing."""
    t = df["time"].to_numpy()
    acc = acceleration_magnitude(df)
    release = threshold * RELEASE_FRACTION

    swings = []
    start = None
    for time_s, a in zip(t, acc):
        if start is None and a > threshold:
            start = time_s
        elif start is not None and a < release:
            if time_s - start >= MIN_DURATION_S:
                swings.append((float(start), float(time_s)))
            start = None
    if start is not None and t[-1] - start >= MIN_DURATION_S:
        swings.append((float(start), float(t[-1])))   # recording ended mid-swing
    return swings


def summarize_swings(df, swings):
    """One row per swing: timing, peak acceleration, peak rotation."""
    acc = acceleration_magnitude(df)
    gyro = rotation_magnitude(df)
    t = df["time"].to_numpy()

    rows = []
    for i, (start, end) in enumerate(swings, start=1):
        mask = (t >= start) & (t <= end)
        rows.append({
            "swing": i,
            "start_s": round(start, 3),
            "end_s": round(end, 3),
            "duration_s": round(end - start, 3),
            "peak_accel_g": round(float(acc[mask].max()), 2),
            "peak_rotation_dps": round(float(gyro[mask].max()), 1),
        })
    return pd.DataFrame(rows, columns=["swing", "start_s", "end_s", "duration_s",
                                       "peak_accel_g", "peak_rotation_dps"])