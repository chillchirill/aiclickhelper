# Runtime Flow

This document explains what happens during one interaction cycle.

## 1. Startup

Startup begins in [main.py](/d:/aiclickhelper/main.py), which simply calls the package entrypoint in [app.py](/d:/aiclickhelper/aiclickhelper/app.py).

Then the app does this:

1. loads `.env`
2. enables Windows DPI awareness
3. creates the Qt app
4. builds the main controller and helper services
5. shows the always-on-top chat window

## 2. User Sends a Prompt

When the user presses `Send` in [ui/main_window.py](/d:/aiclickhelper/aiclickhelper/ui/main_window.py):

1. the prompt text is read from the input box
2. the input box is cleared
3. `SessionController.submit_user_prompt()` is called

Inside the controller:

1. the message is added to session history
2. an event is written
3. the session is saved
4. the turn execution starts

## 3. Before Taking a Screenshot

The controller emits `capturePreparationStarted`.

The main window listens to that signal and temporarily hides itself.

This matters because otherwise the assistant window would appear in the screenshot and the model might start interacting with the wrong thing.

At the same time, the overlay marker is cleared.

## 4. Screenshot Capture

The controller calls [capture_service.py](/d:/aiclickhelper/aiclickhelper/capture_service.py).

That service:

1. uses `mss`
2. grabs the full virtual desktop
3. saves the PNG locally
4. records monitor metadata
5. optionally writes a debug image with the target marker on it

The resulting metadata object is `CaptureMetadata`.

## 5. API Request

The screenshot is read from disk and encoded as a Base64 data URL.

Then the controller creates a `TurnWorker`, puts it into a `QThread`, and starts it.

`TurnWorker` calls [openai_adapter.py](/d:/aiclickhelper/aiclickhelper/openai_adapter.py).

The adapter:

1. builds the prompt/instruction payload
2. includes the current screenshot as an `input_image`
3. reuses `previous_response_id` if there is one
4. sends the request to `client.responses.create(...)`

## 6. Response Normalization

When the worker finishes, the controller receives:

- `response_id`
- assistant text

That text is passed into [response_normalizer.py](/d:/aiclickhelper/aiclickhelper/response_normalizer.py).

The normalizer tries to turn the model output into a strict internal `GuidedAction`.

If the model output is malformed:

- the app falls back to a safe blocked action
- the session does not silently continue with garbage coordinates

## 7. Coordinate Mapping

The model thinks in screenshot coordinates.

The operating system needs desktop coordinates.

[coordinate_mapper.py](/d:/aiclickhelper/aiclickhelper/coordinate_mapper.py) translates from:

- request image pixel space

to:

- real Windows virtual desktop pixel space

This is why the app can draw the target ring in the correct place.

## 8. Overlay Rendering

Once the action is mapped:

1. the controller emits `actionChanged`
2. the UI updates the textual action panel
3. the overlay window receives the target point
4. the glowing marker is drawn on the desktop

The overlay window is:

- transparent
- always on top
- click-through
- non-focus-stealing

So it acts like visual guidance rather than a real UI surface.

## 9. Auto-Advance

[auto_advance.py](/d:/aiclickhelper/aiclickhelper/auto_advance.py) automates the “ready for next recommendation” part.

Its flow is:

1. wait until the cursor approaches the target
2. hide the ring when the target is reached
3. arm the action
4. wait for confirmation:
   - mouse click for click-like actions
   - Enter for text-entry actions
5. compare a small low-cost screenshot signature
6. when the screen changes, or when timeout is hit, call `continue_after_next()`

So the app still does not click automatically, but it does keep the loop moving when the human likely completed the step.

## 10. Session Continuity

The app keeps a single session object.

That session holds:

- current state
- previous response id
- step counter
- history
- captures
- actions

Because `previous_response_id` is reused, the model conversation stays continuous across turns.

## 11. Error Handling

If something fails:

- capture failure
- API failure
- parse failure

the controller moves the session to an error or blocked state, saves that state, and emits an error signal to the UI.

This keeps failures visible and debuggable instead of silently swallowing them.
