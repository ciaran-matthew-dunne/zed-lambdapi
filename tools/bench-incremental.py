#!/usr/bin/env python3
"""Benchmark incremental checking and debouncing performance.

Simulates editing scenarios to measure how the LSP handles:
1. Initial open (cold check)
2. Edits at the end of the file (incremental reuse)
3. Edits at the beginning (no reuse possible)
4. Rapid successive edits (debouncing)

Usage:
    tools/bench-incremental.py        # run benchmarks
    tools/bench-incremental.py -v     # verbose
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

BASE_SOURCE = """\
require open Stdlib.Set Stdlib.HOL Stdlib.Eq;

// Some declarations
constant symbol A : Set;
symbol f : τ A → τ A;
symbol g : τ A → τ A → τ A;
rule g $x $x ↪ f $x;

symbol h : τ A → τ A;
rule h (f $x) ↪ g $x $x;
"""


def send_change(client, uri, version, text):
    """Send didChange notification."""
    client.send_notification("textDocument/didChange", {
        "textDocument": {"uri": uri, "version": version},
        "contentChanges": [{"text": text}]
    })


def drain_and_time(client, timeout=10):
    """Drain diagnostics. Returns (total_ms, first_diag_ms, diag_count)."""
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
                deadline = time.monotonic() + 1  # reset on activity
    total_ms = (time.monotonic() - t0) * 1000
    diags = []
    for d in diag_raw:
        diags.extend(d.get("params", {}).get("diagnostics", []))
    return total_ms, first_ms or 0, len(diags)


def fmt_result(total_ms, first_ms, n_diags, extra=""):
    return (f"  {first_ms:7.0f}ms check, {total_ms:7.0f}ms total  "
            f"({n_diags} diags){extra}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    opam_prefix = subprocess.run(
        ["opam", "var", "prefix"], capture_output=True, text=True
    ).stdout.strip()
    installed_lib = os.path.join(opam_prefix, "lib", "lambdapi", "lib_root")
    test_dir = os.path.abspath("test")
    map_dirs = [f"Stdlib:{installed_lib}/Stdlib"]
    log_file = os.path.join(test_dir, ".bench-incr.log")

    # Clear old log
    if os.path.exists(log_file):
        os.unlink(log_file)

    # Write temp file
    tmp_path = os.path.join(test_dir, "_bench_incr.lp")
    with open(tmp_path, "w") as f:
        f.write(BASE_SOURCE)
    uri = "file://" + tmp_path

    print(f"{BOLD}Incremental Checking & Debounce Benchmark{RESET}\n")

    client = LSPClient(lib_root=test_dir, map_dirs=map_dirs, log_file=log_file,
                       standard_lsp=True)
    client.start()

    # Initialize
    resp = client.initialize("file://" + test_dir)
    if not resp or not resp.get("result", {}).get("capabilities"):
        print(f"{RED}Failed to initialize{RESET}")
        client.stop()
        sys.exit(1)
    client.send_notification("initialized", {})

    results = []  # (name, first_ms)

    # --- 1. Cold open ---
    print(f"{BOLD}1. Cold open{RESET}")
    client.open_file(uri, BASE_SOURCE)
    total_ms, first_ms, n_diags = drain_and_time(client)
    results.append(("cold open", first_ms))
    print(fmt_result(total_ms, first_ms, n_diags))

    # --- 2. Edit at end (append a line) ---
    print(f"\n{BOLD}2. Edit at end (should reuse prior commands){RESET}")
    for i in range(3):
        text = BASE_SOURCE + f"\n// appended comment {i}\nsymbol bench_{i} : TYPE;\n"
        send_change(client, uri, 10 + i, text)
        total_ms, first_ms, n_diags = drain_and_time(client)
        results.append((f"append #{i}", first_ms))
        print(fmt_result(total_ms, first_ms, n_diags, f"  edit #{i}"))

    # --- 3. Edit at beginning (invalidates all) ---
    print(f"\n{BOLD}3. Edit at beginning (no reuse){RESET}")
    for i in range(3):
        text = f"// changed header {i}\n" + BASE_SOURCE
        send_change(client, uri, 20 + i, text)
        total_ms, first_ms, n_diags = drain_and_time(client)
        results.append((f"prepend #{i}", first_ms))
        print(fmt_result(total_ms, first_ms, n_diags, f"  edit #{i}"))

    # --- 4. No-op change ---
    print(f"\n{BOLD}4. No-op change (identical text){RESET}")
    send_change(client, uri, 30, BASE_SOURCE)
    total_ms, first_ms, n_diags = drain_and_time(client)
    results.append(("no-op change", first_ms))
    print(fmt_result(total_ms, first_ms, n_diags))

    # --- 5. Rapid edits ---
    print(f"\n{BOLD}5. Rapid edits (5 changes in <50ms){RESET}")
    t0 = time.monotonic()
    for i in range(5):
        text = BASE_SOURCE + f"\n// rapid edit {i}\n"
        send_change(client, uri, 40 + i, text)
    total_ms, first_ms, n_diags = drain_and_time(client)
    wall_ms = (time.monotonic() - t0) * 1000
    cold = results[0][1]
    results.append(("rapid 5x", first_ms))
    print(f"  {wall_ms:7.0f}ms wall time  ({n_diags} diags)  "
          f"(naive would be {5 * cold:.0f}ms)")

    # --- 6. Larger file ---
    print(f"\n{BOLD}6. Larger file: append 1 cmd to 50-cmd file{RESET}")
    big_source = BASE_SOURCE
    for i in range(40):
        big_source += f"symbol big_{i} : TYPE;\n"
    send_change(client, uri, 50, big_source)
    drain_and_time(client)  # settle

    big_plus = big_source + "symbol big_final : TYPE;\n"
    send_change(client, uri, 51, big_plus)
    total_ms, first_ms, n_diags = drain_and_time(client)
    results.append(("50-cmd+1 append", first_ms))
    print(fmt_result(total_ms, first_ms, n_diags))

    # Cleanup
    client.send_notification("textDocument/didClose", {"textDocument": {"uri": uri}})
    client.stop()
    os.unlink(tmp_path)

    # --- Summary ---
    print(f"\n{BOLD}Summary (time to first diagnostic){RESET}")
    cold = results[0][1]
    for name, dur in results:
        bar = "█" * max(1, int(dur / 20))
        color = RED if dur > 500 else YELLOW if dur > 200 else GREEN
        speedup = f" {GREEN}({cold/dur:.1f}x faster){RESET}" if dur > 0 and dur < cold * 0.7 else ""
        print(f"  {color}{bar}{RESET} {dur:7.0f}ms  {name}{speedup}")

    # Show incremental reuse from log
    if os.path.exists(log_file):
        with open(log_file) as f:
            log = f.read()
        reuse_lines = [l for l in log.split("\n") if "reusing" in l.lower()]
        if reuse_lines:
            print(f"\n{BOLD}Incremental reuse log:{RESET}")
            for line in reuse_lines:
                print(f"  {DIM}{line}{RESET}")


if __name__ == "__main__":
    main()
