from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import click
from jinja2 import Environment, Template, meta

if TYPE_CHECKING:
    pass


MAX_WINDOWS = 10


def _template_vars(template_str: str) -> set[str]:
    env = Environment()
    ast = env.parse(template_str)
    return meta.find_undeclared_variables(ast)


def _render(template_str: str, variables: dict) -> str:
    return Template(template_str).render(**variables)


def _current_session() -> str | None:
    if not os.environ.get("TMUX"):
        return None
    result = subprocess.run(
        ["tmux", "display-message", "-p", "#S"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _launch(prompts: list[str], session: str | None, max_windows: int) -> None:
    if len(prompts) > max_windows:
        raise click.ClickException(f"{len(prompts)} prompts exceeds max of {max_windows}")

    if session:
        result = subprocess.run(
            ["tmux", "new-session", "-d", "-s", session],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise click.ClickException(
                f"Failed to create session '{session}': {result.stderr.strip()}"
            )
        target = session
    else:
        target = _current_session()
        if not target:
            raise click.ClickException(
                "Not inside a tmux session. Use --session NAME to create one."
            )

    for i, prompt in enumerate(prompts):
        cmd = f"claude {shlex.quote(prompt)}"
        result = subprocess.run(
            ["tmux", "new-window", "-t", f"{target}:", "-n", f"item-{i}", cmd],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise click.ClickException(f"Failed to create window {i}: {result.stderr.strip()}")
        click.echo(f"Launched item-{i}")


def _load_vars(vars_inline: str | None, vars_file: str | None) -> list[dict]:
    if vars_inline:
        parsed = json.loads(vars_inline)
        if not isinstance(parsed, list):
            raise click.UsageError("--vars must be a JSON array")
        return parsed
    path = Path(vars_file)  # type: ignore[arg-type]
    text = path.read_text().strip()
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


@click.command()
@click.argument("prompts", nargs=-1)
@click.option("--template", "-t", "template_src", help="Jinja2 template (file path or inline string)")
@click.option("--vars", "vars_inline", help="JSON array of variable dicts")
@click.option("--vars-file", "vars_file", type=click.Path(exists=True), help="JSON array or JSONL file of variable dicts")
@click.option("--session", "-s", help="Create new tmux session with this name")
@click.option("--max", "max_windows", default=MAX_WINDOWS, show_default=True, help="Max concurrent windows")
def main(
    prompts: tuple[str, ...],
    template_src: str | None,
    vars_inline: str | None,
    vars_file: str | None,
    session: str | None,
    max_windows: int,
) -> None:
    """Launch Claude Code instances in tmux windows."""
    has_prompts = bool(prompts)
    has_template = bool(template_src)
    has_vars = bool(vars_inline) or bool(vars_file)

    if has_prompts and (has_template or has_vars):
        raise click.UsageError("Cannot combine prompt strings with --template/--vars.")
    if vars_inline and vars_file:
        raise click.UsageError("Use either --vars or --vars-file, not both.")
    if has_vars and not has_template:
        raise click.UsageError("--vars/--vars-file requires --template.")
    if has_template and not has_vars:
        raise click.UsageError("--template requires --vars or --vars-file.")
    if not has_prompts and not has_template:
        raise click.UsageError("Provide prompt strings or --template + --vars.")

    if has_prompts:
        final_prompts = list(prompts)
    else:
        template_path = Path(template_src)  # type: ignore[arg-type]
        template_str = template_path.read_text() if template_path.exists() else template_src
        assert isinstance(template_str, str)

        required = _template_vars(template_str)
        all_vars = _load_vars(vars_inline, vars_file)

        for i, var_set in enumerate(all_vars):
            provided = set(var_set.keys())
            if missing := required - provided:
                raise click.UsageError(f"Var set {i}: missing variables: {missing}")
            if extra := provided - required:
                raise click.UsageError(f"Var set {i}: unknown variables: {extra}")

        final_prompts = [_render(template_str, v) for v in all_vars]

    _launch(final_prompts, session, max_windows)
