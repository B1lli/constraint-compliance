#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Refuse commits that carry AI-assistant provenance markers.

Scans staged files (default), a commit message (--message FILE), or the whole
working tree (--all). Exits 1 and lists every hit when a forbidden marker is
found. Product names of agent hosts that the skill has to mention in order to
be usable (see ALLOWED_PHRASES) are masked before matching.

Patterns are written with bracketed first letters so this file does not match
itself.
"""
import os, re, subprocess, sys

ALLOWED_PHRASES = [
    r"[C]laude Code",            # host platform this skill installs into
    r"[C]laude Managed Agents",  # prior-art product compared in docs/METHOD
    r"\.[c]laude/",              # ~/.claude/skills install path
]

FORBIDDEN = [
    (r"[C]o-[A]uthored-[B]y", "co-author trailer"),
    (r"[G]enerated with", "generated-with watermark"),
    (r"[A]nthropic", "vendor name"),
    (r"noreply@[a]nthropic", "vendor e-mail"),
    (r"[F]able", "model name"),
    (r"[M]ythos", "model name"),
    (r"\b[O]pus\b", "model name"),
    (r"\b[S]onnet\b", "model name"),
    (r"\b[H]aiku\b", "model name"),
    (r"[c]laude-[a-z0-9-]+", "model id"),
    (r"[C]laude", "assistant name outside allowed product names"),
    ("\U0001F916", "robot emoji watermark"),  # written as an escape so this file does not match itself
    (r"[L]angcore", "undisclosed company name"),
    (r"[N]oumi", "undisclosed product name"),
]

TEXT_EXT = {".md", ".py", ".txt", ".json", ".yml", ".yaml", ".cff", ".toml", ".sh", ""}


def is_text(path):
    _, ext = os.path.splitext(path)
    return ext.lower() in TEXT_EXT


def scan_text(text, label):
    masked = text
    for pat in ALLOWED_PHRASES:
        masked = re.sub(pat, lambda m: "░" * len(m.group(0)), masked)
    hits = []
    for pat, why in FORBIDDEN:
        for m in re.finditer(pat, masked, re.I if why != "assistant name outside allowed product names" else 0):
            line = masked.count("\n", 0, m.start()) + 1
            hits.append("%s:%d: %s (%s)" % (label, line, text.splitlines()[line - 1].strip()[:100], why))
    return hits


def staged_files():
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\n") if p]


def staged_content(path):
    return subprocess.run(["git", "show", ":" + path], capture_output=True, check=True).stdout.decode("utf-8", "replace")


def tracked_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\n") if p]


def main(argv):
    hits = []
    if "--message" in argv:
        path = argv[argv.index("--message") + 1]
        with open(path, encoding="utf-8", errors="replace") as f:
            hits += scan_text(f.read(), "commit message")
    elif "--all" in argv:
        for p in tracked_files():
            if is_text(p) and os.path.isfile(p):
                with open(p, encoding="utf-8", errors="replace") as f:
                    hits += scan_text(f.read(), p)
    else:
        for p in staged_files():
            if is_text(p):
                hits += scan_text(staged_content(p), p)
    if hits:
        print("check_markers: forbidden provenance markers found, refusing.")
        for h in hits:
            print("  " + h)
        return 1
    print("check_markers: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
