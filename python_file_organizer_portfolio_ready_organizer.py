#!/usr/bin/env python3
"""
organizer.py — Simple, portfolio‑ready file organizer.

Features
- Organizes files by extension into category folders (configurable via JSON).
- Safe by default: dry‑run preview, confirmation prompt.
- Handles name collisions by auto‑renaming ("filename (2).ext").
- Optional recursive scan of subdirectories.
- Skips hidden files/folders by default (can include with a flag).
- Prints a clear summary.

Usage examples
  # Preview what would happen (recommended first)
  python organizer.py --source ~/Downloads --dry-run

  # Actually move files in place under ~/Downloads
  python organizer.py --source ~/Downloads --yes

  # Organize recursively and include hidden files
  python organizer.py -s . --recursive --include-hidden --yes

  # Use a custom rules JSON (see --write-default-rules to generate a template)
  python organizer.py -s ~/Inbox --rules rules.json --yes

Exit codes
  0 success, 1 error (bad args), 2 runtime issue (some operations failed)

Author: (You)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

# ---- Default categorization rules (extension -> folder name) ----
DEFAULT_RULES: Dict[str, str] = {
    # Documents
    ".pdf": "docs",
    ".doc": "docs", ".docx": "docs", ".odt": "docs",
    ".txt": "docs", ".md": "docs", ".rtf": "docs",
    ".xls": "sheets", ".xlsx": "sheets", ".csv": "sheets",
    ".ppt": "slides", ".pptx": "slides",

    # Images
    ".jpg": "images", ".jpeg": "images", ".png": "images", ".gif": "images",
    ".tif": "images", ".tiff": "images", ".bmp": "images", ".webp": "images",

    # Audio / Video
    ".mp3": "audio", ".wav": "audio", ".flac": "audio", ".m4a": "audio",
    ".mp4": "video", ".mov": "video", ".mkv": "video", ".avi": "video",

    # Archives
    ".zip": "archives", ".rar": "archives", ".7z": "archives", ".tar": "archives", ".gz": "archives",

    # Code / Data
    ".py": "code", ".ipynb": "code", ".js": "code", ".ts": "code", ".json": "data",
    ".yml": "config", ".yaml": "config", ".toml": "config",
}

HIDDEN_PATTERN = re.compile(r"(^\.|/\.)")


@dataclass
class MovePlan:
    src: Path
    dst: Path


def load_rules(path: Path | None) -> Dict[str, str]:
    if path is None:
        return DEFAULT_RULES
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # normalize keys to ".ext" lower-case
        normalized = {}
        for k, v in data.items():
            k = k.strip().lower()
            if not k.startswith("."):
                k = "." + k
            normalized[k] = v
        return normalized
    except Exception as e:
        raise SystemExit(f"Failed to load rules from {path}: {e}")


def write_default_rules(path: Path) -> None:
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing rules file: {path}")
    with path.open("w", encoding="utf-8") as f:
        json.dump(DEFAULT_RULES, f, indent=2, ensure_ascii=False)


def iter_files(root: Path, recursive: bool, include_hidden: bool) -> Iterable[Path]:
    if recursive:
        for p in root.rglob("*"):
            if p.is_file():
                if not include_hidden and HIDDEN_PATTERN.search(str(p.relative_to(root))):
                    continue
                yield p
    else:
        for p in root.iterdir():
            if p.is_file():
                if not include_hidden and p.name.startswith("."):
                    continue
                yield p


def categorize(path: Path, rules: Dict[str, str], unknown: str) -> str:
    ext = path.suffix.lower()
    return rules.get(ext, unknown)


def unique_destination(dst_dir: Path, name: str) -> Path:
    """Return a non-colliding destination like "file (2).ext" if needed."""
    candidate = dst_dir / name
    if not candidate.exists():
        return candidate
    stem = Path(name).stem
    suffix = Path(name).suffix
    i = 2
    while True:
        candidate = dst_dir / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def plan_moves(source: Path, dest: Path, recursive: bool, include_hidden: bool,
               rules: Dict[str, str], unknown_folder: str) -> List[MovePlan]:
    moves: List[MovePlan] = []
    for file in iter_files(source, recursive=recursive, include_hidden=include_hidden):
        rel_parent = dest
        category = categorize(file, rules, unknown_folder)
        target_dir = rel_parent / category
        target_dir.mkdir(parents=True, exist_ok=True)
        dst = unique_destination(target_dir, file.name)
        # Skip if src and dst are the same path
        if file.resolve() == dst.resolve():
            continue
        moves.append(MovePlan(src=file, dst=dst))
    return moves


def apply_moves(moves: List[MovePlan]) -> Tuple[int, int, List[str]]:
    ok = 0
    failed = 0
    errors: List[str] = []
    for m in moves:
        try:
            m.dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(m.src), str(m.dst))
            ok += 1
        except Exception as e:
            failed += 1
            errors.append(f"Failed: {m.src} -> {m.dst} ({e})")
    return ok, failed, errors


def human_preview(moves: List[MovePlan], max_show: int = 50) -> str:
    lines = [f"Planned moves: {len(moves)} file(s)"]
    for i, m in enumerate(moves[:max_show], 1):
        lines.append(f"  {i:>3}. {m.src}  ->  {m.dst}")
    if len(moves) > max_show:
        lines.append(f"  ... ({len(moves) - max_show} more)")
    return "\n".join(lines)


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Organize files by extension into category folders.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--source", "-s", type=Path, required=True, help="Folder to organize")
    p.add_argument("--dest", "-d", type=Path, help="Destination root (default: source)")
    p.add_argument("--rules", type=Path, help="Path to JSON rules {'.ext': 'folder'}")
    p.add_argument("--unknown-folder", default="others", help="Folder for unknown extensions")
    p.add_argument("--recursive", action="store_true", help="Scan subdirectories recursively")
    p.add_argument("--include-hidden", action="store_true", help="Include hidden files/folders")
    p.add_argument("--dry-run", action="store_true", help="Preview actions without moving files")
    p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt and proceed")
    p.add_argument("--write-default-rules", type=Path, metavar="FILE",
                   help="Write a default rules JSON to FILE and exit")
    return p.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    if args.write_default_rules:
        write_default_rules(args.write_default_rules)
        print(f"Wrote default rules to {args.write_default_rules}")
        return 0

    source: Path = args.source.expanduser().resolve()
    dest: Path = (args.dest or source).expanduser().resolve()

    if not source.exists() or not source.is_dir():
        print(f"Error: source not found or not a directory: {source}", file=sys.stderr)
        return 1

    rules = load_rules(args.rules)

    moves = plan_moves(
        source=source,
        dest=dest,
        recursive=bool(args.recursive),
        include_hidden=bool(args.include_hidden),
        rules=rules,
        unknown_folder=args.unknown_folder,
    )

    if not moves:
        print("Nothing to do — no files matched.")
        return 0

    print(human_preview(moves))

    if args.dry_run:
        print("\nDry-run: no files were moved.")
        return 0

    if not args.yes:
        try:
            proceed = input("\nProceed to move these files? [y/N]: ").strip().lower() == "y"
        except EOFError:
            proceed = False
        if not proceed:
            print("Aborted.")
            return 0

    ok, failed, errors = apply_moves(moves)

    print(f"\nDone. Moved: {ok}, Failed: {failed}")
    if errors:
        print("\nErrors:")
        for e in errors:
            print("  -", e)
        return 2 if failed else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
