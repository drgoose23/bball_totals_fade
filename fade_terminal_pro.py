import dash
from dash import html, dcc, Output, Input, State, ALL, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
from datetime import datetime, timedelta, timezone
import json

ODDS_API_KEY = 'c9aaca97ab2496374d156e483571b6c6'
ODDS_BASE_URL = 'https://api.the-odds-api.com/v4'

# Track API usage locally
odds_api_calls_today = 0
odds_api_last_reset = datetime.now().strftime('%Y-%m-%d')

app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap"
], suppress_callback_exceptions=True)

def convert_utc_to_est(utc_time_str):
    """Convert UTC time string to EST/EDT (automatically handles DST)"""
    try:
        # Parse UTC time from ESPN API
        dt_utc = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
       
        year = dt_utc.year
       
        march_second_sunday = 8 + (6 - datetime(year, 3, 8).weekday()) % 7
        nov_first_sunday = 1 + (6 - datetime(year, 11, 1).weekday()) % 7
        
        dst_start = datetime(year, 3, march_second_sunday, 7, 0, tzinfo=timezone.utc)  # 2 AM EST = 7 AM UTC
        dst_end = datetime(year, 11, nov_first_sunday, 6, 0, tzinfo=timezone.utc)    # 2 AM EDT = 6 AM UTC
        
        # Check if we're in DST period
        if dst_start <= dt_utc < dst_end:
            # EDT (UTC-4)
            et_tz = timezone(timedelta(hours=-4))
        else:
            # EST (UTC-5) 
            et_tz = timezone(timedelta(hours=-5))
        
        dt_et = dt_utc.astimezone(et_tz)
        return dt_et
        
    except Exception as e:
        print(f"Error converting time: {e}")
        return None

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>CBB Fade Terminal</title>
        {%favicon%}
        {%css%}
        <style>
            * { box-sizing: border-box; }

            body {
                background: #111;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                color: #e5e5e5;
                line-height: 1.5;
                min-height: 100vh;
            }

            /* Cards */
            .card, .pro-card {
                background: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 10px;
                padding: 1.5rem;
            }
            .output-card {
                background: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 10px;
            }

            /* Inputs */
            .form-control {
                background: #1a1a1a !important;
                border: 1px solid #333 !important;
                color: #e5e5e5 !important;
                border-radius: 6px !important;
                font-size: 0.9rem;
                padding: 0.5rem 0.75rem;
            }
            .form-control:focus {
                border-color: #4a9eff !important;
                box-shadow: none !important;
                background: #1a1a1a !important;
            }
            .form-control::placeholder { color: #555 !important; }
            .input-group-text {
                background: #1a1a1a !important;
                border: 1px solid #333 !important;
                color: #888 !important;
                border-radius: 6px !important;
            }

            /* Score +/- buttons */
            .btn-adj {
                background: #222 !important;
                border: 1px solid #333 !important;
                color: #999 !important;
                border-radius: 6px;
                font-weight: 600;
                font-size: 0.85rem;
                min-width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .btn-adj:hover { background: #2a2a2a !important; color: #fff !important; border-color: #4a9eff !important; }

            /* Small +/- buttons */
            .btn-adj-small, .btn-micro {
                background: #222 !important;
                border: 1px solid #333 !important;
                color: #777 !important;
                border-radius: 4px !important;
                font-size: 0.7rem !important;
                padding: 0.15rem 0.35rem !important;
                min-width: 24px !important;
                height: 22px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }
            .btn-adj-small:hover, .btn-micro:hover { color: #fff !important; border-color: #4a9eff !important; }

            /* Labels */
            .label {
                font-size: 0.7rem;
                color: #888;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                margin-bottom: 0.4rem;
                font-weight: 600;
            }
            .metric-value {
                font-family: 'SF Mono', 'Consolas', monospace;
                font-weight: 700;
                font-size: 2rem;
                color: #fff;
                line-height: 1;
            }
            .metric-label {
                font-size: 0.7rem;
                font-weight: 600;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: #888;
                margin-bottom: 0.3rem;
            }

            /* Dropdowns */
            .dark-dropdown .Select-control {
                background: #1a1a1a !important;
                border: 1px solid #333 !important;
                color: #e5e5e5 !important;
                border-radius: 6px !important;
                min-height: 38px;
                font-size: 0.85rem;
            }
            .dark-dropdown .Select-placeholder { color: #555 !important; }
            .dark-dropdown .Select-value-label { color: #e5e5e5 !important; font-weight: 500; }
            .dark-dropdown .Select-input > input { color: #e5e5e5 !important; }
            .dark-dropdown .Select-menu-outer {
                background: #1a1a1a !important;
                border: 1px solid #333 !important;
                border-radius: 6px !important;
                margin-top: 2px;
            }
            .dark-dropdown .Select-menu { background: transparent !important; }
            .dark-dropdown .Select-option {
                color: #aaa !important;
                background: transparent !important;
                padding: 8px 12px !important;
                font-size: 0.85rem;
            }
            .dark-dropdown .Select-option.is-focused { background: #252525 !important; color: #fff !important; }
            .dark-dropdown .Select-option.is-selected { background: #222 !important; color: #4a9eff !important; }

            /* Buttons */
            .btn-primary {
                background: #4a9eff !important;
                border: none !important;
                border-radius: 6px !important;
                font-weight: 600 !important;
                color: #fff !important;
                font-size: 0.85rem !important;
            }
            .btn-primary:hover { background: #3a8eef !important; }
            .btn-secondary {
                background: #222 !important;
                border: 1px solid #333 !important;
                color: #aaa !important;
                border-radius: 6px !important;
                font-size: 0.85rem !important;
            }
            .btn-secondary:hover { background: #2a2a2a !important; color: #fff !important; }

            /* Slider */
            .rc-slider { background: #2a2a2a !important; height: 4px !important; }
            .rc-slider-track { background: #4a9eff !important; height: 4px !important; }
            .rc-slider-handle {
                background: #fff !important;
                border: 2px solid #4a9eff !important;
                width: 16px !important;
                height: 16px !important;
                margin-top: -6px !important;
                box-shadow: none !important;
            }
            .rc-slider-mark-text { color: #666 !important; font-size: 0.7rem !important; }

            /* Tabs */
            .nav-tabs {
                border-bottom: 1px solid #2a2a2a;
            }
            .nav-tabs .nav-link {
                background: transparent;
                border: none;
                color: #888;
                font-weight: 500;
                padding: 0.6rem 1.2rem;
                border-radius: 6px 6px 0 0;
                font-size: 0.85rem;
            }
            .nav-tabs .nav-link:hover { color: #e5e5e5; }
            .nav-tabs .nav-link.active {
                color: #4a9eff;
                background: transparent;
                border-bottom: 2px solid #4a9eff;
            }

            /* Headings - just white, no gradients */
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                color: #fff;
                -webkit-text-fill-color: #fff;
                background: none;
            }

            /* Game selector button */
            .game-selector-btn {
                background: #1a1a1a !important;
                border: 1px solid #333 !important;
                border-radius: 6px !important;
            }
            .game-selector-btn:hover { border-color: #4a9eff !important; }

            /* Game cards in modal */
            .game-card {
                background: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                padding: 0.8rem 1rem;
                margin: 0.4rem 0;
                cursor: pointer;
            }
            .game-card:hover { background: #252525; border-color: #4a9eff; }
            .game-time { color: #4a9eff; font-weight: 600; font-size: 0.8rem; margin-bottom: 0.3rem; }
            .game-matchup { color: #e5e5e5; font-weight: 500; font-size: 0.9rem; }
            .game-details { color: #888; font-size: 0.8rem; }
            .live-indicator { color: #ef4444; font-weight: 600; font-size: 0.75rem; }

            /* Analysis cards */
            .analysis-game-card {
                background: #1e1e1e !important;
                border: 1px solid #2a2a2a !important;
                border-radius: 8px !important;
            }
            .analysis-game-card:hover { background: #252525 !important; border-color: #4a9eff !important; }

            /* Team logos */
            .team-logo {
                object-fit: contain;
                background: #1a1a1a;
                border-radius: 4px;
                border: 1px solid #2a2a2a;
            }
            .team-logo[src=""], .team-logo:not([src]) { display: none; }

            /* Refresh button */
            #refresh_game_button { transition: all 0.15s ease; }
            #refresh_game_button:hover {
                background: rgba(74, 158, 255, 0.1) !important;
                border-color: #4a9eff !important;
                color: #4a9eff !important;
                transform: rotate(180deg);
            }

            /* Scrollbar */
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: #1a1a1a; }
            ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: #444; }

            /* Hide number spinners */
            input[type="number"]::-webkit-outer-spin-button,
            input[type="number"]::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
            input[type="number"] { -moz-appearance: textfield; }
        </style>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                document.addEventListener('wheel', function(e) {
                    if (document.activeElement.type === 'number') { e.preventDefault(); }
                }, { passive: false });
                document.addEventListener('keydown', function(e) {
                    if (e.target.type === 'number' && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
                        if (document.activeElement !== e.target) { e.preventDefault(); }
                    }
                });
            });
        </script>
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

def get_team_logo_url(team_data):
    """Get team logo URL from ESPN data with fallback options"""
    if not team_data:
        return ''
    
    # Try multiple possible logo fields from ESPN
    logo_fields = ['logo', 'logos', 'logoDark', 'logoLight']
    
    for field in logo_fields:
        logo_data = team_data.get(field)
        if logo_data:
            # Handle both string URLs and logo objects
            if isinstance(logo_data, str):
                return logo_data
            elif isinstance(logo_data, list) and len(logo_data) > 0:
                # Take first logo if it's a list
                logo_item = logo_data[0]
                if isinstance(logo_item, dict):
                    return logo_item.get('href', logo_item.get('url', ''))
                elif isinstance(logo_item, str):
                    return logo_item
            elif isinstance(logo_data, dict):
                return logo_data.get('href', logo_data.get('url', ''))
    
    # ESPN fallback URL pattern (common for college basketball)
    team_id = team_data.get('id')
    if team_id:
        # ESPN's standard logo URL pattern
        return f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team_id}.png"
    
    return ''

def fetch_games_by_date(date_str=None):
    """Fetch college basketball games from ESPN's internal API for a specific date"""
    try:
        if date_str:
            # limit=300 and groups=50 ensure we get ALL games, not just top 25
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date_str}&limit=300&groups=50"
        else:
            # For "today", use current date regardless of time - college games often span midnight
            today_str = datetime.now().strftime('%Y%m%d')
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today_str}&limit=300&groups=50"
        
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
            
            # Extract team logos from ESPN data
            home_team_data = home_team.get('team', {})
            away_team_data = away_team.get('team', {})
            
            # Debug: Print available team data keys (remove after testing)
            if len(games) == 0:  # Only print for first game to avoid spam
                print(f"DEBUG: Home team data keys: {list(home_team_data.keys())}")
                if 'logos' in home_team_data:
                    print(f"DEBUG: Home team logos: {home_team_data.get('logos')}")
                if 'logo' in home_team_data:
                    print(f"DEBUG: Home team logo: {home_team_data.get('logo')}")
                print(f"DEBUG: Away team data keys: {list(away_team_data.keys())}")
            
            game_info = {
                'id': event.get('id'),
                'home_team': home_team_data.get('displayName', 'Home'),
                'away_team': away_team_data.get('displayName', 'Away'),
                'home_team_id': home_team_data.get('id'),
                'away_team_id': away_team_data.get('id'),
                'home_team_logo': get_team_logo_url(home_team_data),
                'away_team_logo': get_team_logo_url(away_team_data),
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
                    period = game_info['period']
                    if ':' in clock:
                        mins, secs = clock.split(':')
                        minutes_left = int(mins)
                        seconds_left = int(secs.split('.')[0])  # Remove decimals
                        
                        # Auto-convert to full game time: add 20 min if first half
                        if period == 1:
                            minutes_left += 20
                        
                        game_info['minutes_left'] = minutes_left
                        game_info['seconds_left'] = seconds_left
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

# ===== ODDS API FUNCTIONS =====

def get_basketball_odds(sport_key='basketball_ncaab'):
    """Get odds for college basketball games - tracks API usage"""
    global odds_api_calls_today, odds_api_last_reset
    
    # Reset daily counter
    today = datetime.now().strftime('%Y-%m-%d')
    if today != odds_api_last_reset:
        odds_api_calls_today = 0
        odds_api_last_reset = today
    
    url = f"{ODDS_BASE_URL}/sports/{sport_key}/odds"
    
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'totals',
        'oddsFormat': 'american',
        'dateFormat': 'iso'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Track usage from response headers
        remaining = response.headers.get('x-requests-remaining', '?')
        used = response.headers.get('x-requests-used', '?')
        odds_api_calls_today += 1
        
        games = response.json()
        print(f"📊 Odds API: {len(games)} games | Used: {used} | Remaining: {remaining} | Today's calls: {odds_api_calls_today}")
        return games
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Odds API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text[:200]}")
        return []

def extract_betting_totals(odds_games):
    """Extract betting totals from odds data"""
    betting_data = {}
    
    for game in odds_games:
        # Create key from team names for matching
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Extract totals from all sportsbooks
        totals = []
        for bookmaker in game.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market['key'] == 'totals':
                    for outcome in market['outcomes']:
                        if outcome['name'] == 'Over':
                            totals.append(outcome['point'])
        
        if totals:
            avg_total = sum(totals) / len(totals)
            total_range = max(totals) - min(totals) if len(totals) > 1 else 0
            
            # Store with multiple possible team name combinations
            game_keys = [
                f"{away_team}|{home_team}",
                f"{home_team}|{away_team}"
            ]
            
            betting_info = {
                'avg_total': avg_total,
                'total_range': total_range,
                'num_books': len(totals),
                'commence_time': game['commence_time']
            }
            
            for key in game_keys:
                betting_data[key] = betting_info
    
    return betting_data

def match_espn_with_odds(espn_games, betting_data):
    """Match ESPN games with betting lines"""
    matched_games = []
    
    for espn_game in espn_games:
        home_team = espn_game.get('home_team', '')
        away_team = espn_game.get('away_team', '')
        
        # Try to match with betting data
        match_key = f"{away_team}|{home_team}"
        betting_info = betting_data.get(match_key)
        
        # Add betting data if found
        enhanced_game = espn_game.copy()
        if betting_info:
            enhanced_game.update({
                'betting_total': betting_info['avg_total'],
                'betting_range': betting_info['total_range'],
                'num_sportsbooks': betting_info['num_books'],
                'has_betting_line': True
            })
        else:
            enhanced_game['has_betting_line'] = False
        
        matched_games.append(enhanced_game)
    
    return matched_games

def format_game_option(game):
    """Format game data for dropdown display - clean and professional"""
    def shorten_team_name(name, max_len=12):
        """Aggressively shorten team names for clean display"""
        if len(name) <= max_len:
            return name
        
        # Smart abbreviations
        replacements = {
            'University': 'U',
            'College': 'C', 
            'State': 'St',
            'Northern': 'N',
            'Southern': 'S',
            'Eastern': 'E',
            'Western': 'W',
            'Central': 'C',
            'International': 'Intl',
            'Technology': 'Tech',
            'Institute': 'Tech'
        }
        
        for full, abbrev in replacements.items():
            name = name.replace(full, abbrev)
            if len(name) <= max_len:
                return name
        
        # If still too long, truncate
        return name[:max_len-1] + "…"
    
    away = shorten_team_name(game['away_team'])
    home = shorten_team_name(game['home_team'])
    
    if game['is_live']:
        # Show raw ESPN time - user controls conversion with toggle
        display_clock = game['clock']
        
        score = f"{game['away_score']}-{game['home_score']}"
        return {
            'label': f"{away} {score} {home} • {display_clock}",
            'value': game['id']
        }
    else:
        try:
            dt_est = convert_utc_to_est(game['date'])
            if dt_est:
                time = dt_est.strftime('%I:%M%p EST').lower().replace('m', '')
            else:
                time = game['clock']
        except:
            time = game['clock']
        
        return {
            'label': f"{time} {away} @ {home}",
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
        html.Div([
            # Main input field (normal like others)
            dbc.Input(
                id=input_id, 
                type="number", 
                style={"textAlign": "center", "marginBottom": "0.5rem"}
            ),
            # Small +/- buttons below the input
            html.Div([
                dbc.Button("−", id={"type": "dec", "index": input_id}, 
                          className="btn-micro", size="sm"),
                dbc.Button("+", id={"type": "inc", "index": input_id}, 
                          className="btn-micro", size="sm"),
            ], style={
                "display": "flex", 
                "gap": "0.25rem", 
                "justifyContent": "center"
            })
        ])
    ], className="mb-3")


app.layout = dbc.Container([
    # Game Reminder (top-left)
    html.Div([
        dbc.Input(
            id="game_reminder_input",
            type="text",
            placeholder="Game reminder...",
            style={"width": "200px", "fontSize": "0.8rem"}
        )
    ], style={"position": "absolute", "top": "12px", "left": "12px", "zIndex": "1000"}),
    
    # Header
    html.Div([
        html.H3("CBB Fade Terminal", style={"marginBottom": "0", "fontSize": "1.4rem"}),
    ], className="text-center", style={"padding": "1.5rem 0 1rem 0"}),
    
    # Tabs
    dbc.Tabs([
        dbc.Tab(label="Live Analysis", tab_id="fade-tab"),
        dbc.Tab(label="Research", tab_id="analysis-tab"),
    ], id="main-tabs", active_tab="fade-tab", className="mb-3"),
    
    html.Div(id="tab-content"),
    
    # Stores
    dcc.Store(id="opening_line", data=None),
    dcc.Store(id="live_games_data", data=[]),
    dcc.Store(id="selected_game_data", data=None),
    dcc.Store(id="persistent_game_selection", data=None),
    dcc.Store(id="today_games_data", data=[]),
    dcc.Store(id="tomorrow_games_data", data=[]),
    dcc.Store(id="week_games_data", data=[]),
    dcc.Store(id="betting_odds_data", data={}),
    dcc.Store(id="odds_api_status", data={}),
    dcc.Store(id="game_reminder_store", data="", storage_type='local'),
    dcc.Interval(id="refresh_games", interval=30*1000, n_intervals=0),
    dcc.Interval(id="refresh_odds", interval=5*60*1000, n_intervals=0),
    
    # Game Selection Modal
    dbc.Modal([
        dbc.ModalHeader([
            html.H5("Select Game", style={"margin": "0"}),
        ], style={"background": "#1a1a1a", "borderBottom": "1px solid #2a2a2a"}),
        dbc.ModalBody([
            dbc.Input(
                id="game_search_input",
                placeholder="Search teams...", 
                style={"marginBottom": "0.75rem"}
            ),
            html.Div(id="game_selection_grid", style={"maxHeight": "50vh", "overflowY": "auto"})
        ], style={"background": "#1a1a1a", "padding": "1rem"}),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="game_modal_close", className="btn-secondary", size="sm")
        ], style={"background": "#1a1a1a", "borderTop": "1px solid #2a2a2a"})
    ], id="game_selection_modal", is_open=False, centered=True, size="lg", backdrop="static")
], fluid=True, style={"maxWidth": "1200px", "padding": "0 1.5rem"})


def create_fade_tab():
    """Create the fade system tab layout"""
    return dbc.Row([
        # Inputs
        dbc.Col([
            html.Div([
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
                            html.Span(" (ESPN)", style={"fontSize": "0.65rem", "color": "#666", "marginLeft": "4px"})
                        ]),
                        html.Div([
                            html.Button(
                                id="game_selector_button",
                                children=[
                                    html.Div("Select Game", id="game_selector_text", style={"color": "#888"}),
                                    html.Div("⌄", style={"marginLeft": "auto"})
                                ],
                                className="game-selector-btn",
                                style={
                                    "width": "100%", 
                                    "display": "flex", 
                                    "alignItems": "center",
                                    "justifyContent": "space-between",
                                    "padding": "0.5rem 0.75rem",
                                    "cursor": "pointer",
                                }
                        ),
                        html.Button(
                            "↻",
                            id="refresh_game_button",
                            className="btn btn-secondary",
                            style={
                                "width": "36px",
                                "height": "36px", 
                                "marginLeft": "6px",
                                "fontSize": "1rem",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                            },
                            title="Refresh live scores and time"
                        ),
                        ], style={"display": "flex", "alignItems": "start"}),
                        # Store selected game ID and button text separately for persistence
                        dcc.Store(id="live_game_selector", data=None),
                        dcc.Store(id="selected_game_text", data="Select Game"),
                    ], className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col(score_input("Home", "team1"), width=6),
                        dbc.Col(score_input("Away", "team2"), width=6),
                    ]),
                    
                    html.Div([
                        html.Div("Live Total", className="label"),
                        dbc.Input(id="live_total", type="number"),
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Div("Minutes", className="label"),
                            dbc.Input(id="mins_left", type="number", min=0)
                        ], width=6),
                        dbc.Col([
                            html.Div("Seconds", className="label"),
                            dbc.Input(id="secs_left", type="number", min=0, max=59)
                        ], width=6),
                    ], className="mb-2"),
                    
                    # First Half Toggle
                    html.Div([
                        dbc.Checklist(
                            id="first_half_toggle",
                            options=[{"label": "First Half (+20 min)", "value": "first_half"}],
                            value=[],
                            inline=True,
                            style={"fontSize": "0.75rem", "color": "#888"}
                        )
                    ], className="mb-3", style={"textAlign": "center"}),
                    
                    html.Div([
                        html.Div("Your Under (optional)", className="label"),
                        dbc.Input(id="my_bet", type="number"),
                    ], className="mb-4"),
                    
                    html.Div([
                        html.Div([
                            html.Span("Threshold: ", style={"color": "#888", "fontSize": "0.75rem"}),
                            html.Span(id="thresh_val", style={"color": "#e5e5e5", "fontWeight": "600"})
                        ], className="mb-2"),
                        dcc.Slider(id="threshold_slider", min=2.5, max=6, step=0.25, value=4.0,
                                   marks={2.5: '2.5', 4: '4', 6: '6'})
                    ])
            ], className="pro-card")
        ], lg=4, md=5),
        dbc.Col([
            html.Div(id="output"),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div("Analysis Depth", className="label"),
                        dbc.InputGroup([
                            dbc.Input(
                                id="live_analysis_games_input",
                                type="text",
                                value="5",
                                style={"textAlign": "center", "maxWidth": "60px"}
                            ),
                            dbc.InputGroupText("games")
                        ], size="sm")
                    ], width=4),
                    dbc.Col(width=8)
                ], className="mb-3")
            ], id="analysis_controls", style={"display": "none"}),
            html.Div(id="team_context_display", className="mt-3")  
        ], lg=8, md=7)
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
                                clearable=True,
                                searchable=True,
                                className="dark-dropdown"
                            ),
                        ], width=6),
                        dbc.Col([
                            dcc.Dropdown(
                                id="team2_selector", 
                                options=[],
                                clearable=True,
                                searchable=True,
                                className="dark-dropdown"
                            ),
                        ], width=6),
                    ]),
                ], className="mb-3"),
                
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Div("Lookback Games", className="label"),
                            dbc.InputGroup([
                                dbc.Input(
                                    id="games_count_input",
                                    type="text",
                                    value="5",
                                    style={"textAlign": "center", "maxWidth": "60px"}
                                ),
                                dbc.InputGroupText("games")
                            ], size="sm")
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                html.Span("Analysis Based On: ", className="label", style={"display": "inline-block", "marginRight": "6px"}),
                                html.Span(id="games_count_display", style={"fontSize": "0.8rem", "color": "#4a9eff", "fontWeight": "600"})
                            ], style={"marginTop": "1rem"})
                        ], width=9),
                    ]),
                ], className="mb-3"),
                
                html.Div(id="team-analysis-display", className="card", style={"minHeight": "400px"})
            ], width=6)
        ]),
        
        # Hidden button for callback compatibility
        html.Button(
            id="game_selector_button",
            style={"display": "none"}
        )
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
    # Don't force "0" to appear - keep inputs clean
    t1 = t1 if t1 is not None else None
    t2 = t2 if t2 is not None else None
    d = 1 if t["type"] == "inc" else -1
    if t["index"] == "team1": 
        t1 = max(0, (t1 or 0) + d)
        t1 = None if t1 == 0 else t1  # Don't show 0
    elif t["index"] == "team2": 
        t2 = max(0, (t2 or 0) + d)  
        t2 = None if t2 == 0 else t2  # Don't show 0
    return t1, t2


# ESPN API Callbacks
# ===== ESPN REFRESH (every 30 sec - FREE) =====
@app.callback(
    Output("live_games_data", "data"),
    Output("today_games_data", "data"),
    Output("tomorrow_games_data", "data"),
    Output("week_games_data", "data"),
    Input("refresh_games", "n_intervals")
)
def refresh_espn_games(n):
    """Fetch games from ESPN every 30 sec (FREE - no API limit)"""
    # Get extended date ranges for more games
    today = datetime.now().strftime('%Y%m%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    # Include yesterday's late games that might still be live  
    yesterday_games = fetch_games_by_date(yesterday)
    today_games = fetch_games_by_date(today)
    tomorrow_games = fetch_games_by_date(tomorrow)
    
    # Combine all current/live games from multiple days
    all_live_candidates = yesterday_games + today_games + tomorrow_games
    live_games_expanded = [g for g in all_live_candidates if g['state'] in ['in', 'pre']]
    
    # Get week's games (next 10 days for more options)
    week_games = []
    for days_ahead in range(-1, 10):
        date_str = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y%m%d')
        games = fetch_games_by_date(date_str)
        week_games.extend(games)
    
    # Remove duplicates based on game ID
    seen_ids = set()
    unique_week_games = []
    for game in week_games:
        if game['id'] not in seen_ids:
            unique_week_games.append(game)
            seen_ids.add(game['id'])
    
    print(f"🏀 ESPN: {len(live_games_expanded)} live/upcoming | {len(unique_week_games)} total games")
    return live_games_expanded, today_games, tomorrow_games, unique_week_games


# ===== ODDS API REFRESH (every 5 min - PAID, ~288 calls/day max) =====
@app.callback(
    Output("betting_odds_data", "data"),
    Output("odds_api_status", "data"),
    Input("refresh_odds", "n_intervals"),
)
def refresh_odds_data(n):
    """Fetch betting odds every 5 min (PAID - conserves API credits)
    
    Budget math at 5-min interval:
      12 calls/hr × 12 hrs active use = ~144 calls/day
      144 × 30 days = ~4,320 calls/month (well under 20k limit)
    """
    try:
        odds_games = get_basketball_odds()
        betting_data = extract_betting_totals(odds_games)
        
        status = {
            "remaining": "?",
            "used": "?",
            "last_refresh": datetime.now().strftime('%I:%M %p'),
            "matched_games": len(betting_data),
            "calls_today": odds_api_calls_today
        }
        
        print(f"💰 Odds API: Matched {len(betting_data)} games with betting lines")
        return betting_data, status
    except Exception as e:
        print(f"❌ Error fetching odds: {e}")
        status = {
            "remaining": "?",
            "used": "?", 
            "last_refresh": f"Error at {datetime.now().strftime('%I:%M %p')}",
            "matched_games": 0,
            "calls_today": odds_api_calls_today
        }
        return {}, status

# Modal Callbacks
@app.callback(
    Output("game_selection_modal", "is_open"),
    [Input("game_selector_button", "n_clicks"),
     Input("game_modal_close", "n_clicks"),
     Input({"type": "game-card", "index": ALL}, "n_clicks")],
    [State("game_selection_modal", "is_open"),
     State("main-tabs", "active_tab")],
    prevent_initial_call=True
)
def toggle_game_modal(open_clicks, close_clicks, game_clicks, is_open, active_tab):
    """Open/close game selection modal"""
    try:
        # Only process if we're on the fade tab (where the button exists)
        if active_tab != "fade-tab":
            return False
            
        # Only open when button is explicitly clicked
        if ctx.triggered_id == "game_selector_button" and open_clicks:
            return True
        # Close when cancel clicked or any game card clicked
        elif ctx.triggered_id == "game_modal_close" or (game_clicks and any(game_clicks)):
            return False
        # Default to closed state
        return False
    except Exception:
        # Graceful fallback for any callback issues
        return False

@app.callback(
    Output("game_search_input", "value"),
    Input("game_selection_modal", "is_open"),
    prevent_initial_call=True
)
def clear_search_on_modal_open(is_open):
    """Clear search input when modal opens"""
    if is_open:
        return ""  # Clear the search when modal opens
    return dash.no_update

@app.callback(
    Output("game_selection_grid", "children"),
    [Input("live_games_data", "data"),
     Input("game_search_input", "value")]
)
def populate_game_modal(games_data, search_term):
    """Populate modal with game cards, filtered by search term"""
    if not games_data:
        return html.Div("No games available", style={"color": "#888", "textAlign": "center", "padding": "2rem"})
    
    # Filter games based on search term
    filtered_games = games_data
    if search_term and search_term.strip():
        search_lower = search_term.strip().lower()
        filtered_games = []
        for game in games_data:
            home_team = game.get('home_team', '').lower()
            away_team = game.get('away_team', '').lower()
            if search_lower in home_team or search_lower in away_team:
                filtered_games.append(game)
    
    if not filtered_games:
        return html.Div(f"No games found matching '{search_term}'", 
                       style={"color": "#888", "textAlign": "center", "padding": "2rem"})
    
    game_cards = []
    for i, game in enumerate(filtered_games):
        if game['is_live']:
            # Show raw ESPN time - user controls conversion with toggle
            display_clock = game['clock']
            
            time_display = html.Div([
                html.Span("LIVE", className="live-indicator"),
                html.Span(f" • {display_clock}", style={"color": "#888", "fontSize": "0.8rem"})
            ], className="game-time")
            details = f"{game['away_score']}-{game['home_score']} • Total: {game['away_score'] + game['home_score']}"
        else:
            try:
                dt_est = convert_utc_to_est(game['date'])
                if dt_est:
                    time_str = dt_est.strftime('%I:%M%p EST').lower().replace('m', '')
                else:
                    time_str = game['clock']
            except:
                time_str = game['clock']
            time_display = html.Div(time_str, className="game-time")
            details = "Upcoming"
        
        card = html.Div([
            time_display,
            html.Div([
                # Away team with logo
                html.Span([
                    html.Img(src=game.get('away_team_logo', ''), 
                            style={"width": "20px", "height": "20px", "marginRight": "6px", "borderRadius": "3px", "verticalAlign": "middle"},
                            className="team-logo") if game.get('away_team_logo') else None,
                    html.Span(game['away_team'], style={"verticalAlign": "middle"})
                ], style={"display": "inline-flex", "alignItems": "center"}),
                
                html.Span(" @ ", style={"margin": "0 8px", "color": "#666"}),
                
                # Home team with logo  
                html.Span([
                    html.Img(src=game.get('home_team_logo', ''), 
                            style={"width": "20px", "height": "20px", "marginRight": "6px", "borderRadius": "3px", "verticalAlign": "middle"},
                            className="team-logo") if game.get('home_team_logo') else None,
                    html.Span(game['home_team'], style={"verticalAlign": "middle"})
                ], style={"display": "inline-flex", "alignItems": "center"})
            ], className="game-matchup", style={"display": "flex", "alignItems": "center"}),
            html.Div(details, className="game-details")
        ], className="game-card", id={"type": "game-card", "index": i}, n_clicks=0)
        
        game_cards.append(card)
    
    return game_cards

@app.callback(
    [Output("live_game_selector", "data"),
     Output("selected_game_text", "data")],
    [Input({"type": "game-card", "index": ALL}, "n_clicks")],
    [State("live_games_data", "data")],
    prevent_initial_call=True
)
def select_game_from_modal(game_clicks, games_data):
    """Handle game selection from modal"""
    print(f"DEBUG: select_game_from_modal called with clicks: {game_clicks}, games_data length: {len(games_data) if games_data else 0}")
    
    # Don't reset if no clicks - this was causing the reset!
    if not any(game_clicks):
        print("DEBUG: No clicks detected - preventing update to avoid reset")
        raise dash.exceptions.PreventUpdate
    
    if not games_data:
        print("DEBUG: No games data - preventing update")
        raise dash.exceptions.PreventUpdate
    
    # Find which game was clicked (look for the highest click count)
    clicked_index = None
    max_clicks = 0
    for i, clicks in enumerate(game_clicks):
        if clicks and clicks > max_clicks:
            max_clicks = clicks
            clicked_index = i
    
    if clicked_index is not None and clicked_index < len(games_data):
        selected_game = games_data[clicked_index]
        
        # Create display text with live score if available
        if selected_game.get('is_live'):
            game_text = f"{selected_game['away_team']} {selected_game['away_score']}-{selected_game['home_score']} {selected_game['home_team']}"
        else:
            game_text = f"{selected_game['away_team']} @ {selected_game['home_team']}"
        
        # Truncate if too long
        if len(game_text) > 40:
            game_text = game_text[:37] + "..."
            
        print(f"DEBUG: Selected game ID: {selected_game['id']}, Text: {game_text}")
        return selected_game['id'], game_text
    
    print("DEBUG: No valid game found - preventing update")
    raise dash.exceptions.PreventUpdate

# Separate callback to update button text from persistent storage
@app.callback(
    Output("game_selector_text", "children"),
    Input("selected_game_text", "data")
)
def update_button_text(game_text):
    """Update button text from persistent storage"""
    return game_text or "Select Game"

# Removed legacy dropdown callback - now using modal selection only

@app.callback(
    [Output("selected_game_data", "data"),
     Output("persistent_game_selection", "data")],
    Input("live_game_selector", "data"),
    State("live_games_data", "data")
)
def store_selected_game(game_id, games_data):
    """Store selected game data in both temporary and persistent storage"""
    if not game_id or not games_data:
        print(f"DEBUG: store_selected_game - No game_id ({game_id}) or games_data ({len(games_data) if games_data else 0} games)")
        return None, None
    
    # Handle both string and int game IDs
    selected_game = next((game for game in games_data if str(game['id']) == str(game_id)), None)
    
    if selected_game:
        print(f"DEBUG: Found selected game: {selected_game['away_team']} @ {selected_game['home_team']} (ID: {selected_game['id']})")
        # Store the same data in both places - one for form auto-fill, one for persistence
        return selected_game, selected_game
    else:
        print(f"DEBUG: No game found with ID: {game_id}")
        print(f"Available game IDs: {[game['id'] for game in games_data[:5]]}")  # Show first 5 IDs
        return None, None

@app.callback(
    Output("team1", "value", allow_duplicate=True),
    Output("team2", "value", allow_duplicate=True), 
    Output("live_total", "value", allow_duplicate=True),
    Output("mins_left", "value", allow_duplicate=True),
    Output("secs_left", "value", allow_duplicate=True),
    Input("selected_game_data", "data"),
    State("betting_odds_data", "data"),
    prevent_initial_call=True
)
def auto_fill_from_game(game_data, betting_odds_data):
    """Auto-fill scores, time, and live total from selected game"""
    if not game_data:
        raise dash.exceptions.PreventUpdate
    
    # Extract scores from ESPN data structure
    home_score = int(game_data.get('home_score', 0) or 0)
    away_score = int(game_data.get('away_score', 0) or 0)
    
    # Don't show "0" unless it's an actual score from live game
    if home_score == 0 and not game_data.get('is_live'):
        home_score = None
    if away_score == 0 and not game_data.get('is_live'):
        away_score = None
    
    # Parse time from clock
    minutes_left = 0
    seconds_left = 0
    
    clock = game_data.get('clock', '0:00')
    period = game_data.get('period', 2)
    is_live = game_data.get('is_live', False)
    
    if is_live and clock:
        try:
            if ':' in clock:
                time_parts = clock.split(':')
                minutes_left = int(time_parts[0])
                seconds_part = time_parts[1].split('.')[0]
                seconds_left = int(seconds_part)
                
                # Auto-convert to full game time: add 20 min if first half
                if period == 1:
                    minutes_left += 20
        except (ValueError, IndexError):
            minutes_left = 0
            seconds_left = 0
    
    # Get betting odds total for live_total - ONLY if betting line exists
    live_total = None
    if betting_odds_data and game_data:
        away_team_name = game_data.get('away_team', '')
        home_team_name = game_data.get('home_team', '')
        
        match_key1 = f"{away_team_name}|{home_team_name}"
        match_key2 = f"{home_team_name}|{away_team_name}"
        
        betting_info = betting_odds_data.get(match_key1) or betting_odds_data.get(match_key2)
        if betting_info:
            live_total = betting_info.get('avg_total')
            if live_total:
                print(f"DEBUG: ✅ Found betting total: {live_total}")
    
    # Leave live_total as None if no betting line found
    if live_total is None:
        print(f"DEBUG: No betting line found - leaving Live Total empty")
    
    print(f"DEBUG: Auto-filling - away:{away_score}, home:{home_score}, total:{live_total}, time:{minutes_left}:{seconds_left:02d}")
    
    return (
        away_score,
        home_score,
        live_total,
        minutes_left,
        seconds_left
    )

@app.callback(
    [Output("team1", "value", allow_duplicate=True),
     Output("team2", "value", allow_duplicate=True),
     Output("mins_left", "value", allow_duplicate=True),
     Output("secs_left", "value", allow_duplicate=True)],
    Input("refresh_game_button", "n_clicks"),
    [State("persistent_game_selection", "data"),
     State("live_games_data", "data")],
    prevent_initial_call=True
)
def refresh_game_data(n_clicks, selected_game_data, games_data):
    """Refresh only the scores and time from ESPN without changing other inputs"""
    if not n_clicks or not selected_game_data:
        raise dash.exceptions.PreventUpdate
    
    # Get the selected game ID
    game_id = selected_game_data.get('id')
    if not game_id:
        raise dash.exceptions.PreventUpdate
    
    try:
        # Fetch fresh data from ESPN for this specific game
        fresh_games = fetch_live_games()  # Gets current live games
        
        # Find our specific game in the fresh data
        fresh_game_data = None
        for game in fresh_games:
            if str(game.get('id')) == str(game_id):
                fresh_game_data = game
                break
        
        if not fresh_game_data:
            print(f"DEBUG: Could not find game {game_id} in fresh ESPN data")
            raise dash.exceptions.PreventUpdate
        
        # Extract fresh scores and time
        home_score = fresh_game_data.get('home_score')
        away_score = fresh_game_data.get('away_score')
        
        # Handle time parsing with first/second half conversion
        minutes_left = None
        seconds_left = None
        
        if fresh_game_data.get('is_live') and fresh_game_data.get('clock'):
            try:
                clock = fresh_game_data.get('clock', '0:00')
                period = fresh_game_data.get('period', 2)
                
                if ':' in clock:
                    time_parts = clock.split(':')
                    minutes_left = int(time_parts[0])
                    seconds_part = time_parts[1].split('.')[0]  # Remove decimal part
                    seconds_left = int(seconds_part)
                    
                    # No automatic conversion - user controls via First Half toggle
            except (ValueError, IndexError):
                minutes_left = None
                seconds_left = None
        
        print(f"DEBUG: Refreshed scores - Home: {home_score}, Away: {away_score}, Time: {minutes_left}:{seconds_left:02d}")
        
        return (
            home_score if home_score is not None else dash.no_update,
            away_score if away_score is not None else dash.no_update, 
            minutes_left if minutes_left is not None else dash.no_update,
            seconds_left if seconds_left is not None else dash.no_update
        )
        
    except Exception as e:
        print(f"DEBUG: Error refreshing game data: {e}")
        raise dash.exceptions.PreventUpdate

@app.callback(
    Output("mins_left", "value", allow_duplicate=True),
    Input("first_half_toggle", "value"),
    State("mins_left", "value"),
    prevent_initial_call=True
)
def handle_first_half_toggle(toggle_value, current_mins):
    """Handle first half toggle - add/subtract 20 minutes"""
    if current_mins is None:
        current_mins = 0
    
    is_first_half_checked = "first_half" in (toggle_value or [])
    
    # Determine if we should add or subtract 20
    if is_first_half_checked:
        # Toggle was just checked - add 20 minutes
        new_mins = current_mins + 20
        print(f"DEBUG: First Half toggle CHECKED - Adding 20: {current_mins} → {new_mins}")
    else:
        # Toggle was just unchecked - subtract 20 minutes (but not below 0)
        new_mins = max(0, current_mins - 20)
        print(f"DEBUG: First Half toggle UNCHECKED - Subtracting 20: {current_mins} → {new_mins}")
    
    return new_mins

@app.callback(
    Output("output", "children"),
    Input("team1", "value"), Input("team2", "value"), Input("live_total", "value"),
    Input("mins_left", "value"), Input("secs_left", "value"), Input("my_bet", "value"),
    Input("period_type", "value"), Input("threshold_slider", "value")
)
def update_output(t1, t2, live_total, mins, secs, my_bet, period, threshold):
    # Handle None values for calculation without forcing UI display
    mins_calc = mins if mins is not None else 0
    secs_calc = secs if secs is not None else 0
    min_left = mins_calc + secs_calc / 60
    
    if None in [t1, t2, live_total, period] or min_left <= 0:
        return html.Div([
            html.Div([
                html.Span("Awaiting input", style={"color": "#555", "fontSize": "0.85rem"})
            ], className="text-center py-5")
        ], className="output-card", style={"minHeight": "400px", "display": "flex", 
                                           "alignItems": "center", "justifyContent": "center"})
    
    r = get_fade_analysis(t1, t2, live_total, min_left, my_bet, period, threshold)
    pct = r['pct']
    over_thresh = r['required_pace'] >= r['threshold']
    curr = r['actual_pace']
    req = r['required_pace']
    
    # Signal logic
    if pct >= 25 and over_thresh:
        signal, signal_color, border_color = "Under", "#4ade80", "#4ade8044"
    elif pct >= 10 and over_thresh:
        signal, signal_color, border_color = "Under", "#86efac", "#86efac33"
    elif pct >= 0 or not over_thresh:
        signal, signal_color, border_color = "Hold", "#888888", "#88888833"
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
        marker=dict(size=[10, 12], color=['#666', signal_color], line=dict(color='#222', width=2)),
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
        plot_bgcolor='#161616',
        height=150,
        margin=dict(l=40, r=20, t=20, b=30),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(family='Inter', size=11, color='#666'), fixedrange=True),
        yaxis=dict(range=[0, max_y], showgrid=True, gridcolor='#222', zeroline=False, 
                   tickfont=dict(family='Inter', size=10, color='#555'),
                   title=dict(text='pts/min', font=dict(size=10, color='#555')), fixedrange=True),
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
        html.Div([
            # Signal Header
            html.Div([
                html.H3(signal, style={"fontSize": "1.6rem", "fontWeight": "700", "color": signal_color, "margin": "0"}),
                html.P(f"U{r['live_total']}" if pct >= 10 and over_thresh else "Monitor", 
                       style={"fontSize": "0.85rem", "color": "#888", "margin": "0.3rem 0 0 0"})
            ], style={
                "textAlign": "center",
                "padding": "1.2rem",
                "marginBottom": "1.2rem",
                "borderRadius": "8px",
                "background": "#1e1e1e",
                "border": f"1px solid {signal_color}40"
            }),
            
            # Metrics Grid
            dbc.Row([
                dbc.Col([
                    html.Div("Current Score", className="metric-label"),
                    html.Div(f"{r['total']}", style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#e5e5e5"})
                ], className="text-center", width=3),
                dbc.Col([
                    html.Div("Points Needed", className="metric-label"),
                    html.Div(f"{r['needed']}", style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#f59e0b"})
                ], className="text-center", width=3),
                dbc.Col([
                    html.Div("Current Pace", className="metric-label"),
                    html.Div(f"{curr:.1f}", style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#60a5fa"})
                ], className="text-center", width=3),
                dbc.Col([
                    html.Div("Required Pace", className="metric-label"),
                    html.Div(f"{req:.1f}", style={"fontSize": "1.4rem", "fontWeight": "700", "color": signal_color})
                ], className="text-center", width=3),
            ], className="mb-3"),
            
            # Time
            html.Div([
                html.Span(f"{r['elapsed']}m elapsed", style={"color": "#666"}),
                html.Span(" · ", style={"color": "#444"}),
                html.Span(f"{r['remaining']}m remaining", style={"color": "#666"})
            ], className="text-center mb-3", style={"fontSize": "0.8rem"}),
            
            # Pace chart
            dcc.Graph(figure=fig, config={'displayModeBar': False, 'staticPlot': True}),
            
            # Position tracker
            position_block if position_block else ""
        ], className="pro-card")
    ])

@app.callback(
    [Output("team_context_display", "children"),
     Output("analysis_controls", "style")],
    [Input("persistent_game_selection", "data"),
     Input("live_analysis_games_input", "value")],
    [State("betting_odds_data", "data")],
    prevent_initial_call=True
)
def update_team_context(selected_game_data, games_count, betting_odds_data):
    """Show team analysis context for selected game"""
    try:
        if not selected_game_data:
            return "", {"display": "none"}
        
        # Validate games count
        try:
            games_count = int(games_count) if games_count else 5
            if games_count < 3:
                games_count = 3
            elif games_count > 25:
                games_count = 25
        except (ValueError, TypeError):
            games_count = 5
        
        # Get team IDs and names from ESPN data
        home_team_id = selected_game_data.get('home_team_id')
        away_team_id = selected_game_data.get('away_team_id')
        home_team_name = selected_game_data.get('home_team')
        away_team_name = selected_game_data.get('away_team')
        
        # Debug print (remove after testing)
        print(f"DEBUG: home_team_id={home_team_id}, away_team_id={away_team_id}")
        print(f"DEBUG: home_team_name={home_team_name}, away_team_name={away_team_name}")
        print(f"DEBUG: using {games_count} games for analysis")
        
        if not home_team_id or not away_team_id:
            # Show basic game info even without team IDs for analysis
            return html.Div([
                html.Div([
                    html.H5("Matchup Selected", style={"color": "#e2e8f0", "fontSize": "1.1rem", "fontWeight": "600", "margin": "0"}),
                    html.P(f"{away_team_name or 'Away Team'} @ {home_team_name or 'Home Team'}", 
                           style={"color": "#888", "fontSize": "0.9rem", "margin": "0.5rem 0"}),
                    html.P("Historical analysis requires ESPN team data", 
                           style={"color": "#666", "fontSize": "0.8rem", "margin": "1rem 0 0 0"})
                ], className="pro-card")
            ]), {"display": "block"}
        
        # Get team stats with error handling using dynamic games count
        home_stats = get_team_stats(home_team_id, games_count)
        away_stats = get_team_stats(away_team_id, games_count)
        
        if not home_stats or not away_stats:
            return html.Div([
                html.Div([
                    html.H5("Team Analysis", style={"color": "#e5e5e5", "fontSize": "1.1rem", "fontWeight": "600", "margin": "0"}),
                    html.P(f"{away_team_name} @ {home_team_name}", style={"color": "#999", "fontSize": "0.9rem", "margin": "0.5rem 0"}),
                    html.P("Historical data unavailable", style={"color": "#666", "fontSize": "0.85rem", "margin": "1rem 0 0 0"})
                ], className="pro-card")
            ]), {"display": "block"}
        
        # Calculate implied total
        implied_total = home_stats['avg_team_score'] + away_stats['avg_team_score']
        implied_total_per_min = implied_total / 40
        
        # Get betting line for this matchup
        betting_info = None
        if betting_odds_data:
            # Try to match with betting data using team names
            match_key = f"{away_team_name}|{home_team_name}"
            betting_info = betting_odds_data.get(match_key)
            
            # Try reverse if not found
            if not betting_info:
                reverse_key = f"{home_team_name}|{away_team_name}"
                betting_info = betting_odds_data.get(reverse_key)
        
        return html.Div([
        html.Div([
            # Clean Header with Team Logos
            html.Div([
                html.H5("Matchup Intelligence", 
                       style={"color": "#e5e5e5", "fontSize": "1.1rem", "fontWeight": "600", "margin": "0 0 0.5rem 0"}),
                html.Div([
                    html.Img(src=selected_game_data.get('away_team_logo', ''), 
                            style={"width": "20px", "height": "20px", "marginRight": "6px", "borderRadius": "2px"},
                            className="team-logo") if selected_game_data.get('away_team_logo') else None,
                    html.Span(f"{away_team_name} @ ", style={"color": "#60a5fa"}),
                    html.Img(src=selected_game_data.get('home_team_logo', ''), 
                            style={"width": "20px", "height": "20px", "margin": "0 6px", "borderRadius": "2px"},
                            className="team-logo") if selected_game_data.get('home_team_logo') else None,
                    html.Span(home_team_name, style={"color": "#34d399"})
                ], style={"display": "flex", "alignItems": "center", "fontSize": "0.9rem", "margin": "0"})
            ], style={"marginBottom": "1.5rem"}),
            
            # Key Metrics Row
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div("Projected Total pts/min", className="metric-label"),
                        html.Div(f"{implied_total_per_min:.2f}", 
                                style={"fontSize": "1.6rem", "fontWeight": "700", "color": "#f59e0b", "lineHeight": "1"})
                    ])
                ], className="text-center", width=4),
                dbc.Col([
                    html.Div([
                        html.Div("Betting Line" + (f" ({betting_info['num_books']} books)" if betting_info else ""), className="metric-label"),
                        html.Div(f"{betting_info['avg_total']:.1f}" if betting_info else "No Line", 
                                style={"fontSize": "1.6rem", "fontWeight": "700", 
                                      "color": "#4a9eff" if betting_info else "#666", "lineHeight": "1"})
                    ])
                ], className="text-center", width=4),
                dbc.Col([
                    html.Div([
                        html.Div("Avg Scoring", className="metric-label"),
                        html.Div(
                            f"{away_stats['avg_team_score']:.0f} + {home_stats['avg_team_score']:.0f}",
                            style={"fontSize": "1.6rem", "fontWeight": "700", "color": "#d4d4d8", "lineHeight": "1"})
                    ])
                ], className="text-center", width=4),
            ], className="mb-4"),
            
            # Team Cards
            dbc.Row([
                # Away Team
                dbc.Col([
                    html.Div([
                        html.Div([
                            # Team logo and name
                            html.Div([
                                html.Img(src=selected_game_data.get('away_team_logo', ''), 
                                        style={"width": "24px", "height": "24px", "marginRight": "8px", "borderRadius": "3px"},
                                        className="team-logo") if selected_game_data.get('away_team_logo') else None,
                                html.H6(away_team_name[:18] + "..." if len(away_team_name) > 18 else away_team_name, 
                                       style={"color": "#60a5fa", "fontSize": "0.9rem", "fontWeight": "600", "margin": "0", "display": "inline"})
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "0.5rem"}),
                            html.Div(f"{away_stats['avg_team_score']:.1f}", 
                                    style={"fontSize": "1.5rem", "fontWeight": "700", "color": "#60a5fa", "lineHeight": "1"}),
                            html.Div("PPG", style={"fontSize": "0.7rem", "color": "#666", "marginBottom": "0.5rem"}),
                            
                            html.Div([
                                html.Span(f"{away_stats['avg_points_per_minute']:.2f}", 
                                         style={"fontSize": "1rem", "color": "#f59e0b", "fontWeight": "700"}),
                                html.Span(" pts/min", style={"fontSize": "0.65rem", "color": "#666", "marginLeft": "2px"})
                            ], className="mb-2"),
                            
                            html.Div([
                                html.Span("Defense: ", style={"fontSize": "0.75rem", "color": "#999"}),
                                html.Span(f"{away_stats['avg_opp_score']:.1f}", 
                                         style={"fontSize": "0.75rem", "color": "#f87171", "fontWeight": "500"})
                            ], className="mb-1"),
                            
                            html.Div([
                                html.Span("Road: ", style={"fontSize": "0.75rem", "color": "#999"}),
                                html.Span(f"{away_stats['away_avg']:.1f}" if away_stats['away_games'] > 0 else "N/A", 
                                         style={"fontSize": "0.75rem", "color": "#d4d4d8", "fontWeight": "500"})
                            ])
                        ])
                    ], style={
                        "background": "#1e1e1e",
                        "border": "1px solid #2a2a2a",
                        "borderRadius": "8px",
                        "padding": "1rem"
                    })
                ], width=5),
                
                # VS Separator
                dbc.Col([
                    html.Div("VS", 
                            style={
                                "textAlign": "center", 
                                "fontSize": "0.8rem", 
                                "color": "#666", 
                                "fontWeight": "600",
                                "paddingTop": "2rem"
                            })
                ], width=2),
                
                # Home Team
                dbc.Col([
                    html.Div([
                        html.Div([
                            # Team logo and name
                            html.Div([
                                html.Img(src=selected_game_data.get('home_team_logo', ''), 
                                        style={"width": "24px", "height": "24px", "marginRight": "8px", "borderRadius": "3px"},
                                        className="team-logo") if selected_game_data.get('home_team_logo') else None,
                                html.H6(home_team_name[:18] + "..." if len(home_team_name) > 18 else home_team_name,
                                       style={"color": "#34d399", "fontSize": "0.9rem", "fontWeight": "600", "margin": "0", "display": "inline"})
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "0.5rem"}),
                            html.Div(f"{home_stats['avg_team_score']:.1f}", 
                                    style={"fontSize": "1.5rem", "fontWeight": "700", "color": "#34d399", "lineHeight": "1"}),
                            html.Div("PPG", style={"fontSize": "0.7rem", "color": "#666", "marginBottom": "0.5rem"}),
                            
                            html.Div([
                                html.Span(f"{home_stats['avg_points_per_minute']:.2f}", 
                                         style={"fontSize": "1rem", "color": "#f59e0b", "fontWeight": "700"}),
                                html.Span(" pts/min", style={"fontSize": "0.65rem", "color": "#666", "marginLeft": "2px"})
                            ], className="mb-2"),
                            
                            html.Div([
                                html.Span("Defense: ", style={"fontSize": "0.75rem", "color": "#999"}),
                                html.Span(f"{home_stats['avg_opp_score']:.1f}", 
                                         style={"fontSize": "0.75rem", "color": "#f87171", "fontWeight": "500"})
                            ], className="mb-1"),
                            
                            html.Div([
                                html.Span("Home: ", style={"fontSize": "0.75rem", "color": "#999"}),
                                html.Span(f"{home_stats['home_avg']:.1f}" if home_stats['home_games'] > 0 else "N/A", 
                                         style={"fontSize": "0.75rem", "color": "#d4d4d8", "fontWeight": "500"})
                            ])
                        ])
                    ], style={
                        "background": "#1e1e1e",
                        "border": "1px solid #2a2a2a",
                        "borderRadius": "8px",
                        "padding": "1rem"
                    })
                ], width=5),
            ])
        ], className="pro-card")
    ]), {"display": "block"}
    
    except Exception as e:
        print(f"Error in team context callback: {e}")
        return html.Div([
            html.Div([
                html.H5("Analysis Error", style={"color": "#f87171", "fontSize": "1.1rem", "fontWeight": "600", "margin": "0"}),
                html.P("Unable to load team analysis", style={"color": "#999", "fontSize": "0.9rem", "margin": "0.5rem 0 0 0"})
            ], className="pro-card")
        ]), {"display": "block"}

# Analysis Tab Callbacks
@app.callback(
    Output("games-display", "children"),
    Output("team1_selector", "options"),
    Output("team2_selector", "options"),
    Input("today-btn", "n_clicks"),
    Input("tomorrow-btn", "n_clicks"),
    Input("week-btn", "n_clicks"),
    Input("main-tabs", "active_tab"),  # Auto-load when Research tab opens
    State("today_games_data", "data"),
    State("tomorrow_games_data", "data"),
    State("week_games_data", "data"),
    State("betting_odds_data", "data"),
    prevent_initial_call=True
)
def update_games_display(today_clicks, tomorrow_clicks, week_clicks, active_tab, today_games, tomorrow_games, week_games, betting_odds_data):
    """Update games display based on button selection or auto-load Today when tab opens"""
    ctx_triggered = ctx.triggered[0]['prop_id'] if ctx.triggered else ''
    
    # Auto-load Today's games when Research tab is opened
    if 'main-tabs' in ctx_triggered and active_tab == "analysis-tab":
        games_to_show = today_games or []
        title = "Today's Games"
    # Handle button clicks
    elif 'tomorrow-btn' in ctx_triggered:
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
                create_game_card(game, betting_odds_data) for game in games_to_show
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

# Auto-populate team selectors when game is clicked
@app.callback(
    [Output("team1_selector", "value"),
     Output("team2_selector", "value")],
    Input({"type": "analysis-game-card", "index": ALL}, "n_clicks"),
    [State("today_games_data", "data"),
     State("tomorrow_games_data", "data"),  
     State("week_games_data", "data")],
    prevent_initial_call=True
)
def populate_teams_from_game_click(game_clicks, today_games, tomorrow_games, week_games):
    """Auto-populate team selectors when a game card is clicked"""
    if not any(game_clicks):
        raise dash.exceptions.PreventUpdate
    
    # Get the game ID from the callback context
    if not ctx.triggered or not ctx.triggered[0]['prop_id']:
        raise dash.exceptions.PreventUpdate
    
    game_id = ctx.triggered_id['index'] if ctx.triggered_id and 'index' in ctx.triggered_id else None
    
    if not game_id:
        raise dash.exceptions.PreventUpdate
    
    # Find the game in all possible data sources
    all_games = (today_games or []) + (tomorrow_games or []) + (week_games or [])
    selected_game = next((game for game in all_games if str(game['id']) == str(game_id)), None)
    
    if not selected_game:
        print(f"DEBUG: Game ID {game_id} not found in data")
        raise dash.exceptions.PreventUpdate
    
    # Extract team IDs
    home_team_id = selected_game.get('home_team_id')
    away_team_id = selected_game.get('away_team_id')
    
    print(f"DEBUG: Auto-selected teams from game click - Away: {away_team_id} ({selected_game.get('away_team')}), Home: {home_team_id} ({selected_game.get('home_team')})")
    
    return away_team_id, home_team_id  # Team 1 = Away, Team 2 = Home

def create_game_card(game, betting_odds_data=None):
    """Create a clickable card for displaying game information"""
    status_color = "#4ade80" if game['is_live'] else "#666" if game['state'] == 'pre' else "#f87171"
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
    
    # Get betting total from odds data
    betting_total = None
    if betting_odds_data:
        # Try to match with betting data using the correct key format
        away_team = game.get('away_team', '')
        home_team = game.get('home_team', '')
        
        # Try both possible key combinations  
        game_key1 = f"{away_team}|{home_team}"
        game_key2 = f"{home_team}|{away_team}"
        
        betting_info = betting_odds_data.get(game_key1) or betting_odds_data.get(game_key2)
        if betting_info:
            betting_total = betting_info.get('avg_total')
    
    # Parse game time for display with first/second half conversion
    time_display = game['clock']
    
    if game['is_live']:
        # Show raw ESPN time - user controls conversion with toggle
        time_display = game['clock']
    elif game['state'] == 'pre':
        try:
            dt_est = convert_utc_to_est(game['date'])
            if dt_est:
                time_display = dt_est.strftime('%I:%M %p EST')
            else:
                time_display = game['clock']
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
                    # Away team with logo
                    html.Span([
                        html.Img(src=game.get('away_team_logo', ''), 
                                style={"width": "16px", "height": "16px", "marginRight": "4px", "borderRadius": "2px", "verticalAlign": "middle"},
                                className="team-logo") if game.get('away_team_logo') else None,
                        html.Span(game['away_team'], style={"fontSize": "0.85rem", "color": "#e5e5e5", "verticalAlign": "middle"})
                    ], style={"display": "inline-flex", "alignItems": "center"}),
                    
                    html.Span(f" {score_display} ", style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#fff", "margin": "0 6px"}),
                    
                    # Home team with logo
                    html.Span([
                        html.Img(src=game.get('home_team_logo', ''), 
                                style={"width": "16px", "height": "16px", "marginRight": "4px", "borderRadius": "2px", "verticalAlign": "middle"},
                                className="team-logo") if game.get('home_team_logo') else None,
                        html.Span(game['home_team'], style={"fontSize": "0.85rem", "color": "#e5e5e5", "verticalAlign": "middle"})
                    ], style={"display": "inline-flex", "alignItems": "center"})
                ], style={"display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Span("Click to analyze teams →", style={"fontSize": "0.65rem", "color": "#555", "fontStyle": "italic"})
                ], style={"marginTop": "4px"})
            ], width=7),
            dbc.Col([
                html.Div([
                    html.Span("Line: " if betting_total else "Total: ", style={"fontSize": "0.7rem", "color": "#666"}),
                    html.Span(str(betting_total) if betting_total else (str(total_score) if total_score is not None else "—"), 
                             style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#4a9eff" if betting_total else "#f59e0b"})
                ], className="text-right")
            ], width=5)
        ])
    ], id={"type": "analysis-game-card", "index": game['id']}, n_clicks=0, style={
        "padding": "10px 12px",
        "margin": "6px 0",
        "border": "1px solid #2a2a2a",
        "borderRadius": "8px",
        "background": "#1a1a1a",
        "cursor": "pointer",
        "transition": "all 0.2s ease"
    }, className="analysis-game-card")

def get_team_stats(team_id, num_games=10):
    """Helper function to get team statistics"""
    try:
        if not team_id:
            return None
        
        recent_games = fetch_team_recent_games(team_id, num_games)
        if not recent_games:
            print(f"No recent games found for team {team_id}")
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
        
        # Calculate points per minute (PPG / 40)
        avg_points_per_minute = avg_team_score / 40
        
        return {
            'recent_games': recent_games,
            'avg_team_score': avg_team_score,
            'avg_opp_score': avg_opp_score,
            'avg_total': avg_total,
            'avg_points_per_minute': avg_points_per_minute,
            'home_avg': home_avg,
            'away_avg': away_avg,
            'home_games': len(home_games),
            'away_games': len(away_games)
        }
        
    except Exception as e:
        print(f"Error in get_team_stats for team {team_id}: {e}")
        return None

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
    Input("games_count_input", "value")
)
def update_games_count_display(games_count):
    """Update the games count display"""
    try:
        games_count = int(games_count) if games_count else 5
        if games_count < 3:
            games_count = 3
        elif games_count > 25:
            games_count = 25
    except (ValueError, TypeError):
        games_count = 5
    return f"Last {games_count} games"

@app.callback(
    Output("team-analysis-display", "children"),
    Input("team1_selector", "value"),
    Input("team2_selector", "value"),
    Input("games_count_input", "value"),
    State("team1_selector", "options"),
    State("team2_selector", "options")
)
def update_team_comparison(team1_id, team2_id, games_count, team1_options, team2_options):
    """Update team comparison analysis display"""
    if not team1_id and not team2_id:
        return dbc.CardBody([
            html.P("Select teams to compare their recent performance", className="text-center text-muted py-4")
        ])
    
    # Validate games count from text input
    try:
        games_count = int(games_count) if games_count else 5
        if games_count < 3:
            games_count = 3
        elif games_count > 25:
            games_count = 25
    except (ValueError, TypeError):
        games_count = 5
    
    # Get team names from options
    team1_name = get_team_name_from_options(team1_id, team1_options) if team1_id else None
    team2_name = get_team_name_from_options(team2_id, team2_options) if team2_id else None
    
    # Get team logos using ESPN fallback pattern
    team1_logo_url = f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team1_id}.png" if team1_id else ''
    team2_logo_url = f"https://a.espncdn.com/i/teamlogos/ncaa/500/{team2_id}.png" if team2_id else ''
    
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
        implied_total_per_min = implied_total / 40
        
        comparison_content.extend([
            html.Div([
                html.H6("Team Comparison", style={"color": "#e5e5e5", "textAlign": "center"}),
                html.Div([
                    html.Span("Implied Total pts/min: ", style={"fontSize": "0.9rem", "color": "#666"}),
                    html.Span(f"{implied_total_per_min:.2f}", style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#f59e0b"})
                ], className="text-center mb-4")
            ]),
            
            dbc.Row([
                # Team 1 Column
                dbc.Col([
                    html.Div([
                        html.Img(src=team1_logo_url, 
                                style={"width": "24px", "height": "24px", "marginRight": "8px", "borderRadius": "4px"},
                                className="team-logo") if team1_logo_url else None,
                        html.Span(team1_name or "Team 1", style={"color": "#4ade80", "fontSize": "1rem", "fontWeight": "600"})
                    ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "1rem"}),
                    html.Div("AVG PPG", className="metric-label text-center"),
                    html.Div(f"{team1_stats['avg_team_score']:.1f}", 
                            style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#4ade80", "textAlign": "center"}),
                ], width=5),
                
                # VS Column
                dbc.Col([
                    html.Div("VS", style={"fontSize": "1.5rem", "fontWeight": "700", "color": "#666", 
                                        "textAlign": "center", "paddingTop": "40px"})
                ], width=2),
                
                # Team 2 Column  
                dbc.Col([
                    html.Div([
                        html.Img(src=team2_logo_url, 
                                style={"width": "24px", "height": "24px", "marginRight": "8px", "borderRadius": "4px"},
                                className="team-logo") if team2_logo_url else None,
                        html.Span(team2_name or "Team 2", style={"color": "#3b82f6", "fontSize": "1rem", "fontWeight": "600"})
                    ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "1rem"}),
                    html.Div("AVG PPG", className="metric-label text-center"),
                    html.Div(f"{team2_stats['avg_team_score']:.1f}", 
                            style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#3b82f6", "textAlign": "center"}),
                ], width=5),
            ], className="mb-4"),
            
            html.Hr(style={"borderColor": "#333"}),
        ])
    
    # Show individual team stats
    team_labels = []
    if team1_stats and team2_stats:
        team_labels = [
            (team1_stats, "#4ade80", team1_name or "Team 1", team1_logo_url), 
            (team2_stats, "#3b82f6", team2_name or "Team 2", team2_logo_url)
        ]
    elif team1_stats:
        team_labels = [(team1_stats, "#4ade80", team1_name or "Team Analysis", team1_logo_url)]
    elif team2_stats:
        team_labels = [(team2_stats, "#3b82f6", team2_name or "Team Analysis", team2_logo_url)]
    
    for i, (team_stats, team_color, team_label, team_logo_url) in enumerate(team_labels):
        if not team_stats:
            continue
            
        if i > 0:  # Add separator between teams
            comparison_content.append(html.Hr(style={"borderColor": "#333", "margin": "20px 0"}))
        
        comparison_content.extend([
            html.Div([
                html.Img(src=team_logo_url, 
                        style={"width": "20px", "height": "20px", "marginRight": "8px", "borderRadius": "3px"},
                        className="team-logo") if team_logo_url else None,
                html.Span(team_label, style={"color": team_color, "fontSize": "1rem", "fontWeight": "600"})
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "12px"}),
            
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
                html.Span(f"Recent Games ({len(team_stats['recent_games'])})", 
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
                    }) for game in team_stats['recent_games']
                ], className="mt-2", style={
                    "maxHeight": "200px", 
                    "overflowY": "auto",
                    "border": "1px solid #2a2a2a",
                    "borderRadius": "6px",
                    "padding": "4px"
                })
            ])
        ])
    
    return dbc.CardBody(comparison_content)

# Game Reminder Callbacks
@app.callback(
    Output("game_reminder_store", "data"),
    Input("game_reminder_input", "value"),
    prevent_initial_call=True
)
def save_game_reminder(value):
    return value or ""

@app.callback(
    Output("game_reminder_input", "value"),
    Input("refresh_games", "n_intervals"),
    State("game_reminder_store", "data"),
    prevent_initial_call=True
)
def load_game_reminder_on_startup(n_intervals, stored_value):
    if n_intervals == 0 and stored_value:
        return stored_value
    raise dash.exceptions.PreventUpdate


if __name__ == "__main__":
    app.run(debug=True)
