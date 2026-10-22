"""Streamlit dashboard for swing recordings and live sensor data.

Run from the project root:

    python -m streamlit run python/dashboard.py

Modes (sidebar):
  Recordings - browse saved CSVs, tune the swing threshold, inspect each swing
  Live view  - read the board over USB, graph it live, and save a recording
"""
import sys
from datetime import datetime
from pathlib import Path

# Make "from python.xxx import ..." work no matter how Streamlit launches this file.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import streamlit as st

from python.analyze import plot_acceleration, plot_gyro
from python.ingest import DataValidationError, load_csv
from python.live import WINDOW_SECONDS, LiveStream, SerialSource
from python.swings import DEFAULT_THRESHOLD_G, detect_swings, summarize_swings

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PREFERRED_FILE = "synthetic/multi_swing.csv"   # opens first in Recordings mode if it exists

st.set_page_config(page_title="Cricket Swing Analyzer", layout="wide")
st.title("Cricket Swing Analyzer")


# =====================================================================================
# Live view
# =====================================================================================
def stop_live():
    """Stop the background reader and release the USB port."""
    stream = st.session_state.pop("live_stream", None)
    source = st.session_state.pop("live_source", None)
    if stream is not None:
        stream.stop()
    if source is not None:
        source.close()


@st.fragment(run_every=0.3)
def live_panel():
    """Redraws every 0.3 s without rerunning the whole page."""
    stream = st.session_state.get("live_stream")
    if stream is None:
        return
    stream.threshold = st.session_state.get("live_threshold", DEFAULT_THRESHOLD_G)

    if stream.error:
        st.error(f"Stream stopped: {stream.error}. Press 'Stop and save', check the cable, and start again.")
    data = stream.snapshot()
    if data.size == 0:
        st.info("Connected. Waiting for data...")
        return

    t, acc, gyro = data[:, 0], data[:, 1], data[:, 2]
    keep = t >= t[-1] - WINDOW_SECONDS
    t, acc, gyro = t[keep], acc[keep], gyro[keep]
    rate = (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 and t[-1] > t[0] else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sample rate", f"{rate:.0f} Hz")
    c2.metric("Swings this session", stream.swings)
    c3.metric("Bad lines", stream.bad_lines)
    c4.metric("Samples saved", f"{stream.total:,}")
    st.write(f"**{stream.last_swing or 'Waiting for a swing...'}**")

    fig, (top, bottom) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    top.plot(t, acc, color="black")
    top.axhline(stream.threshold, color="red", linestyle="--",
                label=f"threshold ({stream.threshold:.1f} g)")
    top.set_xlim(t[-1] - WINDOW_SECONDS, t[-1])
    top.set_ylim(0, max(4.0, stream.threshold * 1.5, acc.max() * 1.1))
    top.set_ylabel("Acceleration magnitude (g)")
    top.legend(loc="upper left")
    bottom.plot(t, gyro, color="tab:blue")
    bottom.set_ylim(0, max(300.0, gyro.max() * 1.1))
    bottom.set_ylabel("Rotation rate (deg/s)")
    bottom.set_xlabel("Time (s)")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def render_live():
    from serial.tools import list_ports

    running = "live_stream" in st.session_state
    ports = [p.device for p in list_ports.comports() if "usb" in p.device.lower()]

    port = st.sidebar.selectbox("Serial port", ports, disabled=running or not ports)
    st.sidebar.slider(
        "Swing threshold (g)", min_value=1.0, max_value=12.0, value=1.5, step=0.1,
        key="live_threshold",
        help="A hand wave is gentler than a bat swing, so start low.",
    )

    if not ports:
        st.warning("No USB serial port found. Plug the board in with a data cable "
                   "and make sure no other program (Arduino Serial Monitor, miniterm) is using it.")
        return

    if not running:
        if st.sidebar.button("Start live view", type="primary"):
            try:
                source = SerialSource(port)
            except Exception as e:
                st.error(f"Could not open {port}: {e}")
                return
            out = DATA_DIR / "live" / f"live_{datetime.now():%Y%m%d_%H%M%S}.csv"
            out.parent.mkdir(parents=True, exist_ok=True)
            stream = LiveStream(source, out, st.session_state["live_threshold"])
            stream.start()
            st.session_state["live_source"] = source
            st.session_state["live_stream"] = stream
            st.session_state.pop("last_live_file", None)
            st.rerun()
        last = st.session_state.get("last_live_file")
        if last:
            st.success(f"Saved {last[1]:,} samples to {last[0]}. "
                       "Switch to Recordings mode to inspect it.")
        else:
            st.info("Press **Start live view** in the sidebar, then move the sensor.")
    else:
        if st.sidebar.button("Stop and save"):
            stream = st.session_state["live_stream"]
            st.session_state["last_live_file"] = (stream.csv_path, stream.total)
            stop_live()
            st.rerun()
        live_panel()


mode = st.sidebar.radio("Mode", ["Recordings", "Live view"])
if mode != "Live view":
    stop_live()          # leaving live mode releases the USB port
else:
    render_live()
    st.stop()


# =====================================================================================
# Recordings
# =====================================================================================
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