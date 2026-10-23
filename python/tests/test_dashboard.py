"""Exercise the dashboard without a browser or physical sensor."""
import pytest

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
    assert app.selectbox[0].options == ['/dev/ttyACM0']


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


def test_sensor_discovery_updates_after_hotplug(monkeypatch):
    from types import SimpleNamespace
    from serial.tools import list_ports
    devices = []
    monkeypatch.setattr(list_ports, 'comports', lambda: list(devices))
    app = AppTest.from_file('../dashboard.py', default_timeout=45).run()
    assert app.selectbox[0].disabled
    devices.append(SimpleNamespace(device='/dev/ttyACM0'))
    app.run()
    assert not app.exception
    assert app.selectbox[0].options == ['/dev/ttyACM0']
    assert not app.selectbox[0].disabled
    assert app.selectbox[0].value == '/dev/ttyACM0'
    devices.clear()
    app.run()
    assert app.selectbox[0].disabled


@pytest.mark.parametrize("failure", ["unplugged", "silent", "error"])
def test_disconnection_stops_and_preserves_session(monkeypatch, tmp_path, failure):
    from serial.tools import list_ports
    from types import SimpleNamespace
    import time
    ports = [] if failure == 'unplugged' else [SimpleNamespace(device='/dev/ttyACM0')]
    monkeypatch.setattr(list_ports, 'comports', lambda: ports)
    stopped, closed = [], []
    recording = tmp_path / 'session.csv'
    recording.write_text('time_us,ax,ay,az,gx,gy,gz\n')
    app = AppTest.from_file('../dashboard.py', default_timeout=45)
    app.session_state['live_stream'] = SimpleNamespace(
        last_sample_at=time.monotonic() - (10 if failure == "silent" else 0),
        error=OSError("Disconnected") if failure == "error" else None,
        csv_path=recording, total=50,
        stop=lambda: stopped.append(True))
    app.session_state['live_source'] = SimpleNamespace(close=lambda: closed.append(True))
    app.session_state['active_port'] = '/dev/ttyACM0'
    app.run()
    assert not app.exception
    assert stopped and closed
    assert app.session_state['last_live_file'] == (recording, 50)
    assert 'reconnect' in app.warning[0].value.lower()


def test_start_error_remains_visible_across_polling(monkeypatch):
    from serial.tools import list_ports
    from types import SimpleNamespace
    from python import live
    monkeypatch.setattr(list_ports, 'comports', lambda: [SimpleNamespace(device='/dev/ttyACM0')])
    def unavailable(port):
        raise OSError('Port is busy')
    monkeypatch.setattr(live, 'SerialSource', unavailable)
    app = AppTest.from_file('../dashboard.py', default_timeout=45).run()
    app.button[0].click().run()
    assert not app.exception
    assert 'Port is busy' in app.error[0].value
    app.run()
    assert 'Port is busy' in app.error[0].value
