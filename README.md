# AiClickHelper

## Overview

AiClickHelper is a Windows-only PyQt5 desktop assistant for guided GUI interaction. It captures the current desktop, sends the screenshot and recent session context to the OpenAI Responses API, receives one recommended next action, and presents that action in two ways:

- a compact always-on-top chat window
- a transparent click-through overlay that marks the target on screen

The application is advisory-first. It does not automatically click or type in its current form. The operator remains responsible for performing the action, while the app manages session state, visual guidance, and the turn-by-turn loop.

## Key Features

- Full virtual desktop capture across monitors
- One-step-at-a-time action recommendations from the OpenAI Responses API
- Always-on-top chat-style interface for prompts, status, and current guidance
- Transparent overlay marker for target location
- Automatic continuation when the user appears to have completed the current step
- Local persistence of session history, captures, actions, and errors
- JSONL event logging for debugging and replay
- Debug screenshot output with annotated target markers

## How It Works

At a high level, the app runs a controlled loop:

1. The user enters a task prompt.
2. The main window hides itself so it does not appear in the capture.
3. The app captures the current desktop and saves the screenshot locally.
4. A worker thread sends the screenshot and recent session context to OpenAI.
5. The response is normalized into a strict internal `GuidedAction`.
6. Screenshot-space coordinates are mapped to real Windows desktop coordinates.
7. The UI shows the action text and the overlay marks the target on screen.
8. The app waits for the operator to review or perform the step, then continues.

### Architecture

The project is split into focused layers instead of one large GUI file:

- `app.py`
  Startup and object wiring. Loads `.env`, enables DPI awareness, creates the Qt application, and connects the main components.
- `controller.py`
  The orchestration layer. Manages sessions, captures, OpenAI requests, response handling, coordinate mapping, persistence, and UI events.
- `ui/main_window.py`
  The always-on-top desktop window that displays chat history, current action details, and input controls.
- `overlay.py`
  The transparent on-screen overlay that renders the target marker.
- `openai_adapter.py`
  The only module that talks directly to the OpenAI API.
- `response_normalizer.py`
  Converts model output into a strict internal action shape and falls back safely when the response is malformed.
- `capture_service.py`
  Handles full-desktop screenshots, data URL encoding, and optional annotated debug images.
- `coordinate_mapper.py`
  Maps screenshot coordinates to actual Windows virtual desktop coordinates.
- `session_store.py` and `event_logger.py`
  Persist session data and append JSONL event logs.
- `auto_advance.py` and `cursor_watcher.py`
  Detect when the operator has likely completed a step and keep the loop moving.

### Threading Model

OpenAI requests run on a `QThread` worker so the main UI remains responsive during network calls.

## Requirements

- Windows
- Python
- An OpenAI API key

### Python Dependencies

```text
PyQt5>=5.15,<6
openai>=1.75.0
mss>=10.0.0
Pillow>=10.4.0
```

## Installation

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Alternatively, use the convenience script:

```powershell
.\run.ps1
```

The script creates a virtual environment if needed, installs dependencies, loads `.env`, and starts the application.

## Configuration

Set `OPENAI_API_KEY` before running the app. You can use either a process environment variable or a local `.env` file.

### Example `.env`

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.4
```

### Supported Configuration

- `OPENAI_API_KEY`
  Required. Used to authenticate with OpenAI.
- `OPENAI_MODEL`
  Optional. Defaults to `gpt-5.4`.

### Local Data Storage

Session data is stored locally under:

```text
%LOCALAPPDATA%\AiClickHelper
```

If `LOCALAPPDATA` is unavailable, the app falls back to:

```text
.aiclickhelper-data
```

Each session stores:

- `session.json`
- `events.jsonl`
- screenshots
- optional annotated debug images

## Usage

Run the application:

```powershell
python main.py
```

Typical workflow:

1. Launch the app.
2. Enter a prompt describing the task you want to complete in the target application.
3. Review the recommended next action in the chat window.
4. Use the overlay marker to locate the target on screen.
5. Perform the action yourself.
6. Let auto-advance continue when appropriate, or press `Next` manually.

## Project Structure

```text
.
├── main.py
├── run.ps1
├── requirements.txt
├── computer_use.md
├── docs/
├── tests/
└── aiclickhelper/
    ├── app.py
    ├── auto_advance.py
    ├── capture_service.py
    ├── config.py
    ├── controller.py
    ├── coordinate_mapper.py
    ├── cursor_watcher.py
    ├── dpi.py
    ├── event_logger.py
    ├── models.py
    ├── openai_adapter.py
    ├── optional_executor.py
    ├── overlay.py
    ├── response_normalizer.py
    ├── session_store.py
    └── ui/
        └── main_window.py
```

## Current Limitations

- Windows-only
- Advisory-first workflow only
- No automatic click or type execution in the current MVP
- Single active session model
- Depends on the OpenAI Responses API and a valid API key

## Future Improvements

The codebase already includes an `OptionalExecutor` seam reserved for future click/type execution support, but that path is intentionally disabled in the current MVP.

## Additional Notes

- The OpenAI integration is isolated behind `OpenAIAdapter`, which keeps API request and response details separate from the UI and controller code.
- The app hides its own window before capture to reduce the chance of the model reasoning about the assistant UI instead of the target application.
- The repository includes documentation and tests for the main persistence, normalization, and coordinate mapping logic.
