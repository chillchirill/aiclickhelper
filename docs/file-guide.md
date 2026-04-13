# File Guide

This is the practical “what should I open first?” guide.

## Root Files

### [main.py](/d:/aiclickhelper/main.py)

Tiny launcher. It imports the package entrypoint and starts the app.

### [run.ps1](/d:/aiclickhelper/run.ps1)

Convenience PowerShell script.

It:

- creates a virtual environment
- installs dependencies
- loads `.env`
- launches the app

### [requirements.txt](/d:/aiclickhelper/requirements.txt)

Python dependencies for the project.

## Core Package

### [aiclickhelper/config.py](/d:/aiclickhelper/aiclickhelper/config.py)

Configuration values.

This is where timeouts and basic app behavior defaults live.

### [aiclickhelper/models.py](/d:/aiclickhelper/aiclickhelper/models.py)

The shared data vocabulary of the app.

Start here if you want to know:

- what a session looks like
- what an action looks like
- what states exist

### [aiclickhelper/app.py](/d:/aiclickhelper/aiclickhelper/app.py)

Application wiring and startup.

### [aiclickhelper/controller.py](/d:/aiclickhelper/aiclickhelper/controller.py)

Main orchestrator.

This is the file to read if you want to understand the full loop.

### [aiclickhelper/openai_adapter.py](/d:/aiclickhelper/aiclickhelper/openai_adapter.py)

The only place that talks directly to OpenAI.

### [aiclickhelper/response_normalizer.py](/d:/aiclickhelper/aiclickhelper/response_normalizer.py)

Turns raw model text into a strongly-shaped internal action.

### [aiclickhelper/coordinate_mapper.py](/d:/aiclickhelper/aiclickhelper/coordinate_mapper.py)

Converts screenshot coordinates to real screen coordinates.

### [aiclickhelper/capture_service.py](/d:/aiclickhelper/aiclickhelper/capture_service.py)

Handles full-screen capture and debug image output.

### [aiclickhelper/session_store.py](/d:/aiclickhelper/aiclickhelper/session_store.py)

Saves sessions and event logs to disk.

### [aiclickhelper/event_logger.py](/d:/aiclickhelper/aiclickhelper/event_logger.py)

Appends JSON event records to the session log.

## UI and Desktop Interaction

### [aiclickhelper/ui/main_window.py](/d:/aiclickhelper/aiclickhelper/ui/main_window.py)

The compact always-on-top chat window.

### [aiclickhelper/overlay.py](/d:/aiclickhelper/aiclickhelper/overlay.py)

Transparent desktop overlay that shows the glowing target marker.

### [aiclickhelper/cursor_watcher.py](/d:/aiclickhelper/aiclickhelper/cursor_watcher.py)

Polls cursor position and detects when the operator reaches the target.

### [aiclickhelper/auto_advance.py](/d:/aiclickhelper/aiclickhelper/auto_advance.py)

Decides when to automatically continue to the next model turn.

### [aiclickhelper/dpi.py](/d:/aiclickhelper/aiclickhelper/dpi.py)

Enables Windows DPI awareness before Qt is initialized.

This is important for correct coordinate mapping on scaled displays.

## Files Reserved for Future Work

### [aiclickhelper/optional_executor.py](/d:/aiclickhelper/aiclickhelper/optional_executor.py)

Placeholder for future automation execution.

Right now the app is advisory-first, so this file is intentionally not active.

## Suggested Reading Path

If you want to understand the project quickly:

1. [models.py](/d:/aiclickhelper/aiclickhelper/models.py)
2. [app.py](/d:/aiclickhelper/aiclickhelper/app.py)
3. [controller.py](/d:/aiclickhelper/aiclickhelper/controller.py)
4. [ui/main_window.py](/d:/aiclickhelper/aiclickhelper/ui/main_window.py)
5. [openai_adapter.py](/d:/aiclickhelper/aiclickhelper/openai_adapter.py)
6. [capture_service.py](/d:/aiclickhelper/aiclickhelper/capture_service.py)
7. [overlay.py](/d:/aiclickhelper/aiclickhelper/overlay.py)
8. [auto_advance.py](/d:/aiclickhelper/aiclickhelper/auto_advance.py)
