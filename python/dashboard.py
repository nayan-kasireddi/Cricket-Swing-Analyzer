"""Cricket Swing Analyzer dashboard.

Run from the project root (so Streamlit picks up .streamlit/config.toml):

    python -m streamlit run python/dashboard.py

Pages (sidebar):
  Live   - read the board over USB, see force and spin as you swing, save a recording
  Review - open a saved recording, see each swing, and zoom into one
"""
import sys
from datetime import datetime
from pathlib import Path

# Make "from python.xxx import ..." work no matter how Streamlit launches this file.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import streamlit as st

from python import ui
from python.analyze import acceleration_magnitude, rotation_magnitude
from python.ingest import DataValidationError, load_csv
from python.live import WINDOW_SECONDS, LiveStream, SerialSource
from python.swings import DEFAULT_THRESHOLD_G, detect_swings, summarize_swings

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PREFERRED_FILE = "synthetic/multi_swing.csv"   # opens first on the Review page if it exists
EXPECTED_RATE_HZ = 500
SENSOR_LIMIT_G = 15.9          # the MPU6050 is set to +/-16 g
SENSOR_LIMIT_DPS = 1990.0      # and +/-2000 deg/s

st.set_page_config(page_title="Cricket Swing Analyzer", page_icon="🏏", layout="wide")
st.markdown(ui.css(), unsafe_allow_html=True)


def show_chart(fig):
    st.pyplot(fig)
    plt.close(fig)


def explainer():
    with st.expander("How to read these charts"):
        st.markdown(
            "**Force on the bat** shows how hard the sensor is pushed or pulled, in g. "
            "1 g is normal gravity, so a sensor lying still reads about 1 g.\n\n"
            "**Bat spin** shows how fast the bat turns, in degrees a second. "
            "360 deg/s is one full turn every second.\n\n"
            "**Swing trigger** is the red dashed line. A swing starts when the force goes above it. "
            "It ends once the bat has been calm for a moment, so one swing counts once."
        )


# =====================================================================================
# Live page
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
        st.markdown(ui.status_pill_html("error", "Connection lost"), unsafe_allow_html=True)
        st.error(f"The board stopped sending data ({stream.error}). "
                 "Click Stop and save, check the USB cable, then start again.")
    data = stream.snapshot()
    if data.size == 0:
        st.markdown(ui.status_pill_html("warn", "Connected, waiting for data"), unsafe_allow_html=True)
        return

    t, acc, gyro = data[:, 0], data[:, 1], data[:, 2]
    keep = t >= t[-1] - WINDOW_SECONDS
    t, acc, gyro = t[keep], acc[keep], gyro[keep]
    rate = (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 and t[-1] > t[0] else 0.0

    if stream.error:
        pass
    elif rate and rate < 0.8 * EXPECTED_RATE_HZ:
        st.markdown(ui.status_pill_html("warn", f"Streaming at {rate:.0f} Hz, expected {EXPECTED_RATE_HZ}"),
                    unsafe_allow_html=True)
    else:
        st.markdown(ui.status_pill_html("live", f"Streaming at {rate:.0f} Hz"), unsafe_allow_html=True)

    log = list(stream.swing_log)
    last = log[-1] if log else None
    st.markdown(ui.scoreboard_html([
        {"value": len(log), "label": "Swings this session"},
        {"value": f"{last['peak_g']:.1f}" if last else "–", "unit": "g", "label": "Last swing, peak force"},
        {"value": f"{last['peak_dps']:.0f}" if last else "–", "unit": "deg/s", "label": "Last swing, peak spin",
         "note": ui.spin_note(last["peak_dps"]) if last else None},
        {"value": f"{last['duration']:.2f}" if last else "–", "unit": "s", "label": "Last swing, time"},
    ]), unsafe_allow_html=True)

    x = t - t[-1]                                   # seconds ago, so "now" is always 0
    fig, (top, bottom) = ui.new_figure(2, height=5.2)
    ui.draw_force(top, x, acc, stream.threshold)
    top.set_ylim(0, max(4.0, stream.threshold * 1.5, float(acc.max()) * 1.1))
    ui.draw_spin(bottom, x, gyro)
    bottom.set_ylim(0, max(300.0, float(gyro.max()) * 1.1))
    bottom.set_xlim(-WINDOW_SECONDS, 0)
    bottom.set_xlabel("Seconds ago")
    fig.tight_layout()
    show_chart(fig)

    st.markdown(ui.section_title_html("Swings this session"), unsafe_allow_html=True)
    st.markdown(ui.scorecard_html(log), unsafe_allow_html=True)
    st.caption(f"Recording to {Path(stream.csv_path).name}, {stream.total:,} samples saved, "
               f"{stream.bad_lines} unreadable lines.")


def render_live():
    from serial.tools import list_ports

    running = "live_stream" in st.session_state
    ports = [p.device for p in list_ports.comports()]

    st.markdown(ui.page_header_html(
        "Live swings",
        "Move the sensor and watch the force and spin as they happen. Each swing is counted and logged below.",
    ), unsafe_allow_html=True)

    port = st.sidebar.selectbox("Sensor port", ports, disabled=running or not ports)
    st.sidebar.slider(
        "Swing trigger (g)", min_value=1.0, max_value=12.0, value=1.5, step=0.1, key="live_threshold",
        help="Lower catches gentle swings. Higher ignores small bumps. A hand wave is gentler than a bat swing, so start low.",
    )

    if not ports:
        st.markdown(ui.status_pill_html("error", "No sensor found"), unsafe_allow_html=True)
        st.warning("Plug the board in with a data USB cable, then refresh this page. "
                   "Close the Arduino Serial Monitor if it is open, because it blocks the port.")
        return

    if not running:
        if st.sidebar.button("Start live view", type="primary"):
            try:
                source = SerialSource(port)
            except Exception as e:
                st.error(f"Could not open {port}: {e}. Close any program using the port and try again.")
                return
            out = DATA_DIR / "live" / f"live_{datetime.now():%Y%m%d_%H%M%S}.csv"
            out.parent.mkdir(parents=True, exist_ok=True)
            stream = LiveStream(source, out, st.session_state["live_threshold"])
            stream.start()
            st.session_state["live_source"] = source
            st.session_state["live_stream"] = stream
            st.session_state.pop("last_live_file", None)
            st.rerun()
        st.markdown(ui.status_pill_html("idle", "Ready"), unsafe_allow_html=True)
        last = st.session_state.get("last_live_file")
        if last:
            st.success(f"Saved {last[1]:,} samples to {Path(last[0]).name}. "
                       "Open the Review page to look at it.")
        else:
            st.markdown(ui.empty_html("Press Start live view in the sidebar, then move the sensor."),
                        unsafe_allow_html=True)
    else:
        if st.sidebar.button("Stop and save"):
            stream = st.session_state["live_stream"]
            st.session_state["last_live_file"] = (stream.csv_path, stream.total)
            stop_live()
            st.rerun()
        live_panel()
    explainer()


# =====================================================================================
# Review page
# =====================================================================================
def render_review():
    st.markdown(ui.page_header_html(
        "Review swings",
        "Open a saved recording to see every swing in it, then zoom into one.",
    ), unsafe_allow_html=True)

    files = sorted(DATA_DIR.glob("**/*.csv"))
    if not files:
        st.markdown(ui.empty_html("No recordings found. Use the Live page to record one."),
                    unsafe_allow_html=True)
        return

    labels = [f.relative_to(DATA_DIR).as_posix() for f in files]
    default_index = labels.index(PREFERRED_FILE) if PREFERRED_FILE in labels else 0
    choice = st.sidebar.selectbox("Recording", labels, index=default_index)
    threshold = st.sidebar.slider(
        "Swing trigger (g)", min_value=1.0, max_value=12.0, value=float(DEFAULT_THRESHOLD_G), step=0.1,
        help="A swing starts when the force on the bat goes above this value.",
    )

    try:
        df = load_csv(DATA_DIR / choice)
    except DataValidationError as e:
        st.error(f"Could not open {choice}: {e} Pick another recording in the sidebar.")
        return

    df["time"] = df["time"] - df["time"].iloc[0]
    acc = acceleration_magnitude(df)
    gyro = rotation_magnitude(df)
    t = df["time"].to_numpy()
    swings = detect_swings(df, threshold)
    summary = summarize_swings(df, swings) if swings else None

    clipped = (df[["ax", "ay", "az"]].abs().to_numpy().max() >= SENSOR_LIMIT_G
               or df[["gx", "gy", "gz"]].abs().to_numpy().max() >= SENSOR_LIMIT_DPS)
    if clipped:
        st.warning("The sensor hit its measurement limit in this recording, so the biggest peaks "
                   "may read lower than they really were.")

    st.caption(f"{choice}: {len(df):,} samples over {t[-1]:.1f} seconds.")

    if summary is not None:
        fastest = float(summary["peak_rotation_dps"].max())
        cells = [
            {"value": len(swings), "label": "Swings found"},
            {"value": f"{summary['peak_accel_g'].max():.1f}", "unit": "g", "label": "Strongest swing, peak force"},
            {"value": f"{fastest:.0f}", "unit": "deg/s", "label": "Fastest spin", "note": ui.spin_note(fastest)},
            {"value": f"{summary['duration_s'].mean():.2f}", "unit": "s", "label": "Average swing time"},
        ]
    else:
        cells = [
            {"value": 0, "label": "Swings found"},
            {"value": "–", "unit": "g", "label": "Strongest swing, peak force"},
            {"value": "–", "unit": "deg/s", "label": "Fastest spin"},
            {"value": "–", "unit": "s", "label": "Average swing time"},
        ]
    st.markdown(ui.scoreboard_html(cells), unsafe_allow_html=True)

    fig, axes = ui.new_figure(2, height=5.2)
    ui.draw_force(axes[0], t, acc, threshold)
    ui.draw_spin(axes[1], t, gyro)
    ui.shade_swings(axes, swings)
    axes[1].set_xlabel("Seconds into the recording")
    fig.tight_layout()
    show_chart(fig)

    st.markdown(ui.section_title_html("Swings"), unsafe_allow_html=True)
    if summary is None:
        st.markdown(ui.empty_html("No swings found at this trigger. Lower it with the slider in the sidebar."),
                    unsafe_allow_html=True)
        explainer()
        return
    rows = [{"number": r.swing, "start": r.start_s, "duration": r.duration_s,
             "peak_g": r.peak_accel_g, "peak_dps": r.peak_rotation_dps}
            for r in summary.itertuples(index=False)]
    st.markdown(ui.scorecard_html(rows), unsafe_allow_html=True)

    st.markdown(ui.section_title_html("Look at one swing"), unsafe_allow_html=True)
    numbers = list(range(1, len(swings) + 1))
    if len(numbers) <= 10:
        picked = st.segmented_control("Swing", numbers, default=1, format_func=lambda n: f"Swing {n}")
    else:
        picked = st.selectbox("Swing", numbers, format_func=lambda n: f"Swing {n}")
    number = picked or 1
    start, end = swings[number - 1]
    pad = max(0.3, (end - start) * 0.5)             # show some calm before and after
    mask = (t >= start - pad) & (t <= end + pad)
    wt, wacc, wgyro = t[mask], acc[mask], gyro[mask]

    fig, axes = ui.new_figure(2, height=4.8)
    ui.draw_force(axes[0], wt, wacc)
    ui.draw_spin(axes[1], wt, wgyro)
    ui.shade_swings(axes, [(start, end)])
    peak = int(wacc.argmax())
    axes[0].plot(wt[peak], wacc[peak], "o", color=ui.BALL, markersize=6)
    axes[0].annotate(f"{wacc[peak]:.1f} g", xy=(wt[peak], wacc[peak]), xytext=(8, 0),
                     textcoords="offset points", color=ui.BALL, fontsize=10, va="center")
    axes[1].set_xlabel("Seconds into the recording")
    fig.tight_layout()
    show_chart(fig)
    explainer()


# =====================================================================================
# Navigation
# =====================================================================================
st.sidebar.markdown("### Cricket Swing Analyzer")
page = st.sidebar.radio("Page", ["Live", "Review"], label_visibility="collapsed")
if page == "Live":
    render_live()
else:
    stop_live()          # leaving the Live page releases the USB port
    render_review()