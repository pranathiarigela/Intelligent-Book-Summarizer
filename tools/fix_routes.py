#!/usr/bin/env python3
"""
tools/fix_routes.py

Searches Python files in the repo (current directory subtree) for lines that assign
st.session_state["route"] = "some_route" (string literal) and replaces the pattern
with navigate("some_route").

It:
 - creates a backup copy file.py.bak before editing
 - removes an immediately following rerun call (safe_rerun(), _safe_rerun(), st.experimental_rerun())
 - inserts `from utils.router import navigate` at top of file if not present

Run:
    python tools/fix_routes.py
"""

import os
import re
import shutil
from pathlib import Path

# Root directory to scan (project root)
ROOT = Path(".").resolve()

# File globs to scan
INCLUDE_GLOBS = ["**/*.py"]

# Pattern to match: st.session_state["route"] = "some_route"
ASSIGN_RE = re.compile(
    r'^(?P<prefix>\s*)st\.session_state\[\s*[\'"]route[\'"]\s*\]\s*=\s*[\'"](?P<route>[^\'"]+)[\'"]\s*(?:#.*)?$',
    flags=re.MULTILINE
)

# Pattern to match rerun lines immediately following assignment
RERUN_RE = re.compile(
    r'^\s*(?:safe_rerun\(\)|_safe_rerun\(\)|st\.experimental_rerun\(\))\s*(?:#.*)?$',
    flags=re.MULTILINE
)

# Import line to ensure exists
IMPORT_LINE = "from utils.router import navigate\n"

# Files to skip (virtualenv, .venv, hidden .git, migrations etc.)
SKIP_DIRS = {".git", "__pycache__", "venv", ".venv", "env", "node_modules", "build", "dist", ".idea", ".pytest_cache"}

def should_skip_path(p: Path) -> bool:
    for part in p.parts:
        if part in SKIP_DIRS:
            return True
    return False

def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text

    # Find all assignments of the exact form st.session_state["route"] = "xxx"
    # We'll perform replacements line-by-line to keep context for removing rerun lines.
    lines = text.splitlines(keepends=True)
    i = 0
    changed = False
    out_lines = []

    while i < len(lines):
        line = lines[i]
        m = ASSIGN_RE.match(line)
        if m:
            indent = m.group("prefix") or ""
            route = m.group("route")
            # Build replacement: navigate("route") with same indent
            replacement = f'{indent}navigate("{route}")\n'
            out_lines.append(replacement)
            changed = True
            i += 1
            # If the next non-empty line is a rerun call, skip it
            # (remove it because navigate will rerun)
            if i < len(lines):
                # peek next few lines while they are only whitespace or comments
                j = i
                while j < len(lines) and lines[j].strip() == "":
                    out_lines.append(lines[j])  # keep blank lines
                    j += 1
                if j < len(lines):
                    next_line = lines[j]
                    if RERUN_RE.match(next_line):
                        # skip this rerun line
                        i = j + 1
                    else:
                        i = j
                else:
                    i = j
            continue
        else:
            out_lines.append(line)
            i += 1

    new_text = "".join(out_lines)

    # If changed, ensure import exists; if not, add it near top (after shebang / encoding / docstring / initial comments)
    if changed:
        if IMPORT_LINE.strip() not in new_text:
            # find insertion point: after initial module docstring or after initial block of comments/imports
            insert_at = 0
            # skip shebang
            if new_text.startswith("#!"):
                first_nl = new_text.find("\n")
                insert_at = first_nl + 1 if first_nl >= 0 else 0
            # if file starts with a triple-quoted docstring, insert after it
            triple_doc_match = re.match(r'(\s*(""".*?"""|\'\'\'.*?\'\'\'))', new_text, flags=re.DOTALL)
            if triple_doc_match:
                insert_at = triple_doc_match.end()
            # Otherwise, just prepend import after any initial newline
            new_text = new_text[:insert_at] + IMPORT_LINE + new_text[insert_at:]

    if changed and new_text != original:
        # backup
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
        path.write_text(new_text, encoding="utf-8")
        print(f"Modified: {path}  (backup: {bak})")
        return True

    return False

def main():
    print(f"Scanning for Python files under {ROOT} ...")
    modified = []
    for glob in INCLUDE_GLOBS:
        for p in ROOT.glob(glob):
            if p.is_file() and not should_skip_path(p):
                try:
                    if process_file(p):
                        modified.append(p)
                except Exception as e:
                    print(f"Error processing {p}: {e}")
    if modified:
        print("\nDone. Modified files:")
        for m in modified:
            print(" -", m)
        print("\nBackups saved with .bak extension. Review changes, run tests, and commit.")
    else:
        print("No matching assignments found (no files changed).")

if __name__ == "__main__":
    main()
