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