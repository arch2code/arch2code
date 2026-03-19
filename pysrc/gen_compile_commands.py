#!/usr/bin/env python3

import argparse
import json
import os
import shlex
import sys
from typing import Iterable


def _iter_lines(path: str) -> Iterable[str]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            yield line.rstrip("\n")


def _looks_like_compile(tokens: list[str], compilers: set[str]) -> bool:
    if not tokens:
        return False
    exe = os.path.basename(tokens[0])
    if exe not in compilers:
        return False
    return "-c" in tokens


def _extract_source(tokens: list[str]) -> str | None:
    for i, t in enumerate(tokens):
        if t == "-c" and i + 1 < len(tokens):
            return tokens[i + 1]
    for t in tokens:
        if t.startswith("-c") and len(t) > 2:
            return t[2:]
    return None


def _is_verilator_command(tokens: list[str]) -> bool:
    return "-DVERILATOR" in tokens


def _wants_verilator_flags_for_file(path: str) -> bool:
    # Prefer VERILATOR flags only for the verilator wrapper sources.
    norm = path.replace("\\", "/")
    return "/verif/vl_wrap/" in norm


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Generate compile_commands.json by parsing `make -n` output. "
            "Supports merging multiple make outputs (e.g. normal + VL_DUT=1) "
            "while keeping at most one entry per source file."
        )
    )
    ap.add_argument(
        "input",
        nargs="+",
        help="One or more files containing captured `make -n` output",
    )
    ap.add_argument("output", help="Path to write compile_commands.json")
    ap.add_argument(
        "--directory",
        default=None,
        help="Working directory to record in compile_commands (default: cwd)",
    )
    ap.add_argument(
        "--compiler",
        action="append",
        default=["clang++", "g++"],
        help="Compiler executable names to match (repeatable)",
    )
    ap.add_argument(
        "--summary",
        action="store_true",
        help="Print a short summary to stdout",
    )
    args = ap.parse_args(argv)

    directory = args.directory or os.getcwd()
    compilers = set(args.compiler)

    candidates_by_file: dict[str, list[dict[str, str]]] = {}
    seen: set[tuple[str, str]] = set()

    for in_path in args.input:
        for line in _iter_lines(in_path):
            line = line.strip()
            if not line:
                continue
            # Only compile steps; ignore mkdir/touch/arch2code invocations.
            if " -c " not in line and not line.startswith(("clang++ ", "g++ ")):
                continue

            try:
                tokens = shlex.split(line)
            except ValueError:
                continue

            if not _looks_like_compile(tokens, compilers):
                continue

            src = _extract_source(tokens)
            if not src:
                continue

            src_path = os.path.normpath(src)
            cmd = " ".join(shlex.quote(t) for t in tokens)

            key = (src_path, cmd)
            if key in seen:
                continue
            seen.add(key)

            entry = {
                "directory": directory,
                "command": cmd,
                "file": src_path,
            }
            candidates_by_file.setdefault(src_path, []).append(entry)

    chosen: list[dict[str, str]] = []
    for src_path in sorted(candidates_by_file.keys()):
        entries = candidates_by_file[src_path]
        if len(entries) == 1:
            chosen.append(entries[0])
            continue

        parsed: list[tuple[dict[str, str], bool]] = []
        for e in entries:
            try:
                toks = shlex.split(e["command"])
            except ValueError:
                toks = []
            parsed.append((e, _is_verilator_command(toks)))

        prefer_v = _wants_verilator_flags_for_file(src_path)
        if prefer_v:
            v = [e for (e, is_v) in parsed if is_v]
            chosen.append(v[0] if v else entries[0])
        else:
            nv = [e for (e, is_v) in parsed if not is_v]
            chosen.append(nv[0] if nv else entries[0])

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(chosen, f, indent=2)
        f.write("\n")

    if args.summary:
        first = chosen[0]["file"] if chosen else None
        print(f"entries {len(chosen)}")
        print(f"first_file {first}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
