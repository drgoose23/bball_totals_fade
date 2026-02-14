import dash
from dash import html, dcc, Output, Input, State, ALL, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
from datetime import datetime, timedelta
import json

app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
], suppress_callback_exceptions=True)

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
            /* Dropdown Styling for Dark Theme */
            .Select-control { background: #222 !important; border-color: #333 !important; }
            .Select-value-label, .Select-placeholder, .Select-input input { color: #fff !important; }
            .Select-menu-outer { background: #222 !important; border-color: #333 !important; }
            .Select-option { background: #222 !important; color: #fff !important; }
            .Select-option.is-focused { background: #333 !important; color: #fff !important; }
            .Select-option:hover { background: #333 !important; color: #fff !important; }
            .Select-arrow { border-color: #666 transparent transparent !important; }
            
            /* Modern Dash Dropdown Styling */
            .dash-dropdown .Select-control { background: #222 !important; border-color: #333 !important; }
            .dash-dropdown .Select-value-label, .dash-dropdown .Select-placeholder { color: #fff !important; }
            .dash-dropdown .Select-menu-outer { background: #222 !important; border-color: #333 !important; }
            .dash-dropdown .Select-option { background: #222 !important; color: #fff !important; padding: 8px 12px !important; }
            .dash-dropdown .Select-option.is-focused { background: #333 !important; color: #fff !important; }
            .dash-dropdown .Select-option:hover { background: #333 !important; color: #fff !important; }
            
            /* Newer Dash Component Styling */
            .dash-dropdown > div > div { background: #222 !important; border-color: #333 !important; }
            .dash-dropdown .dropdown-content { background: #222 !important; border-color: #333 !important; }
            .dash-dropdown .dropdown-content .dropdown-item { color: #fff !important; background: #222 !important; }
            .dash-dropdown .dropdown-content .dropdown-item:hover { background: #333 !important; color: #fff !important; }
            
            /* Dark Dropdown Class Styling */
            .dark-dropdown .Select-control { background: #222 !important; border-color: #333 !important; color: #fff !important; }
            .dark-dropdown .Select-placeholder { color: #999 !important; }
            .dark-dropdown .Select-value-label { color: #fff !important; }
            .dark-dropdown .Select-input > input { color: #fff !important; }
            .dark-dropdown .Select-menu-outer { background: #222 !important; border-color: #333 !important; }
            .dark-dropdown .Select-menu { background: #222 !important; }
            .dark-dropdown .Select-option { color: #fff !important; background: #222 !important; }
            .dark-dropdown .Select-option.is-focused { background: #333 !important; color: #fff !important; }
            .dark-dropdown .Select-option.is-selected { background: #444 !important; color: #fff !important; }
            .dark-dropdown .Select-arrow-zone { border-color: #666 transparent transparent !important; }
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

def fetch_games_by_date(date_str=None):
    """Fetch college basketball games from ESPN's internal API for a specific date"""
    try:
        if date_str:
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date_str}"
        else:
            # For "today", use current date regardless of time - college games often span midnight
            today_str = datetime.now().strftime('%Y%m%d')
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today_str}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        games = []
        for event in data.get('events', []):
            competition = event.get('competitions', [{}])[0]
            status = event.get('status', {})
            competitors = competition.get('competitors', [])
            
            if len(competitors) != 2:
                continue
                
            home_team = next((c for c in competitors if c.get('homeAway') == 'home'), {})
            away_team = next((c for c in competitors if c.get('homeAway') == 'away'), {})
            
            state = status.get('type', {}).get('state', '')
            
            game_info = {
                'id': event.get('id'),
                'home_team': home_team.get('team', {}).get('displayName', 'Home'),
                'away_team': away_team.get('team', {}).get('displayName', 'Away'),
                'home_team_id': home_team.get('team', {}).get('id'),
                'away_team_id': away_team.get('team', {}).get('id'),
                'home_score': int(home_team.get('score', 0)),
                'away_score': int(away_team.get('score', 0)),
                'status_text': status.get('type', {}).get('detail', 'Pre-Game'),
                'period': status.get('period', 1),
                'clock': status.get('displayClock', '20:00'),
                'is_live': state == 'in',
                'is_final': state == 'post',
                'date': event.get('date', ''),
                'state': state
            }
            
            # Parse time remaining
            if game_info['is_live']:
                try:
                    clock = game_info['clock']
                    if ':' in clock:
                        mins, secs = clock.split(':')
                        game_info['minutes_left'] = int(mins)
                        game_info['seconds_left'] = int(secs)
                    else:
                        game_info['minutes_left'] = 0
                        game_info['seconds_left'] = 0
                except:
                    game_info['minutes_left'] = 0
                    game_info['seconds_left'] = 0
            else:
                game_info['minutes_left'] = 20 if state == 'pre' else 0
                game_info['seconds_left'] = 0
            
            games.append(game_info)
        
        return games
    except Exception as e:
        print(f"Error fetching games: {e}")
        return []

def fetch_live_games():
    """Fetch current live games - wrapper for backwards compatibility"""
    games = fetch_games_by_date()
    # Only return live and pre-game for the fade system
    return [g for g in games if g['state'] in ['in', 'pre']]

def fetch_team_recent_games(team_id, num_games=10):
    """Fetch recent games for a team to calculate averages"""
    try:
        # ESPN team schedule endpoint
        url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{team_id}/schedule"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        completed_games = []
        events = data.get('events', [])
        
        # Filter completed games by checking if scores exist (more reliable than game state)
        for event in events:
            competition = event.get('competitions', [{}])[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) == 2:
                home_team = next((c for c in competitors if c.get('homeAway') == 'home'), {})
                away_team = next((c for c in competitors if c.get('homeAway') == 'away'), {})
                
                # Check if both teams have scores (indicates completed game)
                home_score_data = home_team.get('score', {})
                away_score_data = away_team.get('score', {})
                
                if (isinstance(home_score_data, dict) and home_score_data.get('value') is not None and 
                    isinstance(away_score_data, dict) and away_score_data.get('value') is not None):
                    
                    # This game has scores, so it's completed
                    team_was_home = str(home_team.get('team', {}).get('id')) == str(team_id)
                    
                    home_score = int(home_score_data.get('value', 0))
                    away_score = int(away_score_data.get('value', 0))
                    
                    if team_was_home:
                        team_score = home_score
                        opp_score = away_score
                        opponent = away_team.get('team', {}).get('displayName', 'Unknown')
                    else:
                        team_score = away_score
                        opp_score = home_score
                        opponent = home_team.get('team', {}).get('displayName', 'Unknown')
                    
                    completed_games.append({
                        'date': event.get('date', ''),
                        'team_score': team_score,
                        'opponent_score': opp_score,
                        'total_points': team_score + opp_score,
                        'opponent': opponent,
                        'location': 'Home' if team_was_home else 'Away'
                    })
        
        # Return the most recent num_games
        return completed_games[-num_games:] if completed_games else []
        
    except Exception as e:
        print(f"Error fetching team games: {e}")
        return []

def format_game_option(game):
    """Format game data for dropdown display"""
    if game['is_live']:
        status = "🔴 LIVE"
        score_display = f"{game['away_team']} {game['away_score']}-{game['home_score']} {game['home_team']}"
        time_display = game['clock']
        total_score = game['away_score'] + game['home_score']
        return {
            'label': f"{status} {score_display} ({time_display}) - Total: {total_score}",
            'value': game['id']
        }
    else:
        status = "⏰ PRE"
        score_display = f"{game['away_team']} @ {game['home_team']}"
        try:
            dt = datetime.fromisoformat(game['date'].replace('Z', '+00:00'))
            time_display = dt.strftime('%I:%M %p ET')
        except:
            time_display = game['clock']
        return {
            'label': f"{status} {score_display} ({time_display})",
            'value': game['id']
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
    html.H4("Basketball Analysis System", className="text-center py-4", style={"fontWeight": "600"}),
    
    dbc.Tabs([
        dbc.Tab(label="Fade System", tab_id="fade-tab"),
        dbc.Tab(label="Game Analysis", tab_id="analysis-tab"),
    ], id="main-tabs", active_tab="fade-tab", className="mb-4"),
    
    html.Div(id="tab-content"),
    
    # Stores
    dcc.Store(id="opening_line", data=None),
    dcc.Store(id="live_games_data", data=[]),
    dcc.Store(id="selected_game_data", data=None),
    dcc.Store(id="today_games_data", data=[]),
    dcc.Store(id="tomorrow_games_data", data=[]),
    dcc.Store(id="week_games_data", data=[]),
    dcc.Interval(id="refresh_games", interval=15*1000, n_intervals=0)  # Refresh every 15 seconds
], fluid=True, style={"maxWidth": "1200px"})


def create_fade_tab():
    """Create the fade system tab layout"""
    return dbc.Row([
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
                            ], value=40, clearable=False, className="dark-dropdown")
                        ], width=6),
                        dbc.Col([
                            html.Div("Period", className="label"),
                            dcc.Dropdown(id="period_type", options=[], value=None, clearable=False, className="dark-dropdown")
                        ], width=6),
                    ], className="mb-3"),
                    
                    html.Div([
                        html.Div([
                            html.Span("Live Game", className="label"),
                            html.Span(" (ESPN)", style={"fontSize": "0.65rem", "color": "#555", "marginLeft": "6px"})
                        ]),
                        dcc.Dropdown(
                            id="live_game_selector",
                            options=[],
                            placeholder="Select live game or enter manually below...",
                            clearable=True,
                            style={"color": "#fff"},
                            className="dark-dropdown"
                        ),
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
    ])

def create_analysis_tab():
    """Create the game analysis tab layout"""
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H5("Game Schedule", className="mb-3", style={"fontWeight": "600"}),
                
                dbc.ButtonGroup([
                    dbc.Button("Today", id="today-btn", color="primary", size="sm"),
                    dbc.Button("Tomorrow", id="tomorrow-btn", color="secondary", size="sm"),
                    dbc.Button("This Week", id="week-btn", color="secondary", size="sm"),
                ], className="mb-3"),
                
                html.Div(id="games-display", className="card", style={"minHeight": "400px"})
            ], width=6),
            
            dbc.Col([
                html.H5("Team Analysis", className="mb-3", style={"fontWeight": "600"}),
                
                html.Div([
                    html.Div("Team Comparison Analysis", className="label"),
                    dbc.Row([
                        dbc.Col([
                            dcc.Dropdown(
                                id="team1_selector",
                                options=[],
                                placeholder="Select Team 1...",
                                clearable=True,
                                searchable=True,
                                className="dark-dropdown"
                            ),
                        ], width=6),
                        dbc.Col([
                            dcc.Dropdown(
                                id="team2_selector", 
                                options=[],
                                placeholder="Select Team 2...",
                                clearable=True,
                                searchable=True,
                                className="dark-dropdown"
                            ),
                        ], width=6),
                    ]),
                ], className="mb-3"),
                
                html.Div([
                    html.Div([
                        html.Span("Recent Games: ", className="label", style={"display": "inline-block", "marginRight": "10px"}),
                        html.Span(id="games_count_display", style={"fontSize": "0.8rem", "color": "#f59e0b", "fontWeight": "600"})
                    ]),
                    dcc.Slider(
                        id="games_count_slider",
                        min=5, max=20, step=5, value=10,
                        marks={5: '5', 10: '10', 15: '15', 20: '20'},
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], className="mb-3"),
                
                html.Div(id="team-analysis-display", className="card", style={"minHeight": "400px"})
            ], width=6)
        ])
    ])

@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab")
)
def switch_tabs(active_tab):
    """Switch between fade system and analysis tabs"""
    if active_tab == "analysis-tab":
        return create_analysis_tab()
    return create_fade_tab()

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


# ESPN API Callbacks
@app.callback(
    Output("live_games_data", "data"),
    Output("today_games_data", "data"),
    Output("tomorrow_games_data", "data"),
    Output("week_games_data", "data"),
    Input("refresh_games", "n_intervals")
)
def refresh_all_games(n):
    """Fetch all games data every interval"""
    live_games = fetch_live_games()
    
    # Get today's date in YYYYMMDD format
    today = datetime.now().strftime('%Y%m%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    
    today_games = fetch_games_by_date(today)
    tomorrow_games = fetch_games_by_date(tomorrow)
    
    # Get week's games (next 7 days)
    week_games = []
    for days_ahead in range(0, 7):
        date_str = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y%m%d')
        games = fetch_games_by_date(date_str)
        week_games.extend(games)
    
    return live_games, today_games, tomorrow_games, week_games

@app.callback(
    Output("live_game_selector", "options"),
    Input("live_games_data", "data")
)
def update_game_options(games_data):
    """Update game selector options"""
    if not games_data:
        return []
    return [format_game_option(game) for game in games_data]

@app.callback(
    Output("selected_game_data", "data"),
    Input("live_game_selector", "value"),
    State("live_games_data", "data")
)
def store_selected_game(game_id, games_data):
    """Store selected game data"""
    if not game_id or not games_data:
        return None
    return next((game for game in games_data if game['id'] == game_id), None)

@app.callback(
    Output("team1", "value", allow_duplicate=True),
    Output("team2", "value", allow_duplicate=True), 
    Output("mins_left", "value", allow_duplicate=True),
    Output("secs_left", "value", allow_duplicate=True),
    Input("selected_game_data", "data"),
    prevent_initial_call=True
)
def auto_fill_from_game(game_data):
    """Auto-fill scores and time from selected game"""
    if not game_data:
        raise dash.exceptions.PreventUpdate
    
    return (
        game_data.get('home_score', 0),
        game_data.get('away_score', 0),
        game_data.get('minutes_left', 0),
        game_data.get('seconds_left', 0)
    )

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

# Analysis Tab Callbacks
@app.callback(
    Output("games-display", "children"),
    Output("team1_selector", "options"),
    Output("team2_selector", "options"),
    Input("today-btn", "n_clicks"),
    Input("tomorrow-btn", "n_clicks"),
    Input("week-btn", "n_clicks"),
    State("today_games_data", "data"),
    State("tomorrow_games_data", "data"),
    State("week_games_data", "data"),
    prevent_initial_call=True
)
def update_games_display(today_clicks, tomorrow_clicks, week_clicks, today_games, tomorrow_games, week_games):
    """Update games display based on button selection"""
    ctx_triggered = ctx.triggered[0]['prop_id'] if ctx.triggered else ''
    
    if 'tomorrow-btn' in ctx_triggered:
        games_to_show = tomorrow_games or []
        title = "Tomorrow's Games"
    elif 'week-btn' in ctx_triggered:
        games_to_show = week_games or []
        title = "This Week's Games"
    else:
        games_to_show = today_games or []
        title = "Today's Games"
    
    if not games_to_show:
        games_content = html.Div([
            html.P(f"No games found for {title.lower()}", 
                   className="text-center text-muted py-4")
        ])
        team_options = []
    else:
        games_content = html.Div([
            html.Div([
                html.H6(title, style={"color": "#e5e5e5", "display": "inline-block", "marginBottom": "8px"}),
                html.Span(f" ({len(games_to_show)} games)", 
                         style={"fontSize": "0.8rem", "color": "#666", "marginLeft": "8px"})
            ], className="mb-3"),
            
            html.Div([
                create_game_card(game) for game in games_to_show
            ], style={"maxHeight": "500px", "overflowY": "auto"})  # Add scroll for many games
        ])
        
        # Create team options from all games (for both dropdowns)
        team_options = []
        seen_teams = set()
        for game in games_to_show:
            for team_name, team_id in [(game['home_team'], game['home_team_id']), 
                                     (game['away_team'], game['away_team_id'])]:
                if team_id and team_name not in seen_teams:
                    team_options.append({"label": team_name, "value": team_id})
                    seen_teams.add(team_name)
        
        # Sort team options alphabetically for easier searching
        team_options.sort(key=lambda x: x['label'])
    
    return dbc.CardBody(games_content), team_options, team_options

def create_game_card(game):
    """Create a card for displaying game information"""
    status_color = "#4ade80" if game['is_live'] else "#71717a" if game['state'] == 'pre' else "#f87171"
    status_text = "LIVE" if game['is_live'] else "UPCOMING" if game['state'] == 'pre' else "FINAL"
    
    if game['is_final']:
        score_display = f"{game['away_score']}-{game['home_score']}"
        total_score = game['away_score'] + game['home_score']
    elif game['is_live']:
        score_display = f"{game['away_score']}-{game['home_score']}"
        total_score = game['away_score'] + game['home_score']
    else:
        score_display = "@"  # Use @ for upcoming games
        total_score = None
    
    # Parse game time for upcoming games
    time_display = game['clock']
    if game['state'] == 'pre':
        try:
            dt = datetime.fromisoformat(game['date'].replace('Z', '+00:00'))
            time_display = dt.strftime('%I:%M %p ET')
        except:
            time_display = game['clock']
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span(status_text, style={"fontSize": "0.7rem", "color": status_color, "fontWeight": "600"}),
                    html.Span(f"  {time_display}", style={"fontSize": "0.7rem", "color": "#666", "marginLeft": "8px"})
                ]),
                html.Div([
                    html.Span(game['away_team'], style={"fontSize": "0.85rem", "color": "#e5e5e5"}),
                    html.Span(f" {score_display} ", style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#fff", "margin": "0 6px"}),
                    html.Span(game['home_team'], style={"fontSize": "0.85rem", "color": "#e5e5e5"})
                ])
            ], width=7),
            dbc.Col([
                html.Div([
                    html.Span("Total: ", style={"fontSize": "0.7rem", "color": "#666"}),
                    html.Span(str(total_score) if total_score is not None else "—", 
                             style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#f59e0b"})
                ], className="text-right")
            ], width=5)
        ])
    ], style={
        "padding": "10px 12px",
        "margin": "6px 0",
        "border": "1px solid #2a2a2a",
        "borderRadius": "8px",
        "background": "#1a1a1a",
        "cursor": "pointer" if game['is_live'] else "default"
    })

def get_team_stats(team_id, num_games=10):
    """Helper function to get team statistics"""
    if not team_id:
        return None
    
    recent_games = fetch_team_recent_games(team_id, num_games)
    if not recent_games:
        return None
    
    # Calculate averages
    avg_team_score = sum(g['team_score'] for g in recent_games) / len(recent_games)
    avg_opp_score = sum(g['opponent_score'] for g in recent_games) / len(recent_games)
    avg_total = sum(g['total_points'] for g in recent_games) / len(recent_games)
    
    # Calculate additional stats
    home_games = [g for g in recent_games if g.get('location') == 'Home']
    away_games = [g for g in recent_games if g.get('location') == 'Away']
    
    home_avg = sum(g['team_score'] for g in home_games) / len(home_games) if home_games else 0
    away_avg = sum(g['team_score'] for g in away_games) / len(away_games) if away_games else 0
    
    return {
        'recent_games': recent_games,
        'avg_team_score': avg_team_score,
        'avg_opp_score': avg_opp_score,
        'avg_total': avg_total,
        'home_avg': home_avg,
        'away_avg': away_avg,
        'home_games': len(home_games),
        'away_games': len(away_games)
    }

def get_team_name_from_options(team_id, team_options):
    """Helper function to get team name from dropdown options"""
    if not team_id or not team_options:
        return None
    
    for option in team_options:
        if str(option.get('value')) == str(team_id):
            return option.get('label')
    return None

@app.callback(
    Output("games_count_display", "children"),
    Input("games_count_slider", "value")
)
def update_games_count_display(games_count):
    """Update the games count display"""
    return f"{games_count} games"

@app.callback(
    Output("team-analysis-display", "children"),
    Input("team1_selector", "value"),
    Input("team2_selector", "value"),
    Input("games_count_slider", "value"),
    State("team1_selector", "options"),
    State("team2_selector", "options")
)
def update_team_comparison(team1_id, team2_id, games_count, team1_options, team2_options):
    """Update team comparison analysis display"""
    if not team1_id and not team2_id:
        return dbc.CardBody([
            html.P("Select teams to compare their recent performance", className="text-center text-muted py-4")
        ])
    
    # Get team names from options
    team1_name = get_team_name_from_options(team1_id, team1_options) if team1_id else None
    team2_name = get_team_name_from_options(team2_id, team2_options) if team2_id else None
    
    # Get stats for both teams with specified games count
    team1_stats = get_team_stats(team1_id, games_count) if team1_id else None
    team2_stats = get_team_stats(team2_id, games_count) if team2_id else None
    
    if not team1_stats and not team2_stats:
        return dbc.CardBody([
            html.P("No data available for selected teams", className="text-center text-muted py-4")
        ])
    
    # Create comparison layout
    comparison_content = []
    
    # If both teams selected, show head-to-head comparison
    if team1_stats and team2_stats:
        implied_total = team1_stats['avg_team_score'] + team2_stats['avg_team_score']
        
        comparison_content.extend([
            html.Div([
                html.H6("Team Comparison", style={"color": "#e5e5e5", "textAlign": "center"}),
                html.Div([
                    html.Span("Implied Total: ", style={"fontSize": "0.9rem", "color": "#666"}),
                    html.Span(f"{implied_total:.1f}", style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#f59e0b"})
                ], className="text-center mb-4")
            ]),
            
            dbc.Row([
                # Team 1 Column
                dbc.Col([
                    html.H6(team1_name or "Team 1", className="text-center mb-3", 
                           style={"color": "#4ade80", "fontSize": "1rem", "fontWeight": "600"}),
                    html.Div("AVG PPG", className="metric-label text-center"),
                    html.Div(f"{team1_stats['avg_team_score']:.1f}", 
                            style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#4ade80", "textAlign": "center"}),
                    html.Div("vs OPP", className="metric-label text-center mt-2"),
                    html.Div(f"{team1_stats['avg_opp_score']:.1f}", 
                            style={"fontSize": "1.2rem", "color": "#f87171", "textAlign": "center"}),
                ], width=5),
                
                # VS Column
                dbc.Col([
                    html.Div("VS", style={"fontSize": "1.5rem", "fontWeight": "700", "color": "#666", 
                                        "textAlign": "center", "paddingTop": "40px"})
                ], width=2),
                
                # Team 2 Column  
                dbc.Col([
                    html.H6(team2_name or "Team 2", className="text-center mb-3", 
                           style={"color": "#3b82f6", "fontSize": "1rem", "fontWeight": "600"}),
                    html.Div("AVG PPG", className="metric-label text-center"),
                    html.Div(f"{team2_stats['avg_team_score']:.1f}", 
                            style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#3b82f6", "textAlign": "center"}),
                    html.Div("vs OPP", className="metric-label text-center mt-2"),
                    html.Div(f"{team2_stats['avg_opp_score']:.1f}", 
                            style={"fontSize": "1.2rem", "color": "#f87171", "textAlign": "center"}),
                ], width=5),
            ], className="mb-4"),
            
            html.Hr(style={"borderColor": "#333"}),
        ])
    
    # Show individual team stats
    team_labels = []
    if team1_stats and team2_stats:
        team_labels = [
            (team1_stats, "#4ade80", team1_name or "Team 1"), 
            (team2_stats, "#3b82f6", team2_name or "Team 2")
        ]
    elif team1_stats:
        team_labels = [(team1_stats, "#4ade80", team1_name or "Team Analysis")]
    elif team2_stats:
        team_labels = [(team2_stats, "#3b82f6", team2_name or "Team Analysis")]
    
    for i, (team_stats, team_color, team_label) in enumerate(team_labels):
        if not team_stats:
            continue
            
        if i > 0:  # Add separator between teams
            comparison_content.append(html.Hr(style={"borderColor": "#333", "margin": "20px 0"}))
        
        comparison_content.extend([
            html.H6(team_label, style={"color": team_color, "marginBottom": "12px"}),
            
            dbc.Row([
                dbc.Col([
                    html.Div("TOTAL PPG", className="metric-label"),
                    html.Div(f"{team_stats['avg_total']:.1f}", 
                            style={"fontSize": "1.2rem", "fontWeight": "600", "color": "#f59e0b"})
                ], className="text-center"),
                dbc.Col([
                    html.Div("HOME PPG", className="metric-label"),
                    html.Div(f"{team_stats['home_avg']:.1f}" if team_stats['home_games'] > 0 else "N/A", 
                            style={"fontSize": "1rem", "color": "#a3a3a3", "fontWeight": "500"})
                ], className="text-center"),
                dbc.Col([
                    html.Div("AWAY PPG", className="metric-label"), 
                    html.Div(f"{team_stats['away_avg']:.1f}" if team_stats['away_games'] > 0 else "N/A",
                            style={"fontSize": "1rem", "color": "#a3a3a3", "fontWeight": "500"})
                ], className="text-center"),
            ], className="mb-3"),
            
            # Recent games for this team (show last 5 for compact display)
            html.Div([
                html.Span(f"Recent Games ({len(team_stats['recent_games'][-5:])})", 
                         style={"fontSize": "0.85rem", "color": "#e5e5e5", "fontWeight": "500"}),
                html.Div([
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Span(f"vs {game['opponent']}", style={"fontSize": "0.75rem", "color": "#ccc"}),
                                html.Span(f" ({game.get('location', 'N/A')})", 
                                         style={"fontSize": "0.65rem", "color": "#666", "marginLeft": "4px"})
                            ], width=6),
                            dbc.Col([
                                html.Span(f"{game['team_score']}-{game['opponent_score']}", 
                                         style={"fontSize": "0.75rem", "fontWeight": "600", "color": "#fff"})
                            ], width=3),
                            dbc.Col([
                                html.Span(f"{game['total_points']}", 
                                         style={"fontSize": "0.75rem", "color": "#f59e0b"})
                            ], width=3)
                        ])
                    ], style={
                        "padding": "6px 8px",
                        "margin": "3px 0",
                        "border": "1px solid #2a2a2a",
                        "borderRadius": "4px",
                        "background": "#1a1a1a"
                    }) for game in team_stats['recent_games'][-5:]
                ], className="mt-2")
            ])
        ])
    
    return dbc.CardBody(comparison_content)


if __name__ == "__main__":
    app.run(debug=True)
