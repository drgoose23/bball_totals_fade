import dash
from dash import html, dcc, Output, Input, State, ALL, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
from datetime import datetime, timedelta, timezone

ODDS_API_KEY = 'c352f4d244a2a3ae32f32136f8d908ac'
ODDS_BASE_URL = 'https://api.the-odds-api.com/v4'

app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
], suppress_callback_exceptions=True)

def convert_utc_to_est(utc_time_str):
    """Convert UTC time string to EST/EDT (automatically handles DST)"""
    try:
        # Parse UTC time from ESPN API
        dt_utc = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
        
        year = dt_utc.year
        
        # Approximate DST dates (this covers most cases accurately)
        # DST starts 2nd Sunday in March, ends 1st Sunday in November
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
        <title>Fade System</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
                font-family: 'Inter', sans-serif;
                color: #e2e8f0;
                font-weight: 400;
            }
            .card {
                background: rgba(26, 32, 44, 0.8);
                border: 1px solid rgba(74, 85, 104, 0.3);
                border-radius: 12px;
                backdrop-filter: blur(8px);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            }
            .form-control {
                background: rgba(26, 32, 44, 0.7) !important;
                border: 1px solid rgba(74, 85, 104, 0.4) !important;
                color: #e2e8f0 !important;
                font-weight: 400;
                border-radius: 6px !important;
                font-size: 0.9rem;
                padding: 0.6rem 0.8rem;
                transition: all 0.2s ease;
            }
            .form-control:focus {
                border-color: #4a5568 !important;
                box-shadow: 0 0 0 2px rgba(74, 85, 104, 0.2) !important;
            }
            .form-control::placeholder { color: #718096 !important; }
            .btn-adj {
                background: rgba(74, 85, 104, 0.15) !important;
                border: 1px solid rgba(74, 85, 104, 0.2) !important;
                color: #a0aec0 !important;
                font-weight: 500;
                border-radius: 4px;
                transition: all 0.2s ease;
                font-size: 0.8rem;
                padding: 0.25rem 0.5rem;
                min-width: 32px;
            }
            .btn-adj:hover { 
                background: rgba(74, 85, 104, 0.25) !important; 
                color: #e2e8f0 !important;
                border-color: rgba(74, 85, 104, 0.3) !important;
            }
            .btn-adj:active {
                background: rgba(74, 85, 104, 0.35) !important;
                transform: scale(0.95);
            }
            .btn-adj-small {
                background: rgba(74, 85, 104, 0.1) !important;
                border: 1px solid rgba(74, 85, 104, 0.15) !important;
                color: #a0aec0 !important;
                font-weight: 400;
                border-radius: 3px;
                transition: all 0.2s ease;
                font-size: 0.7rem;
                padding: 0.15rem 0.3rem;
                min-width: 24px;
                height: 28px;
            }
            .btn-adj-small:hover { 
                background: rgba(74, 85, 104, 0.2) !important; 
                color: #e2e8f0 !important;
                border-color: rgba(74, 85, 104, 0.25) !important;
            }
            .btn-adj-small:active {
                background: rgba(74, 85, 104, 0.3) !important;
                transform: scale(0.92);
            }
            .label { 
                font-size: 0.75rem; 
                color: #a0aec0; 
                text-transform: uppercase; 
                letter-spacing: 0.8px; 
                margin-bottom: 0.5rem; 
                font-weight: 500;
            }
            .output-card {
                background: rgba(24, 24, 27, 0.9);
                border: 1px solid rgba(39, 39, 42, 0.6);
                border-radius: 20px;
                backdrop-filter: blur(12px);
                box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
            }
            .metric-value { 
                font-weight: 600;
                font-size: 2rem;
                letter-spacing: -0.02em;
                line-height: 1;
            }
            .metric-label {
                font-size: 0.75rem;
                font-weight: 500;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: #a0aec0;
                margin-bottom: 0.25rem;
            }
            .pro-card {
                background: rgba(26, 32, 44, 0.9);
                border: 1px solid rgba(74, 85, 104, 0.25);
                border-radius: 12px;
                padding: 1.5rem;
                backdrop-filter: blur(10px);
                box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
            }
            /* Professional Dropdown Styling */
            .dark-dropdown .Select-control { 
                background: rgba(26, 32, 44, 0.9) !important; 
                border: 1px solid rgba(74, 85, 104, 0.4) !important; 
                color: #e2e8f0 !important; 
                border-radius: 8px !important;
                min-height: 42px;
                font-size: 0.9rem;
                font-family: 'SF Mono', Consolas, monospace;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            .dark-dropdown .Select-control:hover {
                border-color: rgba(74, 85, 104, 0.6) !important;
                background: rgba(26, 32, 44, 0.95) !important;
            }
            .dark-dropdown .Select-placeholder { 
                color: #718096 !important; 
                font-weight: 400; 
                font-family: 'Inter', sans-serif;
            }
            .dark-dropdown .Select-value-label { 
                color: #f7fafc !important; 
                font-weight: 500; 
                font-family: 'SF Mono', Consolas, monospace;
            }
            .dark-dropdown .Select-input > input { 
                color: #e2e8f0 !important; 
                font-family: 'SF Mono', Consolas, monospace;
            }
            .dark-dropdown .Select-menu-outer { 
                background: rgba(26, 32, 44, 0.98) !important; 
                border: 1px solid rgba(74, 85, 104, 0.4) !important; 
                border-radius: 8px !important;
                backdrop-filter: blur(12px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
                max-height: 300px;
            }
            .dark-dropdown .Select-menu { 
                background: transparent !important;
                max-height: 280px;
            }
            .dark-dropdown .Select-option { 
                color: #cbd5e0 !important; 
                background: transparent !important; 
                padding: 12px 16px !important;
                font-size: 0.9rem;
                font-family: 'SF Mono', Consolas, monospace;
                font-weight: 500;
                transition: all 0.15s ease;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .dark-dropdown .Select-option.is-focused { 
                background: rgba(74, 85, 104, 0.2) !important; 
                color: #f7fafc !important; 
            }
            .dark-dropdown .Select-option.is-selected { 
                background: rgba(74, 85, 104, 0.3) !important; 
                color: #ffffff !important; 
            }
            
            /* Professional Button Styling */
            .btn-primary {
                background: #2d3748 !important;
                border: none !important;
                border-radius: 6px !important;
                font-weight: 500 !important;
                padding: 0.5rem 1rem !important;
                font-size: 0.85rem !important;
                transition: all 0.2s ease !important;
                box-shadow: none !important;
                color: #e2e8f0 !important;
            }
            .btn-primary:hover {
                background: #4a5568 !important;
                color: #f7fafc !important;
            }
            .btn-primary:active {
                background: #1a202c !important;
                transform: scale(0.98) !important;
            }
            .btn-secondary {
                background: rgba(45, 55, 72, 0.1) !important;
                border: 1px solid rgba(45, 55, 72, 0.2) !important;
                color: #a0aec0 !important;
                border-radius: 6px !important;
                font-weight: 500 !important;
                padding: 0.5rem 1rem !important;
                font-size: 0.85rem !important;
                transition: all 0.2s ease !important;
            }
            .btn-secondary:hover {
                background: rgba(45, 55, 72, 0.15) !important;
                border-color: rgba(45, 55, 72, 0.3) !important;
                color: #e2e8f0 !important;
            }
            .btn-secondary:active {
                background: rgba(45, 55, 72, 0.25) !important;
                transform: scale(0.98) !important;
            }
            
            /* Professional Slider */
            .rc-slider {
                background: rgba(74, 85, 104, 0.3) !important;
                border-radius: 3px !important;
                height: 4px !important;
            }
            .rc-slider-track {
                background: #4a5568 !important;
                border-radius: 3px !important;
                height: 4px !important;
            }
            .rc-slider-handle {
                background: #e2e8f0 !important;
                border: 2px solid #4a5568 !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
                width: 18px !important;
                height: 18px !important;
                margin-top: -7px !important;
            }
            .rc-slider-mark-text {
                color: #a0aec0 !important;
                font-size: 0.75rem !important;
            }
            
            /* Game Selection Modal */
            .game-selector-btn:hover {
                background: rgba(26, 32, 44, 0.95) !important;
                border-color: rgba(74, 85, 104, 0.6) !important;
                transform: translateY(-1px);
            }
            
            .game-card {
                background: rgba(26, 32, 44, 0.6);
                border: 1px solid rgba(74, 85, 104, 0.3);
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
                cursor: pointer;
                transition: all 0.2s ease;
                font-family: 'SF Mono', Consolas, monospace;
            }
            
            .game-card:hover {
                background: rgba(74, 85, 104, 0.2);
                border-color: rgba(74, 85, 104, 0.5);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            }
            
            .game-time {
                color: #68d391;
                font-weight: 600;
                font-size: 0.9rem;
                margin-bottom: 0.5rem;
            }
            
            .game-matchup {
                color: #e2e8f0;
                font-weight: 500;
                font-size: 1rem;
                margin-bottom: 0.25rem;
            }
            
            .game-details {
                color: #a0aec0;
                font-size: 0.8rem;
            }
            
            .live-indicator {
                color: #f56565;
                font-weight: 600;
                font-size: 0.8rem;
            }
            
            /* Analysis Game Cards */
            .analysis-game-card:hover {
                background: rgba(74, 85, 104, 0.15) !important;
                border-color: rgba(74, 85, 104, 0.4) !important;
                transform: translateY(-1px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            }
            
            /* Team Logos */
            .team-logo {
                object-fit: contain;
                filter: brightness(0.95);
                transition: all 0.2s ease;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 3px;
            }
            .team-logo:hover {
                filter: brightness(1.1);
                transform: scale(1.05);
            }
            /* Hide broken images */
            .team-logo[src=""], .team-logo:not([src]) {
                display: none;
            }
            
            /* Hide number input spinners/scrollers */
            input[type="number"]::-webkit-outer-spin-button,
            input[type="number"]::-webkit-inner-spin-button {
                -webkit-appearance: none !important;
                margin: 0 !important;
            }
            
            input[type="number"] {
                -moz-appearance: textfield !important;
            }
            
            /* Prevent accidental scroll changes on number inputs */
            input[type="number"]:focus {
                -moz-appearance: textfield !important;
            }
            
            /* Game Search Input */
            #game_search_input.form-control {
                /* Prevent event bubbling that might close modal */
                z-index: 1050 !important;
                position: relative !important;
            }
            
            #game_search_input.form-control:focus {
                border-color: #4fd1c7 !important;
                box-shadow: 0 0 0 2px rgba(79, 209, 199, 0.2) !important;
                z-index: 1051 !important;
            }
            
            #game_search_input.form-control::placeholder {
                color: #718096 !important;
                font-style: italic;
            }
            
            /* Prevent modal from closing when clicking in search area */
            .modal-body {
                position: relative;
                z-index: 1040;
            }
            
            /* Refresh button styling */
            #refresh_selected_game_btn:hover {
                background: rgba(74, 85, 104, 0.4) !important;
                color: #e2e8f0 !important;
                border-color: rgba(74, 85, 104, 0.6) !important;
                transform: scale(1.05);
            }
            
            #refresh_selected_game_btn:active {
                background: rgba(74, 85, 104, 0.6) !important;
                transform: scale(0.95);
            }
        </style>
        <script>
            // Prevent modal from closing when interacting with search input
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Setting up search input protection...');
                
                // Add event listeners to prevent modal close on search input interaction
                document.addEventListener('click', function(e) {
                    if (e.target && (e.target.id === 'game_search_input' || e.target.id === 'clear_search_btn')) {
                        console.log('Preventing click propagation for search elements');
                        e.stopPropagation();
                    }
                });
                
                document.addEventListener('keydown', function(e) {
                    if (e.target && e.target.id === 'game_search_input') {
                        console.log('Preventing keydown propagation for search input');
                        e.stopPropagation();
                    }
                });
                
                document.addEventListener('input', function(e) {
                    if (e.target && e.target.id === 'game_search_input') {
                        console.log('Search input changed:', e.target.value);
                        e.stopPropagation();
                    }
                });
                
                document.addEventListener('focus', function(e) {
                    if (e.target && e.target.id === 'game_search_input') {
                        console.log('Search input focused');
                        e.stopPropagation();
                    }
                });
                
                // Prevent number inputs from changing values on trackpad/mousewheel scroll
                document.addEventListener('wheel', function(e) {
                    if (e.target && e.target.type === 'number' && document.activeElement === e.target) {
                        console.log('Preventing number input scroll change');
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }, { passive: false });
                
                // Prevent accidental arrow key changes
                document.addEventListener('keydown', function(e) {
                    if (e.target && e.target.type === 'number') {
                        if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                            // Only allow arrow keys if user is actively focused on the input
                            if (document.activeElement !== e.target) {
                                e.preventDefault();
                            }
                        }
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
            # Add parameters to get more comprehensive data
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date_str}&limit=300"
        else:
            # For "today", use current date regardless of time - college games often span midnight
            today_str = datetime.now().strftime('%Y%m%d')
            url = f"http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={today_str}&limit=300"
        
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
                        
                        # Automatically convert first half time to full game time remaining
                        if period == 1:  # First half
                            original_mins = minutes_left
                            minutes_left += 20  # Add 20 for entire second half
                            print(f"DEBUG: First half auto-conversion - ESPN: {original_mins}:{seconds_left:02d} → Full game: {minutes_left}:{seconds_left:02d}")
                        # If period == 2 (second half) or overtime, leave as is
                        
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
    """Get odds for college basketball games"""
    url = f"{ODDS_BASE_URL}/sports/{sport_key}/odds"
    
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',  # US sportsbooks
        'markets': 'totals',  # Just totals for now (simpler)
        'oddsFormat': 'american',
        'dateFormat': 'iso'
    }
    
    try:
        print(f"🔍 Requesting odds from: {url}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        games = response.json()
        print(f"📊 Odds API: Found {len(games)} games with betting lines")
        
        # Debug: Show first game if available
        if games:
            first_game = games[0]
            print(f"🔍 Sample game: {first_game.get('away_team', 'Unknown')} @ {first_game.get('home_team', 'Unknown')}")
        else:
            print(f"⚠️ Odds API returned empty games list")
        
        return games
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Odds API Error: {e}")
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
        score = f"{game['away_score']}-{game['home_score']}"
        return {
            'label': f"{away} {score} {home} • {game['clock']}",
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
        dbc.InputGroup([
            dbc.Button("−", id={"type": "dec", "index": input_id}, className="btn-adj px-3"),
            dbc.Input(id=input_id, type="number", placeholder="0", style={"textAlign": "center"}),
            dbc.Button("+", id={"type": "inc", "index": input_id}, className="btn-adj px-3"),
        ], size="sm")
    ], className="mb-3")

def small_input_with_buttons(label, input_id, placeholder="-", min_val=None, max_val=None):
    input_props = {
        "id": input_id, 
        "type": "number", 
        "placeholder": placeholder, 
        "style": {"textAlign": "center"}
    }
    if min_val is not None:
        input_props["min"] = min_val
    if max_val is not None:
        input_props["max"] = max_val
    
    return html.Div([
        html.Div(label, className="label"),
        dbc.InputGroup([
            dbc.Button("−", id={"type": "dec_small", "index": input_id}, className="btn-adj-small px-1"),
            dbc.Input(**input_props),
            dbc.Button("+", id={"type": "inc_small", "index": input_id}, className="btn-adj-small px-1"),
        ], size="sm")
    ], className="mb-3")


app.layout = dbc.Container([
    # Professional Header
    html.Div([
        html.H2("- CBB Fade Terminal -", 
                style={"fontWeight": "600", "color": "#f7fafc", "marginBottom": "0.5rem", "letterSpacing": "-0.02em"}),
    ], className="text-center", style={"padding": "2rem 0 1.5rem 0"}),
    
    # Professional Tabs
    dbc.Tabs([
        dbc.Tab(label="Live Analysis", tab_id="fade-tab", 
                style={"fontSize": "0.9rem", "fontWeight": "500"}),
        dbc.Tab(label="Research", tab_id="analysis-tab",
                style={"fontSize": "0.9rem", "fontWeight": "500"}),
    ], id="main-tabs", active_tab="fade-tab", className="mb-4",
       style={"borderBottom": "1px solid rgba(63, 63, 70, 0.3)"}),
    
    html.Div(id="tab-content"),
    
    # Stores
    dcc.Store(id="opening_line", data=None),
    dcc.Store(id="live_games_data", data=[]),
    dcc.Store(id="selected_game_data", data=None),
    dcc.Store(id="persistent_game_selection", data=None),  # Completely separate storage for game selection
    dcc.Store(id="today_games_data", data=[]),
    dcc.Store(id="tomorrow_games_data", data=[]),
    dcc.Store(id="week_games_data", data=[]),
    dcc.Store(id="betting_odds_data", data={}),
    dcc.Interval(id="refresh_games", interval=30*1000, n_intervals=0),  # Refresh every 30 seconds (less frequent to avoid search interference)
    
    # Game Selection Modal
    dbc.Modal([
        dbc.ModalHeader([
            html.H4("Select Game", style={"color": "#f7fafc", "margin": "0"}),
        ], style={"background": "rgba(26, 32, 44, 0.95)", "border": "none"}),
        dbc.ModalBody([
            # Search bar
            html.Div([
                dbc.InputGroup([
                    dbc.Input(
                        id="game_search_input",
                        placeholder="Search teams (e.g., 'Duke', 'Carolina', 'Lakers')...",
                        type="text",
                        autoComplete="off",
                        style={
                            "background": "rgba(45, 55, 72, 0.9)",
                            "border": "1px solid rgba(74, 85, 104, 0.5)",
                            "borderRadius": "8px 0 0 8px",
                            "color": "#f7fafc",
                            "fontSize": "0.9rem",
                            "padding": "0.75rem"
                        }
                    ),
                    dbc.Button(
                        "✕",
                        id="clear_search_btn",
                        color="secondary",
                        size="sm",
                        style={
                            "background": "rgba(74, 85, 104, 0.3)",
                            "border": "1px solid rgba(74, 85, 104, 0.5)",
                            "borderRadius": "0 8px 8px 0",
                            "color": "#a0aec0",
                            "fontSize": "0.8rem",
                            "padding": "0.5rem",
                            "minWidth": "40px"
                        }
                    )
                ], className="mb-3")
            ]),
            # Games grid
            html.Div(id="game_selection_grid", style={"maxHeight": "50vh", "overflowY": "auto"})
        ], style={"background": "rgba(26, 32, 44, 0.95)", "border": "none", "padding": "1.5rem"}),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="game_modal_close", className="pro-button-secondary", size="sm")
        ], style={"background": "rgba(26, 32, 44, 0.95)", "border": "none"})
    ], id="game_selection_modal", is_open=False, centered=True, size="lg", backdrop="static", keyboard=False)
], fluid=True, style={"maxWidth": "1400px", "padding": "0 2rem"})


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
                            html.Span(" (ESPN)", style={"fontSize": "0.65rem", "color": "#555", "marginLeft": "6px"})
                        ]),
                        html.Button(
                            id="game_selector_button",
                            children=[
                                html.Div("Select Game", id="game_selector_text", style={"color": "#a0aec0"}),
                                html.Div("⌄", style={"fontSize": "1.2rem", "marginLeft": "auto"})
                            ],
                            className="game-selector-btn",
                            style={
                                "width": "100%", 
                                "display": "flex", 
                                "alignItems": "center",
                                "justifyContent": "space-between",
                                "padding": "0.75rem 1rem",
                                "background": "rgba(26, 32, 44, 0.9)",
                                "border": "1px solid rgba(74, 85, 104, 0.4)",
                                "borderRadius": "8px",
                                "cursor": "pointer",
                                "transition": "all 0.2s ease"
                            }
                        ),
                        # Small refresh button for selected game
                        html.Div([
                            dbc.Button(
                                "🔄",
                                id="refresh_selected_game_btn",
                                color="secondary",
                                size="sm",
                                style={
                                    "background": "rgba(74, 85, 104, 0.2)",
                                    "border": "1px solid rgba(74, 85, 104, 0.4)",
                                    "color": "#a0aec0",
                                    "fontSize": "0.8rem",
                                    "padding": "0.4rem 0.6rem",
                                    "marginTop": "0.5rem",
                                    "borderRadius": "6px"
                                },
                                title="Refresh live scores for selected game"
                            )
                        ], style={"textAlign": "right"}),
                        # Store selected game ID and button text separately for persistence
                        dcc.Store(id="live_game_selector", data=None),
                        dcc.Store(id="selected_game_text", data="Select Game"),
                    ], className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col(score_input("Home", "team1"), width=6),
                        dbc.Col(score_input("Away", "team2"), width=6),
                    ]),
                    
                    small_input_with_buttons("Live Total", "live_total"),
                    
                    dbc.Row([
                        dbc.Col([
                            small_input_with_buttons("Minutes", "mins_left", min_val=0)
                        ], width=6),
                        dbc.Col([
                            small_input_with_buttons("Seconds", "secs_left", min_val=0, max_val=59)
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
                                placeholder="5",
                                style={"textAlign": "center", "fontWeight": "600", "fontSize": "0.85rem"}
                            ),
                            dbc.InputGroupText("games", style={
                                "background": "rgba(26, 32, 44, 0.8)",
                                "border": "1px solid rgba(74, 85, 104, 0.4)",
                                "color": "#a0aec0",
                                "fontSize": "0.75rem"
                            })
                        ], size="sm")
                    ], width=3),
                    dbc.Col(width=9)
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
                    dbc.Row([
                        dbc.Col([
                            html.Div("Lookback Games", className="label"),
                            dbc.InputGroup([
                                dbc.Input(
                                    id="games_count_input",
                                    type="text",
                                    value="5",
                                    placeholder="5",
                                    style={"textAlign": "center", "fontWeight": "600", "fontSize": "0.9rem"}
                                ),
                                dbc.InputGroupText("games", style={
                                    "background": "rgba(26, 32, 44, 0.8)",
                                    "border": "1px solid rgba(74, 85, 104, 0.4)",
                                    "color": "#a0aec0",
                                    "fontSize": "0.8rem"
                                })
                            ], size="sm")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Span("Analysis Based On: ", className="label", style={"display": "inline-block", "marginRight": "8px"}),
                                html.Span(id="games_count_display", style={"fontSize": "0.85rem", "color": "#68d391", "fontWeight": "600"})
                            ], style={"marginTop": "1.2rem"})
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
    t1, t2 = t1 or 0, t2 or 0
    d = 1 if t["type"] == "inc" else -1
    if t["index"] == "team1": t1 = max(0, t1 + d)
    elif t["index"] == "team2": t2 = max(0, t2 + d)
    return t1, t2

@app.callback(
    Output("live_total", "value"), Output("mins_left", "value"), Output("secs_left", "value"),
    Input({"type": "inc_small", "index": ALL}, "n_clicks"),
    Input({"type": "dec_small", "index": ALL}, "n_clicks"),
    State("live_total", "value"), State("mins_left", "value"), State("secs_left", "value"),
    prevent_initial_call=True
)
def adj_small_inputs(inc, dec, live_total, mins, secs):
    if not ctx.triggered_id: raise dash.exceptions.PreventUpdate
    t = ctx.triggered_id
    
    live_total = live_total or 0
    mins = mins or 0
    secs = secs or 0
    
    d = 1 if t["type"] == "inc_small" else -1
    
    if t["index"] == "live_total":
        live_total = max(0, live_total + d)
    elif t["index"] == "mins_left":
        mins = max(0, mins + d)
    elif t["index"] == "secs_left":
        secs = max(0, min(59, secs + d))  # Keep seconds between 0-59
    
    return live_total, mins, secs


# ESPN API Callbacks
@app.callback(
    Output("live_games_data", "data"),
    Output("today_games_data", "data"),
    Output("tomorrow_games_data", "data"),
    Output("week_games_data", "data"),
    Output("betting_odds_data", "data"),
    Input("refresh_games", "n_intervals")
)
def refresh_all_games(n):
    """Fetch all games data every interval"""
    # Expand date ranges for more comprehensive coverage
    today = datetime.now().strftime('%Y%m%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y%m%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    
    # Get today's games (including yesterday's late games that might still be live)
    yesterday_games = fetch_games_by_date(yesterday)
    today_games = fetch_games_by_date(today)
    tomorrow_games = fetch_games_by_date(tomorrow)
    
    # Combine all current/live games from multiple days for more options
    all_current_games = yesterday_games + today_games + tomorrow_games
    
    # Also get games from the next few days to include busy game days
    for days_ahead in range(2, 7):  # Days 2-6 ahead (Tuesday through Saturday)
        future_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y%m%d')
        future_games = fetch_games_by_date(future_date)
        all_current_games.extend(future_games)
    
    # Show live games + upcoming games from all fetched days (not just today)
    live_games = [g for g in all_current_games if g['state'] in ['in', 'pre']]
    
    # Get extended week's games (next 14 days for more options)
    week_games = []
    for days_ahead in range(-1, 14):  # Include yesterday through next 13 days
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
    
    # Fetch betting odds
    try:
        odds_games = get_basketball_odds()
        betting_data = extract_betting_totals(odds_games)
        print(f"📊 Game Summary:")
        print(f"   Yesterday: {len(yesterday_games)} games")
        print(f"   Today: {len(today_games)} games") 
        print(f"   Tomorrow: {len(tomorrow_games)} games")
        print(f"   Live/Upcoming: {len(live_games)} games (across all days)")
        print(f"   Total Week: {len(unique_week_games)} games")
        print(f"   Betting Lines: {len(betting_data)} matched")
    except Exception as e:
        print(f"❌ Error fetching odds: {e}")
        betting_data = {}
    
    return live_games, today_games, tomorrow_games, unique_week_games, betting_data

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
        
        # Get the component that triggered this callback
        triggered_id = ctx.triggered_id
        print(f"DEBUG: Modal callback triggered by: {triggered_id}")
            
        # Only open when button is explicitly clicked
        if triggered_id == "game_selector_button" and open_clicks:
            print("DEBUG: Opening modal")
            return True
        # Close when cancel clicked
        elif triggered_id == "game_modal_close" and close_clicks:
            print("DEBUG: Closing modal - cancel button")
            return False
        # Close when game card clicked
        elif triggered_id and "game-card" in str(triggered_id) and game_clicks and any(game_clicks):
            print("DEBUG: Closing modal - game selected")
            return False
        # Stay in current state for any other triggers
        else:
            print(f"DEBUG: Keeping modal state: {is_open}")
            return is_open
    except Exception as e:
        print(f"DEBUG: Modal callback error: {e}")
        # Graceful fallback - maintain current state
        return is_open if is_open is not None else False

@app.callback(
    Output("game_search_input", "value", allow_duplicate=True),
    Input("clear_search_btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_search_input(n_clicks):
    """Clear search input when X button is clicked"""
    if n_clicks:
        return ""
    raise dash.exceptions.PreventUpdate

@app.callback(
    Output("game_selection_grid", "children"),
    Input("live_games_data", "data"),
    Input("game_search_input", "value")
)
def populate_game_modal(games_data, search_term):
    """Populate modal with game cards (with search filtering)"""
    print(f"DEBUG: populate_game_modal called with search_term: '{search_term}', games: {len(games_data) if games_data else 0}")
    
    if not games_data:
        return html.Div("No games available", style={"color": "#a0aec0", "textAlign": "center", "padding": "2rem"})
    
    # Filter games based on search term
    filtered_games = games_data
    if search_term and len(search_term.strip()) > 0:
        search_lower = search_term.lower().strip()
        filtered_games = []
        for game in games_data:
            # Search in team names
            if (search_lower in game.get('home_team', '').lower() or 
                search_lower in game.get('away_team', '').lower()):
                filtered_games.append(game)
    
    if not filtered_games:
        search_msg = f"No games found for '{search_term}'" if search_term else "No games available"
        return html.Div(search_msg, style={"color": "#a0aec0", "textAlign": "center", "padding": "2rem"})
    
    game_cards = []
    for i, game in enumerate(filtered_games):
        if game['is_live']:
            time_display = html.Div([
                html.Span("LIVE", className="live-indicator"),
                html.Span(f" • {game['clock']}", style={"color": "#a0aec0", "fontSize": "0.8rem"})
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
    [State("live_games_data", "data"),
     State("game_search_input", "value")],
    prevent_initial_call=True
)
def select_game_from_modal(game_clicks, games_data, search_term):
    """Handle game selection from modal (with search filtering)"""
    print(f"DEBUG: select_game_from_modal called with clicks: {game_clicks}, games_data length: {len(games_data) if games_data else 0}")
    
    # Don't reset if no clicks - this was causing the reset!
    if not any(game_clicks):
        print("DEBUG: No clicks detected - preventing update to avoid reset")
        raise dash.exceptions.PreventUpdate
    
    if not games_data:
        print("DEBUG: No games data - preventing update")
        raise dash.exceptions.PreventUpdate
    
    # Apply same filtering logic as populate_game_modal
    filtered_games = games_data
    if search_term and len(search_term.strip()) > 0:
        search_lower = search_term.lower().strip()
        filtered_games = []
        for game in games_data:
            if (search_lower in game.get('home_team', '').lower() or 
                search_lower in game.get('away_team', '').lower()):
                filtered_games.append(game)
    
    # Find which game was clicked (look for the highest click count)
    clicked_index = None
    max_clicks = 0
    for i, clicks in enumerate(game_clicks):
        if clicks and clicks > max_clicks:
            max_clicks = clicks
            clicked_index = i
    
    if clicked_index is not None and clicked_index < len(filtered_games):
        selected_game = filtered_games[clicked_index]
        
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

@app.callback(
    Output("selected_game_data", "data", allow_duplicate=True),
    Input("refresh_selected_game_btn", "n_clicks"),
    State("persistent_game_selection", "data"),
    prevent_initial_call=True
)
def refresh_selected_game_data(n_clicks, selected_game_id):
    """Refresh the stored game data by fetching fresh data directly from ESPN"""
    if not n_clicks or not selected_game_id:
        raise dash.exceptions.PreventUpdate
    
    print(f"DEBUG: Refresh button clicked for game ID: {selected_game_id}")
    
    # Fetch fresh live games data directly from ESPN
    try:
        fresh_live_games = fetch_live_games()
        print(f"DEBUG: Fetched {len(fresh_live_games)} fresh games from ESPN")
        
        # Find the selected game in fresh data
        updated_game = None
        for game in fresh_live_games:
            if str(game.get('id')) == str(selected_game_id):
                updated_game = game
                break
        
        if not updated_game:
            print(f"DEBUG: Could not find selected game {selected_game_id} in fresh ESPN data")
            # Try fetching from multiple days
            from datetime import datetime, timedelta
            for days_offset in [-1, 0, 1]:  # Yesterday, today, tomorrow
                date_str = (datetime.now() + timedelta(days=days_offset)).strftime('%Y%m%d')
                day_games = fetch_games_by_date(date_str)
                for game in day_games:
                    if str(game.get('id')) == str(selected_game_id):
                        updated_game = game
                        print(f"DEBUG: Found game in {date_str} data")
                        break
                if updated_game:
                    break
        
        if not updated_game:
            print(f"DEBUG: Still could not find game {selected_game_id} anywhere")
            raise dash.exceptions.PreventUpdate
        
        print(f"DEBUG: ✅ REFRESHING game data for {updated_game.get('away_team', '')} @ {updated_game.get('home_team', '')}")
        print(f"DEBUG: ✅ Fresh scores - {updated_game.get('away_score', 0)}-{updated_game.get('home_score', 0)}")
        print(f"DEBUG: ✅ Fresh time - {updated_game.get('clock', 'N/A')} (Period {updated_game.get('period', 'N/A')})")
        print(f"DEBUG: ✅ Game state - {updated_game.get('state', 'N/A')}")
        
        # Return the fresh game data to update the store
        return updated_game
        
    except Exception as e:
        print(f"DEBUG: Error fetching fresh game data: {e}")
        raise dash.exceptions.PreventUpdate

@app.callback(
    Output("refresh_selected_game_btn", "style"),
    Input("persistent_game_selection", "data")
)
def toggle_refresh_button_visibility(selected_game_id):
    """Show refresh button only when a game is selected"""
    base_style = {
        "background": "rgba(74, 85, 104, 0.2)",
        "border": "1px solid rgba(74, 85, 104, 0.4)",
        "color": "#a0aec0",
        "fontSize": "0.8rem",
        "padding": "0.4rem 0.6rem",
        "marginTop": "0.5rem",
        "borderRadius": "6px"
    }
    
    if selected_game_id:
        # Game selected - show button with hover effect
        base_style.update({
            "display": "inline-block",
            "opacity": "1",
            "cursor": "pointer"
        })
    else:
        # No game selected - hide button
        base_style.update({
            "display": "none",
            "opacity": "0"
        })
    
    return base_style

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
        print("DEBUG: ❌ auto_fill_from_game - No game data")
        raise dash.exceptions.PreventUpdate
    
    print(f"DEBUG: 🔄 AUTO-FILL TRIGGERED for game ID: {game_data.get('id')}")
    
    # Extract scores from ESPN data structure
    home_score = int(game_data.get('home_score', 0) or 0)
    away_score = int(game_data.get('away_score', 0) or 0)
    
    # Parse time from clock (e.g., "12:34" or "12:34.5")
    minutes_left = 0
    seconds_left = 0
    
    clock = game_data.get('clock', '0:00')
    period = game_data.get('period', 2)
    is_live = game_data.get('is_live', False)
    state = game_data.get('state', 'unknown')
    
    print(f"DEBUG: Raw game data - Clock: {clock}, Period: {period}, State: {state}, IsLive: {is_live}")
    
    if is_live and clock:
        try:
            if ':' in clock:
                time_parts = clock.split(':')
                minutes_left = int(time_parts[0])
                # Handle seconds with decimals
                seconds_part = time_parts[1].split('.')[0]  # Remove decimal part
                seconds_left = int(seconds_part)
                
                # Automatically convert first half time to full game time remaining
                if period == 1:  # First half - add 20 minutes for entire second half
                    original_mins = minutes_left
                    minutes_left += 20
                    print(f"DEBUG: ✅ First half conversion - ESPN: {original_mins}:{seconds_left:02d} → Full game: {minutes_left}:{seconds_left:02d}")
                else:
                    print(f"DEBUG: ✅ Second half time kept as-is: {minutes_left}:{seconds_left:02d}")
        except (ValueError, IndexError) as e:
            print(f"DEBUG: ❌ Error parsing clock '{clock}': {e}")
            minutes_left = 0
            seconds_left = 0
    
    # Get betting odds total for live_total - ONLY if betting line exists
    live_total = None
    if betting_odds_data and game_data:
        # Get team names for matching with betting data
        away_team_name = game_data.get('away_team', '')
        home_team_name = game_data.get('home_team', '')
        
        # Try to match with betting data using team names
        match_key1 = f"{away_team_name}|{home_team_name}"
        match_key2 = f"{home_team_name}|{away_team_name}"
        
        betting_info = betting_odds_data.get(match_key1) or betting_odds_data.get(match_key2)
        if betting_info:
            live_total = betting_info.get('avg_total')
            if live_total:
                print(f"DEBUG: ✅ Found betting total for {away_team_name} @ {home_team_name}: {live_total}")
            else:
                print(f"DEBUG: ⚠️ No betting total in matched data for {away_team_name} @ {home_team_name}")
        else:
            print(f"DEBUG: ⚠️ No betting data match for {away_team_name} @ {home_team_name}")
            print(f"DEBUG: ⚠️ Available betting keys: {list(betting_odds_data.keys())[:5]}...")  # Show first 5 keys
    else:
        print(f"DEBUG: ⚠️ No betting odds data available or no game data")
    
    # DO NOT use ESPN fallback - leave live_total empty if no betting line
    if live_total is None:
        print(f"DEBUG: ❌ No betting line found - leaving Live Total empty")
    
    away_team = game_data.get('away_team', 'Away')
    home_team = game_data.get('home_team', 'Home')
    
    print(f"DEBUG: ✅ AUTO-FILLING COMPLETE:")
    print(f"DEBUG:   - Game: {away_team} @ {home_team}")
    print(f"DEBUG:   - Scores: Away {away_score} - Home {home_score}")
    print(f"DEBUG:   - Time: {minutes_left}:{seconds_left:02d}")
    print(f"DEBUG:   - Live Total: {live_total} (from betting odds)")
    
    return (
        away_score,  # team1 = away team score
        home_score,  # team2 = home team score
        live_total,  # live_total from betting odds or ESPN fallback
        minutes_left,
        seconds_left
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
    over_thresh = r['required_pace'] >= r['threshold']
    curr = r['actual_pace']
    req = r['required_pace']
    
    # Signal logic - Fixed to be less restrictive for Under signals
    if pct >= 25 and over_thresh:
        signal, signal_color, border_color = "Under", "#4ade80", "#4ade8044"
    elif pct >= 5 and over_thresh:  # Lowered from 10 to 5
        signal, signal_color, border_color = "Under", "#86efac", "#86efac33"
    elif pct >= 0 and over_thresh:  # NEW: Show Under for any positive % when over threshold
        signal, signal_color, border_color = "Under", "#a7f3d0", "#a7f3d033"
    elif not over_thresh:  # Required pace below threshold - Hold
        signal, signal_color, border_color = "Hold", "#71717a", "#71717a33"
    elif pct >= -15:  # Negative percentage but not too bad - Hold
        signal, signal_color, border_color = "Hold", "#fbbf24", "#fbbf2433"
    else:  # Very negative percentage - Pass
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
            html.Div([
            # Professional Signal Header
                html.Div([
                html.Div([
                    html.H3(signal, style={"fontSize": "1.8rem", "fontWeight": "700", "color": signal_color, "margin": "0", "lineHeight": "1"}),
                    html.P(f"U{r['live_total']}" if pct >= 10 and over_thresh else "Monitor", 
                           style={"fontSize": "0.9rem", "color": "#a1a1aa", "margin": "0.5rem 0 0 0", "fontWeight": "500"})
                ])
            ], style={
                "textAlign": "center",
                "padding": "1.5rem",
                "marginBottom": "1.5rem",
                "borderRadius": "16px",
                "background": f"linear-gradient(135deg, {signal_color}15, {signal_color}08)",
                "border": f"1px solid {signal_color}30"
            }),
            
            # Clean Metrics Grid
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div("Current Score", className="metric-label"),
                        html.Div(f"{r['total']}", style={"fontSize": "1.6rem", "fontWeight": "700", "color": "#f4f4f5", "lineHeight": "1"})
                    ])
                ], className="text-center", width=3),
                dbc.Col([
                    html.Div([
                        html.Div("Points Needed", className="metric-label"),
                        html.Div(f"{r['needed']}", style={"fontSize": "1.6rem", "fontWeight": "700", "color": "#f59e0b", "lineHeight": "1"})
                    ])
                ], className="text-center", width=3),
                dbc.Col([
                    html.Div([
                        html.Div("Current Pace", className="metric-label"),
                        html.Div(f"{curr:.1f}", style={"fontSize": "1.6rem", "fontWeight": "700", "color": "#60a5fa", "lineHeight": "1"})
                    ])
                ], className="text-center", width=3),
                dbc.Col([
                    html.Div([
                        html.Div("Required Pace", className="metric-label"),
                        html.Div(f"{req:.1f}", style={"fontSize": "1.6rem", "fontWeight": "700", "color": signal_color, "lineHeight": "1"})
                    ])
                ], className="text-center", width=3),
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
                           style={"color": "#a0aec0", "fontSize": "0.9rem", "margin": "0.5rem 0"}),
                    html.P("Historical analysis requires ESPN team data", 
                           style={"color": "#718096", "fontSize": "0.8rem", "margin": "1rem 0 0 0"})
                ], className="pro-card")
            ]), {"display": "block"}
        
        # Get team stats with error handling using dynamic games count
        home_stats = get_team_stats(home_team_id, games_count)
        away_stats = get_team_stats(away_team_id, games_count)
        
        if not home_stats or not away_stats:
            return html.Div([
                html.Div([
                    html.H5("Team Analysis", style={"color": "#f4f4f5", "fontSize": "1.1rem", "fontWeight": "600", "margin": "0"}),
                    html.P(f"{away_team_name} @ {home_team_name}", style={"color": "#a1a1aa", "fontSize": "0.9rem", "margin": "0.5rem 0"}),
                    html.P("Historical data unavailable", style={"color": "#71717a", "fontSize": "0.85rem", "margin": "1rem 0 0 0"})
                ], className="pro-card")
            ]), {"display": "block"}
        
        # Calculate implied total
        implied_total = home_stats['avg_team_score'] + away_stats['avg_team_score']
        implied_total_per_min = implied_total / 40
        
        # Get betting line for this matchup
        betting_info = None
        if betting_odds_data:
            # Try to match with betting data using team names
            match_key1 = f"{away_team_name}|{home_team_name}"
            match_key2 = f"{home_team_name}|{away_team_name}"
            betting_info = betting_odds_data.get(match_key1) or betting_odds_data.get(match_key2)
        
        return html.Div([
        html.Div([
            # Clean Header with Team Logos
            html.Div([
                html.H5("Matchup Intelligence", 
                       style={"color": "#f4f4f5", "fontSize": "1.1rem", "fontWeight": "600", "margin": "0 0 0.5rem 0"}),
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
                                      "color": "#10d9c4" if betting_info else "#71717a", "lineHeight": "1"})
                    ])
                ], className="text-center", width=4),
                dbc.Col([
                    html.Div([
                        html.Div("Line pts/min" if betting_info else "Avg Scoring", className="metric-label"),
                        html.Div(
                            f"{(betting_info['avg_total'] / 40):.2f}" if betting_info 
                            else f"{away_stats['avg_team_score']:.0f} + {home_stats['avg_team_score']:.0f}",
                            style={"fontSize": "1.6rem" if betting_info else "1.2rem", "fontWeight": "700" if betting_info else "600", 
                                   "color": "#10d9c4" if betting_info else "#d4d4d8", "lineHeight": "1"})
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
                            html.Div("PPG", style={"fontSize": "0.7rem", "color": "#71717a", "marginBottom": "0.5rem"}),
                            
                            html.Div([
                                html.Span(f"{away_stats['avg_points_per_minute']:.2f}", 
                                         style={"fontSize": "1rem", "color": "#f59e0b", "fontWeight": "700"}),
                                html.Span(" pts/min", style={"fontSize": "0.65rem", "color": "#71717a", "marginLeft": "2px"})
                            ], className="mb-2"),
                            
                            html.Div([
                                html.Span("Defense: ", style={"fontSize": "0.75rem", "color": "#a1a1aa"}),
                                html.Span(f"{away_stats['avg_opp_score']:.1f}", 
                                         style={"fontSize": "0.75rem", "color": "#f87171", "fontWeight": "500"})
                            ], className="mb-1"),
                            
                            html.Div([
                                html.Span("Road: ", style={"fontSize": "0.75rem", "color": "#a1a1aa"}),
                                html.Span(f"{away_stats['away_avg']:.1f}" if away_stats['away_games'] > 0 else "N/A", 
                                         style={"fontSize": "0.75rem", "color": "#d4d4d8", "fontWeight": "500"})
                            ])
                        ])
                    ], style={
                        "background": "rgba(96, 165, 250, 0.05)",
                        "border": "1px solid rgba(96, 165, 250, 0.2)",
                        "borderRadius": "12px",
                        "padding": "1rem"
                    })
                ], width=5),
                
                # VS Separator
                dbc.Col([
                    html.Div("VS", 
                            style={
                                "textAlign": "center", 
                                "fontSize": "0.8rem", 
                                "color": "#71717a", 
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
                            html.Div("PPG", style={"fontSize": "0.7rem", "color": "#71717a", "marginBottom": "0.5rem"}),
                            
                            html.Div([
                                html.Span(f"{home_stats['avg_points_per_minute']:.2f}", 
                                         style={"fontSize": "1rem", "color": "#f59e0b", "fontWeight": "700"}),
                                html.Span(" pts/min", style={"fontSize": "0.65rem", "color": "#71717a", "marginLeft": "2px"})
                            ], className="mb-2"),
                            
                            html.Div([
                                html.Span("Defense: ", style={"fontSize": "0.75rem", "color": "#a1a1aa"}),
                                html.Span(f"{home_stats['avg_opp_score']:.1f}", 
                                         style={"fontSize": "0.75rem", "color": "#f87171", "fontWeight": "500"})
                            ], className="mb-1"),
                            
                            html.Div([
                                html.Span("Home: ", style={"fontSize": "0.75rem", "color": "#a1a1aa"}),
                                html.Span(f"{home_stats['home_avg']:.1f}" if home_stats['home_games'] > 0 else "N/A", 
                                         style={"fontSize": "0.75rem", "color": "#d4d4d8", "fontWeight": "500"})
                            ])
                        ])
                    ], style={
                        "background": "rgba(52, 211, 153, 0.05)",
                        "border": "1px solid rgba(52, 211, 153, 0.2)",
                        "borderRadius": "12px",
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
                html.P("Unable to load team analysis", style={"color": "#a1a1aa", "fontSize": "0.9rem", "margin": "0.5rem 0 0 0"})
            ], className="pro-card")
        ]), {"display": "block"}

# Analysis Tab Callbacks
@app.callback(
    Output("games-display", "children"),
    Output("team1_selector", "options"),
    Output("team2_selector", "options"),
    Output("today-btn", "color"),
    Output("tomorrow-btn", "color"),
    Output("week-btn", "color"),
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
    """Update games display and button states based on selection or auto-load Today when tab opens"""
    ctx_triggered = ctx.triggered[0]['prop_id'] if ctx.triggered else ''
    
    # Determine which button should be selected and what data to show
    if 'tomorrow-btn' in ctx_triggered:
        games_to_show = tomorrow_games or []
        title = "Tomorrow's Games"
        button_colors = ("secondary", "primary", "secondary")  # Today, Tomorrow, Week
    elif 'week-btn' in ctx_triggered:
        games_to_show = week_games or []
        title = "This Week's Games"
        button_colors = ("secondary", "secondary", "primary")
    else:
        # Default to Today (including when Research tab opens)
        games_to_show = today_games or []
        title = "Today's Games"
        button_colors = ("primary", "secondary", "secondary")
    
    if not games_to_show:
        games_content = html.Div([
            html.P(f"No games found for {title.lower()}", 
                   className="text-center text-muted py-4")
        ])
        team_options = []
        return (dbc.CardBody(games_content), 
                team_options, 
                team_options, 
                button_colors[0],  # Today button color
                button_colors[1],  # Tomorrow button color  
                button_colors[2])  # Week button color
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
    
    return (dbc.CardBody(games_content), 
            team_options, 
            team_options, 
            button_colors[0],  # Today button color
            button_colors[1],  # Tomorrow button color  
            button_colors[2])  # Week button color

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
    
    # Parse game time for upcoming games
    time_display = game['clock']
    if game['state'] == 'pre':
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
                    html.Span("Click to analyze teams →", style={"fontSize": "0.65rem", "color": "#4a5568", "fontStyle": "italic"})
                ], style={"marginTop": "4px"})
            ], width=7),
            dbc.Col([
                html.Div([
                    html.Span("Line: " if betting_total else "Total: ", style={"fontSize": "0.7rem", "color": "#666"}),
                    html.Span(str(betting_total) if betting_total else (str(total_score) if total_score is not None else "—"), 
                             style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#10d9c4" if betting_total else "#f59e0b"})
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
    State("team2_selector", "options"),
    State("betting_odds_data", "data")
)
def update_team_comparison(team1_id, team2_id, games_count, team1_options, team2_options, betting_odds_data):
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
        
        # Get betting line for this matchup
        betting_info = None
        if betting_odds_data and team1_name and team2_name:
            # Try both possible key combinations
            match_key1 = f"{team1_name}|{team2_name}"
            match_key2 = f"{team2_name}|{team1_name}"
            betting_info = betting_odds_data.get(match_key1) or betting_odds_data.get(match_key2)
        
        comparison_content.extend([
            html.Div([
                html.H6("Team Comparison", style={"color": "#e5e5e5", "textAlign": "center"}),
                
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div("Projected Total pts/min", className="metric-label"),
                            html.Div(f"{implied_total_per_min:.2f}", style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#f59e0b"})
                        ])
                    ], className="text-center", width=6),
                    dbc.Col([
                        html.Div([
                            html.Div("Betting Line" + (f" ({betting_info['num_books']} books)" if betting_info else ""), className="metric-label"),
                            html.Div(
                                f"{betting_info['avg_total']:.1f} ({betting_info['avg_total'] / 40:.2f} pts/min)" if betting_info else "No Line", 
                                style={"fontSize": "1.4rem", "fontWeight": "700", 
                                       "color": "#10d9c4" if betting_info else "#71717a"})
                        ])
                    ], className="text-center", width=6),
                ], className="mb-4")
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
                    html.Div("PTS/MIN", className="metric-label text-center mt-2"),
                    html.Div(f"{team1_stats['avg_points_per_minute']:.2f}", 
                            style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#f59e0b", "textAlign": "center"}),
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
                    html.Div([
                        html.Img(src=team2_logo_url, 
                                style={"width": "24px", "height": "24px", "marginRight": "8px", "borderRadius": "4px"},
                                className="team-logo") if team2_logo_url else None,
                        html.Span(team2_name or "Team 2", style={"color": "#3b82f6", "fontSize": "1rem", "fontWeight": "600"})
                    ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "1rem"}),
                    html.Div("AVG PPG", className="metric-label text-center"),
                    html.Div(f"{team2_stats['avg_team_score']:.1f}", 
                            style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#3b82f6", "textAlign": "center"}),
                    html.Div("PTS/MIN", className="metric-label text-center mt-2"),
                    html.Div(f"{team2_stats['avg_points_per_minute']:.2f}", 
                            style={"fontSize": "1.4rem", "fontWeight": "700", "color": "#f59e0b", "textAlign": "center"}),
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
                    html.Div("PTS/MIN", className="metric-label"),
                    html.Div(f"{team_stats['avg_points_per_minute']:.2f}", 
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
                    "border": "1px solid rgba(74, 85, 104, 0.2)",
                    "borderRadius": "6px",
                    "padding": "4px"
                })
            ])
        ])
    
    return dbc.CardBody(comparison_content)


if __name__ == "__main__":
    app.run(debug=True)
