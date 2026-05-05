"""
SCADA Control Center - Live Dashboard
-------------------------------------
A web-based supervisory control and data acquisition (SCADA) dashboard
built with Dash and Plotly.

Architecture
------------
    sensor_simulator  -->  background poll thread (1 Hz)  -->  historian DB
                                                                    |
                                                                    v
                                                          Dash app (1 s refresh)
                                                                    |
                                                                    v
                                                            Browser (HMI)

Run:
    python app.py
Then open http://127.0.0.1:8050 in a browser.
"""

import threading
import time
from datetime import datetime

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go

from sensor_simulator import read_all, SENSORS
from database import init_db, log_all, get_latest_per_tag, get_history, get_active_alarms


# --------------------------------------------------------------------------
# Background sensor poller: simulates the SCADA "scan cycle" every 1 second.
# --------------------------------------------------------------------------
POLL_INTERVAL_S = 1.0


def poll_loop():
    while True:
        try:
            log_all(read_all())
        except Exception as e:
            print(f"[poller] error: {e}")
        time.sleep(POLL_INTERVAL_S)


def start_poller():
    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()


# --------------------------------------------------------------------------
# Styling - industrial dark theme typical of SCADA HMIs
# --------------------------------------------------------------------------
COLORS = {
    "bg": "#0B1320",
    "panel": "#162032",
    "panel_alt": "#1E2B40",
    "border": "#2A3A55",
    "text": "#E6EDF7",
    "text_dim": "#8AA0BD",
    "normal": "#10B981",
    "warning": "#F59E0B",
    "critical": "#EF4444",
    "accent": "#3B82F6",
}

STATUS_COLOR = {
    "NORMAL": COLORS["normal"],
    "WARNING": COLORS["warning"],
    "CRITICAL": COLORS["critical"],
}

CARD_STYLE = {
    "backgroundColor": COLORS["panel"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "8px",
    "padding": "16px",
    "minWidth": "180px",
    "flex": "1",
    "fontFamily": "Consolas, monospace",
}


# --------------------------------------------------------------------------
# Dashboard components
# --------------------------------------------------------------------------
def build_kpi_card(reading):
    """A single sensor 'tile' showing tag, current value, unit, and status."""
    color = STATUS_COLOR[reading["status"]]
    return html.Div(
        style={**CARD_STYLE, "borderLeft": f"4px solid {color}"},
        children=[
            html.Div(reading["tag"],
                     style={"color": COLORS["text_dim"], "fontSize": "12px",
                            "letterSpacing": "1px"}),
            html.Div(reading["name"],
                     style={"color": COLORS["text"], "fontSize": "14px",
                            "marginBottom": "8px"}),
            html.Div(
                children=[
                    html.Span(f"{reading['value']:.2f}",
                              style={"fontSize": "30px", "fontWeight": "bold",
                                     "color": COLORS["text"]}),
                    html.Span(f" {reading['unit']}",
                              style={"fontSize": "14px",
                                     "color": COLORS["text_dim"],
                                     "marginLeft": "4px"}),
                ]
            ),
            html.Div(reading["status"],
                     style={"color": color, "fontSize": "12px",
                            "fontWeight": "bold", "marginTop": "6px",
                            "letterSpacing": "1px"}),
        ],
    )


def build_alarm_panel(alarms):
    """Active alarm list. Shows 'no active alarms' when the plant is healthy."""
    header = html.Div(
        f"ACTIVE ALARMS ({len(alarms)})",
        style={"color": COLORS["text_dim"], "fontSize": "12px",
               "letterSpacing": "2px", "marginBottom": "10px"},
    )
    if not alarms:
        body = html.Div(
            "No active alarms - all process variables nominal",
            style={"color": COLORS["normal"], "fontSize": "14px",
                   "fontFamily": "Consolas, monospace"},
        )
    else:
        body = html.Div([
            html.Div(
                style={"display": "flex", "justifyContent": "space-between",
                       "padding": "8px 12px", "marginBottom": "4px",
                       "backgroundColor": COLORS["panel_alt"],
                       "borderLeft": f"4px solid {STATUS_COLOR[a['status']]}",
                       "borderRadius": "4px",
                       "fontFamily": "Consolas, monospace"},
                children=[
                    html.Span(f"{a['tag']} - {a['name']}",
                              style={"color": COLORS["text"]}),
                    html.Span(f"{a['value']} {a['unit']}",
                              style={"color": COLORS["text"]}),
                    html.Span(a["status"],
                              style={"color": STATUS_COLOR[a["status"]],
                                     "fontWeight": "bold"}),
                ],
            )
            for a in alarms
        ])
    return html.Div(
        style={**CARD_STYLE, "minWidth": "100%"},
        children=[header, body],
    )


def build_trend_figure(tag):
    """Time-series chart for one tag, with warning/critical limit lines."""
    history = get_history(tag, limit=120)  # last ~2 minutes at 1 Hz
    s = SENSORS[tag]

    if not history:
        x, y = [], []
    else:
        x = [h["timestamp"] for h in history]
        y = [h["value"] for h in history]

    fig = go.Figure()

    # Trend line, colour by latest status
    latest_status = history[-1]["status"] if history else "NORMAL"
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines",
        line=dict(color=STATUS_COLOR[latest_status], width=2),
        name=tag, hovertemplate="%{y:.2f} " + s["unit"] + "<extra></extra>",
    ))

    # Warning and critical limit reference lines
    for limit, dash, label in [
        (s["warning_high"], "dot", "warn high"),
        (s["warning_low"], "dot", "warn low"),
        (s["critical_high"], "dash", "crit high"),
        (s["critical_low"], "dash", "crit low"),
    ]:
        fig.add_hline(y=limit, line=dict(color=COLORS["text_dim"],
                                          width=1, dash=dash))

    fig.update_layout(
        title=dict(text=f"{tag} - {s['name']}",
                   font=dict(color=COLORS["text"], size=14)),
        paper_bgcolor=COLORS["panel"], plot_bgcolor=COLORS["panel"],
        font=dict(color=COLORS["text_dim"], family="Consolas, monospace"),
        xaxis=dict(showgrid=False, color=COLORS["text_dim"], showticklabels=False),
        yaxis=dict(gridcolor=COLORS["border"], color=COLORS["text_dim"],
                   title=s["unit"]),
        margin=dict(l=50, r=20, t=40, b=20), height=250, showlegend=False,
    )
    return fig


# --------------------------------------------------------------------------
# Dash app
# --------------------------------------------------------------------------
app = dash.Dash(__name__)
app.title = "SCADA Control Center"

app.layout = html.Div(
    style={"backgroundColor": COLORS["bg"], "minHeight": "100vh",
           "padding": "20px", "fontFamily": "Segoe UI, sans-serif"},
    children=[
        # Header
        html.Div(
            style={"display": "flex", "justifyContent": "space-between",
                   "alignItems": "center", "marginBottom": "20px",
                   "paddingBottom": "12px",
                   "borderBottom": f"1px solid {COLORS['border']}"},
            children=[
                html.Div([
                    html.H1("SCADA CONTROL CENTER",
                            style={"color": COLORS["text"], "margin": 0,
                                   "letterSpacing": "3px", "fontSize": "22px"}),
                    html.Div("Process Monitoring & Historian",
                             style={"color": COLORS["text_dim"],
                                    "fontSize": "12px", "letterSpacing": "1px"}),
                ]),
                html.Div(id="live-clock",
                         style={"color": COLORS["accent"], "fontSize": "20px",
                                "fontFamily": "Consolas, monospace"}),
            ],
        ),

        # KPI cards
        html.Div(id="kpi-row",
                 style={"display": "flex", "gap": "12px", "flexWrap": "wrap",
                        "marginBottom": "16px"}),

        # Alarm panel
        html.Div(id="alarm-row", style={"marginBottom": "16px"}),

        # Trend charts (2 per row)
        html.Div(id="trends-row",
                 style={"display": "grid",
                        "gridTemplateColumns": "repeat(2, 1fr)", "gap": "12px"}),

        # Auto refresh tick
        dcc.Interval(id="tick", interval=1000, n_intervals=0),
    ],
)


# --------------------------------------------------------------------------
# Callback: refresh entire dashboard each tick
# --------------------------------------------------------------------------
@app.callback(
    Output("live-clock", "children"),
    Output("kpi-row", "children"),
    Output("alarm-row", "children"),
    Output("trends-row", "children"),
    Input("tick", "n_intervals"),
)
def refresh(_):
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    latest = get_latest_per_tag()
    alarms = get_active_alarms()

    cards = [build_kpi_card(r) for r in latest]
    alarm_panel = build_alarm_panel(alarms)
    trends = [dcc.Graph(figure=build_trend_figure(tag),
                        config={"displayModeBar": False})
              for tag in SENSORS]
    return now, cards, alarm_panel, trends


# --------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    start_poller()
    print("SCADA dashboard running on http://127.0.0.1:8050")
    app.run(debug=False, host="127.0.0.1", port=8050)
