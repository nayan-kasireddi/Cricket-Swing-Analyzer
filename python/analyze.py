"""Load, plot, and summarize IMU recordings."""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from python.ingest import load_csv  # validated loading lives in ingest.py

# --- core.py hookup: one place to swap in Nayan's version ---
# Nayan's core.py currently has empty placeholders. Set USE_CORE = True
# once his acceleration_magnitude() returns real values.
USE_CORE = False


def _standin_acceleration_magnitude(df):
    """Stand-in: sqrt(ax^2 + ay^2 + az^2)."""
    return np.sqrt(df["ax"] ** 2 + df["ay"] ** 2 + df["az"] ** 2).to_numpy()


if USE_CORE:
    from python.core import acceleration_magnitude
else:
    acceleration_magnitude = _standin_acceleration_magnitude


def rotation_magnitude(df):
    """Combined rotation rate across the three gyro axes."""
    return np.sqrt(df["gx"] ** 2 + df["gy"] ** 2 + df["gz"] ** 2).to_numpy()


def plot_acceleration(df, ax=None, title="Acceleration"):
    """Plot ax, ay, az plus the combined magnitude."""
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))
    for col in ("ax", "ay", "az"):
        ax.plot(df["time"], df[col], label=col, alpha=0.6)
    ax.plot(df["time"], acceleration_magnitude(df), label="magnitude", color="black", linewidth=1.5)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Acceleration (g)")
    ax.set_title(title)
    ax.legend(loc="upper right")
    return ax


def plot_gyro(df, ax=None, title="Rotation rate"):
    """Plot gx, gy, gz plus the combined magnitude."""
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))
    for col in ("gx", "gy", "gz"):
        ax.plot(df["time"], df[col], label=col, alpha=0.6)
    ax.plot(df["time"], rotation_magnitude(df), label="magnitude", color="black", linewidth=1.5)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Rotation rate (deg/s)")
    ax.set_title(title)
    ax.legend(loc="upper right")
    return ax


def summary_stats(df):
    """Return a dict of headline numbers for a recording."""
    acc = acceleration_magnitude(df)
    gyro = rotation_magnitude(df)
    duration = float(df["time"].iloc[-1] - df["time"].iloc[0])
    return {
        "samples": len(df),
        "duration_s": round(duration, 3),
        "sample_rate_hz": round((len(df) - 1) / duration, 1),
        "peak_accel_g": round(float(acc.max()), 3),
        "time_of_peak_accel_s": round(float(df["time"].iloc[int(acc.argmax())]), 3),
        "mean_accel_g": round(float(acc.mean()), 3),
        "peak_rotation_dps": round(float(gyro.max()), 1),
    }


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/synthetic/normal_swing.csv"
    data = load_csv(path)

    print(f"Summary for {path}")
    for key, value in summary_stats(data).items():
        print(f"  {key}: {value}")

    fig, (top, bottom) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    plot_acceleration(data, ax=top, title=f"Acceleration: {Path(path).name}")
    plot_gyro(data, ax=bottom, title="Rotation rate")
    fig.tight_layout()

    out = Path("images")
    out.mkdir(exist_ok=True)
    fig.savefig(out / f"{Path(path).stem}.png", dpi=150)
    plt.show()