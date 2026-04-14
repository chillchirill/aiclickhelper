# AiClickHelper: Use of Polymorphism, File Handling, and Dictionaries

## 1. Introduction

AiClickHelper is a Windows PyQt5 desktop assistant. The user enters a task, the app captures the desktop, sends the screenshot and session context to OpenAI, receives one recommended action, and shows it in the main window and overlay. The system is advisory: the user performs the action, while the app stores the session and prepares the next step.

The project has a clear structure. `main.py` starts the app, `app.py` connects the main objects, `SessionController` controls the workflow, `MainWindow` displays the conversation, `OverlayWindow` marks the target, and the service classes handle screenshots, API requests, response parsing, and persistence.

## 2. Specific Cases in This Project

### Polymorphism

Polymorphism appears mainly through Qt inheritance.

`MainWindow(QMainWindow)` extends the standard Qt window with chat history, status display, prompt input, and the `Next` action flow.

`OverlayWindow(QWidget)` is the clearest example because it overrides `paintEvent()`. Qt still treats it as a widget, but the subclass provides custom drawing logic for the target ring, crosshair, and label.

Several runtime classes also inherit from `QObject`: `SessionController`, `TurnWorker`, `CursorProximityWatcher`, and `AutoAdvanceController`. Because they share the same Qt base type, they can all use signals, timers, and thread integration, while each class keeps a separate responsibility.

There is a smaller case in `models.py`, where `ActionType`, `Speaker`, and `SessionState` inherit from both `str` and `Enum`. This lets the same values work in program logic and in JSON output.

### File Handling

File handling is essential because the app keeps a full record of each session.

`load_dotenv()` reads `.env` and loads environment variables such as the API key.

`SessionStore.save_session()` writes `session.json`, which stores the current history, actions, captures, summary, and error state.

`EventLogger.append()` writes events to `events.json`, one JSON object per line. These logs record prompt submission, screenshot capture, guided action creation, and errors.

`SessionController._capture_current_screen()` saves screenshots such as `step-001.png`. When debug output is enabled, the app also writes annotated copies showing the mapped target.

`CaptureService.encode_image_data_url()` reads the saved screenshot back from disk and converts it into a data URL for the OpenAI request. File handling is therefore part of both storage and execution.

### Dictionaries

Dictionaries are used to move structured data through the program.

In `openai_adapter.py`, `_build_request()` creates the API request as a nested dictionary containing the model, instructions, recent context, image input, and previous response ID.

In `response_normalizer.py`, the assistant output is parsed into a dictionary called `payload`. The code then reads fields such as `"action_type"`, `"target_point"`, `"confidence"`, and `"user_instruction"` to build a `GuidedAction`. If the data is invalid, the app falls back to a blocked action.

The controller also logs event details as dictionaries, for example prompt text, screenshot metadata, and action metadata.

Finally, `_to_json_safe()` converts dataclasses, enums, lists, and dictionaries into data that `json.dump()` can save. A smaller example appears in the UI, where a dictionary maps speaker values to chat labels.

## 3. Summary

In AIClickHelper, these techniques support the real workflow rather than existing as isolated concepts. Polymorphism structures the Qt components, file handling preserves sessions and screenshots, and dictionaries carry structured data between the API, controller, storage, and UI.

This design is consistent with the human-in-the-loop approach described in OpenAI’s computer use documentation, where the model works from the current screen state but higher-risk actions remain under user control (OpenAI, 2026).

## Reference

OpenAI (2026) *Computer use*. Available at: https://developers.openai.com/api/docs/guides/tools-computer-use (Accessed: 14 April 2026).
