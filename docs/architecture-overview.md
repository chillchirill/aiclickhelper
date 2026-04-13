# Architecture Overview

This document explains how the application is structured and which part is responsible for what.

## 1. High-Level Picture

The program is a Windows desktop helper that:

1. shows a small always-on-top chat window
2. captures the screen
3. sends the screenshot and context to OpenAI
4. receives one recommended next action
5. draws a target overlay on the screen
6. waits for the operator to act
7. automatically continues when the action appears to be completed

Architecturally, this is not “one giant GUI file”. It is split into layers.

## 2. Main Layers

### App Wiring

File: [app.py](/d:/aiclickhelper/aiclickhelper/app.py)

This is the composition root.

It:

- loads environment variables from `.env`
- enables Windows DPI awareness
- creates the Qt application
- creates the controller
- creates the overlay
- creates the proximity watcher
- creates the auto-advance controller
- connects signals between them
- opens the main window

In other words: this file assembles the object graph.

### UI Layer

File: [ui/main_window.py](/d:/aiclickhelper/aiclickhelper/ui/main_window.py)

This is the visible desktop window.

It is intentionally small and always on top.

It is responsible for:

- showing chat history
- showing the latest recommended action in text form
- accepting a new prompt
- allowing manual `Next`
- temporarily hiding itself before screenshot capture

This file does not own the session logic. It delegates real work to the controller.

### Controller / Orchestration Layer

File: [controller.py](/d:/aiclickhelper/aiclickhelper/controller.py)

This is the heart of the app.

It coordinates:

- session creation/reset
- prompt submission
- screenshot capture
- OpenAI request execution
- response normalization
- coordinate mapping
- session persistence
- event emission for the UI

If you want to know “what happens when the user clicks Send?”, this is the main file to read.

### Data Model Layer

File: [models.py](/d:/aiclickhelper/aiclickhelper/models.py)

This contains the shapes of the main objects:

- session state
- chat message
- recommended action
- capture metadata
- events
- enums for action types and UI states

This file is useful because it gives you the vocabulary of the whole project.

### OpenAI Integration Layer

File: [openai_adapter.py](/d:/aiclickhelper/aiclickhelper/openai_adapter.py)

This file hides the API details from the rest of the app.

It is responsible for:

- reading the API key
- building the request payload
- passing screenshot + context to the Responses API
- extracting assistant text from the response

The rest of the app does not need to know the exact wire shape of the API call.

### Screenshot / OS Interaction Layer

Files:

- [capture_service.py](/d:/aiclickhelper/aiclickhelper/capture_service.py)
- [overlay.py](/d:/aiclickhelper/aiclickhelper/overlay.py)
- [auto_advance.py](/d:/aiclickhelper/aiclickhelper/auto_advance.py)
- [cursor_watcher.py](/d:/aiclickhelper/aiclickhelper/cursor_watcher.py)
- [dpi.py](/d:/aiclickhelper/aiclickhelper/dpi.py)

These files interact with the operating system or low-level Qt behavior.

They handle:

- taking full-desktop screenshots
- drawing the overlay ring
- polling cursor position
- detecting click / Enter / screen change for auto-next
- enabling per-monitor DPI awareness on Windows

## 3. Why the App Uses a Controller

Without a controller, the UI would have to know:

- how to capture images
- how to talk to OpenAI
- how to save sessions
- how to parse model output
- how to update the overlay

That would quickly become unmaintainable.

So the design uses this rule:

- UI displays and forwards user intent
- controller owns workflow
- services do isolated pieces of work

This is similar to MVC/MVVM/controller-heavy desktop architectures in other languages.

## 4. Threading Model

The OpenAI request is made on a worker thread, not the UI thread.

Why:

- network calls can block
- blocking the main Qt thread would freeze the window

So the workflow is:

1. UI asks controller to submit prompt
2. controller captures screenshot on main flow
3. controller creates `TurnWorker`
4. worker moves to `QThread`
5. worker makes the API call
6. worker emits a signal back with the result
7. controller updates state and UI

This is standard desktop app hygiene.

## 5. Persistence Model

The app stores session data locally through [session_store.py](/d:/aiclickhelper/aiclickhelper/session_store.py).

A session records:

- message history
- captures
- actions
- current state
- errors

Events are also appended to `events.jsonl`, which is useful for debugging and replaying what happened.

## 6. Safety Model

The app is advisory-first.

That means:

- the model suggests what to do
- the overlay shows where
- the human operator still performs the real action

Even with auto-advance, the app is still not automatically clicking for the user. It only decides when to request the next recommendation.

## 7. Most Important Design Tradeoff

This app prefers:

- simple flow
- clear state ownership
- human-in-the-loop behavior

over:

- maximum automation
- deep framework abstractions
- hidden “magic”

That makes it easier to inspect, debug, and extend.
