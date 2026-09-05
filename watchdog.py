"""
watchdog.py — file watchdog for deployed agent workspaces

Monitors a directory an agent is running in. If files change, copies
them into a timestamped review folder for human inspection. If nothing
changes, stays quiet and cleans up old empty snapshots.

Zero AI involved. Dumb observer. Can't be talked out of noticing things.

Usage:
    python watchdog.py <directory>
    python watchdog.py <directory> --interval 30    # check every 30s (default 60)
    python watchdog.py <directory> --keep 10        # keep last 10 reviews (default 20)
    python watchdog.py <directory> --clean          # delete all existing reviews and exit

Output:
    watchdog_data/reviews/<timestamp>/
        CHANGES.md          summary of what changed
        before/             copies of modified files before the change
        after/              copies of added or modified files after
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

WATCH_DATA = Path(__file__).parent / "watchdog_data"
REVIEWS_DIR = WATCH_DATA / "reviews"
LAST_DIR = WATCH_DATA / "last"       # snapshot of files at previous check
STATE_FILE = WATCH_DATA / "state.json"

# File extensions that mean the agent touched its own code — red alert
SELF_REWRITE_EXTENSIONS = {".py", ".ps1", ".bat", ".cmd", ".js", ".ts"}


# ── console encoding ─────────────────────────────────────────────────
# Many Windows consoles default to cp1252, which cannot print the tick and
# warning symbols below. Printing one there raises UnicodeEncodeError and
# kills the watcher on its first check. Try to switch the console to UTF-8;
# if that is not possible, fall back to plain ASCII markers.

def _use_unicode() -> bool:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        return True
    except Exception:
        enc = (getattr(sys.stdout, "encoding", "") or "").lower()
        return enc.replace("-", "") in ("utf8", "utf8mb4")


UNICODE_OK = _use_unicode()

OK_MARK    = "✓" if UNICODE_OK else "OK "      # ✓
WARN_MARK  = "⚠ " if UNICODE_OK else "!! "     # ⚠
ALERT_MARK = "\U0001f6a8" if UNICODE_OK else "***"  # 🚨


# ── hashing and scanning ─────────────────────────────────────────────

def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return "UNREADABLE"


def scan(root: Path) -> dict[str, str]:
    """Return {relative_path_str: sha256} for every file under root,
    excluding our own watchdog_data directory."""
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        # Never watch our own output
        try:
            path.relative_to(WATCH_DATA)
            continue
        except ValueError:
            pass
        rel = path.relative_to(root).as_posix()
        result[rel] = hash_file(path)
    return result


def diff(before: dict[str, str], after: dict[str, str]) -> dict[str, list[str]]:
    added = sorted(k for k in after if k not in before)
    deleted = sorted(k for k in before if k not in after)
    modified = sorted(k for k in after if k in before and before[k] != after[k])
    return {"added": added, "deleted": deleted, "modified": modified}


def has_changes(d: dict[str, list]) -> bool:
    return bool(d["added"] or d["deleted"] or d["modified"])


# ── snapshot management ──────────────────────────────────────────────

def save_last(root: Path, state: dict[str, str]) -> None:
    """Update LAST_DIR to match current state without deleting the folder
    (Windows sometimes holds locks that make rmtree fail)."""
    LAST_DIR.mkdir(parents=True, exist_ok=True)

    # Remove stale files no longer in current state
    for existing in list(LAST_DIR.rglob("*")):
        if existing.is_file():
            rel = existing.relative_to(LAST_DIR).as_posix()
            if rel not in state:
                try:
                    existing.unlink()
                except OSError:
                    pass

    # Copy/overwrite current files
    for rel in state:
        src = root / rel.replace("/", os.sep)
        dst = LAST_DIR / rel.replace("/", os.sep)
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
        except OSError:
            pass


def save_review(
    root: Path,
    changes: dict[str, list[str]],
    timestamp: str,
) -> Path:
    review_dir = REVIEWS_DIR / timestamp
    review_dir.mkdir(parents=True, exist_ok=True)

    # After: copies of added/modified files
    for rel in changes["added"] + changes["modified"]:
        src = root / rel.replace("/", os.sep)
        dst = review_dir / "after" / rel.replace("/", os.sep)
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        except OSError:
            pass

    # Before: copies of modified files from last snapshot
    for rel in changes["modified"]:
        src = LAST_DIR / rel.replace("/", os.sep)
        if src.exists():
            dst = review_dir / "before" / rel.replace("/", os.sep)
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            except OSError:
                # File vanished or got locked between the exists() check and
                # the copy. Routine when watching a folder something else is
                # actively writing to. Never worth dying over.
                pass

    # CHANGES.md
    self_rewrites = [
        f for f in changes["added"] + changes["modified"]
        if Path(f).suffix in SELF_REWRITE_EXTENSIONS
    ]

    lines = [f"# Changes detected — {timestamp}", ""]

    if self_rewrites:
        lines += [
            "## !! AGENT MODIFIED ITS OWN CODE !!",
            "",
            "The following script files changed. Review carefully.",
            "",
        ]
        for f in self_rewrites:
            lines.append(f"  {f}")
        lines.append("")

    lines += [f"## Added  ({len(changes['added'])})"]
    for f in changes["added"]:
        lines.append(f"  + {f}")

    lines += ["", f"## Modified  ({len(changes['modified'])})"]
    for f in changes["modified"]:
        tag = "  !! " if f in self_rewrites else "  ~ "
        lines.append(f"{tag}{f}")

    lines += ["", f"## Deleted  ({len(changes['deleted'])})"]
    for f in changes["deleted"]:
        lines.append(f"  - {f}")

    lines += [
        "",
        "---",
        "Files are in after/ (new versions) and before/ (previous versions).",
        "Delete this folder once reviewed, or leave it as a record.",
    ]

    (review_dir / "CHANGES.md").write_text("\n".join(lines), encoding="utf-8")
    return review_dir


def trim_reviews(keep: int) -> None:
    """Delete oldest review folders if we have more than `keep`."""
    existing = sorted(REVIEWS_DIR.iterdir()) if REVIEWS_DIR.exists() else []
    for old in existing[:-keep]:
        shutil.rmtree(old, ignore_errors=True)


# ── display ───────────────────────────────────────────────────────────

def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def print_status(label: str, detail: str = "") -> None:
    print(f"[{ts()}] {label}", end="")
    if detail:
        print(f"  {detail}", end="")
    print()


# ── main loop ─────────────────────────────────────────────────────────

def watch(root: Path, interval: int, keep: int) -> None:
    WATCH_DATA.mkdir(exist_ok=True)
    REVIEWS_DIR.mkdir(exist_ok=True)

    print(f"Watching : {root}")
    print(f"Interval : {interval}s")
    print(f"Reviews  : {REVIEWS_DIR}")
    print(f"Press Ctrl-C to stop.")
    print("-" * 60)

    # Baseline
    print_status("Scanning baseline...")
    current = scan(root)
    save_last(root, current)
    previous = current
    print_status(f"Baseline: {len(current)} files")

    quiet_checks = 0

    consecutive_errors = 0

    while True:
        time.sleep(interval)

        # A watchdog must not die quietly. Anything unexpected gets reported
        # and the loop carries on — a watcher that stopped without telling you
        # is worse than no watcher, because you go on trusting it.
        try:
            current = scan(root)
            changes = diff(previous, current)
        except Exception as exc:
            consecutive_errors += 1
            print_status(f"!! Error during scan ({type(exc).__name__}: {exc})",
                         f"— still watching, {consecutive_errors} in a row")
            if consecutive_errors >= 10:
                print_status("!! 10 consecutive failures — stopping.")
                print("   Something is wrong with the watched folder or this "
                      "script.\n   The audit or agent you were watching is "
                      "unaffected.")
                return
            continue
        consecutive_errors = 0

        if not has_changes(changes):
            quiet_checks += 1
            print_status(
                f"{OK_MARK} No changes",
                f"(quiet for {quiet_checks} check{'s' if quiet_checks != 1 else ''})"
            )
            save_last(root, current)
            previous = current
            continue

        # Changes found
        quiet_checks = 0
        n = len(changes["added"]) + len(changes["modified"]) + len(changes["deleted"])
        self_rewrites = [
            f for f in changes["added"] + changes["modified"]
            if Path(f).suffix in SELF_REWRITE_EXTENSIONS
        ]

        if self_rewrites:
            print_status(f"{ALERT_MARK} AGENT MODIFIED ITS OWN CODE "
                         f"— {n} file(s) changed")
            for f in self_rewrites:
                print(f"        !! {f}")
        else:
            print_status(f"{WARN_MARK} Changes detected — {n} file(s)")

        for f in changes["added"]:
            print(f"       + {f}")
        for f in changes["modified"]:
            print(f"       ~ {f}")
        for f in changes["deleted"]:
            print(f"       - {f}")

        try:
            review_dir = save_review(root, changes, stamp())
            print(f"       → Review saved: {review_dir}")
            trim_reviews(keep)
        except Exception as exc:
            # Saving the review failed, but we already printed WHAT changed
            # above, which is the part that matters. Say so and keep going.
            print(f"       !! Could not save review copies "
                  f"({type(exc).__name__}: {exc})")
            print(f"       !! The change list above is still accurate.")

        save_last(root, current)
        previous = current


# ── entry point ───────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Agent workspace file watchdog")
    p.add_argument("directory", help="Directory to watch")
    p.add_argument("--interval", type=int, default=60,
                   help="Seconds between checks (default 60)")
    p.add_argument("--keep", type=int, default=20,
                   help="Max review folders to keep (default 20)")
    p.add_argument("--clean", action="store_true",
                   help="Delete all existing review folders and exit")
    args = p.parse_args()

    root = Path(args.directory).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory.")
        sys.exit(1)

    if args.clean:
        if REVIEWS_DIR.exists():
            shutil.rmtree(REVIEWS_DIR)
            print(f"Cleared: {REVIEWS_DIR}")
        else:
            print("Nothing to clean.")
        return

    try:
        watch(root, args.interval, args.keep)
    except KeyboardInterrupt:
        print(f"\n[{ts()}] Stopped.")


if __name__ == "__main__":
    main()
