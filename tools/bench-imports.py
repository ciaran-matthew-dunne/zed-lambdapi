#!/usr/bin/env python3
"""Benchmark LSP performance with different stdlib import strategies.

Measures didOpen + diagnostics time for files with varying imports
to identify which modules and import styles cause lag.

Usage:
    tools/bench-imports.py           # run all benchmarks
    tools/bench-imports.py -v        # verbose output
"""

import json
import os
import subprocess
import sys
import tempfile
import time

# Reuse LSPClient from test-lsp.py
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


# --- Benchmark scenarios ---

# Each scenario: (label, lp_source)
# The source must be a valid lambdapi file that type-checks.

BODY = """\
// Minimal body to trigger type-checking
symbol bench_sym : TYPE;
"""

SCENARIOS = [
    ("no imports", BODY),

    ("require open Set", "require open Stdlib.Set;\n" + BODY),

    ("require open Set HOL Eq",
     "require open Stdlib.Set Stdlib.HOL Stdlib.Eq;\n" + BODY),

    ("require open Set HOL Eq + use nat",
     "require open Stdlib.Set Stdlib.HOL Stdlib.Eq;\n"
     "symbol bench_f : τ nat → τ nat;\n"),

    ("require open Set HOL Eq Prop Bool Classic",
     "require open Stdlib.Set Stdlib.HOL Stdlib.Eq "
     "Stdlib.Prop Stdlib.Bool Stdlib.Classic;\n" + BODY),

    ("require open Set HOL Eq Nat",
     "require open Stdlib.Set Stdlib.HOL Stdlib.Eq Stdlib.Nat;\n" + BODY),

    ("require open Set HOL Eq Nat List",
     "require open Stdlib.Set Stdlib.HOL Stdlib.Eq Stdlib.Nat Stdlib.List;\n" + BODY),

    ("require open ALL heavy (Set HOL Eq Nat List Prop Bool Classic)",
     "require open Stdlib.Set Stdlib.HOL Stdlib.Eq Stdlib.Nat Stdlib.List "
     "Stdlib.Prop Stdlib.Bool Stdlib.Classic;\n" + BODY),

    # Qualified imports (require without open)
    ("require Set (qualified)",
     "require Stdlib.Set;\n" + BODY),

    ("require Set HOL Eq (qualified)",
     "require Stdlib.Set Stdlib.HOL Stdlib.Eq;\n" + BODY),

    ("require Set HOL Eq Nat (qualified)",
     "require Stdlib.Set Stdlib.HOL Stdlib.Eq Stdlib.Nat;\n" + BODY),

    ("require Set HOL Eq Nat List (qualified)",
     "require Stdlib.Set Stdlib.HOL Stdlib.Eq Stdlib.Nat Stdlib.List;\n" + BODY),

    ("require ALL heavy qualified",
     "require Stdlib.Set Stdlib.HOL Stdlib.Eq Stdlib.Nat Stdlib.List "
     "Stdlib.Prop Stdlib.Bool Stdlib.Classic;\n" + BODY),

    # Mixed: require some, open only what's needed
    ("require Nat List; open Set HOL Eq",
     "require Stdlib.Nat Stdlib.List;\n"
     "require open Stdlib.Set Stdlib.HOL Stdlib.Eq;\n" + BODY),
]


def run_scenario(client, label, source, test_dir, verbose=False):
    """Open a file with given source, measure diagnostics time, then close it."""
    # Write temp file
    tmp_path = os.path.join(test_dir, "_bench.lp")
    with open(tmp_path, "w") as f:
        f.write(source)
    uri = "file://" + tmp_path

    # didOpen + drain diagnostics
    t0 = time.monotonic()
    client.open_file(uri, source)
    diag_raw = client.drain_notifications(timeout=15)
    dur_ms = (time.monotonic() - t0) * 1000

    diags = []
    for d in diag_raw:
        diags.extend(d.get("params", {}).get("diagnostics", []))
    errors = [d for d in diags if d.get("severity", 0) <= 2]
    diag_bytes = sum(len(json.dumps(d)) for d in diag_raw)

    # didClose
    client.send_notification("textDocument/didClose", {
        "textDocument": {"uri": uri}
    })

    # Clean up
    os.unlink(tmp_path)

    return {
        "label": label,
        "dur_ms": dur_ms,
        "diag_count": len(diags),
        "error_count": len(errors),
        "diag_bytes": diag_bytes,
        "errors": [d.get("message", "?")[:80] for d in errors[:3]],
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark LSP import performance")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-n", "--repeat", type=int, default=1,
                        help="repeat each scenario N times (default: 1)")
    args = parser.parse_args()

    # Setup
    opam_prefix = subprocess.run(
        ["opam", "var", "prefix"], capture_output=True, text=True
    ).stdout.strip()
    installed_lib = os.path.join(opam_prefix, "lib", "lambdapi", "lib_root")
    if not os.path.isdir(installed_lib):
        print(f"{RED}Error: lib_root not found at {installed_lib}{RESET}")
        sys.exit(1)

    test_dir = os.path.abspath("test")
    map_dirs = [f"Stdlib:{installed_lib}/Stdlib"]
    log_file = os.path.join(test_dir, ".bench-imports.log")

    print(f"{BOLD}LSP Import Performance Benchmark{RESET}")
    print(f"{DIM}lib root:  {test_dir}{RESET}")
    print(f"{DIM}map dirs:  {', '.join(map_dirs)}{RESET}")
    print(f"{DIM}repeats:   {args.repeat}{RESET}")
    print()

    # Start LSP once, reuse for all scenarios
    client = LSPClient(lib_root=test_dir, map_dirs=map_dirs, log_file=log_file,
                       standard_lsp=True)
    client.start()

    root_uri = "file://" + test_dir
    resp = client.initialize(root_uri)
    if not resp or not resp.get("result", {}).get("capabilities"):
        print(f"{RED}Failed to initialize LSP{RESET}")
        client.stop()
        sys.exit(1)
    client.send_notification("initialized", {})

    results = []
    for label, source in SCENARIOS:
        times = []
        for i in range(args.repeat):
            r = run_scenario(client, label, source, test_dir, verbose=args.verbose)
            times.append(r["dur_ms"])
            if not client.alive:
                print(f"{RED}Server died during: {label}{RESET}")
                client.stop()
                sys.exit(1)

        avg_ms = sum(times) / len(times)
        r["dur_ms"] = avg_ms
        results.append(r)

        # Display
        bar = "█" * max(1, int(avg_ms / 50))
        color = RED if avg_ms > 2000 else YELLOW if avg_ms > 500 else GREEN
        err_flag = f" {RED}({r['error_count']} errors){RESET}" if r["error_count"] else ""
        print(f"  {color}{bar}{RESET} {avg_ms:7.0f}ms  "
              f"{r['diag_count']:3d} diags  {r['diag_bytes']:6d}B  {label}{err_flag}")
        if args.verbose and r["errors"]:
            for e in r["errors"]:
                print(f"    {DIM}{e}{RESET}")

    client.stop()

    # Summary
    print(f"\n{BOLD}Summary{RESET}")
    baseline = results[0]["dur_ms"] if results else 1
    for r in sorted(results, key=lambda x: x["dur_ms"]):
        ratio = r["dur_ms"] / baseline if baseline > 0 else 0
        print(f"  {r['dur_ms']:7.0f}ms  ({ratio:5.1f}x)  {r['label']}")

    # Compare open vs qualified for same module sets
    print(f"\n{BOLD}Open vs Qualified{RESET}")
    open_results = {r["label"]: r for r in results if "require open" in r["label"]}
    qual_results = {r["label"]: r for r in results if "qualified" in r["label"]}
    # Match by rough module count
    pairs = [
        ("require open Set", "require Set (qualified)"),
        ("require open Set HOL Eq", "require Set HOL Eq (qualified)"),
        ("require open Set HOL Eq Nat", "require Set HOL Eq Nat (qualified)"),
        ("require open Set HOL Eq Nat List", "require Set HOL Eq Nat List (qualified)"),
        ("require open ALL heavy (Set HOL Eq Nat List Prop Bool Classic)",
         "require ALL heavy qualified"),
    ]
    by_label = {r["label"]: r for r in results}
    for open_l, qual_l in pairs:
        o = by_label.get(open_l)
        q = by_label.get(qual_l)
        if o and q:
            diff = o["dur_ms"] - q["dur_ms"]
            pct = (diff / q["dur_ms"] * 100) if q["dur_ms"] > 0 else 0
            arrow = "slower" if diff > 0 else "faster"
            print(f"  {o['dur_ms']:6.0f}ms (open) vs {q['dur_ms']:6.0f}ms (qual)  "
                  f"→ open is {abs(diff):.0f}ms {arrow} ({abs(pct):.0f}%)")


if __name__ == "__main__":
    main()
