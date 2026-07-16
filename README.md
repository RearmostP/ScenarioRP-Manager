# ScenarioRP Manager

Local PySide6 manager for the ScenarioRP development server.

## Setup

```powershell
cd ScenarioRP-Manager
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

From the project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\manager.ps1
```

## Configuration

Edit `config.json` when a relative path changes. Relative paths are resolved from the ScenarioRP project root, so the project can move between drive letters.

## MVP Limits

The current MVP is a PySide6 frontend that runs PowerShell scripts from `scripts/` and displays their output.

Server operations live in standalone PowerShell scripts. Each script can be run manually from PowerShell.

## Script Backend

The GUI calls only high-level scripts:

- `start-all.ps1`
- `stop-all.ps1`
- `restart-all.ps1`
- `safe-shutdown.ps1`
- `status.ps1`
- `open-txadmin.ps1`

Single-purpose scripts are also executable directly:

- `start-server.ps1`
- `stop-server.ps1`
- `restart-server.ps1`
- `start-discord-bot.ps1`
- `stop-discord-bot.ps1`
- `restart-discord-bot.ps1`
- `announce-discord-offline.ps1`

## UI Editing

The main window layout lives in `ui/main_window.ui` and can be edited with Qt Designer. Keep the existing object names when changing widgets, because `ui/main_window.py` connects logic by those names.
