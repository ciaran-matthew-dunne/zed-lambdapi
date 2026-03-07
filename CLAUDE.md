# zed-lambdapi

Zed extension for [Lambdapi](https://github.com/Deducteam/lambdapi), a proof assistant for the lambda-Pi-calculus modulo rewriting.

## Project Goal

Build a nice proof assistant interface for Lambdapi in Zed. The broader goal is improving and modifying surrounding tooling (LSP, grammar, extension) to support interactive proving, not just syntax highlighting. Zed's extension API is more restricted than VS Code's, but this is an advantage — it forces clever, elegant solutions.

## Project Scope

Three related repos (all in `~/prog/`), each with its own git history:

| Repo | Purpose | Language |
|------|---------|----------|
| `zed-lambdapi` (here) | Zed extension: LSP launch, queries, code labels | Rust (WASM) |
| `tree-sitter-lambdapi` | Tree-sitter grammar for `.lp` files | JavaScript (grammar.js) |
| `lambdapi` | Lambdapi itself: type checker + LSP server | OCaml |

**Important**: The grammar lives in `tree-sitter-lambdapi`, not here. `extension.toml` references it by URL + commit rev. Zed fetches and compiles the grammar from that repo when installing the extension. During dev, `extension.toml` points to a local `file://` URL; for release, it points to GitHub. Use `make local`/`make remote` to switch. Changes to grammar rules (node types, parse behavior) must be made in `tree-sitter-lambdapi` — the `.scm` query files here must match that grammar's node types.

The `lambdapi` repo is a custom fork where we modify the LSP server (OCaml). Use `opam` to install/switch between dev builds (`opam pin` or local installs).

## Key Files

- `src/zed-lambdapi.rs` — Extension entry point (LSP command, symbol labels)
- `extension.toml` — Extension manifest (grammar source, LSP config)
- `languages/lambdapi/*.scm` — Tree-sitter queries (highlights, folds, indents, outline, etc.)
- `languages/lambdapi/config.toml` — Language config (file ext, brackets, comments)
- `tools/lp-goals` — Python tool for proof goals via LSP
- `Makefile` — Build/dev automation

## Build & Dev Workflow

```bash
make grammar          # regenerate tree-sitter parser (--abi=14 for Zed compat)
make test             # tree-sitter test corpus
make parse F=file.lp  # parse a single file
make sync             # update extension.toml rev to latest grammar commit
make local / remote   # switch grammar between file:// (dev) and GitHub (release)
make dev              # grammar → commit → sync (ready to install)
make release          # grammar → commit → push → remote → sync
```

Install in Zed: `zed: install dev extension` → select this directory.

Debug: `zed --foreground` for logs, or `println!` in Rust (stdout forwarded to Zed process). Typical workflow: `zed --foreground . | tee ~/.local/share/zed/logs/Zed.log` to capture logs for analysis.

## Lambdapi LSP

Launched via `lambdapi lsp --lib-root=...` (no `--standard-lsp` to get extended goal diagnostics).

Supports: hover, go-to-definition, document symbols, diagnostics, custom `proof/goals` request.

### Fixed Issues (in custom fork `~/prog/lambdapi`)

- **Go-to-definition crash on Ghost/stdlib symbols** (fixed): Added `Sign.Ghost.path` guard in `do_definition`, preserved full qident (module path + name) from rangemap via `get_symbol`, added `find_sym` helper that searches `in_scope` then `Sign.find_qualified`, and safe fallback positions for external symbols to avoid SIGSEGV from dangling `sym_pos` refs.
- **Diagnostic ranges too wide** (fixed): Severity-4 hint diagnostics now collapse to zero-width range at start position in `lsp_base.ml:mk_diagnostic`, so Zed doesn't underline entire commands.

### Testing

Automated LSP tests: `python3 tools/test-lsp.py` (21 tests). Tests hover, go-to-definition, diagnostics, and document symbols across local files (nat.lp, proofs.lp) and stdlib imports (stdlib.lp). Requires `--map-dir=Stdlib:<opam_prefix>/lib/lambdapi/lib_root/Stdlib` for stdlib resolution.

### Interactive Proving (planned)

No interactive proof support yet. The plan:
- Use **Zed tasks** to launch a **TUI** (terminal UI) that displays proof goals
- The TUI communicates with the LSP (or lambdapi binary directly) via a channel
- This lets us control the proof-stepping UX (scrolling through proofs, goal display) without needing a custom Zed panel (which the extension API doesn't support)
- The LSP's custom `proof/goals` request and extended diagnostics with `goal_info` are the data sources

### Completions & Hover (planned)

- Improve hover to show documentation for stdlib symbols, tactics, etc.
- Improve completions — use all available extension API functionality since the API is limited anyway (maximize what we get from it)

## Conventions

- Tree-sitter queries use Zed capture names (`@keyword`, `@function`, `@type`, etc.)
- Unicode operators have ASCII alternatives (→/->  λ/\  Π/forall  ≔/:=  ↪/|->  ⊢/|-  ≡/==)
- Extension uses `zed_extension_api = "0.7.0"`
- Grammar must be generated with `--abi=14` (Zed doesn't yet support ABI 15)
- Grammar pointed at local `file://` URL during dev, GitHub URL for release
- `grammars/` dir is Zed's build cache (gitignored), not our code

---

## Reference: Zed Extension Development

Docs: https://zed.dev/docs/extensions/developing-extensions

### extension.toml

Required fields: `id`, `name`, `version`, `schema_version` (= 1), `authors`, `description`, `repository`.

Grammar config:
```toml
[grammars.mylang]
repository = "https://github.com/user/tree-sitter-mylang"
rev = "<commit-sha>"
path = "optional/subdir"      # if grammar.js isn't at repo root
```

Language server config:
```toml
[language_servers.my-lsp]
name = "My LSP"
languages = ["My Language"]
```

### Rust Extension API

Extensions are Rust compiled to WASM (`crate-type = ["cdylib"]`).

```rust
impl zed::Extension for MyExtension {
    fn new() -> Self;
    fn language_server_command(...) -> Result<zed::Command>;  // LSP binary + args
    fn label_for_symbol(...) -> Option<CodeLabel>;            // symbol list labels
    fn label_for_completion(...) -> Option<CodeLabel>;        // completion labels
}
zed::register_extension!(MyExtension);
```

### Language Directory (languages/mylang/)

| File | Purpose |
|------|---------|
| `config.toml` | name, grammar, path_suffixes, line_comments, tab_size, hard_tabs |
| `highlights.scm` | Syntax highlighting (40+ capture types) |
| `brackets.scm` | Bracket matching (@open, @close) |
| `outline.scm` | Code structure / symbol navigation |
| `indents.scm` | Auto-indentation (@indent, @dedent) |
| `folds.scm` | Code folding regions |
| `injections.scm` | Embedded languages |
| `locals.scm` | Scope-aware highlighting (@local.scope, @local.definition, @local.reference) |
| `overrides.scm` | Context-dependent settings |
| `textobjects.scm` | Vim text objects |
| `runnables.scm` | Detect runnable code blocks |
| `redactions.scm` | Screen-share privacy |
| `tags.scm` | Symbol tags for navigation |

### Capabilities

Extensions request permissions: `process:exec` (run commands), `download_file` (fetch remote files), `npm:install` (install packages). Users can restrict via `granted_extension_capabilities` setting.

### Publishing

Fork `zed-industries/extensions`, add extension as git submodule (HTTPS), update `extensions.toml`, run `pnpm sort-extensions`, open PR. License required (MIT, Apache-2.0, GPL-3.0, etc.).

---

## Reference: Language Server Protocol (LSP 3.17)

Spec: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/

### Lifecycle

| Method | Direction | Purpose |
|--------|-----------|---------|
| `initialize` | client→server | Exchange capabilities |
| `initialized` | client→server | Confirm init complete |
| `shutdown` | client→server | Prepare to exit |
| `exit` | client→server | Terminate process |

### Text Document Sync

| Method | Purpose |
|--------|---------|
| `textDocument/didOpen` | Document opened |
| `textDocument/didChange` | Document edited |
| `textDocument/didSave` | Document saved |
| `textDocument/didClose` | Document closed |
| `textDocument/publishDiagnostics` | Server pushes errors/warnings |

### Language Features

| Method | Purpose |
|--------|---------|
| `textDocument/completion` | Autocomplete |
| `textDocument/hover` | Info on hover |
| `textDocument/signatureHelp` | Function signature info |
| `textDocument/definition` | Go to definition |
| `textDocument/declaration` | Go to declaration |
| `textDocument/typeDefinition` | Go to type definition |
| `textDocument/implementation` | Find implementations |
| `textDocument/references` | Find all references |
| `textDocument/documentHighlight` | Highlight related symbols |
| `textDocument/documentSymbol` | List document structure |
| `textDocument/codeAction` | Quick fixes / refactors |
| `textDocument/codeLens` | Inline metadata |
| `textDocument/formatting` | Format document |
| `textDocument/rangeFormatting` | Format selection |
| `textDocument/rename` | Rename symbol |
| `textDocument/inlayHint` | Inline type hints (3.17+) |

### Workspace

| Method | Purpose |
|--------|---------|
| `workspace/symbol` | Search symbols across workspace |
| `workspace/executeCommand` | Run a command |
| `workspace/applyEdit` | Apply edits across files |
| `workspace/didChangeConfiguration` | Settings changed |
| `workspace/workspaceFolders` | Query open folders |

### Lambdapi LSP Specifics

Lambdapi implements a subset: `initialize`, `textDocument/didOpen`, `textDocument/didChange`, `textDocument/didClose`, `textDocument/hover`, `textDocument/definition`, `textDocument/documentSymbol`, `textDocument/publishDiagnostics`.

Custom request: `proof/goals` (params: uri + position → goals + logs). Without `--standard-lsp`, diagnostics include `goal_info` field with embedded proof goals.

---

## Reference: Debug Adapter Protocol (DAP)

Spec: https://microsoft.github.io/debug-adapter-protocol/specification

### Base Protocol

JSON messages over stdin/stdout with `Content-Length` header (like LSP). Three message types: **requests** (client→adapter), **responses** (adapter→client), **events** (adapter→client, unsolicited).

### Session Lifecycle

1. **initialize** — exchange capabilities
2. **setBreakpoints / setExceptionBreakpoints** — configure breakpoints
3. **configurationDone** — end config phase
4. **launch** (start program) or **attach** (connect to running)
5. Execution: adapter sends `stopped` events on breakpoints/exceptions
6. **terminate** / **disconnect** — end session

### Key Requests

| Request | Purpose |
|---------|---------|
| `initialize` | Capability negotiation |
| `launch` / `attach` | Start or connect to debuggee |
| `setBreakpoints` | Source breakpoints |
| `setFunctionBreakpoints` | Function breakpoints |
| `setExceptionBreakpoints` | Exception handling |
| `configurationDone` | End configuration |
| `threads` | List active threads |
| `stackTrace` | Get call stack |
| `scopes` | Variable scopes for a frame |
| `variables` | Inspect variables |
| `setVariable` | Modify a variable |
| `evaluate` | Eval expression in context |
| `continue` / `next` / `stepIn` / `stepOut` / `pause` | Execution control |
| `terminate` / `disconnect` | End session |

### Key Events

| Event | Purpose |
|-------|---------|
| `initialized` | Adapter ready for config |
| `stopped` | Execution paused (breakpoint, step, exception) |
| `continued` | Execution resumed |
| `exited` | Debuggee exited |
| `terminated` | Debug session ending |
| `output` | Console/debug output |
| `breakpoint` | Breakpoint state changed |

### Zed DAP Integration

In `config.toml`, specify debuggers:
```toml
debuggers = ["my-debugger"]
```
Implement debugger adapter in extension Rust code. Zed's DAP support is relatively new.
