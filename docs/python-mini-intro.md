# Python Mini Introduction for This Project

This document is written for someone who already understands programming concepts, but does not yet feel comfortable reading Python code.

The goal is not to teach all Python. The goal is to make this codebase readable.

## 1. The Big Mental Shift

If you come from languages like C#, Java, TypeScript, Kotlin, Go, or C++, most ideas here are familiar:

- modules instead of namespaces/packages in the same style
- classes and objects
- enums
- data models
- callbacks/events
- background worker threads

The main differences are:

- Python syntax is much smaller and more permissive
- indentation is part of the syntax
- types are mostly hints, not strict runtime rules
- many “small classes” here are `@dataclass` models rather than hand-written OOP objects

## 2. Imports

Example:

```python
from pathlib import Path
from typing import Optional
```

This is similar to importing types or modules in other languages.

- `pathlib.Path` is Python’s nicer path abstraction
- `Optional[T]` means “this may be `T` or `None`”

## 3. Indentation Instead of Braces

Python uses indentation where many languages use `{}`:

```python
if value:
    do_something()
else:
    do_other_thing()
```

So indentation is not style only. It is syntax.

## 4. Functions

Example:

```python
def load_dotenv(path: str = ".env") -> None:
    ...
```

How to read this:

- `def` declares a function
- `path: str` means `path` is expected to be a string
- `= ".env"` gives a default value
- `-> None` means the function does not return a useful value

Type hints make the code easier to understand, but Python usually does not enforce them at runtime.

## 5. Classes and Objects

Example:

```python
class OpenAIAdapter:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
```

Read this like a normal class:

- `class OpenAIAdapter:` declares the class
- `__init__` is the constructor
- `self` is the current object instance, similar to `this`
- `self._config` is an instance field

Python does not have strict private fields. By convention:

- `_name` means “internal, do not touch casually”
- `__name` would trigger name-mangling, but this project mostly uses single underscore

## 6. Methods

Inside a class:

```python
def request_guided_action(self, session: SessionData, new_prompt: str) -> tuple[str, str]:
    ...
```

That is just an instance method.

The first parameter is always `self` for instance methods.

## 7. `@dataclass`

This project uses `@dataclass` a lot.

Example from the codebase:

```python
@dataclass
class Point2D:
    x: float
    y: float
    coord_space: CoordinateSpace
```

Think of this as a compact “data-only class”.

Instead of writing:

- a constructor
- field assignments
- useful repr/debug output
- equality helpers

Python generates most of that for you.

This is similar in spirit to:

- C# records / DTOs
- Kotlin data classes
- TypeScript interfaces plus class-like runtime objects

In this project, `@dataclass` is mostly used for:

- session state
- action models
- capture metadata
- event payloads

## 8. `field(default_factory=...)`

Example:

```python
created_at: str = field(default_factory=utc_now_iso)
```

This means:

- when a new object is created
- call `utc_now_iso()`
- use the result as the default value

This is important for mutable values or computed defaults.

## 9. Enums

Example:

```python
class SessionState(str, Enum):
    IDLE = "idle"
    CAPTURING = "capturing"
```

This gives a fixed set of allowed values.

Why `str, Enum` instead of only `Enum`?

Because the enum values also behave nicely as strings when saved, displayed, or serialized.

This is very useful for:

- JSON persistence
- logging
- UI labels

## 10. `classmethod`

Example:

```python
@classmethod
def create(cls, speaker: Speaker, text: str) -> "ChatMessage":
    return cls(...)
```

This is a factory method attached to the class, not a specific instance.

Use it when you want:

- cleaner construction
- generated IDs
- generated timestamps
- default setup

This is similar to static factory methods in other languages.

## 11. `property`

Example:

```python
@property
def latest_capture_path(self) -> Optional[str]:
    ...
```

This lets you access a method like a field:

```python
controller.latest_capture_path
```

instead of:

```python
controller.latest_capture_path()
```

It is useful for read-only computed values.

## 12. Signals and Events in PyQt

PyQt uses signals and slots instead of plain callbacks in many places.

Example:

```python
chatUpdated = pyqtSignal()
statusChanged = pyqtSignal(str)
```

This means the object can emit events:

- `chatUpdated` with no payload
- `statusChanged` with one string payload

Then another object connects to them:

```python
controller.chatUpdated.connect(self._refresh_chat)
```

This is conceptually similar to:

- C# events
- Qt/C++ signals and slots
- observer pattern

## 13. Background Work with `QThread`

The app does not call the OpenAI API directly on the UI thread.

Instead it creates a worker object and moves it to a `QThread`.

Why?

Because if a slow network request runs on the UI thread, the window freezes.

So the design is:

- UI thread handles widgets and user interaction
- worker thread handles blocking API call
- worker emits a signal when finished
- UI thread receives the result and updates the screen

This is the same general idea as background workers in most GUI frameworks.

## 14. `Optional[T]` and `None`

Python uses `None` as the “no value” marker.

So:

```python
Optional[GuidedAction]
```

means:

- either a `GuidedAction`
- or `None`

Equivalent conceptually to nullable references.

## 15. String Interpolation

Python uses f-strings:

```python
f"Action: {action.action_type.value}"
```

This is similar to:

- JavaScript template strings
- C# string interpolation

## 16. Why There Are So Many Small Files

This codebase splits responsibility by concern:

- config
- models
- controller
- OpenAI adapter
- capture service
- overlay
- UI

That is intentional.

It keeps each file easier to reason about, especially in a GUI app where state, rendering, system APIs, and network logic can get tangled very fast.

## 17. Reading Strategy for This Project

If Python syntax still feels unfamiliar, read the code in this order:

1. `models.py`
   Data shapes and enums.
2. `app.py`
   Application wiring.
3. `controller.py`
   Main workflow.
4. `ui/main_window.py`
   What the user sees.
5. `openai_adapter.py`
   API call shape.
6. `capture_service.py`, `overlay.py`, `auto_advance.py`
   OS and UI interaction helpers.

## 18. Most Important Takeaway

Do not try to read Python as “mysterious scripting”.

For this project, it is best read as:

- data models
- services
- controller/orchestrator
- GUI layer
- event-driven flow

The syntax is smaller than in many languages, but the architecture is not unusual.
