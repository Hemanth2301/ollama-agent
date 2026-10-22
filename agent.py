"""
Local AI agent for VS Code, using a model from Ollama.

The agent can list folders and read text files - inside ONE allowed folder only.

Setup (once, in the VS Code terminal):
    pip install -r requirements.txt

Run:
    Press F5 in VS Code   (or type:  python agent.py)

Settings (optional, change below or set as environment variables):
    OLLAMA_MODEL   - which Ollama model to use     (default: empty = use the model already running)
    OLLAMA_HOST    - Ollama REST service address   (default: http://localhost:11434)
    AGENT_FOLDER   - which folder the agent may see (default: the "my_files" folder next to this script)
"""

import os
import sys
from pathlib import Path

try:
    import ollama
except ImportError:
    print("The 'ollama' package is missing. In the VS Code terminal run:\n    pip install -r requirements.txt")
    sys.exit(1)

# ---------------- Settings ----------------

# Leave empty to automatically use the model that is already running in Ollama.
MODEL = os.environ.get("OLLAMA_MODEL", "").strip()

# Ollama REST service address. Default: http://localhost:11434
# Use another PC's Ollama, e.g. "http://192.168.1.50:11434"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").strip()
client = ollama.Client(host=OLLAMA_HOST)

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = Path(os.environ.get("AGENT_FOLDER", SCRIPT_DIR / "my_files")).resolve()

MAX_FILE_CHARS = 4000   # small models have limited memory - keep files short
MAX_TOOL_ROUNDS = 5     # how many tool calls the agent may make per question


# ---------------- Helpers ----------------

def _safe_path(path: str) -> Path:
    """Resolve a path and make sure it stays inside BASE_DIR."""
    p = (BASE_DIR / path).resolve()
    if p != BASE_DIR and BASE_DIR not in p.parents:
        raise ValueError("Access denied: path is outside the allowed folder.")
    return p


# ---------------- Tools the agent can use ----------------

def list_files(folder: str = ".") -> str:
    """List the files and subfolders in a folder.

    Args:
        folder: Folder path relative to the base folder. Use "." for the base folder.

    Returns:
        A list of names, with folders marked by a trailing slash.
    """
    try:
        p = _safe_path(folder)
        items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        lines = [f"{i.name}/" if i.is_dir() else f"{i.name} ({i.stat().st_size} bytes)"
                 for i in items]
        return "\n".join(lines) or "(empty folder)"
    except Exception as e:
        return f"Error: {e}"


def read_file(path: str) -> str:
    """Read the text content of a file.

    Args:
        path: File path relative to the base folder.

    Returns:
        The file content (shortened if very long).
    """
    try:
        p = _safe_path(path)
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_FILE_CHARS:
            text = text[:MAX_FILE_CHARS] + "\n...(file shortened)"
        return text
    except Exception as e:
        return f"Error: {e}"


def find_files(name_part: str) -> str:
    """Search all subfolders for files whose name contains some text.

    Args:
        name_part: Part of the file name to search for, for example "bill" or ".pdf".

    Returns:
        Matching file paths relative to the base folder.
    """
    try:
        needle = name_part.lower()
        hits = [str(p.relative_to(BASE_DIR)) for p in BASE_DIR.rglob("*")
                if p.is_file() and needle in p.name.lower()]
        return "\n".join(hits[:50]) or "No matching files found."
    except Exception as e:
        return f"Error: {e}"


TOOLS = {"list_files": list_files, "read_file": read_file, "find_files": find_files}

SYSTEM_PROMPT = (
    "You are a helpful personal assistant that can look at the user's files. "
    "Use list_files to see what is in a folder, find_files to search for a file by name, "
    "and read_file to read a file. Only use tools when needed. "
    "Never invent file names or contents. Answer briefly and clearly."
)


# ---------------- Startup checks ----------------

def check_ollama() -> bool:
    """Connect to the Ollama REST service and pick a model that is already available."""
    global MODEL
    try:
        available = [m.model for m in client.list().models]
        running = [m.model for m in client.ps().models]
    except Exception:
        print(f"Cannot connect to the Ollama REST service at {OLLAMA_HOST}.")
        print("Start the Ollama app (or run 'ollama serve') and try again.")
        return False

    if MODEL and MODEL in available:
        return True

    if MODEL:
        print(f"Model '{MODEL}' is not available on this Ollama.")

    # Prefer a model that is already running, otherwise any installed model.
    choice = (running or available or [None])[0]
    if choice is None:
        print("Your Ollama has no models yet. Either:")
        print("  - use a cloud model (no download):  ollama signin   then set OLLAMA_MODEL=glm-5.3-flash:cloud")
        print("  - or download a small local model:  ollama pull llama3.2:3b")
        return False

    MODEL = choice
    print(f"Using model '{MODEL}'" + (" (already running)" if MODEL in running else "") + ".")
    if len(available) > 1:
        print("Other models you have: " + ", ".join(m for m in available if m != MODEL))
    return True


# ---------------- The agent loop ----------------

def ask_agent(messages: list) -> None:
    """Let the model think, call tools, and print its final answer."""
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat(model=MODEL, messages=messages, tools=list(TOOLS.values()))
        messages.append(response.message)

        if not response.message.tool_calls:
            print(f"\nAgent: {response.message.content}\n")
            return

        for call in response.message.tool_calls:
            name = call.function.name
            args = call.function.arguments or {}
            print(f"  [tool] {name}({args})")
            func = TOOLS.get(name)
            try:
                result = func(**args) if func else f"Error: unknown tool {name}"
            except TypeError as e:
                result = f"Error: wrong arguments for {name}: {e}"
            messages.append({"role": "tool", "content": str(result), "tool_name": name})

    print("\nAgent: (stopped after too many tool calls - try asking more simply)\n")


def main() -> None:
    if not check_ollama():
        sys.exit(1)

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Agent ready  |  model: {MODEL}  |  allowed folder: {BASE_DIR}")
    print("Type your question. Commands: 'clear' = forget the chat, 'exit' = quit.\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print("Bye!")
            break
        if user_input.lower() == "clear":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("(chat cleared)\n")
            continue

        messages.append({"role": "user", "content": user_input})
        try:
            ask_agent(messages)
        except KeyboardInterrupt:
            print("\n(stopped)\n")
        except Exception as e:
            print(f"\nError talking to Ollama: {e}\n")


if __name__ == "__main__":
    main()