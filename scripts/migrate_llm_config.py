#!/usr/bin/env python3
"""Migrate scenario YAML files to provider-prefixed model strings.

For every string/list value under llm: that lacks a provider prefix,
rewrites it as openrouter:<original>.

Usage:
    python scripts/migrate_llm_config.py          # Show diff only
    python scripts/migrate_llm_config.py --apply  # Write changes
"""

import argparse
import re
import sys
from pathlib import Path


# Keys directly under llm: that hold model specs (not numeric settings)
MODEL_KEYS = {"model", "events", "actors", "rules", "metrics", "summary", "analysis", "referee"}

# Keys under llm: that hold numeric/dict settings - skip their children
SETTINGS_KEYS = {"temperature", "max_tokens", "max_tokens_by_task"}


def is_model_string(value: str) -> bool:
    """Return True if value looks like a model name (not a number, not already prefixed)."""
    value = value.strip()
    if not value:
        return False
    # Skip if already has a provider prefix
    if ":" in value:
        return False
    # Skip if it's a pure number (max_tokens values like "3500")
    try:
        float(value)
        return False
    except ValueError:
        pass
    return True


def migrate_yaml_text(text: str) -> tuple[str, list[str]]:
    """Add openrouter: prefix to bare model strings in YAML text.

    Returns (new_text, list_of_change_descriptions).
    Uses a line-by-line approach to preserve YAML formatting exactly.
    """
    lines = text.splitlines(keepends=True)
    result = []
    changes = []

    in_llm_section = False
    llm_indent = -1

    # Track context stack to skip settings subsections
    in_settings_subsection = False
    settings_indent = -1

    # Track when we're inside the actors per-actor dict
    in_actors_dict = False
    actors_indent = -1

    # Track current model key context for list items
    current_model_key = None
    current_model_key_indent = -1

    for lineno, line in enumerate(lines, 1):
        raw_stripped = line.rstrip('\n')
        stripped = raw_stripped.lstrip()
        indent = len(raw_stripped) - len(stripped)

        # Skip blank lines and comments (pass through unchanged)
        if not stripped or stripped.startswith('#'):
            result.append(line)
            continue

        # ── Detect entering llm: section at top level ──────────────────────
        if re.match(r'^llm\s*:', line):
            in_llm_section = True
            llm_indent = indent
            in_settings_subsection = False
            in_actors_dict = False
            current_model_key = None
            result.append(line)
            continue

        # ── If not in llm section, pass through ────────────────────────────
        if not in_llm_section:
            result.append(line)
            continue

        # ── Check if we've left the llm section ────────────────────────────
        if indent <= llm_indent and stripped and not stripped.startswith('-'):
            in_llm_section = False
            in_settings_subsection = False
            in_actors_dict = False
            current_model_key = None
            result.append(line)
            continue

        # ── Skip contents of settings subsections (max_tokens_by_task etc.) ─
        if in_settings_subsection:
            if indent <= settings_indent:
                in_settings_subsection = False
            else:
                result.append(line)
                continue

        # ── Direct children of llm: (one indent level deeper) ──────────────
        key_match = re.match(r'^(\s*)(\w[\w-]*)\s*:', line)
        if key_match and indent == llm_indent + 2:
            key = key_match.group(2)

            # Settings key: mark subsection to skip
            if key in SETTINGS_KEYS:
                in_settings_subsection = True
                settings_indent = indent
                in_actors_dict = False
                current_model_key = None
                result.append(line)
                continue

            # Model key: set context and check for inline value
            if key in MODEL_KEYS:
                current_model_key = key
                current_model_key_indent = indent
                in_actors_dict = (key == "actors")
                actors_indent = indent if in_actors_dict else -1

                rest = line[key_match.end():]
                # Check for inline string value (not a block starting a list/dict)
                inline_match = re.match(r'''\s*["']([^'"]+)["']\s*(?:#.*)?$''', rest)
                if not inline_match:
                    # Unquoted inline value
                    inline_match = re.match(r'''\s*([^#\n\[\{]+?)\s*(?:#.*)?$''', rest)

                if inline_match:
                    model_val = inline_match.group(1).strip().strip('"').strip("'")
                    if is_model_string(model_val):
                        indent_str = key_match.group(1)
                        new_line = f'{indent_str}{key}: "openrouter:{model_val}"\n'
                        changes.append(f"  Line {lineno}: {key}: {model_val!r} → openrouter:{model_val}")
                        result.append(new_line)
                        continue

                result.append(line)
                continue

        # ── List items under a model key ───────────────────────────────────
        list_match = re.match(r'^(\s*)-\s+(.+)$', line)
        if list_match and current_model_key and indent > current_model_key_indent:
            item_str = list_match.group(2).strip().strip('"').strip("'")
            prefix_spaces = list_match.group(1)
            if is_model_string(item_str):
                new_line = f'{prefix_spaces}- "openrouter:{item_str}"\n'
                changes.append(
                    f"  Line {lineno}: [{current_model_key}] - {item_str!r} → openrouter:{item_str}"
                )
                result.append(new_line)
                continue

        # ── Per-actor dict entries under actors: ───────────────────────────
        if in_actors_dict and key_match and indent > actors_indent:
            actor_key = key_match.group(2)
            rest = line[key_match.end():]
            inline_match = re.match(r'''\s*["']([^'"]+)["']\s*(?:#.*)?$''', rest)
            if not inline_match:
                inline_match = re.match(r'''\s*([^#\n\[\{]+?)\s*(?:#.*)?$''', rest)
            if inline_match:
                model_val = inline_match.group(1).strip().strip('"').strip("'")
                if is_model_string(model_val):
                    indent_str = key_match.group(1)
                    new_line = f'{indent_str}{actor_key}: "openrouter:{model_val}"\n'
                    changes.append(
                        f"  Line {lineno}: actors.{actor_key}: {model_val!r} → openrouter:{model_val}"
                    )
                    result.append(new_line)
                    continue

        result.append(line)

    return "".join(result), changes


def main():
    parser = argparse.ArgumentParser(
        description="Migrate LLM config to provider-prefixed model strings"
    )
    parser.add_argument("--apply", action="store_true", help="Write changes to disk")
    parser.add_argument(
        "--scenarios-dir",
        default="scenarios",
        help="Root directory to scan for scenario YAML files (default: scenarios)",
    )
    args = parser.parse_args()

    root = Path(args.scenarios_dir)
    if not root.exists():
        print(f"Error: scenarios directory not found: {root}", file=sys.stderr)
        sys.exit(1)

    yaml_files = sorted(root.rglob("*.yaml")) + sorted(root.rglob("*.yml"))
    total_changes = 0

    for filepath in yaml_files:
        text = filepath.read_text(encoding="utf-8")
        if "llm:" not in text:
            continue

        new_text, changes = migrate_yaml_text(text)
        if not changes:
            continue

        total_changes += len(changes)
        print(f"\n{filepath}:")
        for change in changes:
            print(change)

        if args.apply:
            filepath.write_text(new_text, encoding="utf-8")
            print(f"  → Written")

    if total_changes == 0:
        print("No changes needed – all model strings already have provider prefixes.")
    elif not args.apply:
        print(f"\nTotal: {total_changes} change(s) found. Run with --apply to write.")
    else:
        print(f"\nTotal: {total_changes} change(s) written.")


if __name__ == "__main__":
    main()
