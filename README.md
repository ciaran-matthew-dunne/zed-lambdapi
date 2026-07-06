# zed-lambdapi

[Zed](https://zed.dev) extension for [Lambdapi](https://github.com/Deducteam/lambdapi), a proof assistant based on the lambda-Pi-calculus modulo rewriting.

## Features

- **Syntax highlighting** — full coverage of Lambdapi syntax: commands, tactics, modifiers, rewrite rules, unicode operators, pattern variables, qualified identifiers, and more
- **LSP integration** — hover info, go-to-definition, document symbols, and diagnostics via the Lambdapi language server
- **Code outline** — navigate symbols, inductive types, constructors, rules, and notations in the symbol panel
- **Code folding** — fold proof blocks, inductive definitions, and rule groups
- **Auto-indentation** — context-aware indentation for proofs, rules, and blocks
- **Bracket matching** — pairs for `()`, `[]`, `{}`
- **Interactive proof goals** — a terminal goals panel (`lp-goals`) that shows the proof state at your cursor and refreshes as you edit, like the VS Code extension's goals view
- **Proof debugger** — line breakpoints on tactic lines, step / continue, goals + hypotheses panel, via the `lambdapi dap` Debug Adapter Protocol server

## Requirements

- [Zed](https://zed.dev) editor
- [opam](https://opam.ocaml.org/) with an active switch

## Installation

### 1. Install Lambdapi (custom fork)

This extension requires a [custom fork](https://github.com/ciaran-matthew-dunne/lambdapi) of Lambdapi with improved LSP support (focused diagnostics, go-to-definition fixes, richer hover). If you already have Lambdapi installed, the fork will replace it in your current opam switch.

```bash
opam pin add lambdapi git+https://github.com/ciaran-matthew-dunne/lambdapi.git
eval $(opam env)
```

To switch back to upstream Lambdapi later:
```bash
opam pin remove lambdapi
opam install lambdapi
```

### 2. Install the Zed extension

```bash
git clone https://github.com/ciaran-matthew-dunne/zed-lambdapi
```

In Zed, open the command palette and run:
```
zed: install dev extension
```
Select the cloned directory.

### Environment

The extension finds Lambdapi via `which lambdapi` or the `LAMBDAPI_PATH` environment variable. It resolves the library root from `OPAM_SWITCH_PREFIX` (or `LAMBDAPI_LIB_ROOT`). Make sure `eval $(opam env)` has been run in your shell before launching Zed.

## Unicode Input

Lambdapi makes heavy use of Unicode symbols (`→`, `λ`, `Π`, `≔`, `↪`, `∀`, `∃`, `∧`, `∨`, etc.). To input these in Zed, we use **snippets** based on the naming conventions from the [unicode-math](https://ctan.org/pkg/unicode-math) LaTeX package (see the [symbol table](http://mirrors.ctan.org/macros/unicodetex/latex/unicode-math/unimath-symbols.pdf)).

Type a symbol name (e.g. `to`, `lambda`, `forall`, `coloneq`) and select it from the autocomplete menu to insert the corresponding Unicode character.

### Setup

Copy [`snippets/lambdapi.json`](snippets/lambdapi.json) to your Zed snippets directory:

```bash
mkdir -p ~/.config/zed/snippets
cp snippets/lambdapi.json ~/.config/zed/snippets/
```

Restart Zed. The snippets will be available in all `.lp` files via autocomplete.

## Interactive proof goals

Zed extensions cannot open custom panels, so the goals view lives in
Zed's terminal instead: a persistent panel (`tools/lp-goals`) runs the
Lambdapi LSP, and a keybinding sends it your cursor position.

### Setup

Install the tool somewhere on your `PATH`:

```bash
make install-goals        # installs to ~/.local/bin/lp-goals
```

Add the two tasks to `~/.config/zed/tasks.json` (or a project's
`.zed/tasks.json`):

```json
[
  {
    "label": "Lambdapi: Goals Panel",
    "command": "lp-goals",
    "args": ["serve", "$ZED_FILE"],
    "reveal": "always",
    "hide": "never",
    "allow_concurrent_runs": false
  },
  {
    "label": "Lambdapi: Goals at Cursor",
    "command": "lp-goals",
    "args": ["at", "$ZED_FILE", "$ZED_ROW", "$ZED_COLUMN"],
    "reveal": "never",
    "hide": "always"
  }
]
```

Bind a key to the cursor task in `~/.config/zed/keymap.json`:

```json
[
  {
    "context": "Editor",
    "bindings": {
      "ctrl-alt-g": ["task::Spawn", { "task_name": "Lambdapi: Goals at Cursor" }]
    }
  }
]
```

### Usage

1. Open a `.lp` file and run the **Lambdapi: Goals Panel** task
   (`task: spawn` from the command palette). The panel opens in the
   terminal dock and type-checks the file.
2. Put the cursor on a tactic line and press `ctrl-alt-g`. The panel
   shows the open goals and hypotheses at that exact point: at the
   start of the line you see the state *before* the tactic runs, and
   at the end of the line the state *after* it.
3. Edit the proof and save — the panel re-checks the file and refreshes
   the goals at your last position automatically. Errors are shown at
   the bottom of the panel.

For a hands-free experience enable autosave in `settings.json`, so the
panel refreshes shortly after you stop typing:

```json
{ "autosave": { "after_delay": { "milliseconds": 600 } } }
```

The panel reads the file from disk, so unsaved edits are invisible to
it until autosave (or `ctrl-s`) kicks in.

`lp-goals once FILE LINE [COL]` also works as a plain CLI, outside Zed.
It resolves `lambdapi` the same way the extension does (`LAMBDAPI_PATH`,
`LAMBDAPI_LIB_ROOT`/`OPAM_SWITCH_PREFIX`, `LAMBDAPI_MAP_DIRS`).

## Project Structure

```
src/zed-lambdapi.rs              Extension entry point (LSP, labels, DAP)
extension.toml                    Extension manifest
tools/lp-goals                    Terminal proof goals panel
debug_adapter_schemas/
  lambdapi.json                   Schema for `.zed/debug.json` entries
languages/lambdapi/
  config.toml                     Language configuration
  highlights.scm                  Syntax highlighting queries
  outline.scm                     Symbol outline queries
  brackets.scm                    Bracket matching
  folds.scm                       Code folding
  indents.scm                     Auto-indentation
  locals.scm                      Scope-aware highlighting
  tags.scm                        Symbol tags
  injections.scm                  Embedded languages
  overrides.scm                   Context-dependent settings
```

## Debugging proofs

Add a `.zed/debug.json` next to your project (an example lives in `test/.zed/debug.json`):

```json
[
  {
    "label": "Lambdapi: debug current file",
    "adapter": "lambdapi",
    "request": "launch",
    "program": "$ZED_FILE",
    "stopOnEntry": true
  }
]
```

Open a `.lp` file, click the gutter to set a breakpoint on a tactic line (inside a `begin … end` block), and pick the configuration from Zed's **Debug** panel. The debugger pauses before each tactic; the **Variables** view shows each open goal as `goal[i]: "?N: <type>"` and expanding a goal lists its hypotheses. `Step Over` advances one tactic; `Continue` runs to the next breakpoint or the end of the proof.

The tree-sitter grammar lives in a [separate repository](https://github.com/ciaran-matthew-dunne/tree-sitter-lambdapi).

## License

MIT
