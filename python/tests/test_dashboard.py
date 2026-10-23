"""Exercise the dashboard without a browser or physical sensor."""
from streamlit.testing.v1 import AppTest


def test_review_recordings():
    app = AppTest.from_file('../dashboard.py', default_timeout=45).run()
    app.sidebar.radio[0].set_value('Review').run()
    assert not app.exception and not app.error
    assert any('Swings found' in item.value and '>3<' in item.value for item in app.markdown)
    app.sidebar.selectbox[0].select('synthetic/stationary.csv').run()
    assert not app.exception and not app.error
    assert any('Swings found' in item.value and '>0<' in item.value for item in app.markdown)


def test_linux_pico_port_is_selectable(monkeypatch):
    from types import SimpleNamespace
    from serial.tools import list_ports
    monkeypatch.setattr(list_ports, 'comports', lambda: [SimpleNamespace(device='/dev/ttyACM0')])
    app = AppTest.from_file('../dashboard.py', default_timeout=45).run()
    assert not app.exception
    assert app.sidebar.selectbox[0].options == ['/dev/ttyACM0']


def test_review_duration_excludes_board_uptime(monkeypatch):
    from python import ingest
    from python.generate_test_data import make_multi_swing
    recording = make_multi_swing()
    recording['time'] += 80
    monkeypatch.setattr(ingest, 'load_csv', lambda path: recording.copy())
    app = AppTest.from_file('../dashboard.py', default_timeout=45).run()
    app.sidebar.radio[0].set_value('Review').run()
    assert not app.exception and not app.error
    assert '8.0 seconds' in app.caption[0].value
