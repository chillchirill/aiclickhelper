# AiClickHelper Programme Description and the Use of Polymorphism, File Handling, and Dictionaries

## 1. Introduction and Background Research

### Overview of the Program

AiClickHelper is a Windows desktop application written in Python with PyQt5. Its purpose is to support a human operator while completing tasks in another graphical user interface. The program captures the current desktop, sends the screenshot together with the current session context to the OpenAI Responses API, receives one recommended next action, and then presents that action in a small chat-style window and a transparent on-screen overlay. The operator remains in control at all times, so the software is advisory rather than fully autonomous.

From a structural perspective, the program is divided into clear layers. The application entry point in `aiclickhelper/app.py` creates the main objects and connects them together. The orchestration logic is handled by `SessionController` in `aiclickhelper/controller.py`. The persistent session data is managed by `SessionStore` in `aiclickhelper/session_store.py`. The visible user interface is implemented in `aiclickhelper/ui/main_window.py`, while `aiclickhelper/overlay.py` draws the visual marker on the desktop.

### Background Concepts

Polymorphism is an object-oriented programming concept in which different objects can be treated through a common interface while still performing behaviour specific to their own type. In Python, polymorphism often appears through inheritance, method overriding, and duck typing. This makes Python suitable for GUI applications because framework classes can define a shared interface and subclasses can implement specialised behaviour.

File handling refers to creating, opening, reading, writing, and appending data in files. In Python, file handling is commonly performed through context managers such as `with open(...)`, which help ensure files are safely closed after use. File handling is important in real software because applications usually need to persist settings, logs, screenshots, or user data between runs.

Dictionaries are one of Python's core built-in data structures. A dictionary stores data as key-value pairs, which makes it especially useful for structured information such as JSON payloads, configuration values, event details, and mappings between program states and user-facing text.

### Background Sources

The discussion in this report aligns with the Python documentation, which explains object-oriented programming through classes and inheritance, file operations through built-in I/O and `pathlib`, and associative data storage through dictionaries. These sources are appropriate for academic referencing because they are primary technical documentation published by the Python Software Foundation.

## 2. Description of the Patterns

### How Python Implements Polymorphism

Python supports polymorphism in multiple ways:

1. through inheritance, where a subclass extends a parent class;
2. through method overriding, where a subclass provides its own implementation of a shared method;
3. through duck typing, where an object is accepted because it behaves correctly rather than because it belongs to one exact class.

In AiClickHelper, the clearest example is the PyQt class hierarchy. `MainWindow` inherits from `QMainWindow` in `aiclickhelper/ui/main_window.py`, `OverlayWindow` inherits from `QWidget` in `aiclickhelper/overlay.py`, and both are still treated by Qt as window objects that can be shown, hidden, resized, and updated. At the same time, each subclass performs different behaviour. For example, `OverlayWindow.paintEvent()` overrides the standard widget painting behaviour so the overlay can draw a pulsing target marker on the desktop. This is runtime polymorphism because Qt calls the method appropriate to the concrete object.

Another practical example is `SessionController` and `TurnWorker`, which both inherit from `QObject` in `aiclickhelper/controller.py`. Because they are Qt objects, they can participate in the signal-slot system even though they have different responsibilities. This shows how a framework can interact with different objects through the same base type while allowing each one to provide specialised logic.

My own simplified example is shown below:

```python
class Notification:
    def send(self):
        raise NotImplementedError


class EmailNotification(Notification):
    def send(self):
        return "Sending an email"


class SmsNotification(Notification):
    def send(self):
        return "Sending an SMS"


def deliver_message(item: Notification):
    print(item.send())
```

In this example, `deliver_message()` can work with different subclasses through the same interface. This is similar to how Qt works with different window objects in AiClickHelper.

### How Python Implements File Handling

Python file handling normally uses:

1. path management through `pathlib.Path`;
2. context managers with `with ... open(...)`;
3. text or JSON serialisation for persistent storage.

AiClickHelper uses file handling extensively. In `aiclickhelper/app.py`, the `load_dotenv()` function reads the `.env` file using `Path(path).read_text(...)` and loads environment values into `os.environ`. In `aiclickhelper/session_store.py`, the `save_session()` method creates directories if necessary and writes the complete session to `session.json` using `json.dump(...)`. In `aiclickhelper/event_logger.py`, the `append()` method opens `events.jsonl` in append mode and stores each new event on a separate line. The controller also saves screenshots and debug images to session-specific folders.

This means file handling is not a minor feature in this project; it is part of the core workflow. Without file handling, the program would lose screenshots, chat history, action history, and debugging records after every run.

My own simplified example is:

```python
from pathlib import Path

report_path = Path("report.txt")

with report_path.open("w", encoding="utf-8") as file:
    file.write("Step 1 completed\n")

with report_path.open("a", encoding="utf-8") as file:
    file.write("Step 2 completed\n")

with report_path.open("r", encoding="utf-8") as file:
    content = file.read()

print(content)
```

This example demonstrates the same principles used in the application: create or open a file, write structured content, append more data, and read it back when needed.

### How Python Implements Dictionaries

Python dictionaries store data in key-value pairs and are especially useful when data needs named fields. They are flexible, fast to access, and naturally compatible with JSON. In practice, dictionaries often act as a bridge between in-memory objects and external APIs or file formats.

AiClickHelper uses dictionaries in several important places:

1. In `aiclickhelper/openai_adapter.py`, the API request is assembled as a nested dictionary containing keys such as `"model"`, `"instructions"`, `"input"`, and `"reasoning"`.
2. In `aiclickhelper/response_normalizer.py`, the program parses the model's JSON output into a Python dictionary called `payload`, then reads keys like `"action_type"`, `"target_point"`, `"confidence"`, and `"user_instruction"`.
3. In `aiclickhelper/session_store.py`, helper function `_to_json_safe()` recursively converts dataclasses, enums, lists, and dictionaries into a JSON-safe dictionary structure before saving.
4. In `aiclickhelper/ui/main_window.py`, a dictionary is used to map `Speaker.USER`, `Speaker.ASSISTANT`, and `Speaker.SYSTEM` to readable labels in the chat window.

These examples show that dictionaries are central to this application because they support configuration-like mappings, API communication, event details, and serialisation.

My own simplified example is:

```python
student = {
    "name": "Anna",
    "course": "Computer Science",
    "grade": 85
}

print(student["name"])
student["grade"] = 90
student["email"] = "anna@example.com"
```

This example demonstrates why dictionaries are useful: values can be accessed by meaningful keys, updated later, and extended with new information.

### How the Three Techniques Work Together in This Program

The three concepts are closely connected in AiClickHelper rather than isolated from one another.

- Polymorphism supports the GUI architecture because different Qt-based objects can behave as windows, widgets, or controllers while still integrating through common framework interfaces.
- File handling supports persistence because sessions, logs, screenshots, and configuration data must be saved and loaded from disk.
- Dictionaries support structured communication because both API requests and API responses are easiest to represent as named key-value pairs.

Together, these techniques make the application easier to organise, extend, and debug.

## 3. Summary and Conclusion

This assessment shows that AiClickHelper is more than a simple script. It is a structured Python application that combines GUI programming, API communication, data modelling, and persistent storage. Polymorphism is visible in the way Qt objects are subclassed and customised, especially through classes such as `MainWindow`, `OverlayWindow`, `SessionController`, and `TurnWorker`. File handling is used to load environment variables, save session history, append event logs, and manage screenshots. Dictionaries are used throughout the code to represent JSON payloads, event details, and display mappings.

From my reflection, these three Python techniques are especially effective when they are used together. Polymorphism improves code organisation by allowing each class to specialise its behaviour without breaking the wider framework. File handling makes the program practical because it preserves state across sessions and supports debugging. Dictionaries make the program flexible because external API data and internal structured data can be handled in a readable way.

My experience of analysing this program suggests that Python is well suited to this kind of assessment because the language makes advanced ideas relatively approachable. In particular, the combination of dataclasses, dictionaries, and file I/O creates clear and maintainable code, while PyQt demonstrates how polymorphism becomes useful in a real desktop application rather than only in theory.

## References

Python Software Foundation. (2026). *The Python Tutorial*. Available at: https://docs.python.org/3/tutorial/ (Accessed: 13 April 2026).

Python Software Foundation. (2026). *Built-in Functions*. Available at: https://docs.python.org/3/library/functions.html (Accessed: 13 April 2026).

Python Software Foundation. (2026). *pathlib - Object-oriented filesystem paths*. Available at: https://docs.python.org/3/library/pathlib.html (Accessed: 13 April 2026).

Python Software Foundation. (2026). *json - JSON encoder and decoder*. Available at: https://docs.python.org/3/library/json.html (Accessed: 13 April 2026).
