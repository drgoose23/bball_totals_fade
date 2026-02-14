import dash
from dash import html, dcc, Output, Input, State, ALL, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
])

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Fade System</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background: #111;
                font-family: 'Inter', sans-serif;
                color: #e5e5e5;
            }
            .card {
                background: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 12px;
            }
            .form-control {
                background: #222 !important;
                border: 1px solid #333 !important;
                color: #fff !important;
                font-weight: 500;
            }
            .form-control:focus {
                border-color: #555 !important;
                box-shadow: none !important;
            }
            .form-control::placeholder { color: #555 !important; }
            .btn-adj {
                background: #252525;
                border: 1px solid #333;
                color: #888;
                font-weight: 600;
            }
            .btn-adj:hover { background: #333; color: #fff; border-color: #444; }
            .label { font-size: 0.7rem; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
            .value { font-size: 1.8rem; font-weight: 700; }
            .output-card {
                background: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 16px;
            }
            .metric-value { 
                font-weight: 600;
                font-size: 1.75rem;
                letter-spacing: -0.5px;
            }
            .metric-label {
                font-size: 0.7rem;
                font-weight: 500;
                letter-spacing: 1.5px;
                text-transform: uppercase;
                color: #5a5a6a;
            }
            .divider {
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                margin: 16px 0;
            }
            .Select-control { background: #222 !important; border-color: #333 !important; }
            .Select-value-label, .Select-placeholder, .Select-input input { color: #fff !important; }
            .Select-menu-outer { background: #222 !important; border-color: #333 !important; }
            .Select-option.is-focused { background: #333 !important; }
            .Select-arrow { border-color: #666 transparent transparent !important; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>
'''

PERIOD_TIME_MAPS = {
    40: {'Q (10m)': 10, 'H (20m)': 20, 'FG (40m)': 40},
    48: {'Q (12m)': 12, 'H (24m)': 24, 'FG (48m)': 48}
}


def get_fade_analysis(team1, team2, live_total, min_left, my_bet=None, period_time=10, threshold=4.0):
    total = team1 + team2
    needed = live_total - total
    elapsed = period_time - min_left
    actual_pace = total / elapsed if elapsed > 0 else 0
    required_pace = needed / min_left if min_left > 0 else float('inf')
    pct = ((required_pace - actual_pace) / actual_pace * 100) if actual_pace > 0 else 0
    
    return {
        "total": total,
        "needed": needed,
        "actual_pace": round(actual_pace, 2),
        "required_pace": round(required_pace, 2),
        "pct": round(pct, 1),
        "elapsed": round(elapsed, 1),
        "remaining": round(min_left, 1),
        "threshold": threshold,
        "live_total": live_total,
        "my_bet": my_bet
    }


def score_input(label, input_id):
    return html.Div([
        html.Div(label, className="label"),
        dbc.InputGroup([
            dbc.Button("−", id={"type": "dec", "index": input_id}, className="btn-adj px-3"),
            dbc.Input(id=input_id, type="number", placeholder="0", style={"textAlign": "center"}),
            dbc.Button("+", id={"type": "inc", "index": input_id}, className="btn-adj px-3"),
        ], size="sm")
    ], className="mb-3")


app.layout = dbc.Container([
    html.H4("Fade System", className="text-center py-4", style={"fontWeight": "600"}),
    
    dbc.Row([
        # Inputs
        dbc.Col([
            html.Div([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div("League", className="label"),
                            dcc.Dropdown(id="game_length", options=[
                                {"label": "NCAA", "value": 40},
                                {"label": "NBA", "value": 48}
                            ], value=40, clearable=False)
                        ], width=6),
                        dbc.Col([
                            html.Div("Period", className="label"),
                            dcc.Dropdown(id="period_type", options=[], value=None, clearable=False)
                        ], width=6),
                    ], className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col(score_input("Home", "team1"), width=6),
                        dbc.Col(score_input("Away", "team2"), width=6),
                    ]),
                    
                    html.Div([
                        html.Div("Live Total", className="label"),
                        dbc.Input(id="live_total", type="number", placeholder="-"),
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div("Minutes", className="label"),
                            dbc.Input(id="mins_left", type="number", placeholder="-", min=0)
                        ], width=6),
                        dbc.Col([
                            html.Div("Seconds", className="label"),
                            dbc.Input(id="secs_left", type="number", placeholder="-", min=0, max=59)
                        ], width=6),
                    ], className="mb-4"),
                    
                    html.Div([
                        html.Div("Your Under (optional)", className="label"),
                        dbc.Input(id="my_bet", type="number", placeholder="-"),
                    ], className="mb-4"),
                    
                    html.Div([
                        html.Div([
                            html.Span("Threshold: ", style={"color": "#666", "fontSize": "0.75rem"}),
                            html.Span(id="thresh_val", style={"color": "#fff", "fontWeight": "600"})
                        ], className="mb-2"),
                        dcc.Slider(id="threshold_slider", min=2.5, max=6, step=0.25, value=4.0,
                                   marks={2.5: '2.5', 4: '4', 6: '6'})
                    ])
                ])
            ], className="card")
        ], lg=4, md=5),
        
        # Output
        dbc.Col([html.Div(id="output")], lg=8, md=7)
    ]),
    dcc.Store(id="opening_line", data=None)
], fluid=True, style={"maxWidth": "1000px"})


@app.callback(Output("thresh_val", "children"), Input("threshold_slider", "value"))
def show_thresh(v): return f"{v}"

@app.callback(Output("period_type", "options"), Output("period_type", "value"), Input("game_length", "value"))
def update_periods(gl):
    if gl not in PERIOD_TIME_MAPS: return [], None
    opts = [{"label": k, "value": v} for k, v in PERIOD_TIME_MAPS[gl].items()]
    return opts, opts[-1]['value']

@app.callback(
    Output("team1", "value"), Output("team2", "value"),
    Input({"type": "inc", "index": ALL}, "n_clicks"),
    Input({"type": "dec", "index": ALL}, "n_clicks"),
    State("team1", "value"), State("team2", "value"),
    prevent_initial_call=True
)
def adj_scores(inc, dec, t1, t2):
    if not ctx.triggered_id: raise dash.exceptions.PreventUpdate
    t = ctx.triggered_id
    t1, t2 = t1 or 0, t2 or 0
    d = 1 if t["type"] == "inc" else -1
    if t["index"] == "team1": t1 = max(0, t1 + d)
    elif t["index"] == "team2": t2 = max(0, t2 + d)
    return t1, t2


@app.callback(
    Output("output", "children"),
    Input("team1", "value"), Input("team2", "value"), Input("live_total", "value"),
    Input("mins_left", "value"), Input("secs_left", "value"), Input("my_bet", "value"),
    Input("period_type", "value"), Input("threshold_slider", "value")
)
def update_output(t1, t2, live_total, mins, secs, my_bet, period, threshold):
    mins = mins or 0
    secs = secs or 0
    min_left = mins + secs / 60
    
    if None in [t1, t2, live_total, period] or min_left <= 0:
        return html.Div([
            html.Div([
                html.Span("Awaiting input", style={"color": "#4a4a5a", "fontSize": "0.9rem", "letterSpacing": "1px"})
            ], className="text-center py-5")
        ], className="output-card", style={"minHeight": "500px", "display": "flex", 
                                           "alignItems": "center", "justifyContent": "center"})
    
    r = get_fade_analysis(t1, t2, live_total, min_left, my_bet, period, threshold)
    pct = r['pct']
    over_thresh = r['required_pace'] > r['threshold']
    curr = r['actual_pace']
    req = r['required_pace']
    
    # Signal logic
    if pct >= 25 and over_thresh:
        signal, signal_color, border_color = "Under", "#4ade80", "#4ade8044"
    elif pct >= 10 and over_thresh:
        signal, signal_color, border_color = "Under", "#86efac", "#86efac33"
    elif pct >= 0 or not over_thresh:
        signal, signal_color, border_color = "Hold", "#71717a", "#71717a33"
    elif pct >= -15:
        signal, signal_color, border_color = "Hold", "#fbbf24", "#fbbf2433"
    else:
        signal, signal_color, border_color = "Pass", "#f87171", "#f8717133"

    # Pace visualization - line chart
    max_y = max(req, curr, 1) * 1.25
    fig = go.Figure()
    
    # Convert hex to rgba for fill
    r_col = int(signal_color[1:3], 16)
    g_col = int(signal_color[3:5], 16)
    b_col = int(signal_color[5:7], 16)
    fill_rgba = f'rgba({r_col}, {g_col}, {b_col}, 0.25)'
    
    fig.add_trace(go.Scatter(
        x=['Current', 'Required'],
        y=[curr, req],
        fill='tozeroy',
        fillcolor=fill_rgba,
        line=dict(color=signal_color, width=3),
        mode='lines+markers+text',
        marker=dict(size=[12, 14], color=['#71717a', signal_color], line=dict(color='#27272a', width=2)),
        text=[f'{curr}', f'{req}'],
        textposition=['top center', 'top center'],
        textfont=dict(family='Inter', size=14, color='#e4e4e7'),
        hoverinfo='skip'
    ))
    
    fig.add_hline(y=curr, line_dash="dot", line_color="#3f3f46", line_width=1)
    
    if pct > 0:
        fig.add_annotation(
            x=0.5, xref="paper", y=(curr + req) / 2,
            text=f"+{pct:.0f}%",
            showarrow=False,
            font=dict(family='Inter', size=14, color=signal_color, weight=600),
            opacity=0.9
        )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#18181b',
        height=160,
        margin=dict(l=40, r=20, t=25, b=35),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(family='Inter', size=11, color='#71717a'), fixedrange=True),
        yaxis=dict(range=[0, max_y], showgrid=True, gridcolor='#27272a', zeroline=False, 
                   tickfont=dict(family='Inter', size=10, color='#52525b'),
                   title=dict(text='pts/min', font=dict(size=10, color='#52525b')), fixedrange=True),
        showlegend=False
    )

    # Position tracker
    position_block = None
    if my_bet:
        pts_needed = my_bet - r['total']
        pace_needed = pts_needed / min_left if min_left > 0 else float('inf')
        busted = pts_needed <= 0
        pos_color = "#ef4444" if busted else "#22c55e"
        pos_status = "BUSTED" if busted else "ACTIVE"
        position_block = html.Div([
            html.Div(className="divider"),
            dbc.Row([
                dbc.Col([
                    html.Span("POSITION", className="metric-label"),
                    html.Div([
                        html.Span(f"U{my_bet}", style={"fontSize": "1.2rem", "color": "#e0e0e0"}),
                        html.Span(f"  {pos_status}", style={"fontSize": "0.75rem", "color": pos_color, "marginLeft": "8px"})
                    ])
                ], width=4),
                dbc.Col([
                    html.Span("PTS TO MISS", className="metric-label"),
                    html.Div(f"{pts_needed}", style={"fontSize": "1.2rem", "color": pos_color})
                ], width=4),
                dbc.Col([
                    html.Span("PACE TO MISS", className="metric-label"),
                    html.Div(f"{pace_needed:.2f}", style={"fontSize": "1.2rem", "color": pos_color})
                ], width=4),
            ])
        ], className="mt-3")

    return html.Div([
        dbc.CardBody([
            # Signal header
            html.Div([
                html.Div([
                    html.Span(signal, style={"fontSize": "1.5rem", "fontWeight": "600", "color": signal_color}),
                ]),
                html.Div([
                    html.Span(f"U{r['live_total']}" if pct >= 10 and over_thresh else "—", style={
                        "fontSize": "1rem",
                        "color": "#a1a1aa" if pct >= 10 else "#52525b",
                        "fontWeight": "500"
                    }),
                ], className="mt-1")
            ], style={
                "textAlign": "center",
                "padding": "20px",
                "marginBottom": "8px",
                "borderRadius": "12px",
                "border": f"1px solid {border_color}",
                "background": "#18181b"
            }),
            
            # Metrics row
            dbc.Row([
                dbc.Col([
                    html.Span("SCORED", className="metric-label"),
                    html.Div(f"{r['total']}", className="metric-value", style={"color": "#e0e0e0"})
                ], className="text-center"),
                dbc.Col([
                    html.Span("NEEDED", className="metric-label"),
                    html.Div(f"{r['needed']}", className="metric-value", style={"color": "#f59e0b"})
                ], className="text-center"),
                dbc.Col([
                    html.Span("CURR PACE", className="metric-label"),
                    html.Div(f"{curr}", className="metric-value", style={"color": "#3b82f6"})
                ], className="text-center"),
                dbc.Col([
                    html.Span("REQ PACE", className="metric-label"),
                    html.Div(f"{req}", className="metric-value", style={"color": signal_color})
                ], className="text-center"),
            ], className="mb-4"),
            
            # Time
            html.Div([
                html.Span(f"{r['elapsed']}m elapsed", style={"color": "#5a5a6a"}),
                html.Span(" · ", style={"color": "#3a3a4a"}),
                html.Span(f"{r['remaining']}m remaining", style={"color": "#5a5a6a"})
            ], className="text-center mb-3", style={"fontSize": "0.8rem"}),
            
            # Pace comparison chart
            dcc.Graph(figure=fig, config={'displayModeBar': False, 'staticPlot': True}),
            
            # Position tracker
            position_block if position_block else ""
        ])
    ], className="output-card", style={"border": f"1px solid {border_color}"})


if __name__ == "__main__":
    app.run(debug=True)
