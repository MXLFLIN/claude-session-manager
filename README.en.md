# Claude Session Manager (claude-session-manager)

A small Windows tool for managing **Claude Code session history** with a list and search.

Claude Code stores every session locally as `~/.claude/projects/<project>/<session-id>.jsonl`,
where the file name is a UUID. This tool lists those sessions, makes them searchable,
and lets you move them out of the way.

[中文说明](README.md)

## Features

- Lists all sessions with time, title, project, message count and file size
- Titles come from Claude's own generated title (`ai-title`); if none exists, the first user message is used
- Search filters as you type (title, first message, project path, date)
- Click a column header to sort; click again to reverse
- Refreshes silently every 30 seconds and keeps the current selection
- "Open Recycle Bin" switches the list to recycled sessions; selected ones can be restored
- "Open session" launches a new console in the original project directory and runs `claude --resume <id>`
- "Move to Recycle Bin" moves the `.jsonl` into `projects/_claude_session_recycle/`; nothing is deleted
- Right-click any row: open session / move to recycle bin / show in folder / details
- In the recycle view, the context menu adds a red "Delete permanently" item (confirmation required)
- Before moving, sessions written to within the last 60 seconds are flagged as possibly in use
- Double-click a row for details (title, first message, path, session ID)
- UI available in Chinese and English; switch at runtime in Settings
- Settings window also has a button that opens `~/.claude/CLAUDE.md`

## Usage

Double-click **`ClaudeSessionManager.exe`** (no console window).

Alternatively, double-click `sessions_gui.pyw` (requires Python 3, no third-party packages).

The exe is a small launcher compiled from `launcher.c` (about 65 KB). It starts
`pythonw.exe` on the `.pyw` file in the same directory, so the exe and the pyw
must stay in the same folder, and Python must be installed.

Command line:

```bash
pythonw sessions_gui.pyw
```

## Notes

- Reads local Claude Code data only. No network access, nothing is uploaded.
- "Recycle Bin" means the files are moved into `projects/_claude_session_recycle/`.
  Restoring moves them back into `projects/<project>/`.
- The app does not open the sessions themselves; it starts the `claude` CLI.
- Moving a session that is currently in use can cause file conflicts. Prefer closing it first.

## How it works

Each `.jsonl` file contains one JSON record per line. The tool does three things:

1. Finds the first real user message and uses it as the title when no `ai-title` exists.
2. Counts `user` and `assistant` records.
3. Moves files between the project folder and the recycle folder; Claude Code's
   `--resume` list only shows files in the project folders.

## License

MIT
