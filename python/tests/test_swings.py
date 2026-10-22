import pytest

from python.generate_test_data import make_multi_swing, make_stationary, make_swing
from python.swings import detect_swings, summarize_swings


def test_stationary_has_no_swings():
    assert detect_swings(make_stationary()) == []


def test_slow_swing_is_rejected():
    slow = make_swing(peak_g=1.5, peak_dps=150.0, width_s=0.3)
    assert detect_swings(slow) == []


def test_normal_swing_is_exactly_one():
    assert len(detect_swings(make_swing())) == 1


def test_multi_swing_is_three():
    assert len(detect_swings(make_multi_swing())) == 3


def test_high_threshold_finds_nothing():
    assert detect_swings(make_swing(), threshold=10.0) == []


def test_swing_window_contains_the_peak():
    (start, end), = detect_swings(make_swing(center_s=1.5))
    assert start < 1.5 < end


def test_short_spike_is_ignored():
    df = make_stationary()
    df.loc[100, "ax"] = 5.0        # a single noisy sample, not a swing
    assert detect_swings(df) == []


def test_recording_that_ends_mid_swing():
    df = make_swing(center_s=1.5)
    df = df[df["time"] <= 1.5].reset_index(drop=True)   # cut off at the peak
    swings = detect_swings(df)
    assert len(swings) == 1
    assert swings[0][1] == pytest.approx(df["time"].iloc[-1])


def test_summary_has_one_row_per_swing():
    df = make_multi_swing()
    table = summarize_swings(df, detect_swings(df))
    assert len(table) == 3
    assert list(table.columns) == ["swing", "start_s", "end_s", "duration_s",
                                   "peak_accel_g", "peak_rotation_dps"]
    assert table["peak_accel_g"].between(8.0, 9.0).all()


def test_summary_with_no_swings_is_empty():
    df = make_stationary()
    table = summarize_swings(df, detect_swings(df))
    assert len(table) == 0

# --- One real swing has several acceleration spikes but must count once -------------

def make_bat_swing_recording(starts, rate_hz=500, duration_s=8.0):
    """Each swing: spike when the hands accelerate the bat, a peak near contact, and a spike
    when the follow-through stops, with dips between them. Rotation is one smooth hump."""
    import numpy as np
    import pandas as pd

    t = np.arange(0, duration_s, 1 / rate_hz)
    acc = np.ones_like(t)
    gyro = np.zeros_like(t)
    for t0 in starts:
        for offset, peak, sigma in [(0.0, 6.0, 0.04), (0.25, 9.0, 0.03), (0.45, 6.0, 0.04)]:
            acc += peak * np.exp(-((t - (t0 + offset)) ** 2) / (2 * sigma ** 2))
        gyro += 1000 * np.exp(-((t - (t0 + 0.25)) ** 2) / (2 * 0.15 ** 2))
    return pd.DataFrame({"time": t, "ax": 0.0, "ay": 0.0, "az": acc,
                         "gx": gyro, "gy": 0.0, "gz": 0.0})


def test_one_swing_with_three_acceleration_spikes_counts_once():
    df = make_bat_swing_recording([2.0])
    assert len(detect_swings(df, 2.5)) == 1


def test_two_swings_a_couple_of_seconds_apart_count_twice():
    df = make_bat_swing_recording([1.5, 4.0])
    assert len(detect_swings(df, 2.5)) == 2


def test_a_second_burst_right_after_a_swing_is_ignored():
    # 0.6 s after the swing's last spike: inside the refractory period (the bat being brought back)
    df = make_bat_swing_recording([2.0, 3.1])
    assert len(detect_swings(df, 2.5)) == 1


def test_streaming_tracker_matches_batch_detector():
    from python.swings import SwingTracker
    df = make_bat_swing_recording([1.5, 4.0])
    tracker = SwingTracker(2.5)
    found = []
    for t, ax, ay, az, gx, gy, gz in df[["time", "ax", "ay", "az", "gx", "gy", "gz"]].itertuples(index=False):
        done = tracker.update(t, (ax**2 + ay**2 + az**2) ** 0.5, (gx**2 + gy**2 + gz**2) ** 0.5)
        if done:
            found.append(done)
    assert len(found) == 2
    assert found[0]["peak_g"] > 8 and found[0]["peak_dps"] > 900