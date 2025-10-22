"""
scripts/render_templates.py

Simple template renderer:
- Loads variables from a .env file (python-dotenv)
- Renders templates under --templates (directory) or a single template file
- Writes output to --out preserving base filename (dropping .template)
- Substitutes ${VAR} placeholders from environment

Usage:
  uv run python scripts/render_templates.py --templates deploy/templates --out deploy/rendered --env src/.env
  uv run python scripts/render_templates.py --templates deploy/templates/activitytracker.nginx.ssl.template --out deploy/rendered --env src/.env
"""

import argparse
import os
import re
from pathlib import Path

from dotenv import dotenv_values

PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def render_text(text, env):
    """
    Substitutes `${VAR}` placeholders in `text` using values from `env` with a fallback to the process environment.
    
    Parameters:
        text (str): Input string containing `${VAR}` placeholders.
        env (Mapping[str, str]): Primary mapping of variable names to replacement values; lookups use this mapping first.
    
    Returns:
        str: The input string with each `${VAR}` replaced by `env[VAR]` if present, otherwise by the corresponding `os.environ` value, or an empty string if neither provides a value.
    """
    def repl(m):
        key = m.group(1)
        return env.get(key, os.environ.get(key, ""))

    return PLACEHOLDER_RE.sub(repl, text)


def main():
    """
    Command-line entry point that renders template files using environment variables and writes the results to an output directory.
    
    Parses CLI arguments:
    - --templates: path to a templates directory (collects files ending with `.template`) or a single template file.
    - --out: destination directory to write rendered files (created if missing).
    - --env: optional .env file to load and merge with the process environment.
    
    Loads variables from the optional .env file (if provided and found), merges them with the current environment, substitutes placeholders of the form `${VAR}` in each template using the merged environment (missing variables become empty strings), and writes each rendered file to the output directory preserving the template's base name but dropping the `.template` suffix. Prints warnings when the .env file is missing, notices when no templates are found in a directory, and an error message when the templates path is neither a file nor a directory.
    """
    p = argparse.ArgumentParser()
    p.add_argument(
        "--templates", required=True, help="Templates directory or single template file"
    )
    p.add_argument(
        "--out", required=True, help="Output directory to write rendered files"
    )
    p.add_argument(
        "--env", required=False, default=None, help=".env file to load (optional)"
    )
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load environment variables
    env = {}
    if args.env:
        env_path = Path(args.env)
        if env_path.exists():
            env.update(dotenv_values(str(env_path)))
        else:
            print(
                f"Warning: env file {env_path} not found; falling back to existing environment variables"
            )

    # merge current env as fallback
    env = {k: v for k, v in env.items() if v is not None}
    env.update(os.environ)

    templates_path = Path(args.templates)
    templates = []

    if templates_path.is_dir():
        templates = list(templates_path.glob("*.template"))
        if not templates:
            print(f"No templates found in directory {templates_path}")
            return
    elif templates_path.is_file():
        templates = [templates_path]
    else:
        print(f"Error: {templates_path} is not a valid file or directory")
        return

    # Render templates
    for tmpl in templates:
        text = tmpl.read_text(encoding="utf-8")
        rendered = render_text(text, env)
        out_name = tmpl.name
        out_name = out_name.replace(".template", "")
        out_path = out_dir / out_name
        out_path.write_text(rendered, encoding="utf-8")
        print(f"Rendered {tmpl} -> {out_path}")


if __name__ == "__main__":
    main()