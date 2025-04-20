import dash
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

PERIOD_TIME_MAPS = {
    40: {
        'Quater (10 min)': 10,
        'Half (20 min)': 20,
        'Full Game (40 min)': 40
    },
    48: {
        'Quarter (12 min)': 12,
        'Half (24 min)': 24,
        'Full Game (48 min)': 48
    }
}

def get_fade_analysis(team1_points, team2_points, live_mkt_total, min_left, my_bet=None, opening_line=None,
                      total_game_time=40, threshold=5, period_time=10):
    total_current_points = team1_points + team2_points
    points_needed_for_over = live_mkt_total - total_current_points
    min_elapsed = period_time - min_left if min_left > 0 else period_time
    current_pts_per_min = total_current_points / min_elapsed if min_elapsed > 0 else 0
    pts_per_min = points_needed_for_over / min_left if min_left > 0 else float('inf')

    if pts_per_min > threshold:
        decision = '🔥 HAMMER the UNDER'
    elif pts_per_min < 2.5:
        decision = '📈 Potential OVER?'
    else:
        decision = '⏳ NO TOUCH'

    label = "Live Under" if my_bet is None else "Your bet"
    my_bet = live_mkt_total if my_bet is None else my_bet
    pts_needed_to_miss = my_bet - total_current_points
    pace_needed_for_my_bet_to_miss = pts_needed_to_miss / min_left if min_left > 0 else float('inf')
    busted = pts_needed_to_miss <= 0
    opening_pace = opening_line / total_game_time if opening_line else None

    return {
        "decision": decision,
        "live_total": live_mkt_total,
        "total_current_points": total_current_points,
        "points_needed_for_over": points_needed_for_over,
        "current_pts_per_min": round(current_pts_per_min, 2),
        "market_pts_per_min": round(pts_per_min, 2),
        "pace_needed_to_miss": round(pace_needed_for_my_bet_to_miss, 2),
        "label": label,
        "pts_needed_to_miss": pts_needed_to_miss,
        "busted": busted,
        "opening_pace": round(opening_pace, 2) if opening_pace else None
    }

app.layout = dbc.Container([
    html.H2("🏀 BBall Totals Fade System", className='text-center my-3'),

    dbc.Row([
        dbc.Col([
            html.Label("Game Length (min):", className="mb-1"),
            dcc.Dropdown(
                id="game_length",
                options=[
                    {"label": "College (40 min)", "value": 40},
                    {"label": "NBA (48 min)", "value": 48}
                ],
                value=40,
                clearable=False,
                className="mb-3"
            ),

            html.Label("Select Period:", className="mb-1"),
            dcc.Dropdown(
                id="period_type",
                options=[],
                value=None,
                clearable=False,
                className="mb-3"
            ),

            dbc.Input(id="team1", type="number", placeholder="Team 1 Points", debounce=True),
            dbc.Input(id="team2", type="number", placeholder="Team 2 Points", debounce=True, className="mt-2"),
            dbc.Input(id="opening_line", type="number", placeholder="Opening Line (optional)", debounce=True, className="mt-2"),
            dbc.Input(id="live_total", type="number", placeholder="Live Market Total", debounce=True, className="mt-2"),
            dbc.Input(id="minutes_left", type="number", placeholder="Minutes Left", debounce=True, className="mt-2"),

            html.Label("Threshold (pts/min):", className="mt-3"),
            dbc.Row([
                dbc.Col([
                    dcc.Slider(
                        id="threshold_slider",
                        min=1,
                        max=10,
                        step=0.1,
                        value=5,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className="mb-3"
                    )
                ], width=8),
                dbc.Col([
                    dbc.Input(id="threshold_input", type="number", value=5, min=1, max=10, step=0.1)
                ], width=4)
            ]),

            dbc.Input(id="my_bet", type="number", placeholder="Your Bet (optional)", debounce=True, className="mt-2"),
            dbc.Button("Run It", id="submit", color="primary", className="mt-3 w-100")
        ], md=4),

        dbc.Col([
            html.Div(id="output", className="mt-2")
        ], md=8)
    ])
])

@app.callback(
    Output("threshold_slider", "value"),
    Output("threshold_input", "value"),
    Input("threshold_slider", "value"),
    Input("threshold_input", "value")
)
def sync_threshold(slider_val, input_val):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == "threshold_slider":
        return slider_val, slider_val
    elif triggered_id == "threshold_input":
        return input_val, input_val
    else:
        raise dash.exceptions.PreventUpdate

@app.callback(
    Output("period_type", "options"),
    Output("period_type", "value"),
    Input("game_length", "value")
)
def update_period_dropdown(game_length):
    if game_length not in PERIOD_TIME_MAPS:
        return [], None
    options = [{"label": k, "value": v} for k, v in PERIOD_TIME_MAPS[game_length].items()]
    default_value = options[0]['value']
    return options, default_value

@app.callback(
    Output("output", "children"),
    Input("submit", "n_clicks"),
    State("team1", "value"),
    State("team2", "value"),
    State("live_total", "value"),
    State("opening_line", "value"),
    State("minutes_left", "value"),
    State("my_bet", "value"),
    State("period_type", "value"),
    State("threshold_input", "value"),
    State("game_length", "value")
)
def update_output(n, team1, team2, live_total, opening_line, min_left, my_bet, period_time, threshold, game_length):
    if None in [team1, team2, live_total, min_left, period_time, threshold, game_length]:
        return dbc.Alert("Please fill in all required fields.", color="danger")

    result = get_fade_analysis(
        team1, team2, live_total, min_left, my_bet, opening_line,
        total_game_time=game_length,
        threshold=threshold,
        period_time=period_time
    )

    pace_labels = []
    pace_values = []

    if result['opening_pace'] is not None:
        pace_labels.append("Opening Pace")
        pace_values.append(result['opening_pace'])

    pace_labels += ["Current Pace", "Market-Implied Pace", "Pace to Miss Bet"]
    pace_values += [result['current_pts_per_min'], result['market_pts_per_min'], result['pace_needed_to_miss']]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pace_labels, y=pace_values, mode='markers+lines', marker=dict(size=12)))
    fig.update_layout(
        title="Pace Comparison",
        yaxis_title="Points per Minute",
        xaxis_title="",
        template="plotly_white",
        height=400
    )

    return dbc.Card([
        dbc.CardBody([
            html.H4(f"Decision: {result['decision']}", className="card-title"),
            html.P(f"Live Market Total: {result['live_total']}"),
            html.P(f"Points Scored So Far: {result['total_current_points']}"),
            html.P(f"Points Needed for Over: {result['points_needed_for_over']}"),
            html.P(f"Current Pace (pts/min): {result['current_pts_per_min']}"),
            html.P(f"Market Implied Pace (pts/min): {result['market_pts_per_min']}"),
            html.P(f"Pace Needed to MISS Bet: {result['pace_needed_to_miss']}"),
            html.P(f"Opening Pace: {result['opening_pace']}" if result['opening_pace'] else ""),
            html.Hr(),
            html.P(f"{result['label']} - Points Needed to MISS: {result['pts_needed_to_miss']}"),
            html.P("⚠️ Bet already likely busted." if result['busted'] else "", className="text-danger"),
            dcc.Graph(figure=fig, className="mt-4")
        ])
    ])

if __name__ == "__main__":
    app.run(debug=True)
