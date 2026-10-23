"""Tests for the dashboard's HTML helpers (no Streamlit or matplotlib needed)."""
from python import ui


def test_css_has_no_unfilled_placeholders():
    css = ui.css()
    assert css.startswith("<style>") and css.endswith("</style>")
    assert "%(" not in css
    assert "100%;" in css          # escaped percent signs came through


def test_scoreboard_shows_every_cell_and_escapes_text():
    html = ui.scoreboard_html([
        {"value": 3, "label": "Swings"},
        {"value": "8.4", "unit": "g", "label": "<b>Peak</b>", "note": "a note"},
    ])
    assert html.count('class="cell"') == 2
    assert "&lt;b&gt;Peak&lt;/b&gt;" in html and "<b>Peak</b>" not in html
    assert 'class="unit">g<' in html and "a note" in html


def test_status_pill_falls_back_to_idle_for_unknown_state():
    assert 'class="pill live"' in ui.status_pill_html("live", "Streaming")
    assert 'class="pill idle"' in ui.status_pill_html("nonsense", "Hmm")


def test_scorecard_empty_state_is_an_invitation():
    html = ui.scorecard_html([])
    assert "empty" in html and "<table" not in html


def test_scorecard_rows_and_bar_widths():
    rows = [
        {"number": 1, "start": 1.26, "duration": 0.508, "peak_g": 8.0, "peak_dps": 1000.4},
        {"number": 2, "start": 3.76, "duration": 0.5, "peak_g": 4.0, "peak_dps": 800.0},
    ]
    html = ui.scorecard_html(rows)
    assert html.count("<tr>") == 3                  # one header row plus two swings
    assert "1.3 s" in html and "0.51 s" in html and "8.0 g" in html and "1000 deg/s" in html
    assert "width:100%" in html and "width:50%" in html


def test_spin_note_converts_to_turns():
    assert ui.turns_per_second(720) == 2.0
    assert ui.spin_note(1080) == "about 3.0 full turns a second"


def test_page_header_includes_optional_status():
    assert "pill" not in ui.page_header_html("Title", "Sub")
    assert 'class="pill error"' in ui.page_header_html("Title", "Sub", ("error", "Nope"))