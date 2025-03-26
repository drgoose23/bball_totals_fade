import dash
from dash import html, dcc, Output, Input, State
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Game period mapping
PERIOD_TIME_MAP = {
    'Quarter (10 min)': 10,
    'Half (20 min)': 20,
    'Full Game (40 min)': 40
}

def get_fade_analysis(team1_points, team2_points, live_mkt_total, min_left, my_bet=None, total_game_time=40, threshold=5):
    total_current_points = team1_points + team2_points
    points_needed_for_over = live_mkt_total - total_current_points
    min_elapsed = total_game_time - min_left if min_left > 0 else total_game_time
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

    return {
        "decision": decision,
        "live_total": live_mkt_total,
        "total_current_points": total_current_points,
        "points_needed_for_over": points_needed_for_over,
        "current_pts_per_min": round(current_pts_per_min, 2),
        "market_pts_per_min": round(pts_per_min, 2),
        "label": label,
        "pts_needed_to_miss": pts_needed_to_miss,
        "pace_needed_to_miss": round(pace_needed_for_my_bet_to_miss, 2),
        "busted": busted
    }

app.layout = dbc.Container([
    html.H2("🏀 CBB Totals Fade System", className='text-center my-3'),

    dbc.Row([
        dbc.Col([
            dbc.Input(id="team1", type="number", placeholder="Team 1 Points", debounce=True),
            dbc.Input(id="team2", type="number", placeholder="Team 2 Points", debounce=True, className="mt-2"),
            dbc.Input(id="live_total", type="number", placeholder="Live Market Total", debounce=True, className="mt-2"),
            dbc.Input(id="minutes_left", type="number", placeholder="Minutes Left", debounce=True, className="mt-2"),

            dcc.Dropdown(
                id="period_type",
                options=[{"label": k, "value": v} for k, v in PERIOD_TIME_MAP.items()],
                value=40,
                className="mt-2",
                placeholder="Select Period"
            ),

            html.Label("Threshold (pts/min):", className="mt-3"),
            dcc.Slider(
                id="threshold",
                min=1,
                max=10,
                step=0.1,
                value=5,
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-3"
            ),

            dbc.Input(id="my_bet", type="number", placeholder="Your Bet (optional)", debounce=True, className="mt-2"),
            dbc.Button("Run Analysis", id="submit", color="primary", className="mt-3 w-100")
        ], md=4),

        dbc.Col([
            html.Div(id="output", className="mt-2")  # ✅ This is the missing component
        ], md=8)
    ])
])

@app.callback(
    Output("output", "children"),
    Input("submit", "n_clicks"),
    State("team1", "value"),
    State("team2", "value"),
    State("live_total", "value"),
    State("minutes_left", "value"),
    State("my_bet", "value"),
    State("period_type", "value"),
    State("threshold", "value")
)
def update_output(n, team1, team2, live_total, min_left, my_bet, period_time, threshold):
    if None in [team1, team2, live_total, min_left, period_time, threshold]:
        return dbc.Alert("Please fill in all required fields.", color="danger")
    
    result = get_fade_analysis(team1, team2, live_total, min_left, my_bet, period_time, threshold)

    return dbc.Card([
        dbc.CardBody([
            html.H4(f"Decision: {result['decision']}", className="card-title"),
            html.P(f"Live Market Total: {result['live_total']}"),
            html.P(f"Points Scored So Far: {result['total_current_points']}"),
            html.P(f"Points Needed for Over: {result['points_needed_for_over']}"),
            html.P(f"Current Pace (pts/min): {result['current_pts_per_min']}"),
            html.P(f"Market Implied Pace (pts/min): {result['market_pts_per_min']}"),
            html.Hr(),
            html.P(f"{result['label']} - Points Needed to MISS: {result['pts_needed_to_miss']}"),
            html.P(f"Pace Needed to MISS: {result['pace_needed_to_miss']}"),
            html.P("⚠️ Bet already likely busted." if result['busted'] else "", className="text-danger")
        ])
    ])

if __name__ == "__main__":
    app.run(debug=True)