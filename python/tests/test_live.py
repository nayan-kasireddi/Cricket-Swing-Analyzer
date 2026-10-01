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