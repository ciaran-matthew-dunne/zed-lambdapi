#!/usr/bin/env python3
"""Test go-to-definition on stdlib symbol via lambdapi LSP."""
import subprocess, json, sys, os, time, threading

def send(proc, msg):
    body = json.dumps(msg)
    header = f"Content-Length: {len(body)}\r\n\r\n"
    proc.stdin.write((header + body).encode())
    proc.stdin.flush()

def recv(proc, timeout=10):
    """Read one LSP message from stdout."""
    # Read header
    header = b""
    while b"\r\n\r\n" not in header:
        b = proc.stdout.read(1)
        if not b:
            return None
        header += b
    size = int(header.decode().split(":")[1].strip().split("\r")[0])
    data = proc.stdout.read(size)
    return json.loads(data.decode())

test_file = os.path.abspath("test/stdlib.lp")
test_uri = "file://" + test_file
lib_root = os.path.dirname(test_file)

with open(test_file) as f:
    text = f.read()

# Collect stderr in background
stderr_lines = []
def read_stderr(proc):
    for line in proc.stderr:
        stderr_lines.append(line.decode().rstrip())

proc = subprocess.Popen(
    ["lambdapi", "lsp", f"--lib-root={lib_root}"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    bufsize=0
)
t = threading.Thread(target=read_stderr, args=(proc,), daemon=True)
t.start()

try:
    # Initialize
    send(proc, {"jsonrpc":"2.0","id":1,"method":"initialize","params":{
        "capabilities":{}, "rootUri": "file://" + lib_root
    }})
    r = recv(proc)
    print("init OK:", bool(r))

    send(proc, {"jsonrpc":"2.0","method":"initialized","params":{}})

    # Open doc
    send(proc, {"jsonrpc":"2.0","id":10,"method":"textDocument/didOpen","params":{
        "textDocument":{"uri":test_uri,"languageId":"lp","version":1,"text":text}
    }})

    # Wait and drain diagnostics
    time.sleep(4)
    # Read any pending messages (diagnostics)
    import select
    while select.select([proc.stdout], [], [], 0.5)[0]:
        r = recv(proc)
        if r and r.get("method") == "textDocument/publishDiagnostics":
            diags = r["params"]["diagnostics"]
            print(f"diagnostics: {len(diags)} items")

    # Go-to-definition on _0 (line 11 = 0-indexed 10, col 17)
    print("\n--- go-to-definition on _0 ---")
    send(proc, {"jsonrpc":"2.0","id":2,"method":"textDocument/definition","params":{
        "textDocument":{"uri":test_uri},
        "position":{"line":10,"character":17}
    }})

    r = recv(proc)
    if r:
        print("result:", json.dumps(r, indent=2))
    else:
        print("NO RESPONSE — server crashed")
        print("exit code:", proc.poll())

except Exception as e:
    print(f"Error: {e}")
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except:
        proc.kill()
    time.sleep(0.5)
    print("\n--- SERVER LOG (last 60 lines) ---")
    for line in stderr_lines[-60:]:
        print(line)
