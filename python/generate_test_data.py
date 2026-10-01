"""Generate synthetic IMU data (stand-in for real recordings until Nayan's hardware is ready).

Units are placeholders until we agree on the CSV format with Nayan:
time in seconds, acceleration in g, rotation rate in degrees/second.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SAMPLE_RATE_HZ = 100


def make_stationary(duration_s=5.0, seed=0):
    """A bat sitting still: gravity on az (~1 g) plus small sensor noise."""
    rng = np.random.default_rng(seed)
    n = int(duration_s * SAMPLE_RATE_HZ)
    return pd.DataFrame({
        "time": np.arange(n) / SAMPLE_RATE_HZ,
        "ax": rng.normal(0, 0.02, n),
        "ay": rng.normal(0, 0.02, n),
        "az": 1.0 + rng.normal(0, 0.02, n),
        "gx": rng.normal(0, 0.5, n),
        "gy": rng.normal(0, 0.5, n),
        "gz": rng.normal(0, 0.5, n),
    })


def add_swing(df, center_s, peak_g, peak_dps, width_s=0.15):
    """Add one smooth bump of acceleration and rotation centred at center_s."""
    t = df["time"].to_numpy()
    bump = np.exp(-0.5 * ((t - center_s) / width_s) ** 2)
    df["ax"] += peak_g * bump
    df["ay"] += 0.3 * peak_g * bump
    df["gz"] += peak_dps * bump
    return df


def make_swing(duration_s=3.0, center_s=1.5, peak_g=8.0, peak_dps=1000.0,
               width_s=0.15, seed=1):
    return add_swing(make_stationary(duration_s, seed), center_s, peak_g, peak_dps, width_s)


def make_multi_swing(seed=2):
    df = make_stationary(8.0, seed)
    for center in (1.5, 4.0, 6.5):
        add_swing(df, center, peak_g=8.0, peak_dps=1000.0)
    return df


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "synthetic"
    out.mkdir(parents=True, exist_ok=True)
    make_stationary().to_csv(out / "stationary.csv", index=False)
    make_swing(peak_g=1.5, peak_dps=150.0, width_s=0.3).to_csv(out / "slow_swing.csv", index=False)
    make_swing().to_csv(out / "normal_swing.csv", index=False)
    make_multi_swing().to_csv(out / "multi_swing.csv", index=False)
    print(f"Wrote 4 CSVs to {out}")