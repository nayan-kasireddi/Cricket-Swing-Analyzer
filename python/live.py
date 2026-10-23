"""Live viewer and recorder for streaming IMU data.

The Pico firmware (pico2w_mpu6050.ino) prints one line per sample over Serial:

    time_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,skipped_slots

e.g.  94754100,0.1135,-0.0537,1.0270,-0.55,1.69,0.78,0

Lines starting with "#" (startup banner, I2C error notes) are ignored. The recording is
saved with the header "time_us,ax,ay,az,gx,gy,gz" (skipped_slots is dropped).

Run from the project root:
    python -m python.live --sim                        # fake sensor, no hardware needed
    python -m python.live --list-ports                 # find the board's port
    python -m python.live --port /dev/cu.usbmodemXXXX   # use --list-ports to find it

Close the plot window to stop. Everything received is saved to data/live/*.csv
with time in microseconds; load_csv() converts it to seconds.
"""
import argparse
import math
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from python.generate_test_data import make_multi_swing
from python.ingest import EXPECTED_COLUMNS
from python.swings import DEFAULT_THRESHOLD_G, SwingTracker

SERIAL_TIME_TO_SECONDS = 1e-6   # the firmware reports time in microseconds
WARMUP_MAX_STEP_US = 50_000     # two lines closer than this (50 ms) count as live, continuous data

BAUD_RATE = 115200
WINDOW_SECONDS = 5.0        # how much history the live graph shows


def parse_line(line):
    """Turn 'time,ax,ay,az,gx,gy,gz[,skipped_slots]' into a list of 7 floats, or None if invalid."""
    parts = line.strip().split(",")
    if len(parts) not in (len(EXPECTED_COLUMNS), len(EXPECTED_COLUMNS) + 1):
        return None
    parts = parts[:len(EXPECTED_COLUMNS)]
    try:
        row = [float(p) for p in parts]
        return row if all(math.isfinite(value) for value in row) else None
    except ValueError:
        return None


class SerialSource:
    """Real sensor: reads lines from the board over USB."""

    def __init__(self, port, baud=BAUD_RATE):
        import serial  # imported here so --sim works without pyserial installed
        self.ser = serial.Serial(port, baud, timeout=1)
        self.ser.reset_input_buffer()

    def readline(self):
        return self.ser.readline().decode("utf-8", errors="replace").strip()

    def close(self):
        self.ser.close()


class SimulatedSource:
    """Fake sensor: replays the synthetic multi-swing recording in a loop at 500 Hz."""

    def __init__(self, rate_hz=500):
        self.rows = make_multi_swing()[EXPECTED_COLUMNS].to_numpy()
        self.dt = 1.0 / rate_hz
        self.period = len(self.rows) * self.dt
        self.i = 0
        self.loop = 0
        self.next_t = time.perf_counter()

    def readline(self):
        self.next_t += self.dt
        delay = self.next_t - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
        row = self.rows[self.i]
        t = row[0] + self.loop * self.period
        values = [t / SERIAL_TIME_TO_SECONDS] + list(row[1:])   # microseconds, like real firmware
        self.i += 1
        if self.i == len(self.rows):
            self.i, self.loop = 0, self.loop + 1
        return ",".join(f"{v:.4f}" for v in values)

    def close(self):
        pass


class LiveStream:
    """Reads samples on a background thread, saves them, and keeps a rolling buffer for plotting."""

    def __init__(self, source, csv_path, threshold_g=DEFAULT_THRESHOLD_G):
        self.source = source
        self.csv_path = Path(csv_path)
        self.threshold = threshold_g
        self.samples = deque(maxlen=5000)       # (time_s, accel_mag, gyro_mag)
        self.lock = threading.Lock()
        self.total = 0
        self.bad_lines = 0
        self.swings = 0
        self.last_swing = ""
        self.error = None
        self.tracker = SwingTracker(threshold_g)
        self.t0 = None              # board clock at the first saved sample
        self.swing_log = []         # one dict per finished swing, times relative to session start
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2)

    def snapshot(self):
        with self.lock:
            return np.array(self.samples)

    def _run(self):
        try:
            prev_us = None      # warm-up: skip stale lines the board had buffered before we connected
            started = False
            with open(self.csv_path, "w") as f:
                f.write(",".join(["time_us"] + EXPECTED_COLUMNS[1:]) + "\n")
                while not self._stop.is_set():
                    line = self.source.readline()
                    if not line:
                        continue
                    row = parse_line(line)
                    if row is None:     # boot messages, partial lines, debug prints
                        if not line.startswith("#") and not line.lower().startswith(EXPECTED_COLUMNS[0]):
                            self.bad_lines += 1
                        continue
                    if not started:
                        # The first line(s) after connecting can be old (the board kept streaming
                        # before anyone was listening). Start once two lines in a row are close in time.
                        if prev_us is not None and 0 < row[0] - prev_us < WARMUP_MAX_STEP_US:
                            started = True
                        prev_us = row[0]
                        if not started:
                            continue
                    f.write(",".join(line.strip().split(",")[:len(EXPECTED_COLUMNS)]) + "\n")
                    self._handle(row)
                    if self.total % 100 == 0:
                        f.flush()
        except Exception as e:      # e.g. USB cable unplugged
            self.error = e

    def _handle(self, row):
        t = row[0] * SERIAL_TIME_TO_SECONDS
        acc = float(np.sqrt(row[1] ** 2 + row[2] ** 2 + row[3] ** 2))
        gyro = float(np.sqrt(row[4] ** 2 + row[5] ** 2 + row[6] ** 2))
        if self.t0 is None:
            self.t0 = t
        with self.lock:
            self.samples.append((t, acc, gyro))
            self.total += 1

        # Same swing logic as the Recordings detector (see swings.py): a swing stays "active"
        # while acceleration is high OR the bat is still rotating, so one swing counts once.
        self.tracker.threshold_g = self.threshold      # follows the slider
        done = self.tracker.update(t, acc, gyro)
        if done:
            self.swings += 1
            self.swing_log.append({
                "number": self.swings,
                "start": done["start"] - self.t0,
                "duration": done["end"] - done["start"],
                "peak_g": done["peak_g"],
                "peak_dps": done["peak_dps"],
            })
            self.last_swing = (f"swing {self.swings}: peak {done['peak_g']:.1f} g, "
                               f"{done['peak_dps']:.0f} deg/s, {done['end'] - done['start']:.2f} s")
            print(self.last_swing)


def run_live_plot(stream, window_s=WINDOW_SECONDS):
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    (acc_line,) = top.plot([], [], color="black")
    top.axhline(stream.threshold, color="red", linestyle="--",
                label=f"threshold ({stream.threshold} g)")
    top.set_ylabel("Acceleration magnitude (g)")
    top.legend(loc="upper left")
    (gyro_line,) = bottom.plot([], [], color="tab:blue")
    bottom.set_ylabel("Rotation rate magnitude (deg/s)")
    bottom.set_xlabel("Time (s)")
    status = top.text(0.99, 0.95, "", transform=top.transAxes, ha="right", va="top",
                      family="monospace")

    def update(_):
        data = stream.snapshot()
        if data.size == 0:
            return
        t, acc, gyro = data[:, 0], data[:, 1], data[:, 2]
        keep = t >= t[-1] - window_s
        t, acc, gyro = t[keep], acc[keep], gyro[keep]
        acc_line.set_data(t, acc)
        gyro_line.set_data(t, gyro)
        top.set_xlim(t[-1] - window_s, t[-1])
        top.set_ylim(0, max(4.0, stream.threshold * 1.5, acc.max() * 1.1))
        bottom.set_ylim(0, max(300.0, gyro.max() * 1.1))
        rate = (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 and t[-1] > t[0] else 0.0
        status.set_text(f"{rate:5.1f} Hz | swings: {stream.swings} | bad lines: {stream.bad_lines}")
        if stream.error:
            fig.suptitle(f"Stream stopped: {stream.error}", color="red")
        else:
            fig.suptitle(stream.last_swing or "Waiting for a swing...")

    anim = FuncAnimation(fig, update, interval=50, cache_frame_data=False)  # keep reference
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    plt.show()
    return anim


def main():
    ap = argparse.ArgumentParser(description="Live IMU viewer and recorder")
    ap.add_argument("--sim", action="store_true", help="use a simulated sensor")
    ap.add_argument("--port", help="serial port of the board")
    ap.add_argument("--baud", type=int, default=BAUD_RATE)
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD_G)
    ap.add_argument("--out", help="CSV path (default: data/live/live_<timestamp>.csv)")
    ap.add_argument("--list-ports", action="store_true", help="list serial ports and exit")
    args = ap.parse_args()

    if args.list_ports:
        from serial.tools import list_ports
        for p in list_ports.comports():
            print(f"{p.device} - {p.description}")
        return

    if args.sim:
        source = SimulatedSource()
    elif args.port:
        source = SerialSource(args.port, args.baud)
    else:
        ap.error("give --port PORT or --sim (use --list-ports to find the port)")

    out = Path(args.out) if args.out else Path("data/live") / f"live_{datetime.now():%Y%m%d_%H%M%S}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    stream = LiveStream(source, out, args.threshold)
    stream.start()
    try:
        run_live_plot(stream)
    finally:
        stream.stop()
        source.close()
    print(f"\nSaved {stream.total} samples to {out}")
    print(f"Check it with: python -m python.analyze {out}")


if __name__ == "__main__":
    main()