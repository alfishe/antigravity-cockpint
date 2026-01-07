# 🚀 Antigravity Cockpit Monitor

> **Real-time telemetry and quota tracking for your local Antigravity AI engine.**

![Python](https://img.shields.io/badge/Python-3.6%2B-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Antigravity Cockpit** is a sleek, terminal-based dashboard that hooks into the running `antigravity` language server process to visualize your current usage, remaining credits, and plan status. No more guessing when your quotas will reset.

---

## ✨ Features

- **🔍 Auto-Discovery**: Automatically finds the running Antigravity process, PID, and secure tokens.
- **📊 Live Dashboard**: Updates in real-time (1s interval) to show the latest stats.
- **💳 Credit Tracking**: Visual progress bars for:
  - Monthly Prompt Quotas
  - Flow Credits
- **🤖 Model-Specific Metrics**: Detailed usage breakdown for individual models (e.g., GPT-4, Claude 3.5 Sonnet) including:
  - Usage percentage
  - Time until quota reset
- **🎨 Beautiful TUI**: Clean, ANSI-colored terminal interface.

## 📸 Preview

```text
🚀 Antigravity Cockpit Monitor
PID: 55083 | Port: 55052 | Time: 14:32:01
------------------------------------------------------------
User:  Dev User (dev@example.com)
Plan:  Pro (Tier 1)
Monthly Prompt Quota: 🟢████████░░░░░░░░░░░░ 2,400 / 5,000 (48.0%)
------------------------------------------------------------
Model Name                          Usage                  Reset In
------------------------------------------------------------
claude-3.5-sonnet                   🟢███░░░░░░░░░░░░░░░░░  15.2%  4h 12m
gpt-4-turbo                         🟡██████████░░░░░░░░░░  52.1%  12h 05m
basic-model                         🟢█░░░░░░░░░░░░░░░░░░░   5.0%  N/A
```

## 🛠️ Prerequisites

- **Python 3.6+**
- **macOS** or **Linux** (Requires `ps` and `lsof` command-line tools)
- An active instance of the Antigravity language server running locally.

## 🚀 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/antigravity-cockpit.git
   cd antigravity-cockpit
   ```

2. **Make the script executable:**
   ```bash
   chmod +x monitor_antigravity.py
   ```

3. **Run the monitor:**
   ```bash
   ./monitor_antigravity.py
   # OR
   python3 monitor_antigravity.py
   ```

   *No external dependencies (`pip install`) are required! The script uses only the standard library.*

## ⚙️ How It Works

The script operates by inspecting your system's process list to identify the `antigravity` language server. It securely extracts the necessary **CSRF tokens** and **listening ports** from the process arguments and established TCP connections. It then polls the local gRPC/HTTP endpoint to fetch the latest `GetUserStatus` telemetry directly from the source.

## 🛑 Troubleshooting

- **"Waiting for Antigravity process..."**: Ensure your IDE or the Antigravity service is actually running. The monitor scans for a process named `antigravity` with a `language_server` argument.
- **Permission Denied**: In some setups, you might need elevated privileges to see other processes' arguments. Try running with `sudo` if discovery fails, though typically not required for user-owned processes.

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).

---
*Note: This is an unofficial tool and is not affiliated with the developers of the Antigravity engine.*