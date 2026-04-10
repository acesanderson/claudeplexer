# Claudeplexer

Claudeplexer is a CLI tool for orchestrating multiple Claude Code instances across tmux windows using direct prompts or Jinja2 templates.

## Prerequisites

The following tools must be installed and available in the system PATH:

* **tmux**: Terminal multiplexer for managing windows.
* **Claude Code**: The `claude` CLI tool.
* **Python**: Version 3.13 or higher.

## Installation

Install the package using pip:

```bash
pip install claudeplexer-project
```

## Quick Start

Launch multiple Claude sessions by passing strings as arguments. This command creates a new tmux window for each prompt in the current session:

```bash
claudeplexer "Analyze the security of main.py" "Write unit tests for utils.py"
```

To create a new tmux session instead of using the current one, use the `--session` flag:

```bash
claudeplexer "Refactor the database module" --session audit-work
```

## Core Functionality

Claudeplexer automates the repetitive task of opening multiple windows and typing prompts. It supports complex workflows through Jinja2 templating and structured data.

### Templated Batch Processing

Generate prompts dynamically by combining a template with a list of variables.

**1. Create a template (template.j2 or inline string):**
```text
Review the file {{ filename }} and focus specifically on {{ focus_area }}.
```

**2. Create a variables file (vars.jsonl):**
```json
{"filename": "auth.py", "focus_area": "JWT validation"}
{"filename": "api.py", "focus_area": "rate limiting"}
{"filename": "db.py", "focus_area": "connection pooling"}
```

**3. Execute the batch:**
```bash
claudeplexer --template template.j2 --vars-file vars.jsonl
```

## Usage Reference

### Command Options

| Option | Description |
|--------|-------------|
| `--template`, `-t` | Path to a Jinja2 template file or an inline template string. |
| `--vars` | A JSON array of variable dictionaries. |
| `--vars-file` | Path to a JSON array file or a JSONL (JSON Lines) file. |
| `--session`, `-s` | Name of a new tmux session to create. |
| `--max` | Maximum number of concurrent windows (default: 10). |

### Input Formats

#### Variable Files
The `--vars-file` option accepts two formats:

**JSON Array:**
```json
[
  {"var1": "value1"},
  {"var1": "value2"}
]
```

**JSON Lines (JSONL):**
```json
{"var1": "value1"}
{"var1": "value2"}
```

#### Inline Variables
For quick execution, pass a JSON array directly:
```bash
claudeplexer --template "Fix bugs in {{ module }}" --vars '[{"module": "core"}, {"module": "cli"}]'
```

## Architecture

Claudeplexer operates as a wrapper around the tmux CLI.

1. **Prompt Generation**: Resolves raw strings or renders Jinja2 templates against provided JSON data.
2. **Session Management**: Identifies the active tmux session or initializes a new detached session.
3. **Execution**: Spawns tmux windows using `tmux new-window`, executing the `claude` command with the shell-quoted prompt as the initial argument.

Each window is named sequentially (`item-0`, `item-1`, etc.) to facilitate easy navigation within tmux.
