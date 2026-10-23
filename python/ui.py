"""Look and feel for the dashboard: colors, CSS, HTML builders and chart styling.

The HTML builders are plain functions (no Streamlit needed) so they can be tested.
The palette comes from the game itself: turf green, crease-line white, ball red, willow.
"""
from html import escape

# --- Palette ----------------------------------------------------------------------
TURF = "#0F3D24"        # deep green: scoreboard and sidebar
OUTFIELD = "#1F6B3A"    # mid green: main accent
CHALK = "#F3F5EF"       # page background, like painted crease lines
INK = "#17231C"         # text
MUTED = "#5B6B61"       # secondary text
BALL = "#C8312B"        # ball red: trigger line, peak markers, errors
WILLOW = "#D9B26B"      # bat tan: swing highlights, warnings
SKY = "#2F6F8F"         # second data series (spin)

FONT_STACK = "'Barlow', 'Helvetica Neue', Arial, sans-serif"
DISPLAY_STACK = "'Barlow Condensed', 'Arial Narrow', 'Helvetica Neue', Arial, sans-serif"

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600;700&display=swap');

.stApp, .stApp p, .stApp label, .stApp li, .stApp button, .stApp input { font-family: %(font)s; }
.block-container { padding-top: 2.2rem; max-width: 1180px; }
footer { visibility: hidden; }

.header-row { display: flex; align-items: flex-end; justify-content: space-between;
              gap: 1rem; flex-wrap: wrap; margin-bottom: .25rem; }
.page-title { font-family: %(display)s; font-weight: 600; font-size: 2.8rem; line-height: 1.05;
              color: %(ink)s; margin: 0; }
.page-sub { color: %(muted)s; font-size: 1.05rem; margin: .35rem 0 0; max-width: 62ch; }

.pill { display: inline-flex; align-items: center; gap: .5rem; padding: .3rem .85rem;
        border-radius: 999px; font-size: .92rem; font-weight: 500; background: #E1E8DD; color: %(ink)s; }
.pill .dot { width: .6rem; height: .6rem; border-radius: 50%%; background: %(muted)s; }
.pill.live .dot { background: %(outfield)s; }
.pill.warn { background: #F3E6C8; }
.pill.warn .dot { background: %(willow)s; }
.pill.error { background: #F6DAD7; }
.pill.error .dot { background: %(ball)s; }

.scoreboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
              gap: 1px; background: rgba(243, 245, 239, .18); border-radius: 12px;
              overflow: hidden; margin: 1.1rem 0 1.6rem; }
.scoreboard .cell { background: %(turf)s; color: %(chalk)s; padding: 1.1rem 1.4rem 1.2rem; }
.scoreboard .num { font-family: %(display)s; font-weight: 600; font-size: 3.4rem; line-height: 1;
                   font-variant-numeric: tabular-nums; }
.scoreboard .unit { font-size: 1.1rem; font-weight: 500; margin-left: .35rem; color: #B9CDBF; }
.scoreboard .label { margin-top: .4rem; font-size: .98rem; color: #D2E2D7; }
.scoreboard .note { margin-top: .15rem; font-size: .86rem; color: #A3BDAB; }

.section-title { font-family: %(display)s; font-weight: 600; font-size: 1.6rem; color: %(ink)s;
                 margin: 1.8rem 0 .6rem; }

table.scorecard { width: 100%%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.scorecard th { text-align: right; font-weight: 500; color: %(muted)s; font-size: .92rem;
                padding: .5rem .75rem; border-bottom: 2px solid %(ink)s; }
.scorecard td { text-align: right; padding: .7rem .75rem; border-bottom: 1px solid #D5DCD1;
                font-size: 1.05rem; }
.scorecard th:first-child, .scorecard td:first-child { text-align: left; }
.scorecard td.swing { font-family: %(display)s; font-weight: 600; font-size: 1.3rem; }
.scorecard .force-cell { display: flex; align-items: center; justify-content: flex-end; gap: .8rem; }
.scorecard .bar { width: 90px; height: 6px; background: #DAE2D6; border-radius: 3px; overflow: hidden; }
.scorecard .bar span { display: block; height: 100%%; background: %(outfield)s; }

.empty { padding: 1.3rem 1.5rem; border: 1px dashed #B3C0AF; border-radius: 12px; color: %(muted)s;
         font-size: 1.02rem; }
""" % {
    "font": FONT_STACK, "display": DISPLAY_STACK, "ink": INK, "muted": MUTED, "turf": TURF,
    "outfield": OUTFIELD, "chalk": CHALK, "ball": BALL, "willow": WILLOW,
}


def css():
    """The <style> block to inject once per page."""
    return f"<style>{_CSS}</style>"


# --- Small formatting helpers -----------------------------------------------------
def turns_per_second(deg_per_s):
    """Degrees a second as full turns a second, which is easier to picture."""
    return deg_per_s / 360.0


def spin_note(deg_per_s):
    return f"about {turns_per_second(deg_per_s):.1f} full turns a second"


# --- HTML builders ----------------------------------------------------------------
def page_header_html(title, subtitle, status=None):
    """Page title and one line of help. status is an optional (state, text) pill."""
    pill = status_pill_html(*status) if status else ""
    return (
        f'<div class="header-row"><h1 class="page-title">{escape(title)}</h1>{pill}</div>'
        f'<p class="page-sub">{escape(subtitle)}</p>'
    )


def status_pill_html(state, text):
    """state is one of: idle, live, warn, error."""
    if state not in ("idle", "live", "warn", "error"):
        state = "idle"
    return f'<span class="pill {state}"><span class="dot"></span>{escape(text)}</span>'


def scoreboard_html(cells):
    """cells: list of dicts with value, label, and optional unit and note."""
    parts = []
    for c in cells:
        unit = f'<span class="unit">{escape(c["unit"])}</span>' if c.get("unit") else ""
        note = f'<div class="note">{escape(c["note"])}</div>' if c.get("note") else ""
        parts.append(
            f'<div class="cell"><div class="num">{escape(str(c["value"]))}{unit}</div>'
            f'<div class="label">{escape(c["label"])}</div>{note}</div>'
        )
    return f'<div class="scoreboard">{"".join(parts)}</div>'


def section_title_html(text):
    return f'<h3 class="section-title">{escape(text)}</h3>'


def empty_html(message):
    return f'<div class="empty">{escape(message)}</div>'


def scorecard_html(rows, empty_message="No swings yet. Swing the bat and it will appear here."):
    """rows: dicts with number, start (s), duration (s), peak_g, peak_dps."""
    if not rows:
        return empty_html(empty_message)
    strongest = max(r["peak_g"] for r in rows) or 1.0
    body = []
    for r in rows:
        width = max(4, min(100, round(100 * r["peak_g"] / strongest)))
        body.append(
            "<tr>"
            f'<td class="swing">{int(r["number"])}</td>'
            f'<td>{r["start"]:.1f} s</td>'
            f'<td>{r["duration"]:.2f} s</td>'
            f'<td><div class="force-cell">{r["peak_g"]:.1f} g'
            f'<div class="bar"><span style="width:{width}%"></span></div></div></td>'
            f'<td>{r["peak_dps"]:.0f} deg/s</td>'
            "</tr>"
        )
    return (
        '<table class="scorecard"><thead><tr>'
        "<th>Swing</th><th>Started at</th><th>Swing time</th><th>Peak force</th><th>Peak spin</th>"
        f'</tr></thead><tbody>{"".join(body)}</tbody></table>'
    )


# --- Charts -------------------------------------------------------------------------
def new_figure(rows=2, height=5.2, width=11):
    """A figure that blends into the page: transparent, no boxes, light horizontal grid."""
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": ["Barlow", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "text.color": MUTED, "axes.labelcolor": MUTED,
        "xtick.color": MUTED, "ytick.color": MUTED,
    })
    fig, axes = plt.subplots(rows, 1, figsize=(width, height), sharex=True)
    fig.patch.set_alpha(0)
    axes = [axes] if rows == 1 else list(axes)
    for ax in axes:
        ax.set_facecolor("none")
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color("#B3C0AF")
        ax.grid(axis="y", color="#D5DCD1", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
    return fig, axes


def draw_force(ax, x, acc, trigger=None):
    ax.plot(x, acc, color=OUTFIELD, linewidth=1.5)
    ax.set_ylabel("Force on the bat (g)")
    ax.set_ylim(bottom=0)
    if trigger is not None:
        ax.axhline(trigger, color=BALL, linestyle=(0, (5, 4)), linewidth=1.2)
        ax.annotate(f"swing trigger {trigger:.1f} g", xy=(1, trigger), xycoords=("axes fraction", "data"),
                    xytext=(-4, 5), textcoords="offset points", ha="right", color=BALL, fontsize=9)


def draw_spin(ax, x, gyro):
    ax.plot(x, gyro, color=SKY, linewidth=1.5)
    ax.set_ylabel("Bat spin (deg/s)")
    ax.set_ylim(bottom=0)


def shade_swings(axes, swings):
    """Highlight each (start, end) pair on every axis."""
    for ax in axes:
        for start, end in swings:
            ax.axvspan(start, end, color=WILLOW, alpha=0.35, linewidth=0)