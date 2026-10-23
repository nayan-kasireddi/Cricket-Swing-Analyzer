import pytest

from python.generate_test_data import make_stationary, make_swing
from python.ingest import DataValidationError, load_csv


def write(df, tmp_path, name="data.csv"):
    path = tmp_path / name
    df.to_csv(path, index=False)
    return path


def test_valid_stationary_file_loads(tmp_path):
    df = load_csv(write(make_stationary(), tmp_path))
    assert list(df.columns) == ["time", "ax", "ay", "az", "gx", "gy", "gz"]
    assert len(df) == 2500


def test_valid_swing_file_loads(tmp_path):
    assert len(load_csv(write(make_swing(), tmp_path))) == 1500


def test_missing_file(tmp_path):
    with pytest.raises(DataValidationError, match="File not found"):
        load_csv(tmp_path / "nope.csv")


def test_empty_file(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(DataValidationError, match="empty"):
        load_csv(path)


def test_missing_column(tmp_path):
    df = make_stationary().drop(columns=["gz"])
    with pytest.raises(DataValidationError, match="Missing required column.*gz"):
        load_csv(write(df, tmp_path))


def test_nan_value(tmp_path):
    df = make_stationary()
    df.loc[10, "ax"] = float("nan")
    with pytest.raises(DataValidationError, match="NaN"):
        load_csv(write(df, tmp_path))


def test_blank_row(tmp_path):
    df = make_stationary()
    df.loc[20, :] = float("nan")
    with pytest.raises(DataValidationError, match="NaN"):
        load_csv(write(df, tmp_path))


def test_non_numeric_value(tmp_path):
    df = make_stationary().astype(object)
    df.loc[5, "ay"] = "oops"
    with pytest.raises(DataValidationError, match="Non-numeric"):
        load_csv(write(df, tmp_path))


def test_timestamps_going_backwards(tmp_path):
    df = make_stationary()
    df.loc[50, "time"] = 0.0
    with pytest.raises(DataValidationError, match="not strictly increasing"):
        load_csv(write(df, tmp_path))


def test_wrong_sample_rate(tmp_path):
    df = make_stationary()
    df["time"] = df["time"] * 2          # looks like 50 Hz
    with pytest.raises(DataValidationError, match="Sample rate"):
        load_csv(write(df, tmp_path))


def test_dropped_samples_gap(tmp_path):
    df = make_stationary().drop(index=range(100, 110)).reset_index(drop=True)
    with pytest.raises(DataValidationError, match="Gap in data"):
        load_csv(write(df, tmp_path))


def test_impossible_acceleration(tmp_path):
    df = make_stationary()
    df.loc[30, "az"] = 500.0
    with pytest.raises(DataValidationError, match="Acceleration out of range"):
        load_csv(write(df, tmp_path))


def test_impossible_rotation(tmp_path):
    df = make_stationary()
    df.loc[30, "gx"] = 9000.0
    with pytest.raises(DataValidationError, match="Rotation rate out of range"):
        load_csv(write(df, tmp_path))

def test_millisecond_timestamps_are_converted(tmp_path, monkeypatch):
    import python.ingest as ingest
    monkeypatch.setattr(ingest, "TIME_TO_SECONDS", 0.001)
    df = make_stationary()
    df["time"] = df["time"] * 1000          # firmware-style milliseconds
    loaded = ingest.load_csv(write(df, tmp_path))
    assert loaded["time"].iloc[-1] == pytest.approx(4.998)


def test_firmware_format_is_loaded(tmp_path):
    """Nayan's real output: comment lines, microsecond time, unit-suffixed names, skipped_slots."""
    df = make_stationary()
    df["time"] = (df["time"] * 1_000_000).round().astype(int)
    df["skipped_slots"] = 0
    df.columns = ["time_us", "ax_g", "ay_g", "az_g", "gx_dps", "gy_dps", "gz_dps", "skipped_slots"]
    path = tmp_path / "firmware.csv"
    with open(path, "w") as f:
        f.write("# MPU6050 500 Hz target | polling | +/-16g | +/-2000dps\n")
        df.iloc[:100].to_csv(f, index=False)
        f.write("# Sensor I2C read failed\n")
        df.iloc[100:].to_csv(f, index=False, header=False)
    loaded = load_csv(path)
    assert list(loaded.columns) == ["time", "ax", "ay", "az", "gx", "gy", "gz"]
    assert loaded["time"].iloc[-1] == pytest.approx(4.998)

@pytest.mark.parametrize("column", ["time", "ax", "gx"])
@pytest.mark.parametrize("value", [float("inf"), float("-inf")])
def test_infinite_values_are_rejected(tmp_path, column, value):
    df = make_stationary()
    df.loc[10, column] = value
    with pytest.raises(DataValidationError, match="finite"):
        load_csv(write(df, tmp_path))
