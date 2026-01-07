#!/usr/bin/env python3
import sys
import time
import json
import subprocess
import re
import ssl
import urllib.request
import urllib.error
import signal
import shutil
from datetime import datetime

# Configuration
REFRESH_INTERVAL = 1  # seconds
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
ANSI_CYAN = "\033[36m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_CLEAR_LINE = "\033[K"
ANSI_HOME = "\033[H"
ANSI_CLEAR_SCREEN = "\033[2J"
ANSI_CLEAR_EOS = "\033[J" # Clear from cursor to end of screen

# Custom exception to interrupt sleep on resize
class ResizeInterrupt(Exception):
    pass

def handle_resize(signum, frame):
    """Signal handler for window resize events."""
    raise ResizeInterrupt()

def get_process_info():
    """Finds the Antigravity process and extracts PID and CSRF token."""
    try:
        # ps -ww -eo pid,args ensures we get the full command line without truncation
        cmd = ['ps', '-ww', '-eo', 'pid,args']
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8')
        
        for line in output.splitlines():
            if 'antigravity' in line and 'language_server' in line and '--csrf_token' in line:
                # Extract PID
                parts = line.strip().split(maxsplit=1)
                if not parts: continue
                pid = parts[0]
                
                # Extract CSRF Token
                token_match = re.search(r'--csrf_token[=\s]+([a-f0-9-]+)', line, re.IGNORECASE)
                if token_match:
                    return pid, token_match.group(1)
    except Exception:
        pass
    return None, None

def get_listening_port(pid):
    """Finds the actual listening TCP port for the given PID using lsof."""
    try:
        cmd = ['lsof', '-nP', '-a', '-iTCP', '-sTCP:LISTEN', '-p', str(pid)]
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8')
        
        # Look for a line with a port
        for line in output.splitlines():
            if '(LISTEN)' in line:
                match = re.search(r'(?:127\.0\.0\.1|0\.0\.0\.0|\[::1?\]|\*):(\d+)', line)
                if match:
                    return match.group(1)
    except Exception:
        pass
    return None

def fetch_status(port, token):
    """Fetches user status from the local server."""
    url = f"https://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/GetUserStatus"
    headers = {
        "Content-Type": "application/json",
        "Connect-Protocol-Version": "1",
        "X-Codeium-Csrf-Token": token
    }
    data = json.dumps({
        "metadata": {
            "ideName": "antigravity",
            "extensionName": "antigravity",
            "locale": "en"
        }
    }).encode('utf-8')

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=1) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception:
        return None

def format_time_delta(iso_time_str):
    """Calculates time remaining until reset."""
    if not iso_time_str:
        return "N/A"
    try:
        reset_dt = datetime.strptime(iso_time_str.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
        now_dt = datetime.now(reset_dt.tzinfo)
        delta = reset_dt - now_dt
        
        if delta.total_seconds() < 0:
            return "Resetting..."
            
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        
        if hours > 24:
            days = hours // 24
            return f"{days}d {hours % 24}h"
        return f"{hours}h {minutes}m"
    except Exception:
        return iso_time_str

def color_percentage(percent):
    """Returns ANSI color code based on percentage."""
    if percent > 50: return ANSI_GREEN
    if percent > 20: return ANSI_YELLOW
    return ANSI_RED

def draw_progress_bar(percent, width=20):
    """Draws a text-based progress bar."""
    filled = int(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"{color_percentage(percent)}{bar}{ANSI_RESET}"

def get_terminal_width():
    """Gets the current terminal width."""
    return shutil.get_terminal_size().columns

def print_dashboard(data, pid, port):
    """Prints the dashboard to the terminal."""
    user_status = data.get('userStatus', {})
    plan_info = user_status.get('planStatus', {}).get('planInfo', {})
    prompt_credits = user_status.get('planStatus', {}).get('availablePromptCredits', 0)
    monthly_credits = plan_info.get('monthlyPromptCredits', 0)
    
    term_width = get_terminal_width()
    separator = "-" * min(term_width, 80)
    
    output_lines = []
    
    # Header
    output_lines.append(f"{ANSI_BOLD}🚀 Antigravity Cockpit Monitor{ANSI_RESET}{ANSI_CLEAR_LINE}")
    output_lines.append(f"PID: {ANSI_CYAN}{pid}{ANSI_RESET} | Port: {ANSI_CYAN}{port}{ANSI_RESET} | Time: {datetime.now().strftime('%H:%M:%S')}{ANSI_CLEAR_LINE}")
    output_lines.append(f"{separator}{ANSI_CLEAR_LINE}")
    
    # User Profile
    output_lines.append(f"User:  {ANSI_BOLD}{user_status.get('name', 'Unknown')}{ANSI_RESET} ({user_status.get('email', 'N/A')}){ANSI_CLEAR_LINE}")
    output_lines.append(f"Plan:  {ANSI_CYAN}{plan_info.get('planName', 'Free')}{ANSI_RESET} ({user_status.get('userTier', {}).get('name', 'Unknown')}){ANSI_CLEAR_LINE}")
    
    # Global Credits
    if monthly_credits > 0:
        credit_pct = (prompt_credits / monthly_credits) * 100
        output_lines.append(f"Monthly Prompt Quota: {draw_progress_bar(credit_pct)} {prompt_credits:,} / {monthly_credits:,} ({credit_pct:.1f}%){ANSI_CLEAR_LINE}")
    else:
        output_lines.append(f"Prompt Quota:         {prompt_credits:,} (No limit info){ANSI_CLEAR_LINE}")

    flow_credits = user_status.get('planStatus', {}).get('availableFlowCredits', 0)
    monthly_flow = plan_info.get('monthlyFlowCredits', 0)

    if monthly_flow > 0:
        flow_pct = (flow_credits / monthly_flow) * 100
        output_lines.append(f"Monthly Flow Quota:   {draw_progress_bar(flow_pct)} {flow_credits:,} / {monthly_flow:,} ({flow_pct:.1f}%){ANSI_CLEAR_LINE}")

    output_lines.append(f"{separator}{ANSI_CLEAR_LINE}")
    output_lines.append(f"{ANSI_BOLD}{'Model Name':<35} {'Usage':<22} {'Reset In'}{ANSI_RESET}{ANSI_CLEAR_LINE}")
    output_lines.append(f"{separator}{ANSI_CLEAR_LINE}")
    
    # Models
    models = user_status.get('cascadeModelConfigData', {}).get('clientModelConfigs', [])
    models.sort(key=lambda x: (not x.get('isRecommended', False), x.get('label', '')))

    for model in models:
        name = model.get('label', 'Unknown')[:34] # Truncate long names
        quota = model.get('quotaInfo', {})
        remaining = quota.get('remainingFraction', 0)
        reset_time = quota.get('resetTime')
        
        percent = remaining * 100
        bar = draw_progress_bar(percent, width=15)
        reset_display = format_time_delta(reset_time)
        
        output_lines.append(f"{name:<35} {bar} {percent:>5.1f}%  {reset_display}{ANSI_CLEAR_LINE}")

    print('\n'.join(output_lines))

def main():
    print("Initializing Monitor...")
    
    # Register resize handler
    signal.signal(signal.SIGWINCH, handle_resize)
    
    # Initial clear
    print(ANSI_CLEAR_SCREEN, end='')

    while True:
        try:
            # Always move to Home (Top-Left) before drawing
            print(ANSI_HOME, end='')
            
            pid, token = get_process_info()
            
            if not pid:
                print(f"{ANSI_YELLOW}●{ANSI_RESET} Waiting for Antigravity process...{ANSI_CLEAR_LINE}")
                print(f"  Scanning process list...{ANSI_CLEAR_LINE}")
                print(ANSI_CLEAR_EOS, end='') # Clear everything below
                
                time.sleep(REFRESH_INTERVAL)
                continue
                
            port = get_listening_port(pid)
            if not port:
                print(f"{ANSI_YELLOW}●{ANSI_RESET} Process detected (PID {pid}), waiting for port...{ANSI_CLEAR_LINE}")
                print(f"  Service initializing...{ANSI_CLEAR_LINE}")
                print(ANSI_CLEAR_EOS, end='')
                
                time.sleep(REFRESH_INTERVAL)
                continue
                
            data = fetch_status(port, token)
            
            if data:
                print_dashboard(data, pid, port)
                print(ANSI_CLEAR_EOS, end='') # Clear any leftovers
            else:
                print(f"{ANSI_RED}●{ANSI_RESET} Connected to PID {pid} but API is unresponsive.{ANSI_CLEAR_LINE}")
                print(f"  Retrying request...{ANSI_CLEAR_LINE}")
                print(ANSI_CLEAR_EOS, end='')
            
            sys.stdout.flush()
            time.sleep(REFRESH_INTERVAL)
            
        except ResizeInterrupt:
            # On resize, immediately continue loop which re-prints
            # Screen clearing is handled by ANSI_HOME + ANSI_CLEAR_EOS logic
            continue
            
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{ANSI_RESET}Monitor stopped.")
        sys.exit(0)