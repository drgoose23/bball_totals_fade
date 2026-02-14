import dash
from dash import html, dcc, Output, Input, State, ALL, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
from datetime import datetime, timedelta, timezone
import json

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
        
        # Convert to Eastern Time (automatically handles EST/EDT based on date)
        # During standard time: UTC-5 (EST)
        # During daylight time: UTC-4 (EDT)
        
        # Simple DST check: 2nd Sunday in March to 1st Sunday in November
        # For basketball season (Nov-April), mostly EST except March games
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
        <title>CBB Fade Terminal • v2.0</title>
        {%favicon%}
        {%css%}
        <style>
            /* =====================================================
               PREMIUM TRADING TERMINAL DESIGN SYSTEM v2.0
               High-End Sports Analytics Interface
            ===================================================== */
            
            :root {
                /* Core Palette - Expensive & Professional */
                --void: #050609;
                --primary: #0a0d12;
                --secondary: #0f1419;
                --tertiary: #141922;
                
                /* Glassmorphic Surfaces */
                --glass-primary: rgba(15, 20, 30, 0.85);
                --glass-secondary: rgba(25, 35, 45, 0.75);
                --glass-tertiary: rgba(35, 45, 55, 0.65);
                
                /* Premium Accents */
                --cyan: #00d4ff;
                --violet: #8b5cf6;
                --emerald: #10b981;
                --amber: #f59e0b;
                --rose: #f43f5e;
                
                /* Typography */
                --text-primary: #ffffff;
                --text-secondary: #a1a1aa;
                --text-tertiary: #71717a;
                
                /* Glow Effects */
                --glow-cyan: 0 0 25px rgba(0, 212, 255, 0.4);
                --glow-emerald: 0 0 25px rgba(16, 185, 129, 0.4);
                --glow-amber: 0 0 25px rgba(245, 158, 11, 0.4);
                --glow-violet: 0 0 25px rgba(139, 92, 246, 0.4);
                
                /* Depth & Shadows */
                --shadow-void: 0 0 80px rgba(0, 0, 0, 0.9);
                --shadow-deep: 0 25px 80px rgba(0, 0, 0, 0.6);
                --shadow-mid: 0 15px 50px rgba(0, 0, 0, 0.4);
                --shadow-soft: 0 8px 25px rgba(0, 0, 0, 0.3);
                
                /* Borders */
                --border-primary: rgba(255, 255, 255, 0.12);
                --border-secondary: rgba(255, 255, 255, 0.06);
                --border-accent: rgba(0, 212, 255, 0.35);
                
                /* Animation Curves */
                --ease: cubic-bezier(0.4, 0, 0.2, 1);
                --bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
                --swift: cubic-bezier(0.25, 0.46, 0.45, 0.94);
            }
            
            * {
                box-sizing: border-box;
            }
            
            body {
                background: 
                    radial-gradient(ellipse at top, rgba(0, 212, 255, 0.03) 0%, transparent 50%),
                    radial-gradient(ellipse at bottom, rgba(139, 92, 246, 0.02) 0%, transparent 50%),
                    linear-gradient(180deg, var(--void) 0%, var(--primary) 40%, var(--secondary) 100%);
                background-attachment: fixed;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                color: var(--text-primary);
                font-weight: 400;
                line-height: 1.6;
                overflow-x: hidden;
                min-height: 100vh;
            }
            .card {
                background: var(--glass-primary);
                border: 1px solid var(--border-primary);
                border-radius: 20px;
                backdrop-filter: blur(20px) saturate(180%);
                box-shadow: var(--shadow-deep), inset 0 1px 0 rgba(255, 255, 255, 0.1);
                position: relative;
                overflow: hidden;
                transition: all 0.4s var(--ease);
            }
            
            .card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, var(--border-accent), transparent);
                opacity: 0.6;
            }
            
            .card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-void), var(--glow-cyan);
                border-color: var(--border-accent);
            }
            .form-control {
                background: var(--glass-secondary) !important;
                border: 1px solid var(--border-primary) !important;
                color: var(--text-primary) !important;
                font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
                font-weight: 500;
                border-radius: 12px !important;
                font-size: 0.9rem;
                padding: 0.8rem 1rem;
                transition: all 0.3s var(--ease);
                backdrop-filter: blur(15px);
                position: relative;
            }
            
            .form-control:focus {
                border-color: var(--border-accent) !important;
                box-shadow: var(--glow-cyan), inset 0 0 0 1px var(--border-accent) !important;
                background: var(--glass-primary) !important;
                transform: scale(1.02);
            }
            
            .form-control:hover {
                border-color: var(--border-accent) !important;
                background: var(--glass-primary) !important;
            }
            
            .form-control::placeholder { 
                color: var(--text-tertiary) !important; 
                font-weight: 400;
            }
            .btn-adj {
                background: var(--glass-tertiary) !important;
                border: 1px solid var(--border-primary) !important;
                color: var(--text-secondary) !important;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 600;
                border-radius: 10px;
                transition: all 0.25s var(--ease);
                font-size: 0.85rem;
                padding: 0.4rem 0.7rem;
                min-width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                backdrop-filter: blur(10px);
            }
            
            .btn-adj::before {
                content: '';
                position: absolute;
                inset: 0;
                border-radius: inherit;
                background: linear-gradient(135deg, var(--cyan), var(--violet));
                opacity: 0;
                transition: opacity 0.25s var(--ease);
                z-index: -1;
            }
            
            .btn-adj:hover { 
                color: var(--text-primary) !important;
                border-color: var(--border-accent) !important;
                transform: translateY(-1px) scale(1.05);
                box-shadow: var(--glow-cyan);
            }
            
            .btn-adj:hover::before {
                opacity: 0.1;
            }
            
            .btn-adj:active {
                transform: translateY(0) scale(0.98);
                box-shadow: var(--shadow-soft);
            }
            
            /* Micro Buttons for Score Inputs */
            .btn-micro {
                background: var(--glass-tertiary) !important;
                border: 1px solid var(--border-secondary) !important;
                color: var(--text-tertiary) !important;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 600;
                border-radius: 6px !important;
                font-size: 0.7rem !important;
                padding: 0.2rem 0.4rem !important;
                min-width: 28px !important;
                height: 24px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                transition: all 0.2s var(--ease) !important;
                opacity: 0.7;
            }
            
            .btn-micro:hover {
                color: var(--text-secondary) !important;
                border-color: var(--border-primary) !important;
                background: var(--glass-secondary) !important;
                opacity: 1;
                transform: scale(1.05);
            }
            
            .btn-micro:active {
                transform: scale(0.95);
                opacity: 0.8;
            }
            .label { 
                font-size: 0.75rem; 
                color: var(--text-secondary); 
                text-transform: uppercase; 
                letter-spacing: 1.2px; 
                margin-bottom: 0.6rem; 
                font-weight: 600;
                font-family: 'Inter', sans-serif;
                position: relative;
            }
            
            .label::after {
                content: '';
                position: absolute;
                bottom: -2px;
                left: 0;
                width: 20px;
                height: 1px;
                background: linear-gradient(90deg, var(--cyan), transparent);
                opacity: 0.5;
            }
            .output-card {
                background: var(--glass-primary);
                border: 1px solid var(--border-primary);
                border-radius: 24px;
                backdrop-filter: blur(25px) saturate(200%);
                box-shadow: var(--shadow-void), inset 0 1px 0 rgba(255, 255, 255, 0.1);
                position: relative;
                overflow: hidden;
            }
            
            .output-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, 
                    transparent, 
                    var(--cyan), 
                    var(--violet), 
                    var(--emerald), 
                    transparent
                );
                opacity: 0.6;
            }
            
            .output-card::after {
                content: '';
                position: absolute;
                inset: 1px;
                border-radius: 23px;
                background: linear-gradient(135deg, 
                    rgba(0, 212, 255, 0.02), 
                    rgba(139, 92, 246, 0.02)
                );
                pointer-events: none;
            }
            .metric-value { 
                font-family: 'JetBrains Mono', monospace;
                font-weight: 700;
                font-size: 2.2rem;
                letter-spacing: -0.03em;
                line-height: 0.9;
                background: linear-gradient(135deg, var(--text-primary), var(--cyan));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                transition: all 0.3s var(--ease);
            }
            
            .metric-value:hover {
                transform: scale(1.05);
                filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.3));
            }
            
            .metric-label {
                font-size: 0.75rem;
                font-weight: 600;
                letter-spacing: 1.5px;
                text-transform: uppercase;
                color: var(--text-secondary);
                margin-bottom: 0.4rem;
                font-family: 'Inter', sans-serif;
                position: relative;
            }
            
            .metric-label::before {
                content: '◦';
                color: var(--cyan);
                margin-right: 0.5rem;
                opacity: 0.6;
            }
            .pro-card {
                background: var(--glass-primary);
                border: 1px solid var(--border-primary);
                border-radius: 20px;
                padding: 2rem;
                backdrop-filter: blur(20px) saturate(180%);
                box-shadow: var(--shadow-deep), inset 0 1px 0 rgba(255, 255, 255, 0.08);
                position: relative;
                overflow: hidden;
                transition: all 0.4s var(--ease);
            }
            
            .pro-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, 
                    transparent, 
                    var(--border-accent), 
                    transparent
                );
                opacity: 0.7;
            }
            
            .pro-card:hover {
                transform: translateY(-3px);
                box-shadow: var(--shadow-void), var(--glow-cyan);
                border-color: var(--border-accent);
            }
            
            .pro-card:hover::before {
                background: linear-gradient(90deg, 
                    transparent, 
                    var(--cyan), 
                    var(--violet), 
                    transparent
                );
            }
            /* Premium Dropdown System */
            .dark-dropdown .Select-control { 
                background: var(--glass-secondary) !important; 
                border: 1px solid var(--border-primary) !important; 
                color: var(--text-primary) !important; 
                border-radius: 14px !important;
                min-height: 48px;
                font-size: 0.9rem;
                font-family: 'JetBrains Mono', 'SF Mono', monospace;
                font-weight: 500;
                transition: all 0.3s var(--ease);
                backdrop-filter: blur(15px);
                position: relative;
            }
            
            .dark-dropdown .Select-control::before {
                content: '';
                position: absolute;
                inset: -1px;
                border-radius: inherit;
                background: linear-gradient(135deg, var(--cyan), var(--violet));
                opacity: 0;
                transition: opacity 0.3s var(--ease);
                z-index: -1;
            }
            
            .dark-dropdown .Select-control:hover {
                border-color: var(--border-accent) !important;
                background: var(--glass-primary) !important;
                transform: translateY(-1px);
                box-shadow: var(--glow-cyan);
            }
            
            .dark-dropdown .Select-control:hover::before {
                opacity: 0.1;
            }
            
            .dark-dropdown .Select-placeholder { 
                color: var(--text-tertiary) !important; 
                font-weight: 400; 
                font-family: 'Inter', sans-serif;
            }
            
            .dark-dropdown .Select-value-label { 
                color: var(--text-primary) !important; 
                font-weight: 600; 
                font-family: 'JetBrains Mono', monospace;
            }
            
            .dark-dropdown .Select-input > input { 
                color: var(--text-primary) !important; 
                font-family: 'JetBrains Mono', monospace;
            }
            
            .dark-dropdown .Select-menu-outer { 
                background: var(--glass-primary) !important; 
                border: 1px solid var(--border-accent) !important; 
                border-radius: 14px !important;
                backdrop-filter: blur(25px) saturate(180%);
                box-shadow: var(--shadow-void), var(--glow-cyan);
                max-height: 350px;
                margin-top: 4px;
            }
            
            .dark-dropdown .Select-menu { 
                background: transparent !important;
                max-height: 320px;
            }
            
            .dark-dropdown .Select-option { 
                color: var(--text-secondary) !important; 
                background: transparent !important; 
                padding: 14px 18px !important;
                font-size: 0.9rem;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 500;
                transition: all 0.2s var(--ease);
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                position: relative;
            }
            
            .dark-dropdown .Select-option::before {
                content: '▸';
                color: var(--cyan);
                margin-right: 8px;
                opacity: 0;
                transition: opacity 0.2s var(--ease);
            }
            
            .dark-dropdown .Select-option.is-focused { 
                background: var(--glass-secondary) !important; 
                color: var(--text-primary) !important;
                transform: translateX(4px);
            }
            
            .dark-dropdown .Select-option.is-focused::before {
                opacity: 1;
            }
            
            .dark-dropdown .Select-option.is-selected { 
                background: var(--glass-tertiary) !important; 
                color: var(--cyan) !important;
                font-weight: 600;
            }
            
            /* Premium Button System */
            .btn-primary {
                background: linear-gradient(135deg, var(--cyan), var(--violet)) !important;
                border: 1px solid var(--border-accent) !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                padding: 0.7rem 1.4rem !important;
                font-size: 0.9rem !important;
                font-family: 'Inter', sans-serif;
                transition: all 0.3s var(--ease) !important;
                box-shadow: var(--shadow-soft), var(--glow-cyan) !important;
                color: var(--text-primary) !important;
                position: relative;
                overflow: hidden;
            }
            
            .btn-primary::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s var(--ease);
            }
            
            .btn-primary:hover {
                transform: translateY(-2px) scale(1.02) !important;
                box-shadow: var(--shadow-deep), var(--glow-cyan) !important;
            }
            
            .btn-primary:hover::before {
                left: 100%;
            }
            
            .btn-primary:active {
                transform: translateY(0) scale(0.98) !important;
                box-shadow: var(--shadow-soft) !important;
            }
            
            .btn-secondary {
                background: var(--glass-secondary) !important;
                border: 1px solid var(--border-primary) !important;
                color: var(--text-secondary) !important;
                border-radius: 12px !important;
                font-weight: 500 !important;
                padding: 0.7rem 1.4rem !important;
                font-size: 0.9rem !important;
                font-family: 'Inter', sans-serif;
                transition: all 0.3s var(--ease) !important;
                backdrop-filter: blur(10px);
                position: relative;
            }
            
            .btn-secondary:hover {
                background: var(--glass-primary) !important;
                border-color: var(--border-accent) !important;
                color: var(--text-primary) !important;
                transform: translateY(-1px) !important;
                box-shadow: var(--glow-cyan) !important;
            }
            
            .btn-secondary:active {
                transform: translateY(0) scale(0.98) !important;
                box-shadow: var(--shadow-soft) !important;
            }
            
            /* Premium Slider System */
            .rc-slider {
                background: var(--glass-tertiary) !important;
                border-radius: 8px !important;
                height: 6px !important;
                position: relative;
            }
            
            .rc-slider::before {
                content: '';
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, var(--cyan), var(--violet), var(--emerald));
                transform: translateY(-50%);
                opacity: 0.3;
            }
            
            .rc-slider-track {
                background: linear-gradient(90deg, var(--cyan), var(--violet)) !important;
                border-radius: 8px !important;
                height: 6px !important;
                box-shadow: var(--glow-cyan);
            }
            
            .rc-slider-handle {
                background: var(--text-primary) !important;
                border: 3px solid var(--cyan) !important;
                box-shadow: var(--shadow-mid), var(--glow-cyan) !important;
                width: 24px !important;
                height: 24px !important;
                margin-top: -9px !important;
                transition: all 0.3s var(--ease);
                position: relative;
            }
            
            .rc-slider-handle::before {
                content: '';
                position: absolute;
                inset: 2px;
                border-radius: 50%;
                background: linear-gradient(135deg, var(--cyan), var(--violet));
                opacity: 0.8;
            }
            
            .rc-slider-handle:hover {
                transform: scale(1.2);
                box-shadow: var(--shadow-deep), var(--glow-cyan);
            }
            
            .rc-slider-mark-text {
                color: var(--text-secondary) !important;
                font-size: 0.75rem !important;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 600;
            }
            
            /* Premium Game Selection System */
            .game-selector-btn {
                background: var(--glass-secondary) !important;
                border: 1px solid var(--border-primary) !important;
                border-radius: 14px !important;
                transition: all 0.3s var(--ease) !important;
                backdrop-filter: blur(15px);
                position: relative;
            }
            
            .game-selector-btn::before {
                content: '';
                position: absolute;
                inset: -1px;
                border-radius: inherit;
                background: linear-gradient(135deg, var(--cyan), var(--violet));
                opacity: 0;
                transition: opacity 0.3s var(--ease);
                z-index: -1;
            }
            
            .game-selector-btn:hover {
                background: var(--glass-primary) !important;
                border-color: var(--border-accent) !important;
                transform: translateY(-2px) !important;
                box-shadow: var(--glow-cyan);
            }
            
            .game-selector-btn:hover::before {
                opacity: 0.1;
            }
            
            .game-card {
                background: var(--glass-secondary);
                border: 1px solid var(--border-primary);
                border-radius: 16px;
                padding: 1.2rem;
                margin: 0.6rem 0;
                cursor: pointer;
                transition: all 0.3s var(--ease);
                font-family: 'JetBrains Mono', monospace;
                position: relative;
                overflow: hidden;
                backdrop-filter: blur(15px);
            }
            
            .game-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, transparent, var(--cyan), transparent);
                opacity: 0;
                transition: opacity 0.3s var(--ease);
            }
            
            .game-card:hover {
                background: var(--glass-primary);
                border-color: var(--border-accent);
                transform: translateY(-3px) scale(1.02);
                box-shadow: var(--shadow-deep), var(--glow-cyan);
            }
            
            .game-card:hover::before {
                opacity: 1;
            }
            
            .game-time {
                color: var(--emerald);
                font-weight: 700;
                font-size: 0.9rem;
                margin-bottom: 0.6rem;
                font-family: 'JetBrains Mono', monospace;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                position: relative;
            }
            
            .game-time::before {
                content: '⏰';
                margin-right: 0.5rem;
                opacity: 0.7;
            }
            
            .game-matchup {
                color: var(--text-primary);
                font-weight: 600;
                font-size: 1.05rem;
                margin-bottom: 0.4rem;
                font-family: 'Inter', sans-serif;
                line-height: 1.3;
            }
            
            .game-details {
                color: var(--text-secondary);
                font-size: 0.85rem;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 500;
            }
            
            .live-indicator {
                color: var(--rose);
                font-weight: 700;
                font-size: 0.8rem;
                font-family: 'JetBrains Mono', monospace;
                text-transform: uppercase;
                letter-spacing: 1px;
                position: relative;
                animation: pulse 2s infinite;
            }
            
            .live-indicator::before {
                content: '●';
                margin-right: 0.5rem;
                animation: blink 1s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            @keyframes blink {
                0%, 50% { opacity: 1; }
                51%, 100% { opacity: 0.3; }
            }
            
            /* Premium Analysis Cards */
            .analysis-game-card {
                background: var(--glass-secondary) !important;
                border: 1px solid var(--border-primary) !important;
                border-radius: 14px !important;
                transition: all 0.3s var(--ease) !important;
                backdrop-filter: blur(15px);
                position: relative;
            }
            
            .analysis-game-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, var(--border-accent), transparent);
                opacity: 0;
                transition: opacity 0.3s var(--ease);
            }
            
            .analysis-game-card:hover {
                background: var(--glass-primary) !important;
                border-color: var(--border-accent) !important;
                transform: translateY(-2px) scale(1.01) !important;
                box-shadow: var(--shadow-mid), var(--glow-cyan) !important;
            }
            
            .analysis-game-card:hover::before {
                opacity: 1;
            }
            
            /* Premium Team Logos */
            .team-logo {
                object-fit: contain;
                filter: brightness(0.9) saturate(1.1);
                transition: all 0.3s var(--ease);
                background: var(--glass-tertiary);
                border-radius: 6px;
                border: 1px solid var(--border-secondary);
                position: relative;
            }
            
            .team-logo::after {
                content: '';
                position: absolute;
                inset: 0;
                border-radius: inherit;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
                pointer-events: none;
            }
            
            .team-logo:hover {
                filter: brightness(1.1) saturate(1.2);
                transform: scale(1.08);
                box-shadow: var(--glow-cyan);
                border-color: var(--border-accent);
            }
            
            /* Hide broken images elegantly */
            .team-logo[src=""], .team-logo:not([src]) {
                display: none;
            }
            
            .team-logo[src=""]:after, .team-logo:not([src]):after {
                content: '🏀';
                position: absolute;
                inset: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.8rem;
                opacity: 0.5;
            }
            
            /* =====================================================
               PREMIUM NAVIGATION & HEADER SYSTEM
            ===================================================== */
            
            .nav-tabs {
                border-bottom: 2px solid var(--border-primary);
                margin-bottom: 2rem;
                background: var(--glass-tertiary);
                border-radius: 16px 16px 0 0;
                padding: 0.5rem 0.5rem 0 0.5rem;
                backdrop-filter: blur(15px);
            }
            
            .nav-tabs .nav-link {
                background: transparent;
                border: none;
                color: var(--text-secondary);
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                padding: 1rem 2rem;
                border-radius: 12px;
                transition: all 0.3s var(--ease);
                position: relative;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                font-size: 0.85rem;
                margin-right: 0.5rem;
            }
            
            .nav-tabs .nav-link::before {
                content: '';
                position: absolute;
                bottom: 0;
                left: 50%;
                width: 0;
                height: 2px;
                background: var(--cyan);
                transition: all 0.3s var(--ease);
                transform: translateX(-50%);
            }
            
            .nav-tabs .nav-link:hover {
                color: var(--text-primary);
                background: var(--glass-secondary);
                transform: translateY(-2px);
            }
            
            .nav-tabs .nav-link.active {
                color: var(--cyan);
                background: var(--glass-primary);
                border: 1px solid var(--border-accent);
                box-shadow: var(--glow-cyan);
            }
            
            .nav-tabs .nav-link.active::before {
                width: 60%;
            }
            
            /* Premium Container */
            .container-fluid {
                position: relative;
            }
            
            .container-fluid::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: 
                    radial-gradient(circle at 20% 80%, rgba(0, 212, 255, 0.05) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.05) 0%, transparent 50%);
                pointer-events: none;
                z-index: -1;
            }
            
            /* Enhanced Typography */
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Inter', sans-serif;
                font-weight: 700;
                background: linear-gradient(135deg, var(--text-primary), var(--cyan));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: -0.02em;
            }
            
            /* Number Enhancement */
            .number-display {
                font-family: 'JetBrains Mono', monospace;
                font-variant-numeric: tabular-nums;
                transition: all 0.3s var(--ease);
            }
            
            .number-display:hover {
                transform: scale(1.05);
                text-shadow: 0 0 10px var(--cyan);
            }
            
            /* Scrollbar Styling */
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: var(--glass-tertiary);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(180deg, var(--cyan), var(--violet));
                border-radius: 4px;
                border: 1px solid var(--border-primary);
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(180deg, var(--violet), var(--cyan));
            }
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
    # Professional Header
    html.Div([
        html.H2("CBB Fade Terminal v2.0", 
                style={
                    "fontWeight": "700", 
                    "marginBottom": "0.5rem", 
                    "letterSpacing": "-0.02em",
                    "fontSize": "2.2rem",
                    "textAlign": "center",
                    "position": "relative"
                }),
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
    dcc.Interval(id="refresh_games", interval=15*1000, n_intervals=0),  # Refresh every 15 seconds
    
    # Game Selection Modal
    dbc.Modal([
        dbc.ModalHeader([
            html.H4("Select Game", style={"color": "#f7fafc", "margin": "0"}),
        ], style={"background": "rgba(26, 32, 44, 0.95)", "border": "none"}),
        dbc.ModalBody([
            html.Div(id="game_selection_grid", style={"maxHeight": "60vh", "overflowY": "auto"})
        ], style={"background": "rgba(26, 32, 44, 0.95)", "border": "none", "padding": "1.5rem"}),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="game_modal_close", className="pro-button-secondary", size="sm")
        ], style={"background": "rgba(26, 32, 44, 0.95)", "border": "none"})
    ], id="game_selection_modal", is_open=False, centered=True, size="lg", backdrop="static")
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
                    ], className="mb-4"),
                    
                    html.Div([
                        html.Div("Your Under (optional)", className="label"),
                        dbc.Input(id="my_bet", type="number"),
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
    Output("game_selection_grid", "children"),
    Input("live_games_data", "data")
)
def populate_game_modal(games_data):
    """Populate modal with game cards"""
    if not games_data:
        return html.Div("No games available", style={"color": "#a0aec0", "textAlign": "center", "padding": "2rem"})
    
    game_cards = []
    for i, game in enumerate(games_data):
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
    prevent_initial_call=True
)
def auto_fill_from_game(game_data):
    """Auto-fill scores and time from selected game"""
    if not game_data:
        raise dash.exceptions.PreventUpdate
    
    # Extract scores from ESPN data structure - only fill if there's actual data
    home_score = game_data.get('home_score')
    away_score = game_data.get('away_score')
    
    # Don't show "0" unless it's an actual score from live game
    if home_score == 0 and not game_data.get('is_live'):
        home_score = None
    if away_score == 0 and not game_data.get('is_live'):
        away_score = None
    
    # Parse time from clock (e.g., "12:34" or "12:34.5")
    minutes_left = None
    seconds_left = None
    
    if game_data.get('is_live') and game_data.get('clock'):
        try:
            clock = game_data.get('clock', '0:00')
            if ':' in clock:
                time_parts = clock.split(':')
                minutes_left = int(time_parts[0])
                # Handle seconds with decimals
                seconds_part = time_parts[1].split('.')[0]  # Remove decimal part
                seconds_left = int(seconds_part)
                
                # Only show 0 minutes/seconds if it's actually from live game
                if minutes_left == 0 and seconds_left == 0:
                    minutes_left = 0  # Game actually at 0:00
                    seconds_left = 0
        except (ValueError, IndexError):
            minutes_left = None
            seconds_left = None
    
    # Calculate live total
    live_total = None
    if home_score is not None and away_score is not None:
        live_total = home_score + away_score
    
    print(f"DEBUG: Auto-filling - home:{home_score}, away:{away_score}, total:{live_total}, mins:{minutes_left}, secs:{seconds_left}")
    
    return (
        home_score,
        away_score,
        live_total,
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
    # Handle None values for calculation without forcing UI display
    mins_calc = mins if mins is not None else 0
    secs_calc = secs if secs is not None else 0
    min_left = mins_calc + secs_calc / 60
    
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
    prevent_initial_call=True
)
def update_team_context(selected_game_data, games_count):
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
                        html.Div("Projected Total", className="metric-label"),
                        html.Div(f"{implied_total:.1f}", 
                                style={"fontSize": "1.8rem", "fontWeight": "700", "color": "#f59e0b", "lineHeight": "1"})
                    ])
                ], className="text-center", width=6),
                dbc.Col([
                    html.Div([
                        html.Div("Avg Scoring", className="metric-label"),
                        html.Div(f"{away_stats['avg_team_score']:.0f} + {home_stats['avg_team_score']:.0f}", 
                                style={"fontSize": "1.2rem", "fontWeight": "600", "color": "#d4d4d8", "lineHeight": "1"})
                    ])
                ], className="text-center", width=6),
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
                            html.Div("PPG", style={"fontSize": "0.7rem", "color": "#71717a", "marginBottom": "0.75rem"}),
                            
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
                            html.Div("PPG", style={"fontSize": "0.7rem", "color": "#71717a", "marginBottom": "0.75rem"}),
                            
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
    Input("today-btn", "n_clicks"),
    Input("tomorrow-btn", "n_clicks"),
    Input("week-btn", "n_clicks"),
    Input("main-tabs", "active_tab"),  # Auto-load when Research tab opens
    State("today_games_data", "data"),
    State("tomorrow_games_data", "data"),
    State("week_games_data", "data"),
    prevent_initial_call=True
)
def update_games_display(today_clicks, tomorrow_clicks, week_clicks, active_tab, today_games, tomorrow_games, week_games):
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

def create_game_card(game):
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
                    html.Span("Total: ", style={"fontSize": "0.7rem", "color": "#666"}),
                    html.Span(str(total_score) if total_score is not None else "—", 
                             style={"fontSize": "0.9rem", "fontWeight": "600", "color": "#f59e0b"})
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
                    html.Div([
                        html.Img(src=team1_logo_url, 
                                style={"width": "24px", "height": "24px", "marginRight": "8px", "borderRadius": "4px"},
                                className="team-logo") if team1_logo_url else None,
                        html.Span(team1_name or "Team 1", style={"color": "#4ade80", "fontSize": "1rem", "fontWeight": "600"})
                    ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "1rem"}),
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
                    html.Div([
                        html.Img(src=team2_logo_url, 
                                style={"width": "24px", "height": "24px", "marginRight": "8px", "borderRadius": "4px"},
                                className="team-logo") if team2_logo_url else None,
                        html.Span(team2_name or "Team 2", style={"color": "#3b82f6", "fontSize": "1rem", "fontWeight": "600"})
                    ], style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "1rem"}),
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
                    "border": "1px solid rgba(74, 85, 104, 0.2)",
                    "borderRadius": "6px",
                    "padding": "4px"
                })
            ])
        ])
    
    return dbc.CardBody(comparison_content)


if __name__ == "__main__":
    app.run(debug=True)
