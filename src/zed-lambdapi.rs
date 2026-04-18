use zed_extension_api::{
    self as zed, lsp::Completion, lsp::Symbol, CodeLabel, CodeLabelSpan, Result,
};

struct LambdaPiExtension;

/// Lambdapi binary path, --lib-root argument, and shell environment.
type LambdapiEnv = (String, String, Vec<(String, String)>);

/// Find lambdapi binary and --lib-root arg from worktree environment.
fn find_lambdapi(
    worktree: &zed::Worktree,
) -> std::result::Result<LambdapiEnv, String> {
    let env = worktree.shell_env();

    let lambdapi_path = env
        .iter()
        .find(|(k, _)| k == "LAMBDAPI_PATH")
        .map(|(_, v)| v.clone())
        .or_else(|| worktree.which("lambdapi"))
        .ok_or("lambdapi not found. Install with: opam install lambdapi")?;

    let lib_root_prefix = env
        .iter()
        .find(|(k, _)| k == "LAMBDAPI_LIB_ROOT")
        .or_else(|| env.iter().find(|(k, _)| k == "OPAM_SWITCH_PREFIX"))
        .map(|(_, v)| v.clone())
        .ok_or(
            "Neither LAMBDAPI_LIB_ROOT nor OPAM_SWITCH_PREFIX set. \
             Run: eval $(opam env)",
        )?;
    let lib_root = format!("--lib-root={}/lib/lambdapi/lib_root", lib_root_prefix);

    Ok((lambdapi_path, lib_root, env))
}

impl zed::Extension for LambdaPiExtension {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &zed::LanguageServerId,
        worktree: &zed::Worktree,
    ) -> Result<zed::Command> {
        let (lambdapi_path, lib_root, env) = find_lambdapi(worktree)?;

        // --rich-hover: Zed has the Lambdapi tree-sitter grammar, so it
        // renders the markdown hover cards (modifiers + full declaration)
        // correctly. Other clients that lack a Lambdapi highlighter can
        // omit the flag and get the upstream plain-string hover.
        Ok(zed::Command {
            command: lambdapi_path,
            args: vec![
                "lsp".to_string(),
                "--standard-lsp".to_string(),
                "--rich-hover".to_string(),
                lib_root,
            ],
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

    fn label_for_completion(
        &self,
        _language_server_id: &zed::LanguageServerId,
        completion: Completion,
    ) -> Option<CodeLabel> {
        let detail = completion.detail.as_deref().unwrap_or("");

        match completion.kind {
            // Tactic keyword
            Some(zed::lsp::CompletionKind::Keyword) => {
                let code = format!("{} {}", completion.label, detail);
                let name_len = completion.label.len();
                Some(CodeLabel {
                    spans: vec![
                        CodeLabelSpan::code_range(0..name_len),
                        CodeLabelSpan::literal(
                            format!("  {}", detail),
                            Some("comment".to_string()),
                        ),
                    ],
                    filter_range: (0..name_len).into(),
                    code,
                })
            }
            // Symbol (Function, Constant, etc.)
            _ => {
                let code = format!("symbol {} : {}", completion.label, detail);
                let prefix = "symbol ".len();
                let name_len = completion.label.len();
                Some(CodeLabel {
                    spans: vec![
                        CodeLabelSpan::literal("symbol ", Some("keyword".to_string())),
                        CodeLabelSpan::code_range(prefix..prefix + name_len),
                        CodeLabelSpan::literal(" : ", None),
                        CodeLabelSpan::literal(detail, Some("type".to_string())),
                    ],
                    filter_range: (prefix..prefix + name_len).into(),
                    code,
                })
            }
        }
    }

}

zed::register_extension!(LambdaPiExtension);
