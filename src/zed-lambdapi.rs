use zed_extension_api::{self as zed, lsp::Symbol, CodeLabel, CodeLabelSpan, Result};

struct LambdaPiExtension;

impl zed::Extension for LambdaPiExtension {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &zed::LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<zed::Command> {
        let env = worktree.shell_env();

        // Binary: LAMBDAPI_PATH env var, or find on PATH
        let lambdapi_path = env
            .iter()
            .find(|(k, _)| k == "LAMBDAPI_PATH")
            .map(|(_, v)| v.clone())
            .or_else(|| worktree.which("lambdapi"))
            .ok_or_else(|| "lambdapi not found. Install with: opam install lambdapi")?;

        // Lib root priority: LAMBDAPI_LIB_ROOT > OPAM_SWITCH_PREFIX
        let lib_root_prefix = env
            .iter()
            .find(|(k, _)| k == "LAMBDAPI_LIB_ROOT")
            .or_else(|| env.iter().find(|(k, _)| k == "OPAM_SWITCH_PREFIX"))
            .map(|(_, v)| v.clone())
            .ok_or_else(|| {
                "Neither LAMBDAPI_LIB_ROOT nor OPAM_SWITCH_PREFIX set. \
                 Run: eval $(opam env)".to_string()
            })?;
        let lib_root = format!("--lib-root={}/lib/lambdapi/lib_root", lib_root_prefix);

        // Don't pass --standard-lsp: enables extended diagnostics with goal_info
        let args = vec!["lsp".to_string(), lib_root];

        Ok(zed::Command {
            command: lambdapi_path,
            args,
            env,
        })
    }

    fn label_for_symbol(
        &self,
        _language_server_id: &zed::LanguageServerId,
        symbol: Symbol,
    ) -> Option<CodeLabel> {
        let (prefix, highlight) = match symbol.kind {
            zed::lsp::SymbolKind::Function => ("symbol ", "keyword"),
            zed::lsp::SymbolKind::Constant => ("symbol ", "keyword"),
            zed::lsp::SymbolKind::Variable => ("symbol ", "keyword"),
            zed::lsp::SymbolKind::Class => ("inductive ", "keyword"),
            zed::lsp::SymbolKind::Constructor => ("| ", "punctuation.delimiter"),
            _ => return None,
        };

        let code = format!("{}{} : TYPE", prefix, symbol.name);
        let prefix_len = prefix.len();
        let name_len = symbol.name.len();

        Some(CodeLabel {
            spans: vec![
                CodeLabelSpan::literal(prefix, Some(highlight.to_string())),
                CodeLabelSpan::code_range(prefix_len..prefix_len + name_len),
            ],
            filter_range: (prefix_len..prefix_len + name_len).into(),
            code,
        })
    }
}

zed::register_extension!(LambdaPiExtension);
