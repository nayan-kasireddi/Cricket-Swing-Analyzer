"""Find swings in a recording and summarize each one.

detect_swings() is a stand-in for Nayan's algorithm. It uses the signature agreed
(proposed) with Nayan, so his version can replace it later:
    detect_swings(df, threshold) -> list of (start_time, end_time) in seconds

Why a swing is counted once (bat mechanics): one swing is a single sweep of rotation, but
acceleration magnitude has SEVERAL spikes inside it (the hands accelerating the bat, the
peak around contact, and the sudden stop in the follow-through), with dips between them.
So SwingTracker treats a swing as "active" while acceleration is high OR the bat is still
rotating, ends it only after things stay quiet for HOLD_SECONDS, and ignores new swings for
REFRACTORY_SECONDS afterwards (a batter cannot take a second swing that fast).
"""
import numpy as np
import pandas as pd

from python.analyze import acceleration_magnitude, rotation_magnitude

DEFAULT_THRESHOLD_G = 2.5    # a swing starts when magnitude rises above this
RELEASE_FRACTION = 0.8       # ...and ends when it falls below 80% of the threshold
MIN_DURATION_S = 0.05        # ignore spikes shorter than this (noise)
GYRO_HOLD_DPS = 150.0        # while rotating faster than this, the swing is still going
HOLD_SECONDS = 0.2           # quiet for this long = the swing is over
REFRACTORY_SECONDS = 1.0     # ignore new swings this long after one ends
MAX_SWING_SECONDS = 3.0      # safety cap, so continuous waving cannot become one endless swing


class SwingTracker:
    """Feed samples one at a time; update() returns a finished swing (a dict) or None."""

    def __init__(self, threshold_g=DEFAULT_THRESHOLD_G):
        self.threshold_g = threshold_g
        self.in_swing = False
        self._blocked_until = float("-inf")
        self._armed = True          # a new swing can only start after things have gone quiet
        self._start = self._last_active = 0.0
        self._peak_g = self._peak_dps = 0.0

    def update(self, t, acc_g, gyro_dps):
        if not self.in_swing:
            if t >= self._blocked_until:
                if acc_g > self.threshold_g and self._armed:
                    self.in_swing = True
                    self._start = self._last_active = t
                    self._peak_g, self._peak_dps = acc_g, gyro_dps
                elif acc_g < self.threshold_g * RELEASE_FRACTION and gyro_dps < GYRO_HOLD_DPS:
                    self._armed = True      # quiet again: ready for the next swing
            return None

        self._peak_g = max(self._peak_g, acc_g)
        self._peak_dps = max(self._peak_dps, gyro_dps)
        if acc_g >= self.threshold_g * RELEASE_FRACTION or gyro_dps >= GYRO_HOLD_DPS:
            self._last_active = t
        if t - self._last_active >= HOLD_SECONDS or t - self._start >= MAX_SWING_SECONDS:
            return self._finish()
        return None

    def flush(self):
        """Call when the data ends: returns the swing in progress, if any."""
        return self._finish() if self.in_swing else None

    def _finish(self):
        self.in_swing = False
        self._armed = False
        self._blocked_until = self._last_active + REFRACTORY_SECONDS
        if self._last_active - self._start < MIN_DURATION_S:
            return None
        return {"start": self._start, "end": self._last_active,
                "peak_g": self._peak_g, "peak_dps": self._peak_dps}


def detect_swings(df, threshold=DEFAULT_THRESHOLD_G):
    """Return a list of (start_time, end_time) pairs, one per swing."""
    t = df["time"].to_numpy()
    acc = acceleration_magnitude(df)
    gyro = rotation_magnitude(df)

    tracker = SwingTracker(threshold)
    swings = []
    for time_s, a, g in zip(t, acc, gyro):
        done = tracker.update(float(time_s), float(a), float(g))
        if done and done["end"] - done["start"] >= MIN_DURATION_S:
            swings.append((float(done["start"]), float(done["end"])))
    done = tracker.flush()
    if done and done["end"] - done["start"] >= MIN_DURATION_S:
        swings.append((float(done["start"]), float(done["end"])))
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