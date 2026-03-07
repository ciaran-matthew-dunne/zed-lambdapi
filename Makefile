GRAMMAR_DIR := /home/ciaran/prog/tree-sitter-lambdapi
GRAMMAR_SRC := $(GRAMMAR_DIR)/grammars
EXT_DIR     := $(shell pwd)
ZED_LOG     := $(HOME)/.local/share/zed/logs/Zed.log
LSP_LOG     := /tmp/lambdapi_lsp_log.txt

# Default: regenerate grammar, commit, update rev, and prompt to install
all: grammar commit-grammar sync
	@echo ""
	@echo "Ready. In Zed: 'zed: install dev extension' → select $(EXT_DIR)"

# --- Grammar ---

# Regenerate parser.c from grammar.js
grammar:
	cd $(GRAMMAR_SRC) && tree-sitter generate --abi=14

# Run tree-sitter tests
test:
	cd $(GRAMMAR_SRC) && tree-sitter test

# Parse a file: make parse F=file.lp
parse:
	cd $(GRAMMAR_SRC) && tree-sitter parse "$(F)"

# Test highlighting: make highlight F=file.lp
highlight:
	cd $(GRAMMAR_SRC) && tree-sitter highlight "$(F)"

# --- Git (tree-sitter-lambdapi) ---

# Commit all changes in tree-sitter-lambdapi
commit-grammar:
	cd $(GRAMMAR_DIR) && \
	if [ -n "$$(git status --porcelain)" ]; then \
		git add -A && \
		git commit -m "update grammar"; \
	else \
		echo "tree-sitter-lambdapi: nothing to commit"; \
	fi

# Push tree-sitter-lambdapi to remote
push-grammar:
	cd $(GRAMMAR_DIR) && git push

# --- Extension sync ---

# Update extension.toml rev to latest tree-sitter-lambdapi commit
sync:
	@REV=$$(git -C $(GRAMMAR_DIR) rev-parse HEAD) && \
	sed -i 's|^rev = ".*"|rev = "'$$REV'"|' extension.toml && \
	echo "extension.toml rev = $$REV"

# Switch extension.toml to local file:// URL
local:
	@sed -i 's|^repository = "https://.*"|repository = "file://$(GRAMMAR_DIR)"|' extension.toml
	@echo "Switched to local grammar"

# Switch extension.toml to GitHub URL
remote:
	@sed -i 's|^repository = "file://.*"|repository = "https://github.com/ciaran-matthew-dunne/tree-sitter-lambdapi"|' extension.toml
	@echo "Switched to remote grammar"

# --- Full workflows ---

# Dev cycle: regenerate, commit grammar, sync rev, ready to install
dev: grammar commit-grammar sync
	@echo ""
	@echo "Ready. In Zed: 'zed: install dev extension' → select $(EXT_DIR)"

# Release: switch to remote, commit everything, push both repos
release: grammar commit-grammar push-grammar remote sync
	@REV=$$(git -C $(GRAMMAR_DIR) rev-parse HEAD) && \
	echo "Released with grammar rev $$REV"

# Show current state
status:
	@echo "=== extension.toml ==="
	@grep -A3 '\[grammars.lambdapi\]' extension.toml
	@echo ""
	@echo "=== tree-sitter-lambdapi ==="
	@git -C $(GRAMMAR_DIR) log --oneline -3
	@echo ""
	@git -C $(GRAMMAR_DIR) status --short

# --- Logs ---

# Tail Zed editor logs (live)
zed-logs:
	tail -f $(ZED_LOG)

# Tail lambdapi LSP server logs (live)
lsp-logs:
	tail -f $(LSP_LOG)

# Show recent Zed errors
zed-errors:
	@grep -n 'ERROR\|WARN' $(ZED_LOG) | tail -30

# Show recent LSP log (last 50 lines)
lsp-tail:
	@tail -50 $(LSP_LOG)

# Watch both Zed and LSP logs side by side (requires tmux or two terminals)
logs:
	@echo "=== Zed errors (recent) ==="
	@grep 'ERROR' $(ZED_LOG) | tail -10
	@echo ""
	@echo "=== LSP log (recent) ==="
	@tail -20 $(LSP_LOG)

# --- LSP integration tests ---

# Run LSP integration tests against test/ corpus
test-lsp:
	python3 tools/test-lsp.py

# Run LSP tests with verbose output
test-lsp-v:
	python3 tools/test-lsp.py -v

# Run all tests (grammar + LSP)
test-all: test test-lsp

.PHONY: all grammar test parse highlight commit-grammar push-grammar sync local remote dev release status zed-logs lsp-logs zed-errors lsp-tail logs test-lsp test-lsp-v test-all
