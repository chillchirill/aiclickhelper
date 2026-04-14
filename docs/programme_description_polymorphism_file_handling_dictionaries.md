# AiClickHelper: How the Project Actually Uses Polymorphism, File Handling, and Dictionaries

## 1. Introduction and Project Context

AiClickHelper is a Windows PyQt5 desktop tool built around a simple loop: the user describes a task, the app captures the desktop, sends the screenshot and session context to OpenAI, receives one recommended next step, and shows it as text plus an on-screen marker. The system is advisory rather than autonomous.

That design is close to the computer-use workflow described in the OpenAI guide, where a model inspects the current screen, returns actions, and continues from the updated UI state. The same guide recommends keeping a human in the loop for higher-risk actions, and this project follows that principle because it never performs the final click or typing automatically; it only advises and highlights the target (OpenAI, 2026).

The architecture is clearly separated. `main.py` launches the program. `aiclickhelper/app.py` wires the objects together. `SessionController` in `aiclickhelper/controller.py` controls the flow. `MainWindow` presents the conversation, `OverlayWindow` draws the marker, `CaptureService` handles screenshots, `OpenAIAdapter` sends the request, `ResponseNormalizer` converts the reply into a safe internal action, and `SessionStore` persists the session.

## 2. Specific Cases Inside This App

### Polymorphism as Part of the App Structure

In this project, polymorphism is most visible in the Qt-based class structure. Several classes inherit from Qt base classes and then provide their own behavior while still fitting into the same framework.

The first example is `MainWindow(QMainWindow)` in `aiclickhelper/ui/main_window.py`. Qt treats it as a standard main window, but this subclass adds project-specific behavior: prompt sending, status updates, chat rendering, and the `Next` workflow.

`OverlayWindow(QWidget)` in `aiclickhelper/overlay.py` is a stronger example. It overrides `paintEvent()`, and that is where the app draws the pulsing ring and label over the target point. Qt still sees it as a widget, but during repainting the framework calls the subclass implementation.

Another case is the group of `QObject`-based classes: `SessionController`, `TurnWorker`, `CursorProximityWatcher`, and `AutoAdvanceController`. They share the same Qt base type, so they can all use signals, timers, and thread-aware behavior, but each has a different role. `TurnWorker` handles background API work, `CursorProximityWatcher` checks whether the mouse is near the target, and `AutoAdvanceController` watches for a click, Enter press, or screen change before continuing.

There is also a smaller case in `aiclickhelper/models.py`: enums such as `ActionType`, `Speaker`, and `SessionState` inherit from both `str` and `Enum`. This lets the app treat them as controlled internal values while also storing them directly as strings in JSON and logs.

### File Handling as Part of the Runtime, Not Just Storage

File handling is central to this app because the project is designed to preserve a trace of each run.

The first file-related step appears in `aiclickhelper/app.py`, where `load_dotenv()` reads `.env` and places values into the environment. This is how the application loads the OpenAI key without hard-coding it.

The most important file-handling code lives in `aiclickhelper/session_store.py`. Each session gets its own directory, and `save_session()` writes `session.json` with the current history, actions, captures, summary, and error state.

The project also writes logs in a practical format. `EventLogger.append()` in `aiclickhelper/event_logger.py` stores events in `events.jsonl`, one JSON object per line. The controller records session creation, prompt submission, screenshot capture, guided action creation, and error handling. This produces a replayable timeline of the session.

Screenshot files are another important case. In `SessionController._capture_current_screen()`, each step is saved into a file such as `step-001.png`. If debug images are enabled, the app also writes an annotated copy showing where the mapped target ended up.

Files are not only written for storage. `CaptureService.encode_image_data_url()` reads the saved PNG back from disk and converts it into a data URL for the OpenAI request.

### Dictionaries as the Glue Between Layers

Dictionaries are the main transport format inside the system.

The clearest example is in `aiclickhelper/openai_adapter.py`. `_build_request()` creates the request as a nested dictionary containing the model, instructions, recent context, screenshot input, and optional previous response ID. This is the bridge between the project’s Python objects and the external API format.

The reverse step happens in `aiclickhelper/response_normalizer.py`. The assistant reply is parsed into a dictionary called `payload`, and the code reads keys such as `"action_type"`, `"target_point"`, `"confidence"`, and `"user_instruction"` before creating a `GuidedAction`. If the dictionary is incomplete or invalid, the app falls back to a blocked action.

Dictionaries are also used for event details. When `SessionController` records `user_prompt_submitted`, `screenshot_captured`, or `guided_action_ready`, it passes small detail dictionaries into the logger. This keeps the logging format consistent across the whole app.

Finally, `SessionStore._to_json_safe()` turns dataclasses, enums, and lists into something `json.dump()` can write. The UI also uses a small dictionary in `MainWindow` to map `Speaker.USER`, `Speaker.ASSISTANT`, and `Speaker.SYSTEM` to readable chat labels.

## 3. Summary and Conclusion

What stands out in AiClickHelper is that these features are not present as isolated programming concepts. They are part of the runtime design. Polymorphism makes the Qt-based architecture modular. File handling gives the app memory, screenshots, and logs. Dictionaries let information move cleanly between OpenAI, the controller, the logger, and the UI.

Because of that, the project feels like a real desktop system rather than a demo script. It has a controlled flow, traceable runtime data, and clear separation between components. The strongest design choice is the human-in-the-loop approach: the app uses a computer-use style loop, but it keeps the final action with the operator, which makes the system easier to trust and debug.

## Reference

OpenAI (2026) *Computer use*. Available at: https://developers.openai.com/api/docs/guides/tools-computer-use (Accessed: 14 April 2026).
