from python.live import parse_line


def test_valid_line():
    assert parse_line("1520,0.02,-0.01,0.99,0.3,-0.2,0.1") == [1520, 0.02, -0.01, 0.99, 0.3, -0.2, 0.1]


def test_header_line_is_rejected():
    assert parse_line("time,ax,ay,az,gx,gy,gz") is None


def test_truncated_line_is_rejected():
    assert parse_line("1520,0.02,-0.01") is None


def test_boot_garbage_is_rejected():
    assert parse_line("ets Jun  8 2016 00:22:57") is None
    assert parse_line("") is None


def test_firmware_line_with_skipped_slots_is_accepted():
    assert parse_line("94754100,0.1135,-0.0537,1.0270,-0.55,1.69,0.78,0") == \
        [94754100, 0.1135, -0.0537, 1.0270, -0.55, 1.69, 0.78]


def test_firmware_header_and_comment_lines_are_rejected():
    assert parse_line("time_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,skipped_slots") is None
    assert parse_line("# MPU6050 500 Hz target | polling | +/-16g | +/-2000dps") is None


def test_stale_first_line_is_not_saved(tmp_path):
    """A stale line from before we connected must not create a huge gap in the saved CSV."""
    import time
    from python.ingest import load_csv
    from python.live import LiveStream

    class FakeBoard:
        def __init__(self):
            stale = ["1000000,0.01,0.01,1.00,0.1,0.1,0.1,0"]       # ~86 s before the live data
            live = [f"{87_000_000 + 2000 * i},0.01,0.01,1.00,0.1,0.1,0.1,0" for i in range(600)]
            self.lines = iter(stale + live)

        def readline(self):
            try:
                return next(self.lines)
            except StopIteration:
                time.sleep(0.01)
                return ""

        def close(self):
            pass

    path = tmp_path / "live.csv"
    stream = LiveStream(FakeBoard(), path, 2.5)
    stream.start()
    deadline = time.time() + 5
    while stream.total < 500 and time.time() < deadline:
        time.sleep(0.01)
    stream.stop()
    df = load_csv(path)             # raises DataValidationError if the stale line was kept
    assert len(df) >= 500
    assert df["time"].iloc[0] > 80  # started at the live data, not the stale line


def test_live_stream_logs_each_finished_swing_with_session_relative_times(tmp_path):
    import time
    from python.live import LiveStream
    from python.tests.test_swings import make_bat_swing_recording

    df = make_bat_swing_recording([1.0], duration_s=4.0)
    lines = [f"{50_000_000 + round(t * 1e6)},0,0,{az},{gx},0,0,0"
             for t, az, gx in zip(df["time"], df["az"], df["gx"])]

    class FakeBoard:
        def __init__(self):
            self.lines = iter(lines)

        def readline(self):
            try:
                return next(self.lines)
            except StopIteration:
                time.sleep(0.01)
                return ""

        def close(self):
            pass

    stream = LiveStream(FakeBoard(), tmp_path / "live.csv", 2.5)
    stream.start()
    deadline = time.time() + 10
    while stream.total < len(lines) and time.time() < deadline:
        time.sleep(0.01)
    stream.stop()
    assert len(stream.swing_log) == 1 and stream.swings == 1
    swing = stream.swing_log[0]
    assert swing["number"] == 1
    assert 0.8 < swing["start"] < 1.1          # relative to the first sample, not the board clock
    assert swing["peak_g"] > 8 and swing["peak_dps"] > 900