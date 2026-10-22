# Ollama File Agent

A small, local AI agent written in Python. It connects to the **Ollama REST service** and uses a language model (for example **Llama 3.2 3B**) to answer questions about the files in one folder on your computer.

You chat with it in the terminal. When it needs information, the agent decides by itself to **list**, **search** or **read** files, then answers you.

```
You: What files are in my folder?
  [tool] list_files({'folder': '.'})

Agent: You have one file: welcome.txt (239 bytes).
```

---

## Table of contents

1. [Features](#features)
2. [How it works](#how-it-works)
3. [Project structure](#project-structure)
4. [Requirements](#requirements)
5. [Installation](#installation)
6. [Running the agent](#running-the-agent)
7. [Configuration](#configuration)
8. [Using the agent](#using-the-agent)
9. [Choosing a model](#choosing-a-model)
10. [Safety](#safety)
11. [Troubleshooting](#troubleshooting)
12. [Extending the agent](#extending-the-agent)
13. [FAQ](#faq)

---

## Features

- **Runs locally**: uses your own Ollama installation. No API keys and no cost with local models.
- **Uses the model you already have**: automatically picks the model that is running in Ollama, or any installed model.
- **Three file tools**: list a folder, search files by name, read a text file.
- **Locked to one folder**: the agent cannot see or read anything outside the folder you allow.
- **Read-only**: it cannot change, move or delete files.
- **Remote Ollama support**: can connect to Ollama running on another computer.
- **VS Code ready**: includes a run configuration (`.vscode/launch.json`).
- **Clear error messages**: tells you when Ollama is not running or has no models.

---

## How it works

An agent is **a model + tools + a loop**:

```
          ┌──────────────────────────────────────────────┐
          │                                              │
 You ──►  agent.py ──► Ollama REST service ──► Model     │
          ▲    (http://localhost:11434)          │       │
          │                                      ▼       │
          │                      "I need a tool: list_files(.)"
          │                                      │       │
          └── tool result ◄── agent.py runs the tool ◄───┘
```

1. You type a question.
2. `agent.py` sends your question plus the list of available tools to Ollama.
3. The model either **answers** or **asks to use a tool** (for example `read_file("notes.txt")`).
4. `agent.py` runs the tool and sends the result back to the model.
5. Steps 3–4 repeat (up to 5 times) until the model gives a final answer.

The `ollama` Python package used here is a thin wrapper around Ollama's REST API (`/api/chat`, `/api/tags`, `/api/ps`). The model itself always runs inside Ollama, not inside this program.

---

## Project structure

```
ollama-agent/
├── agent.py            # The agent: settings, tools, startup checks, chat loop
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── my_files/           # Default folder the agent is allowed to see
│   └── welcome.txt     # Example file to test with
└── .vscode/
    └── launch.json     # VS Code run/debug configuration (F5)
```

---

## Requirements

| Requirement | Notes |
|---|---|
| **Windows, macOS or Linux** | Instructions below use Windows PowerShell |
| **Python 3.9 or newer** | [python.org](https://www.python.org/downloads/). On Windows, tick "Add Python to PATH" during install |
| **Ollama** | [ollama.com](https://ollama.com/download), installed and running |
| **At least one model in Ollama** | Local (e.g. `llama3.2`) or cloud (e.g. `glm-5.3-flash:cloud`) |
| **VS Code** (optional) | With the **Python** extension by Microsoft |

A GPU is **not** required. Small models such as Llama 3.2 3B run on a normal CPU.

---

## Installation

### 1. Open the project

Unzip the project, then in VS Code choose **File → Open Folder** and select the `ollama-agent` folder.
Open the terminal with **Ctrl + `**.

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

In Command Prompt (cmd) use `.venv\Scripts\activate.bat` instead.

You should now see `(.venv)` at the start of the terminal line.

> **"Running scripts is disabled on this system"?** Run this once, then activate again:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Select the interpreter in VS Code

Press **Ctrl + Shift + P** → **Python: Select Interpreter** → choose the one with `.venv` in its path.

### 5. Make sure Ollama has a model

Open **http://localhost:11434/api/tags** in your browser.

- If models are listed, you're ready.
- If the list is empty, add one:
  - **Local model:** `ollama pull llama3.2:3b`
  - **Cloud model (no download):** `ollama signin`, then use `glm-5.3-flash:cloud` (see [Configuration](#configuration))

---

## Running the agent

Make sure the **Ollama app is running** first. Then use any of these:

| Method | How | When to use |
|---|---|---|
| **Terminal** | `python agent.py` | Everyday use (recommended) |
| **Run button** | Click **▶ Run Python File** at the top right of `agent.py` | Quick start from the editor |
| **Ctrl + F5** | Run without debugging | Uses `launch.json` settings, starts faster |
| **F5** | Run with the debugger | Debugging: set breakpoints, inspect variables |

> **Note:** Only **F5** and **Ctrl + F5** read the settings in `.vscode/launch.json`.
> When you run `python agent.py` in the terminal, use environment variables instead (see below).

On start you will see something like:

```
Using model 'llama3.2:latest' (already running).
Agent ready  |  model: llama3.2:latest  |  allowed folder: C:\...\ollama-agent\my_files
Type your question. Commands: 'clear' = forget the chat, 'exit' = quit.

You:
```

---

## Configuration

All settings are optional.

| Setting | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | *(empty)* | Model to use. Empty = use the model already running, or any installed model |
| `OLLAMA_HOST` | `http://localhost:11434` | Address of the Ollama REST service. Use another PC's address to run the model there |
| `AGENT_FOLDER` | `my_files` next to `agent.py` | The only folder the agent may see (including its subfolders) |

### In VS Code (`.vscode/launch.json`)

```json
"env": {
    "OLLAMA_MODEL": "llama3.2:latest",
    "OLLAMA_HOST": "http://localhost:11434",
    "AGENT_FOLDER": "C:\\Users\\kumma\\Documents"
}
```

Use double backslashes (`\\`) in Windows paths inside JSON.

### In the PowerShell terminal

```powershell
$env:OLLAMA_MODEL = "llama3.2:latest"
$env:AGENT_FOLDER = "C:\Users\kumma\Documents"
python agent.py
```

These values last until you close that terminal.

### In the code

Constants at the top of `agent.py`:

| Constant | Default | Meaning |
|---|---|---|
| `MAX_FILE_CHARS` | `4000` | Longer files are cut off, because small models have limited memory |
| `MAX_TOOL_ROUNDS` | `5` | Maximum tool calls per question before the agent stops |

---

## Using the agent

### Example questions

```
What files are in my folder?
Read welcome.txt and summarize it
Find files with "bill" in the name
What is in the reports folder?
Read notes.md and list the action items
```

### Chat commands

| Command | Action |
|---|---|
| `clear` | Forget the conversation and start fresh |
| `exit` / `quit` / `bye` | Close the agent |
| **Ctrl + C** | Stop the current answer, or quit at the prompt |

### Available tools

| Tool | What it does |
|---|---|
| `list_files(folder)` | Lists files and subfolders (with file sizes) |
| `find_files(name_part)` | Searches all subfolders for file names containing the text (max 50 results) |
| `read_file(path)` | Reads a text file (first 4,000 characters) |

Lines like `[tool] read_file({'path': 'notes.txt'})` show you each time the agent uses a tool.

### Supported file types

Plain-text files work: `.txt`, `.md`, `.csv`, `.json`, `.py`, `.html`, `.log` and similar.
**PDF, Word and Excel files are not supported yet.** The agent will see them in folder listings but cannot read their content.

---

## Choosing a model

The agent works with any Ollama model that supports **tool calling**.

### CPU only (no GPU)

| Your RAM | Suggested model | Command |
|---|---|---|
| 8 GB | Llama 3.2 3B | `ollama pull llama3.2:3b` |
| 16 GB | Qwen3 8B | `ollama pull qwen3:8b` |
| 16 GB | gpt-oss 20B | `ollama pull gpt-oss:20b` |
| 32 GB | Qwen3 30B-A3B | `ollama pull qwen3:30b-a3b` |

`gpt-oss:20b` and `qwen3:30b-a3b` are MoE ("mixture of experts") models. They use only a small part of their parameters for each word, so they run quite fast on a CPU while being much smarter than a 3B model.

### Cloud models (no download, no strong PC needed)

```powershell
ollama signin
$env:OLLAMA_MODEL = "glm-5.3-flash:cloud"
python agent.py
```

Cloud models are much smarter, but they run on Ollama's servers (your questions and file contents are sent there) and the free plan has usage limits.

### Small-model tips

Llama 3.2 3B is fast but limited. It may sometimes skip a tool, pick the wrong one, or misread a file. If that happens:

- Ask short, direct questions ("Read notes.txt" instead of "Can you maybe check my notes?").
- Type `clear` to start a fresh conversation.
- Try a larger or cloud model for better results.

---

## Safety

- **Read-only.** The agent has no tools to write, rename, move or delete files.
- **Folder lock.** Every path is checked. Attempts to leave the allowed folder (for example `../secret.txt`) are blocked with "Access denied".
- **Local by default.** With a local model, nothing leaves your computer.
- **Cloud models** send your questions and the file contents the agent reads to Ollama's servers. Don't point the agent at private files when using a cloud model.
- **Use a dedicated folder.** Don't set `AGENT_FOLDER` to `C:\` or your whole user folder.

---

## Troubleshooting

| Message / problem | Cause | Fix |
|---|---|---|
| `Cannot connect to the Ollama REST service at http://localhost:11434` | Ollama is not running | Start the Ollama app (llama icon in the taskbar) or run `ollama serve` |
| `Your Ollama has no models yet` | No model installed | `ollama pull llama3.2:3b`, or `ollama signin` and use a cloud model |
| `Model 'xyz' is not available on this Ollama` | `OLLAMA_MODEL` name doesn't match | Run `ollama list` and copy the exact name (e.g. `llama3.2:latest`). The agent falls back to another model automatically |
| `The 'ollama' package is missing` | Dependencies not installed in this environment | Activate `.venv`, then `pip install -r requirements.txt` |
| `running scripts is disabled on this system` | PowerShell execution policy | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| F5 uses the wrong Python | Wrong interpreter selected | **Ctrl + Shift + P** → **Python: Select Interpreter** → pick `.venv` |
| Settings in `launch.json` are ignored | Started with `python agent.py` | `launch.json` is only used by F5 / Ctrl + F5. Use `$env:...` in the terminal |
| `(stopped after too many tool calls)` | Model got stuck in a loop | Ask a simpler question, type `clear`, or use a bigger model |
| Answers are very slow | Model too big for your CPU/RAM | Use a smaller model, close other heavy apps |
| Agent invents file names or content | Small model limitation | Ask it to "use list_files first", or use a bigger model |
| Cloud model returns errors | Free usage limit reached | Wait for the limit to reset, or switch to a local model |

**Useful Ollama commands**

```powershell
ollama list        # installed models
ollama ps          # models currently loaded in memory
ollama pull NAME   # download a model
ollama rm NAME     # delete a model
```

---

## Extending the agent

Adding a new tool takes three steps.

**1. Write a Python function** with type hints and a docstring. Ollama reads these to tell the model what the tool does:

```python
def count_lines(path: str) -> str:
    """Count the number of lines in a text file.

    Args:
        path: File path relative to the base folder.

    Returns:
        The number of lines.
    """
    try:
        p = _safe_path(path)          # always use _safe_path for file access
        return str(len(p.read_text(encoding="utf-8", errors="replace").splitlines()))
    except Exception as e:
        return f"Error: {e}"
```

**2. Register it** in the `TOOLS` dictionary:

```python
TOOLS = {"list_files": list_files, "read_file": read_file,
         "find_files": find_files, "count_lines": count_lines}
```

**3. Mention it** in `SYSTEM_PROMPT` so the model knows when to use it.

### Ideas for new tools

- Read PDF files (using the `pypdf` package)
- Read Word files (using `python-docx`)
- Write notes into a file (add a confirmation step before writing)
- Get today's date and time
- Search inside file contents, not only file names

---

## FAQ

**Do I need to download a model to use this?**
The program itself downloads nothing. It uses whatever models your Ollama already has. If Ollama has none, you need either a local model (`ollama pull`) or a cloud model (`ollama signin`).

**Is it free?**
Yes. Python, Ollama, local models and this code are all free. Ollama's cloud models are free with usage limits.

**Does it need the internet?**
Not with a local model. It works fully offline.

**Can it use Ollama on another computer?**
Yes. Set `OLLAMA_HOST` to that computer's address, for example `http://192.168.1.50:11434`. On that computer, Ollama must be configured to accept network connections (set the environment variable `OLLAMA_HOST=0.0.0.0` there, or enable "Expose Ollama to the network" in Ollama's settings).

**Can I "train" the model on my files?**
This agent doesn't train the model. It reads your files at question time and gives their content to the model. For large document collections, a RAG tool such as AnythingLLM or Open WebUI works better.

**Why F5?**
You don't need it. `python agent.py` works the same. F5 only adds the debugger and the `launch.json` settings.
