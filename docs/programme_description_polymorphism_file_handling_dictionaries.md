# AiClickHelper: Specific Uses of Polymorphism, File Handling, and Dictionaries

## 1. Introduction and Structure of the Program

AiClickHelper is a Windows PyQt5 application that guides a human operator through another GUI. The runtime flow is: `main.py` starts the app, `aiclickhelper/app.py` wires the objects together, `SessionController` handles the turn logic, `CaptureService` takes the screenshot, `OpenAIAdapter` sends the request, `ResponseNormalizer` converts the reply into a local action object, `CoordinateMapper` maps model coordinates to screen coordinates, `MainWindow` shows the instruction, and `OverlayWindow` highlights the target on the desktop.

The program is split into clear layers rather than one large file. The UI layer is in `aiclickhelper/ui/main_window.py`, orchestration is in `aiclickhelper/controller.py`, persistence is in `aiclickhelper/session_store.py`, logging is in `aiclickhelper/event_logger.py`, and screen interaction is handled by `capture_service.py`, `overlay.py`, `cursor_watcher.py`, and `auto_advance.py`.

## 2. Specific Cases in This App

### Polymorphism

The most visible use of polymorphism is through Qt inheritance.

Case 1: `MainWindow(QMainWindow)` in `aiclickhelper/ui/main_window.py`. Qt treats this object as a standard main window, but the subclass adds AiClickHelper-specific behavior such as prompt submission, chat rendering, status updates, and the `Next` action flow.

Case 2: `OverlayWindow(QWidget)` in `aiclickhelper/overlay.py`. This is a stronger example because the subclass overrides `paintEvent()`. Qt calls that method polymorphically when the widget must repaint, and AiClickHelper uses that hook to draw the target ring, crosshair, and label. The overlay is still a widget, but it behaves differently from a default widget.

Case 3: `SessionController(QObject)`, `TurnWorker(QObject)`, `CursorProximityWatcher(QObject)`, and `AutoAdvanceController(QObject)`. These classes share the same Qt base type, which allows them all to use signals, timers, and thread integration, but each object has a different role. `TurnWorker` performs the API request on a worker thread, `SessionController` manages state transitions, `CursorProximityWatcher` emits proximity events, and `AutoAdvanceController` reacts to those events and decides when to continue automatically.

Case 4: enums in `aiclickhelper/models.py` inherit from both `str` and `Enum`. `ActionType`, `Speaker`, and `SessionState` act like controlled program states, but they also behave as strings when the app writes JSON or event logs. This is useful polymorphic behavior because one value works both as an enum in logic and as text in storage.

### File Handling

File handling is part of the core workflow, not just setup.

Case 1: configuration loading in `aiclickhelper/app.py`. `load_dotenv()` reads `.env`, splits each line, and places values into `os.environ`. This is how the app injects the API key without storing it directly in code.

Case 2: session persistence in `aiclickhelper/session_store.py`. `save_session()` creates a per-session directory and writes `session.json`. That file becomes the local source of truth for the current run: message history, captures, actions, current state, summary, and last error.

Case 3: event logging in `aiclickhelper/event_logger.py`. The `append()` method writes to `events.jsonl` in append mode, one JSON object per line. This is a concrete logging mechanism. The controller records `session_created`, `user_prompt_submitted`, `screenshot_captured`, `guided_action_ready`, and `error`, so the app keeps a replayable execution trail.

Case 4: screenshot storage in `aiclickhelper/controller.py` and `aiclickhelper/capture_service.py`. Every turn creates a file like `step-001.png` inside a session-specific screenshots folder. If debug output is enabled, the app also writes annotated images that show the mapped target visually. This is useful for debugging coordinate mistakes and checking whether the model pointed to the correct place.

Case 5: image re-use for API transport in `CaptureService.encode_image_data_url()`. The saved PNG file is read back from disk as bytes, base64-encoded, and sent to OpenAI as a data URL. So file handling is not only for storage; it is also part of the request pipeline.

### Dictionaries

Dictionaries are the main transport format between layers.

Case 1: OpenAI request construction in `aiclickhelper/openai_adapter.py`. `_build_request()` creates a nested dictionary with keys such as `"model"`, `"instructions"`, `"input"`, `"reasoning"`, and optionally `"previous_response_id"`. The same method also creates nested dictionaries inside the `input` list for the text and image items. This is the bridge between local Python objects and the external API.

Case 2: model response normalization in `aiclickhelper/response_normalizer.py`. The assistant output is parsed into a dictionary called `payload`, and the program extracts `"action_type"`, `"target_point"`, `"target_region"`, `"confidence"`, `"user_instruction"`, and other fields. The dictionary is then converted into a `GuidedAction`. If keys are missing or malformed, the code falls back to a blocked action.

Case 3: event details in `SessionController`. When the controller calls `append_event()`, it passes small dictionaries such as `{"prompt": prompt}` or `{"action_type": action.action_type.value, "confidence": action.confidence.value}`. This means dictionaries are the standard format for logging runtime facts.

Case 4: JSON-safe serialization in `aiclickhelper/session_store.py`. `_to_json_safe()` recursively walks through enums, dataclasses, lists, and dictionaries to produce a dictionary structure that `json.dump()` can write. Without that conversion step, the session object graph would not be serializable.

Case 5: UI label mapping in `aiclickhelper/ui/main_window.py`. A dictionary maps `Speaker.USER`, `Speaker.ASSISTANT`, and `Speaker.SYSTEM` to human-readable labels when the chat history is rendered. This is a small case, but it shows dictionary use even in the presentation layer.

## 3. Summary and Conclusion

In this app, polymorphism is mainly architectural: inherited Qt classes let different objects plug into the same framework while keeping specialized behavior. File handling supports the real runtime: loading configuration, saving sessions, writing logs, storing screenshots, and re-reading images for API submission. Dictionaries carry structured data across the whole system: API requests, parsed model replies, event payloads, and serialized session data.

The important point is that these are not abstract textbook features here. They directly support the app's turn-based workflow, debugging, and persistence. Polymorphism shapes how the app is built, file handling preserves what happened, and dictionaries move structured data between every major layer.
