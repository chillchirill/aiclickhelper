# AiClickHelper

Windows-only PyQt5 operator assistant for guided GUI interaction.

## What It Does

- Captures the Windows desktop
- Sends the latest screenshot and session context to the OpenAI Responses API
- Receives one recommended next action at a time
- Shows the action in a chat-style interface
- Draws a transparent on-screen target overlay
- Waits for the operator to review or perform the step and press `Next`

## MVP Scope

- Manual operator workflow only
- Single active session
- Full virtual desktop capture
- Click-through overlay guidance
- Local session persistence in `%LOCALAPPDATA%\AiClickHelper`

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set the API key:

```powershell
$env:OPENAI_API_KEY="your_api_key"
```

## Run

```powershell
python main.py
```

## Notes

- The OpenAI integration is isolated behind `OpenAIAdapter` so the request/response shape can evolve with the local `computer_use.md` guidance without forcing a UI rewrite.
- The app is advisory-first. It does not automatically click or type in MVP.
