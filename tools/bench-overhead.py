#!/usr/bin/env python3
"""Profile the LSP overhead breakdown.

Measures what contributes to the ~1s baseline:
- Process startup / initialize
- parse_text (parsing only, no type-checking)
- check_text with full reuse (parse + incremental skip)
- check_text with no reuse (parse + full type-check)
- Diagnostic serialization / send overhead

Usage:
    tools/bench-overhead.py
"""

import json
import os
import select
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location("test_lsp", os.path.join(os.path.dirname(__file__), "test-lsp.py"))
mod = module_from_spec(spec)
spec.loader.exec_module(mod)
LSPClient = mod.LSPClient

BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


def timed_drain(client, timeout=10):
    """Drain diagnostics, return (time_to_first_ms, total_ms, diag_count, batches)."""
    t0 = time.monotonic()
    first_ms = None
    diag_raw = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([client.proc.stdout], [], [], 0.5)
        if ready:
            msg = client.read_message(timeout=1)
            if msg and msg.get("method") == "textDocument/publishDiagnostics":
                if first_ms is None:
                    first_ms = (time.monotonic() - t0) * 1000
                diag_raw.append(msg)
                deadline = time.monotonic() + 1
    total_ms = (time.monotonic() - t0) * 1000
    n = sum(len(d.get("params", {}).get("diagnostics", [])) for d in diag_raw)
    return first_ms or 0, total_ms, n, len(diag_raw)


def send_change(client, uri, version, text):
    client.send_notification("textDocument/didChange", {
        "textDocument": {"uri": uri, "version": version},
        "contentChanges": [{"text": text}]
    })


def main():
    opam_prefix = subprocess.run(
        ["opam", "var", "prefix"], capture_output=True, text=True
    ).stdout.strip()
    installed_lib = os.path.join(opam_prefix, "lib", "lambdapi", "lib_root")
    test_dir = os.path.abspath("test")
    map_dirs = [f"Stdlib:{installed_lib}/Stdlib"]
    log_file = os.path.join(test_dir, ".bench-overhead.log")
    if os.path.exists(log_file):
        os.unlink(log_file)

    print(f"{BOLD}LSP Overhead Profiling{RESET}\n")

    # --- File size scaling ---
    sources = {}

    sources["empty"] = "// empty\n"

    sources["1 cmd"] = "symbol A : TYPE;\n"

    sources["3 cmds"] = (
        "require open Stdlib.Set Stdlib.HOL Stdlib.Eq;\n"
        "symbol A : Set;\n"
        "symbol f : τ A → τ A;\n"
    )

    sources["10 cmds"] = sources["3 cmds"]
    for i in range(7):
        sources["10 cmds"] += f"symbol s{i} : TYPE;\n"

    sources["50 cmds"] = sources["3 cmds"]
    for i in range(47):
        sources["50 cmds"] += f"symbol s{i} : TYPE;\n"

    sources["100 cmds"] = sources["3 cmds"]
    for i in range(97):
        sources["100 cmds"] += f"symbol s{i} : TYPE;\n"

    sources["test.lp"] = open(os.path.join(test_dir, "test.lp")).read()

    print(f"{BOLD}A. Cold open (process start + initialize + didOpen + check){RESET}")
    print(f"{'file':>12s}  {'lines':>5s}  {'bytes':>6s}  {'first':>7s}  {'total':>7s}  {'diags':>5s}")
    print(f"{'─'*12}  {'─'*5}  {'─'*6}  {'─'*7}  {'─'*7}  {'─'*5}")

    cold_times = {}
    for label, src in sources.items():
        # Fresh LSP process for each to measure cold start
        tmp = os.path.join(test_dir, "_overhead.lp")
        with open(tmp, "w") as f:
            f.write(src)
        uri = "file://" + tmp

        t_start = time.monotonic()
        c = LSPClient(lib_root=test_dir, map_dirs=map_dirs, log_file=log_file,
                      standard_lsp=True)
        c.start()
        t_started = time.monotonic()

        c.initialize("file://" + test_dir)
        c.send_notification("initialized", {})
        t_init = time.monotonic()

        c.open_file(uri, src)
        first_ms, total_ms, n_diags, _ = timed_drain(c)

        startup_ms = (t_started - t_start) * 1000
        init_ms = (t_init - t_started) * 1000
        cold_times[label] = first_ms

        lines = len(src.splitlines())
        print(f"{label:>12s}  {lines:5d}  {len(src):6d}  {first_ms:6.0f}ms  {total_ms:6.0f}ms  {n_diags:5d}")

        c.send_notification("textDocument/didClose", {"textDocument": {"uri": uri}})
        c.stop()
        os.unlink(tmp)

    # --- Incremental reuse overhead ---
    print(f"\n{BOLD}B. Incremental reuse (edit-at-end, measures parse + reuse overhead){RESET}")
    print(f"{'file':>12s}  {'first':>7s}  {'total':>7s}  {'reuse':>10s}")
    print(f"{'─'*12}  {'─'*7}  {'─'*7}  {'─'*10}")

    for label, src in sources.items():
        if label == "empty":
            continue
        tmp = os.path.join(test_dir, "_overhead.lp")
        with open(tmp, "w") as f:
            f.write(src)
        uri = "file://" + tmp

        c = LSPClient(lib_root=test_dir, map_dirs=map_dirs, log_file=log_file,
                      standard_lsp=True)
        c.start()
        c.initialize("file://" + test_dir)
        c.send_notification("initialized", {})
        c.open_file(uri, src)
        timed_drain(c)  # cold open, settle

        # Now edit at end (should reuse everything)
        new_src = src + "// appended\n"
        send_change(c, uri, 2, new_src)
        first_ms, total_ms, n_diags, _ = timed_drain(c)

        # Get reuse info from log
        reuse = "?"
        if os.path.exists(log_file):
            with open(log_file) as f:
                lines = f.readlines()
            for line in reversed(lines):
                if "reusing" in line:
                    reuse = line.strip().split("reusing ")[-1] if "reusing " in line else "?"
                    break

        print(f"{label:>12s}  {first_ms:6.0f}ms  {total_ms:6.0f}ms  {reuse:>10s}")

        c.send_notification("textDocument/didClose", {"textDocument": {"uri": uri}})
        c.stop()
        os.unlink(tmp)

    # --- No-op change overhead ---
    print(f"\n{BOLD}C. No-op change (identical text, measures pure overhead){RESET}")
    print(f"{'file':>12s}  {'first':>7s}  {'total':>7s}")
    print(f"{'─'*12}  {'─'*7}  {'─'*7}")

    for label, src in sources.items():
        if label == "empty":
            continue
        tmp = os.path.join(test_dir, "_overhead.lp")
        with open(tmp, "w") as f:
            f.write(src)
        uri = "file://" + tmp

        c = LSPClient(lib_root=test_dir, map_dirs=map_dirs, log_file=log_file,
                      standard_lsp=True)
        c.start()
        c.initialize("file://" + test_dir)
        c.send_notification("initialized", {})
        c.open_file(uri, src)
        timed_drain(c)

        # No-op: send same text
        send_change(c, uri, 2, src)
        first_ms, total_ms, _, _ = timed_drain(c)

        print(f"{label:>12s}  {first_ms:6.0f}ms  {total_ms:6.0f}ms")

        c.send_notification("textDocument/didClose", {"textDocument": {"uri": uri}})
        c.stop()
        os.unlink(tmp)

    # --- Process startup cost ---
    print(f"\n{BOLD}D. Process startup & initialize (no file opened){RESET}")
    times = []
    for _ in range(3):
        t0 = time.monotonic()
        c = LSPClient(lib_root=test_dir, map_dirs=map_dirs, log_file=log_file,
                      standard_lsp=True)
        c.start()
        t1 = time.monotonic()
        c.initialize("file://" + test_dir)
        c.send_notification("initialized", {})
        t2 = time.monotonic()
        c.stop()
        startup = (t1 - t0) * 1000
        init = (t2 - t1) * 1000
        times.append((startup, init))
    avg_startup = sum(t[0] for t in times) / len(times)
    avg_init = sum(t[1] for t in times) / len(times)
    print(f"  process spawn:  {avg_startup:.0f}ms")
    print(f"  initialize:     {avg_init:.0f}ms")
    print(f"  total:          {avg_startup + avg_init:.0f}ms")

    # --- Summary ---
    print(f"\n{BOLD}E. Summary{RESET}")
    print(f"  Process startup + init: ~{avg_startup + avg_init:.0f}ms")
    if "1 cmd" in cold_times:
        print(f"  Minimum check (1 cmd):  ~{cold_times['1 cmd']:.0f}ms")
    if "test.lp" in cold_times:
        print(f"  Full test.lp check:     ~{cold_times['test.lp']:.0f}ms")
    print(f"\n  The gap between init ({avg_startup + avg_init:.0f}ms) and first check "
          f"({cold_times.get('1 cmd', 0):.0f}ms)")
    print(f"  is the per-check overhead (parse_text + state setup).")


if __name__ == "__main__":
    main()
