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

FONT_STACK = "DejaVu Sans"
DISPLAY_STACK = "'Barlow Condensed', 'Arial Narrow', 'Helvetica Neue', Arial, sans-serif"

_CSS = """
.stApp { background: #F6F5F0; color: #172D25; }
.stApp, .stApp p, .stApp label, .stApp button, .stApp input { font-family: 'Inter', 'Segoe UI', sans-serif; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1260px; }
header[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }

.header-row { display: flex; align-items: flex-end; justify-content: space-between;
              gap: 1rem; flex-wrap: wrap; margin-bottom: .25rem; }
.page-title { font-family: 'Barlow Condensed', 'Arial Narrow', 'Helvetica Neue', Arial, sans-serif; font-weight: 600; font-size: 2.8rem; line-height: 1.05;
              color: #17231C; margin: 0; }
.page-sub { color: #5B6B61; font-size: 1.05rem; margin: .35rem 0 1rem; max-width: 62ch; }

.pill { display: inline-flex; align-items: center; gap: .5rem; padding: .3rem .85rem;
        border-radius: 999px; font-size: .92rem; font-weight: 500; background: #E1E8DD; color: #17231C; }
.pill .dot { width: .6rem; height: .6rem; border-radius: 50%; background: #5B6B61; }
.pill.live .dot { background: #1F6B3A; }
.pill.warn { background: #F3E6C8; }
.pill.warn .dot { background: #D9B26B; }
.pill.error { background: #F6DAD7; }
.pill.error .dot { background: #C8312B; }

.scoreboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
              gap: 1px; background: rgba(243, 245, 239, .18); border-radius: 12px;
              overflow: hidden; margin: 1.1rem 0 1.6rem; }
.scoreboard .cell { background: #0F3D24; color: #F3F5EF; padding: 1.1rem 1.4rem 1.2rem; }
.scoreboard .num { font-family: 'Barlow Condensed', 'Arial Narrow', 'Helvetica Neue', Arial, sans-serif; font-weight: 600; font-size: 3.4rem; line-height: 1;
                   font-variant-numeric: tabular-nums; }
.scoreboard .unit { font-size: 1.1rem; font-weight: 500; margin-left: .35rem; color: #B9CDBF; }
.scoreboard .label { margin-top: .4rem; font-size: .98rem; color: #D2E2D7; }
.scoreboard .note { margin-top: .15rem; font-size: .86rem; color: #A3BDAB; }

.section-title { font-family: 'Barlow Condensed', 'Arial Narrow', 'Helvetica Neue', Arial, sans-serif; font-weight: 600; font-size: 1.6rem; color: #17231C;
                 margin: 1.8rem 0 .6rem; }

table.scorecard { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.scorecard th { text-align: right; font-weight: 500; color: #5B6B61; font-size: .92rem;
                padding: .5rem .75rem; border-bottom: 2px solid #17231C; }
.scorecard td { text-align: right; padding: .7rem .75rem; border-bottom: 1px solid #D5DCD1;
                font-size: 1.05rem; }
.scorecard th:first-child, .scorecard td:first-child { text-align: left; }
.scorecard td.swing { font-weight: 800; font-size: 17px; }
.scorecard .force-cell { display: flex; align-items: center; justify-content: flex-end; gap: 12px; }
.scorecard .bar { width: 60px; height: 4px; background: #E5EADB; border-radius: 3px; overflow: hidden; }
.scorecard .bar span { display: block; height: 100%; background: #8AA864; }
.empty { padding: 30px; background: #FFFDF8; border: 1px dashed #B7C7A8; border-radius: 16px; color: #65775E; font-size: 14px; line-height: 1.8; }
.steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; padding: 22px 0 12px; }
.step { font-size: 12px; color: #71816A; line-height: 1.7; }
.step b { display: block; color: #264A32; font-size: 14px; margin-bottom: 6px; }
.step span { color: #86A36B; font-size: 10px; letter-spacing: 1px; font-weight: 800; }
@keyframes flight { to { stroke-dashoffset: -180; } }
@keyframes float { 50% { transform: translateY(-6px) rotate(8deg); } }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 #689B6550; } 100% { box-shadow: 0 0 0 7px #689B6500; } }
@keyframes enter { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 760px) { .hero { padding: 28px 22px; min-height: 220px; } .hero-copy { width: 80%; } .hero-art { right: -80px; opacity: .25; width: 65%; } .scoreboard { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; } .steps { gap: 14px; } .scoreboard .cell { padding: 18px; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
"""


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
        f'<div class="header-row"><h2 class="page-title">{escape(title)}</h2>{pill}</div>'
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
        '<div class="table-wrap"><table class="scorecard"><thead><tr>'
        "<th>Swing</th><th>Started at</th><th>Swing time</th><th>Peak acceleration</th><th>Peak spin</th>"
        f'</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
    )


# --- Charts -------------------------------------------------------------------------
def new_figure(rows=2, height=5.2, width=11):
    """A figure that blends into the page: transparent, no boxes, light horizontal grid."""
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9, "axes.labelsize": 9,
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
    ax.fill_between(x, acc, color=OUTFIELD, alpha=0.07)
    ax.plot(x, acc, color=OUTFIELD, linewidth=1.7)
    ax.set_ylabel("Acceleration (g)")
    ax.set_ylim(bottom=0)
    if trigger is not None:
        ax.axhline(trigger, color=BALL, linestyle=(0, (5, 4)), linewidth=1.2)
        ax.annotate(f"swing trigger {trigger:.1f} g", xy=(1, trigger), xycoords=("axes fraction", "data"),
                    xytext=(-4, 5), textcoords="offset points", ha="right", color=BALL, fontsize=9)


def draw_spin(ax, x, gyro):
    ax.fill_between(x, gyro, color=SKY, alpha=0.06)
    ax.plot(x, gyro, color=SKY, linewidth=1.7)
    ax.set_ylabel("Bat spin (deg/s)")
    ax.set_ylim(bottom=0)


def shade_swings(axes, swings):
    """Highlight each (start, end) pair on every axis."""
    for ax in axes:
        for start, end in swings:
            ax.axvspan(start, end, color=WILLOW, alpha=0.35, linewidth=0)

# Inline artwork is local, decorative, and never represents a measured bat path.
def hero_html(review=False):
    title = "Every swing.<br>A little better." if not review else "Find your rhythm.<br>Own your next innings."
    subtitle = ("Your practice, in focus. Connect your sensor, take a swing, and turn movement into insight."
                if not review else "Go beyond the score. Explore your recordings and get to know the shape of your swing.")
    return f'''<section class="hero"><div class="hero-copy"><div class="eyebrow">THE PRACTICE LAB / CRICKET SWING ANALYZER</div>
<h1>{title}</h1><p>{subtitle}</p><div class="hero-foot">MEASURE YOUR MOVEMENT. &nbsp; MAKE IT COUNT.</div></div>
<svg class="hero-art" viewBox="0 0 400 330" aria-hidden="true" focusable="false">
<defs><linearGradient id="pitch" x2="1" y2="1"><stop stop-color="#C6D5AB"/><stop offset="1" stop-color="#DCE5CC"/></linearGradient></defs>
<ellipse cx="215" cy="208" rx="172" ry="110" fill="none" stroke="#C6D6B3" stroke-width="1"/>
<ellipse cx="215" cy="208" rx="140" ry="86" fill="none" stroke="#C6D6B3" stroke-dasharray="3 7"/>
<path d="M120 245L239 152L300 183L180 278Z" fill="url(#pitch)"/>
<path d="M148 244L251 164M163 260L267 180M139 238L178 261M237 163L277 186" stroke="#F9FAED" stroke-width="2"/>
<path d="M148 231v-25m6 21v-25m6 21v-25m-14 9l15-11" stroke="#6F8760" stroke-width="3" stroke-linecap="round"/>
<path class="trajectory" d="M192 201Q241 22 349 62" fill="none" stroke="#6C9258" stroke-width="1.5"/>
<circle cx="349" cy="62" r="10" fill="#C15A3D" class="ball"/><path d="M345 55q-4 8 3 14m4-14q-4 7 3 12" stroke="#F4DAD0" fill="none"/>
<g transform="rotate(35 221 168)"><rect x="211" y="101" width="21" height="80" rx="7" fill="#C69D60"/><rect x="216" y="107" width="11" height="62" rx="3" fill="#E8CE9B"/><rect x="218" y="175" width="7" height="42" rx="3" fill="#173F2D"/><path d="M217 185h9m-9 6h9m-9 6h9" stroke="#8FAC77" stroke-width="2"/></g>
<circle cx="290" cy="249" r="25" fill="#193F2E"/><text x="290" y="254" text-anchor="middle" fill="#DDECBC" font-family="sans-serif" font-size="12" font-weight="bold">500</text>
<text x="290" y="288" text-anchor="middle" fill="#6E855E" font-family="sans-serif" font-size="9" letter-spacing="2">HZ TARGET</text></svg></section>'''


def steps_html():
    return ('''<div class="steps"><div class="step"><span>01 / CONNECT</span><b>Plug in. You're up.</b>Your sensor appears automatically when you connect it.</div>
<div class="step"><span>02 / PRACTICE</span><b>Make your move.</b>Start a session and watch your swings take shape.</div>
<div class="step"><span>03 / UNDERSTAND</span><b>Play it back.</b>Save your session and explore every swing in Review.</div></div>''')


def motion_chart(t, acc, gyro, threshold, swings):
    """Linked, zoomable recording charts using Streamlit's existing Altair dependency."""
    import altair as alt
    import pandas as pd

    data = pd.DataFrame({"time": t, "acceleration": acc, "rotation": gyro})
    windows = pd.DataFrame(swings, columns=["start", "end"])
    charts = []
    for field, title, color in (("acceleration", "Acceleration · g", OUTFIELD),
                                ("rotation", "Rotation · degrees / second", SKY)):
        base = alt.Chart(data).encode(x=alt.X("time:Q", title="Time into recording (s)"))
        line = base.mark_line(color=color, strokeWidth=2, clip=True).encode(
            y=alt.Y(f"{field}:Q", title=title, scale=alt.Scale(zero=True)),
            tooltip=[alt.Tooltip("time:Q", title="Time (s)", format=".3f"),
                     alt.Tooltip(f"{field}:Q", title=title, format=".2f")],
        )
        layers = [base.mark_area(color=color, opacity=0.06).encode(y=f"{field}:Q"), line]
        if not windows.empty:
            layers.insert(0, alt.Chart(windows).mark_rect(color=WILLOW, opacity=0.15).encode(
                x="start:Q", x2="end:Q"))
        if field == "acceleration":
            layers.append(alt.Chart(pd.DataFrame({"trigger": [threshold]})).mark_rule(
                color=BALL, strokeDash=[5, 5], opacity=0.6).encode(y="trigger:Q"))
        charts.append(alt.layer(*layers).properties(height=175))
    charts[0] = charts[0].interactive(bind_y=False)
    return alt.vconcat(*charts, spacing=24).resolve_scale(x="shared").configure_view(
        stroke=None).configure_axis(gridColor="#E5E9DE", labelColor=MUTED,
                                   titleColor=MUTED, domain=False, tickSize=0,
                                   titlePadding=14).configure(background="#F6F5F0")
