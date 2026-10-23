"""Load and validate IMU CSV files before anything analyzes them."""
import numpy as np
import pandas as pd

# --- Format settings. Edit here only. ---
# Canonical column names used everywhere in the Python code.
EXPECTED_COLUMNS = ["time", "ax", "ay", "az", "gx", "gy", "gz"]
# Nayan's firmware (pico2w_mpu6050.ino) writes different names; they are renamed on load.
# It also writes a "skipped_slots" column and "#" comment lines, which are ignored.
COLUMN_ALIASES = {
    "time_us": "time", "time_ms": "time", "time_s": "time",
    "ax_g": "ax", "ay_g": "ay", "az_g": "az",
    "gx_dps": "gx", "gy_dps": "gy", "gz_dps": "gz",
}
# Time units implied by the column name. A plain "time" column uses TIME_TO_SECONDS.
TIME_UNITS_BY_NAME = {"time_us": 1e-6, "time_ms": 1e-3, "time_s": 1.0}
TARGET_SAMPLE_RATE_HZ = 500       # firmware samples at 500 Hz (2000 us interval)
SAMPLE_RATE_TOLERANCE = 0.2       # allow +/-20% around the target
TIME_TO_SECONDS = 1.0             # for a plain "time" column: 0.001 if milliseconds
MAX_GAP_FACTOR = 3.0              # a gap > 3x the typical spacing means dropped samples
MAX_ACCEL_G = 16.0                # MPU6050's largest accelerometer range
MAX_GYRO_DPS = 2000.0             # MPU6050's largest gyroscope range


class DataValidationError(ValueError):
    """Raised when a CSV is unusable, with a message saying what is wrong."""


def _rows(index):
    """Convert DataFrame indices to CSV line numbers (header is line 1)."""
    shown = [str(i + 2) for i in list(index)[:5]]
    return ", ".join(shown) + (" ..." if len(index) > 5 else "")


def load_csv(path):
    """Load a CSV, validate it, and return a clean DataFrame."""
    try:
        # comment="#" skips the firmware's "# MPU6050 500 Hz ..." and "# Sensor I2C read failed" lines
        df = pd.read_csv(path, comment="#")
    except FileNotFoundError:
        raise DataValidationError(f"File not found: {path}") from None
    except pd.errors.EmptyDataError:
        raise DataValidationError(f"File is empty: {path}") from None
    except pd.errors.ParserError as e:
        raise DataValidationError(f"Could not parse {path} as CSV: {e}") from None

    # 1. Columns (rename firmware-style names, remember the time units)
    time_scale = TIME_TO_SECONDS
    for name, scale in TIME_UNITS_BY_NAME.items():
        if name in df.columns and "time" not in df.columns:
            time_scale = scale
    df = df.rename(columns={k: v for k, v in COLUMN_ALIASES.items() if v not in df.columns})
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Found: {', '.join(map(str, df.columns))}"
        )
    df = df[EXPECTED_COLUMNS].copy()

    if df.empty:
        raise DataValidationError("File has a header but no data rows.")

    # 2. Numeric values
    for col in EXPECTED_COLUMNS:
        numeric = pd.to_numeric(df[col], errors="coerce")
        bad = numeric.isna() & df[col].notna()
        if bad.any():
            raise DataValidationError(
                f"Non-numeric value in column '{col}' (e.g. {df[col][bad].iloc[0]!r}) "
                f"at CSV line(s): {_rows(df.index[bad])}"
            )
        df[col] = numeric

    # 3. Missing values / blank rows
    nan_mask = df.isna()
    if nan_mask.any().any():
        bad_cols = [c for c in EXPECTED_COLUMNS if nan_mask[c].any()]
        bad_rows = df.index[nan_mask.any(axis=1)]
        raise DataValidationError(
            f"Found {int(nan_mask.sum().sum())} NaN/blank value(s) in column(s) "
            f"{', '.join(bad_cols)} at CSV line(s): {_rows(bad_rows)}"
        )

    if not np.isfinite(df.to_numpy()).all():
        raise DataValidationError("All sensor values and timestamps must be finite.")

    # 4. Timestamps and sample rate
    if len(df) < 2:
        raise DataValidationError("Need at least 2 rows to check the sample rate.")
    dt = np.diff(df["time"].to_numpy()) * time_scale
    if (dt <= 0).any():
        first = int(np.argmax(dt <= 0)) + 1
        raise DataValidationError(
            f"Timestamps are not strictly increasing (first problem at CSV line {first + 2})."
        )
    median_dt = float(np.median(dt))
    rate = 1.0 / median_dt
    if abs(rate - TARGET_SAMPLE_RATE_HZ) / TARGET_SAMPLE_RATE_HZ > SAMPLE_RATE_TOLERANCE:
        raise DataValidationError(
            f"Sample rate is about {rate:.1f} Hz but expected "
            f"{TARGET_SAMPLE_RATE_HZ} Hz (+/-{SAMPLE_RATE_TOLERANCE:.0%}). "
            "Check the time units or the firmware's sample rate."
        )
    if (dt > MAX_GAP_FACTOR * median_dt).any():
        gap = int(np.argmax(dt > MAX_GAP_FACTOR * median_dt)) + 1
        raise DataValidationError(
            f"Gap in data: {dt.max():.3f} s between samples near CSV line {gap + 2} "
            f"(typical spacing is {median_dt:.3f} s). Samples were probably dropped."
        )

    # 5. Physically plausible ranges
    accel_bad = (df[["ax", "ay", "az"]].abs() > MAX_ACCEL_G).any(axis=1)
    if accel_bad.any():
        raise DataValidationError(
            f"Acceleration out of range (> {MAX_ACCEL_G} g) at CSV line(s): "
            f"{_rows(df.index[accel_bad])}. Check units or sensor range setting."
        )
    gyro_bad = (df[["gx", "gy", "gz"]].abs() > MAX_GYRO_DPS).any(axis=1)
    if gyro_bad.any():
        raise DataValidationError(
            f"Rotation rate out of range (> {MAX_GYRO_DPS} deg/s) at CSV line(s): "
            f"{_rows(df.index[gyro_bad])}. Check units or sensor range setting."
        )

    df["time"] = df["time"] * time_scale
    return df