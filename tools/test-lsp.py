#!/usr/bin/env python3
"""Integration tests for the lambdapi LSP server.

Tests hover, go-to-definition, document symbols, and diagnostics
against the test/ corpus. Positions are found dynamically from file
content so tests don't break when lines shift.

Usage:
    tools/test-lsp.py                    # run all tests
    tools/test-lsp.py -v                 # verbose output
    tools/test-lsp.py -k hover           # run only tests matching 'hover'
    tools/test-lsp.py --log-file FILE    # write LSP server log to FILE
"""

import json
import os
import re
import select
import subprocess
import sys
import threading
import time


# --- LSP client ---

class LSPClient:
    def __init__(self, lib_root, map_dirs=None, log_file=None):
        self.lib_root = lib_root
        self.map_dirs = map_dirs or []
        self.log_file = log_file
        self.msg_id = 0
        self.proc = None
        self.stderr_lines = []

    def start(self):
        cmd = ["lambdapi", "lsp", f"--lib-root={self.lib_root}"]
        for md in self.map_dirs:
            cmd.append(f"--map-dir={md}")
        if self.log_file:
            cmd.append(f"--log-file={self.log_file}")
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stderr, daemon=True
        )
        self._stderr_thread.start()

    def _read_stderr(self):
        for line in self.proc.stderr:
            self.stderr_lines.append(line.decode().rstrip())

    def stop(self):
        if self.proc:
            try:
                self.send_request("shutdown", {})
                self.send_notification("exit", {})
                self.proc.stdin.close()
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()
            self.proc = None

    @property
    def alive(self):
        return self.proc and self.proc.poll() is None

    def send_request(self, method, params):
        self.msg_id += 1
        msg = {"jsonrpc": "2.0", "id": self.msg_id, "method": method, "params": params}
        self._write(msg)
        return self.msg_id

    def send_notification(self, method, params):
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        self._write(msg)

    def _write(self, msg):
        body = json.dumps(msg).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self.proc.stdin.write(header + body)
        self.proc.stdin.flush()

    def read_message(self, timeout=10):
        deadline = time.time() + timeout
        header = b""
        while time.time() < deadline:
            ready, _, _ = select.select([self.proc.stdout], [], [], 0.5)
            if not ready:
                continue
            b = self.proc.stdout.read(1)
            if not b:
                return None
            header += b
            if header.endswith(b"\r\n\r\n"):
                size = int(header.decode().split(":")[1].strip().split("\r")[0])
                data = self.proc.stdout.read(size)
                return json.loads(data.decode())
        return None

    def read_response(self, expected_id, timeout=15):
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.read_message(timeout=deadline - time.time())
            if msg is None:
                return None
            if msg.get("id") == expected_id:
                return msg
        return None

    def drain_notifications(self, timeout=5):
        """Read notifications until quiet. Returns list of diagnostics."""
        diagnostics = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            ready, _, _ = select.select([self.proc.stdout], [], [], 0.5)
            if ready:
                msg = self.read_message(timeout=1)
                if msg and msg.get("method") == "textDocument/publishDiagnostics":
                    diagnostics.append(msg)
                deadline = time.time() + 1  # reset on activity
        return diagnostics

    def initialize(self, root_uri):
        mid = self.send_request("initialize", {
            "processId": os.getpid(),
            "rootUri": root_uri,
            "capabilities": {
                "textDocument": {
                    "hover": {"contentFormat": ["markdown", "plaintext"]},
                    "definition": {},
                    "documentSymbol": {},
                }
            },
        })
        resp = self.read_response(mid)
        self.send_notification("initialized", {})
        return resp

    def open_file(self, uri, text):
        self.send_notification("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": "lp",
                "version": 1,
                "text": text,
            }
        })

    def hover(self, uri, line, col):
        mid = self.send_request("textDocument/hover", {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": col},
        })
        return self.read_response(mid)

    def definition(self, uri, line, col):
        mid = self.send_request("textDocument/definition", {
            "textDocument": {"uri": uri},
            "position": {"line": line, "character": col},
        })
        return self.read_response(mid)

    def document_symbols(self, uri):
        mid = self.send_request("textDocument/documentSymbol", {
            "textDocument": {"uri": uri},
        })
        return self.read_response(mid)


# --- Test harness ---

BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"

class TestRunner:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.failures = []

    def ok(self, name, detail=""):
        self.passed += 1
        print(f"  {GREEN}✓{RESET} {name}")
        if self.verbose and detail:
            for line in detail.strip().split("\n"):
                print(f"    {DIM}{line}{RESET}")

    def fail(self, name, reason):
        self.failed += 1
        self.failures.append((name, reason))
        print(f"  {RED}✗{RESET} {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        parts = [f"{GREEN}{self.passed} passed{RESET}"]
        if self.failed:
            parts.append(f"{RED}{self.failed} failed{RESET}")
        print(f"\n{BOLD}{total} tests:{RESET} {', '.join(parts)}")
        if self.failures:
            print(f"\n{RED}Failures:{RESET}")
            for name, reason in self.failures:
                print(f"  {name}: {reason}")
        return self.failed == 0


# --- Position finder ---

class SourceFile:
    """Wraps file text to find (line, col) positions dynamically."""

    def __init__(self, text):
        self.text = text
        self.lines = text.splitlines()

    def find(self, pattern, target=None, occurrence=1, target_occurrence=1):
        """Find a position in the file.

        Args:
            pattern: regex to match the line
            target: substring within the matched line to get the column of.
                    If None, returns column 0 of the matched line.
            occurrence: which line match to use (1-indexed)
            target_occurrence: which occurrence of target within the line (1-indexed)

        Returns:
            (line, col) as 0-indexed LSP position, or None.
        """
        count = 0
        for i, line in enumerate(self.lines):
            if re.search(pattern, line):
                count += 1
                if count == occurrence:
                    col = 0
                    if target:
                        idx = -1
                        start = 0
                        for _ in range(target_occurrence):
                            idx = line.find(target, start)
                            if idx < 0:
                                break
                            start = idx + 1
                        if idx >= 0:
                            col = idx
                    return (i, col)
        return None

    def find_decl(self, name):
        """Find the declaration line of a symbol (the 'symbol <name>' line).
        Returns 0-indexed LSP line number, or None."""
        for i, line in enumerate(self.lines):
            # Match "symbol name" with possible modifiers before it
            if re.search(rf'\bsymbol\b.*\b{re.escape(name)}\b', line):
                return i
            # Also check next line for multi-line declarations like:
            #   opaque symbol\n  name : ...
            if re.search(r'\bsymbol\s*$', line) and i + 1 < len(self.lines):
                if re.search(rf'^\s*{re.escape(name)}\b', self.lines[i + 1]):
                    return i + 1
        return None


# --- Helpers ---

def file_uri(path):
    return "file://" + os.path.abspath(path)


def extract_diagnostics(raw):
    items = []
    for d in raw:
        items.extend(d.get("params", {}).get("diagnostics", []))
    return items


def get_result(resp):
    if resp and resp.get("result") is not None:
        return resp["result"]
    return None


def should_run(name, pattern):
    if pattern is None:
        return True
    return pattern.lower() in name.lower()


# --- Test functions ---

def test_hover(client, runner, uri, pos, label,
               expect_result=True, expect_contains=None):
    if not client.alive:
        runner.fail(f"hover: {label}", "server not running")
        return
    if pos is None:
        runner.fail(f"hover: {label}", "position not found in source")
        return
    line, col = pos
    resp = client.hover(uri, line, col)
    result = get_result(resp)
    if result:
        content = result.get("contents", "")
        if isinstance(content, dict):
            content = content.get("value", "")
        content_str = str(content)
        if expect_contains and expect_contains not in content_str:
            runner.fail(f"hover: {label}",
                        f"expected '{expect_contains}' in: {content_str[:120]}")
        else:
            runner.ok(f"hover: {label}", content_str[:120])
    elif expect_result:
        runner.fail(f"hover: {label}", f"null result (line {line}, col {col})")
    else:
        runner.ok(f"hover: {label}", "null (expected)")


def test_definition(client, runner, uri, pos, label,
                    expect_result=True, expect_line=None, expect_uri=None):
    if not client.alive:
        runner.fail(f"def: {label}", "server not running")
        return
    if pos is None:
        runner.fail(f"def: {label}", "position not found in source")
        return
    line, col = pos
    resp = client.definition(uri, line, col)
    if not client.alive:
        runner.fail(f"def: {label}", "server crashed")
        return
    result = get_result(resp)
    if result:
        loc = result[0] if isinstance(result, list) else result
        target_line = loc.get("range", {}).get("start", {}).get("line")
        target_uri = loc.get("uri", "")
        detail = f"-> {os.path.basename(target_uri)}:{target_line}"
        if expect_line is not None and target_line != expect_line:
            runner.fail(f"def: {label}",
                        f"expected line {expect_line}, got {target_line}")
        elif expect_uri is not None and expect_uri not in target_uri:
            runner.fail(f"def: {label}",
                        f"expected uri containing '{expect_uri}', got {target_uri}")
        else:
            runner.ok(f"def: {label}", detail)
    elif expect_result:
        runner.fail(f"def: {label}", f"null result (line {line}, col {col})")
    else:
        runner.ok(f"def: {label}", "null (expected)")


def test_diagnostics(runner, diag_items, file_label):
    errors = [d for d in diag_items if d.get("severity", 0) <= 2]
    if not errors:
        runner.ok(f"{file_label}: no errors", f"{len(diag_items)} diagnostic(s)")
    else:
        msgs = "; ".join(d.get("message", "?")[:60] for d in errors[:3])
        runner.fail(f"{file_label}: no errors", f"{len(errors)} error(s): {msgs}")

    hints = [d for d in diag_items if d.get("severity", 0) == 4]
    if hints:
        too_wide = [h for h in hints
                    if (h["range"]["end"]["character"]
                        - h["range"]["start"]["character"]) > 30
                    and h["range"]["start"]["line"]
                        == h["range"]["end"]["line"]]
        if not too_wide:
            runner.ok(f"{file_label}: hint ranges focused",
                      f"{len(hints)} hint(s), all focused")
        else:
            runner.fail(f"{file_label}: hint ranges focused",
                        f"{len(too_wide)}/{len(hints)} too wide, "
                        f"e.g. {json.dumps(too_wide[0]['range'])}")


# --- Main test suite ---

def run_tests(client, runner, test_dir, filter_pattern=None):
    root_uri = file_uri(test_dir)

    # Initialize
    print(f"\n{BOLD}Initialize{RESET}")
    resp = client.initialize(root_uri)
    if resp and resp.get("result", {}).get("capabilities"):
        caps = resp["result"]["capabilities"]
        cap_list = [k for k, v in caps.items() if v]
        runner.ok("initialize", f"capabilities: {', '.join(cap_list)}")
    else:
        runner.fail("initialize", "no capabilities in response")
        return

    # Open test.lp and build position index
    test_path = os.path.join(test_dir, "test.lp")
    test_uri = file_uri(test_path)
    with open(test_path) as f:
        test_text = f.read()

    src = SourceFile(test_text)
    client.open_file(test_uri, test_text)
    diags = extract_diagnostics(client.drain_notifications(timeout=10))

    # Diagnostics
    if should_run("diagnostics", filter_pattern):
        print(f"\n{BOLD}Diagnostics{RESET}")
        test_diagnostics(runner, diags, "test.lp")

    # Hover
    if should_run("hover", filter_pattern):
        print(f"\n{BOLD}Hover{RESET}")

        # Hover on "Set" in: constant symbol my_set : Set;
        test_hover(client, runner, test_uri,
                   src.find(r'symbol my_set\b', 'Set'),
                   "Set type", expect_contains="Set")

        # Hover on "nat" in: injective symbol my_inj : τ nat → τ nat;
        test_hover(client, runner, test_uri,
                   src.find(r'symbol my_inj\b', 'nat'),
                   "nat from stdlib")

        # Hover on "first" in: symbol explicit_example ≔ @first ...
        test_hover(client, runner, test_uri,
                   src.find(r'@first', 'first'),
                   "first in @-application")

        # Hover on "double" in: rule double _0 ↪ _0
        test_hover(client, runner, test_uri,
                   src.find(r'^rule double _0', 'double'),
                   "double in rule head")

        # Hover on "_0" in: rule double _0 ↪ _0
        test_hover(client, runner, test_uri,
                   src.find(r'^rule double _0', '_0'),
                   "_0 in rule pattern")

        # Hover on "double" in proof type: double_zero : π (double _0 = _0) ≔
        test_hover(client, runner, test_uri,
                   src.find(r'double_zero.*double', 'double', target_occurrence=2),
                   "double in proof type")

    # Go-to-definition
    if should_run("definition", filter_pattern):
        print(f"\n{BOLD}Go-to-definition{RESET}")

        first_decl = src.find_decl("first")
        double_decl = src.find_decl("double")

        # @first → first declaration
        test_definition(client, runner, test_uri,
                        src.find(r'@first', 'first'),
                        "first -> declaration",
                        expect_line=first_decl)

        # double in rule → double declaration
        test_definition(client, runner, test_uri,
                        src.find(r'^rule double _0', 'double'),
                        "double in rule -> declaration",
                        expect_line=double_decl)

        # double in proof type → double declaration
        test_definition(client, runner, test_uri,
                        src.find(r'double_zero.*double', 'double', target_occurrence=2),
                        "double in proof -> declaration",
                        expect_line=double_decl)

        # nat → stdlib (should not crash)
        test_definition(client, runner, test_uri,
                        src.find(r'symbol my_inj\b', 'nat'),
                        "nat -> stdlib",
                        expect_uri="Stdlib")

        # _0 in rule → stdlib constructor
        test_definition(client, runner, test_uri,
                        src.find(r'^rule double _0', '_0'),
                        "_0 -> stdlib constructor")

    # Document symbols
    if should_run("symbols", filter_pattern):
        print(f"\n{BOLD}Document symbols{RESET}")
        if client.alive:
            resp = client.document_symbols(test_uri)
            result = get_result(resp)
            if result:
                names = [s.get("name", "?") for s in result[:10]]
                if len(result) >= 10:
                    runner.ok("test.lp symbols",
                              f"{len(result)} symbols: {', '.join(names)}...")
                else:
                    runner.fail("test.lp symbols",
                                f"expected >= 10 symbols, got {len(result)}")
            else:
                runner.fail("test.lp symbols", "no result")

    # Server health
    print(f"\n{BOLD}Server health{RESET}")
    if client.alive:
        runner.ok("server alive after all tests")
    else:
        code = client.proc.returncode if client.proc else "?"
        runner.fail("server alive", f"exited with code {code}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Lambdapi LSP integration tests")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-k", "--filter", help="only run tests matching pattern")
    parser.add_argument("--log-file", help="write LSP server log to file")
    parser.add_argument("--test-dir", default="test", help="test directory (default: test)")
    args = parser.parse_args()

    test_dir = os.path.abspath(args.test_dir)
    log_file = args.log_file or os.path.join(test_dir, ".lsp-test.log")

    # Find lambdapi's installed lib_root (for Stdlib resolution)
    opam_prefix = subprocess.run(
        ["opam", "var", "prefix"], capture_output=True, text=True
    ).stdout.strip()
    installed_lib = os.path.join(opam_prefix, "lib", "lambdapi", "lib_root")
    if not os.path.isdir(installed_lib):
        print(f"{RED}Error: lambdapi lib_root not found at {installed_lib}{RESET}")
        sys.exit(1)

    map_dirs = [f"Stdlib:{installed_lib}/Stdlib"]

    print(f"{BOLD}Lambdapi LSP integration tests{RESET}")
    print(f"{DIM}test dir:  {test_dir}{RESET}")
    print(f"{DIM}lib root:  {test_dir}{RESET}")
    print(f"{DIM}map dirs:  {', '.join(map_dirs)}{RESET}")
    print(f"{DIM}lsp log:   {log_file}{RESET}")

    runner = TestRunner(verbose=args.verbose)
    client = LSPClient(lib_root=test_dir, map_dirs=map_dirs, log_file=log_file)
    client.start()

    try:
        run_tests(client, runner, test_dir, filter_pattern=args.filter)
    except Exception as e:
        print(f"\n{RED}Fatal error: {e}{RESET}")
        import traceback
        traceback.print_exc()
    finally:
        client.stop()

    if runner.failed and client.stderr_lines:
        print(f"\n{YELLOW}Server stderr (last 20 lines):{RESET}")
        for line in client.stderr_lines[-20:]:
            print(f"  {DIM}{line}{RESET}")

    ok = runner.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
