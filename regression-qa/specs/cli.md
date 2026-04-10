# Module: cli
_Last updated: 2026-04-06_

## Summary
CLI tool that launches Claude Code instances in parallel tmux windows, either
from literal prompt strings or from a Jinja2 template expanded with variable
dicts.

## Functionality

### Internal: _template_vars(template_str)
- **Description**: Parses a Jinja2 template string and returns the set of
  undeclared variable names.
- **Key inputs**: `template_str: str`
- **Expected response**: `set[str]`
- **Edge cases to test**: empty template returns empty set; template with vars
  returns those var names; template with no vars returns empty set.
- **Already covered**: no

### Internal: _render(template_str, variables)
- **Description**: Renders a Jinja2 template string with the given variable
  dict.
- **Key inputs**: `template_str: str`, `variables: dict`
- **Expected response**: rendered string
- **Edge cases to test**: all vars provided renders correctly; missing var
  renders empty (Jinja2 default).
- **Already covered**: no

### Internal: _load_vars(vars_inline, vars_file)
- **Description**: Loads a list of variable dicts from either a JSON string
  or a file path. File can be a JSON array or JSONL (one JSON object per line).
- **Key inputs**: `vars_inline: str | None`, `vars_file: str | None`
- **Expected response**: `list[dict]`
- **Edge cases to test**:
  - inline JSON array → list of dicts
  - inline non-array JSON → `click.UsageError`
  - file with JSON array → list of dicts
  - file with JSONL → list of dicts
- **Already covered**: no

### CLI: main (claudeplexer)
- **Description**: Click command that validates inputs, resolves prompts (literal
  or template-rendered), and calls `_launch`.
- **Auth required**: no
- **Key inputs** (via CliRunner):
  - positional `prompts` — zero or more literal prompt strings
  - `--template` / `-t` — Jinja2 template (file path or inline string)
  - `--vars` — JSON array of variable dicts (inline)
  - `--vars-file` — path to JSON array or JSONL file
  - `--session` / `-s` — tmux session name
  - `--max` — max concurrent windows (default 10)
- **Expected response**: exits 0, prints "Launched item-N" for each prompt
- **Edge cases to test**:
  - prompts + template → UsageError (exit != 0)
  - --vars + --vars-file together → UsageError
  - --vars without --template → UsageError
  - --template without --vars → UsageError
  - no prompts and no template → UsageError
  - template with inline vars: rendered prompts passed to _launch
  - template with vars-file (JSON array): rendered prompts passed to _launch
  - template with vars-file (JSONL): rendered prompts passed to _launch
  - var set missing required template variable → UsageError
  - var set has extra (unknown) variable → UsageError
  - prompts exceed max_windows → ClickException
  - not in tmux session and no --session → ClickException
  - --session triggers `tmux new-session` subprocess call
- **Already covered**: no (test_basic.py has only a sanity test)
