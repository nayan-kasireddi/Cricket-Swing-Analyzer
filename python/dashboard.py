"""Streamlit dashboard for swing recordings.  Run from the project root:

    python -m streamlit run python/dashboard.py
"""
import sys
from pathlib import Path

# Make "from python.xxx import ..." work no matter how Streamlit launches this file.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import streamlit as st

from python.analyze import plot_acceleration, plot_gyro
from python.ingest import DataValidationError, load_csv
from python.swings import DEFAULT_THRESHOLD_G, detect_swings, summarize_swings

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PREFERRED_FILE = "synthetic/multi_swing.csv"   # opens first if it exists

st.set_page_config(page_title="Cricket Swing Analyzer", layout="wide")
st.title("Cricket Swing Analyzer")

# --- Sidebar: choose a recording and a swing threshold ---------------------------
files = sorted(DATA_DIR.glob("**/*.csv"))
if not files:
    st.error(f"No CSV files found under {DATA_DIR}")
    st.stop()

labels = [f.relative_to(DATA_DIR).as_posix() for f in files]
default_index = labels.index(PREFERRED_FILE) if PREFERRED_FILE in labels else 0
choice = st.sidebar.selectbox("Recording", labels, index=default_index)
threshold = st.sidebar.slider(
    "Swing threshold (g)", min_value=1.0, max_value=12.0,
    value=float(DEFAULT_THRESHOLD_G), step=0.1,
    help="A swing starts when acceleration magnitude rises above this value.",
)

try:
    df = load_csv(DATA_DIR / choice)
except DataValidationError as e:
    st.error(f"Could not load {choice}: {e}")
    st.stop()

swings = detect_swings(df, threshold)

st.caption(f"{choice}: {len(df):,} samples over {df['time'].iloc[-1]:.2f} s")
st.metric("Swings detected", len(swings))


def shade_swings(ax):
    """Shade each detected swing on a plot."""
    for start, end in swings:
        ax.axvspan(start, end, color="tab:orange", alpha=0.2)


# --- Plots ------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 3.5))
plot_acceleration(df, ax=ax, title="Acceleration")
ax.axhline(threshold, color="red", linestyle="--", linewidth=1, label=f"threshold ({threshold:.1f} g)")
ax.legend(loc="upper right")
shade_swings(ax)
st.pyplot(fig)

fig, ax = plt.subplots(figsize=(11, 3.5))
plot_gyro(df, ax=ax, title="Rotation rate")
shade_swings(ax)
st.pyplot(fig)

# --- Swing summary table ----------------------------------------------------------
st.subheader("Swing summary")
if swings:
    summary = summarize_swings(df, swings)
    st.dataframe(
        summary,
        hide_index=True,
        use_container_width=True,
        column_config={
            "swing": "Swing #",
            "start_s": "Start (s)",
            "end_s": "End (s)",
            "duration_s": "Duration (s)",
            "peak_accel_g": "Peak accel (g)",
            "peak_rotation_dps": "Peak rotation (deg/s)",
        },
    )
else:
    st.info("No swings detected at this threshold. Try lowering it with the sidebar slider.")

# --- Swing detail view ------------------------------------------------------------
if swings:
    st.subheader("Swing detail")
    number = st.selectbox("Swing to inspect", range(1, len(swings) + 1))
    start, end = swings[number - 1]
    row = summary.iloc[number - 1]

    c1, c2, c3 = st.columns(3)
    c1.metric("Duration", f"{row['duration_s']:.3f} s")
    c2.metric("Peak acceleration", f"{row['peak_accel_g']:.2f} g")
    c3.metric("Peak rotation", f"{row['peak_rotation_dps']:.0f} deg/s")

    pad = max(0.3, (end - start) * 0.5)           # show some context before and after
    window = df[(df["time"] >= start - pad) & (df["time"] <= end + pad)]

    left, right = st.columns(2)
    with left:
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        plot_acceleration(window, ax=ax, title=f"Swing {number}: acceleration")
        ax.axvspan(start, end, color="tab:orange", alpha=0.2)
        st.pyplot(fig)
    with right:
        fig, ax = plt.subplots(figsize=(5.5, 3.5))
        plot_gyro(window, ax=ax, title=f"Swing {number}: rotation rate")
        ax.axvspan(start, end, color="tab:orange", alpha=0.2)
        st.pyplot(fig)