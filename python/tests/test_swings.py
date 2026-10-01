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