# zed-lambdapi

[Zed](https://zed.dev) extension for [Lambdapi](https://github.com/Deducteam/lambdapi), a proof assistant based on the lambda-Pi-calculus modulo rewriting.

## Features

- **Syntax highlighting** — full coverage of Lambdapi syntax: commands, tactics, modifiers, rewrite rules, unicode operators, pattern variables, qualified identifiers, and more
- **LSP integration** — hover info, go-to-definition, document symbols, and diagnostics via the Lambdapi language server
- **Code outline** — navigate symbols, inductive types, constructors, rules, and notations in the symbol panel
- **Code folding** — fold proof blocks, inductive definitions, and rule groups
- **Auto-indentation** — context-aware indentation for proofs, rules, and blocks
- **Bracket matching** — pairs for `()`, `[]`, `{}`, `{| |}`, `/* */`, and `""`
- **Debug adapter** — early DAP support for proof stepping

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

## Syntax Overview

Lambdapi uses Unicode operators with ASCII alternatives:

| Unicode | ASCII | Meaning |
|---------|-------|---------|
| `→` | `->` | Arrow (function type) |
| `λ` | `\` | Lambda abstraction |
| `Π` | `forall` | Pi type |
| `≔` | `:=` | Definition |
| `↪` | `\|->` | Rewrite hook arrow |
| `⊢` | `\|-` | Turnstile |
| `≡` | `==` | Equivalence |

## Project Structure

```
src/zed-lambdapi.rs          Extension entry point (LSP, labels, DAP)
extension.toml                Extension manifest
languages/lambdapi/
  config.toml                 Language configuration
  highlights.scm              Syntax highlighting queries
  outline.scm                 Symbol outline queries
  brackets.scm                Bracket matching
  folds.scm                   Code folding
  indents.scm                 Auto-indentation
  locals.scm                  Scope-aware highlighting
  tags.scm                    Symbol tags
  injections.scm              Embedded languages
  overrides.scm               Context-dependent settings
```

The tree-sitter grammar lives in a [separate repository](https://github.com/ciaran-matthew-dunne/tree-sitter-lambdapi).

## License

MIT
