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

        let args = vec![
            "lsp".to_string(),
            "--standard-lsp".to_string(),
            lib_root,
        ];

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

    fn label_for_completion(
        &self,
        _language_server_id: &zed::LanguageServerId,
        completion: Completion,
    ) -> Option<CodeLabel> {
        let detail = completion.detail.as_deref().unwrap_or("");
        let name_len = completion.label.len();

        match completion.kind {
            // Tactic keyword. Detail is a one-line description, always
            // present in the initial response.
            Some(zed::lsp::CompletionKind::Keyword) => {
                let code = if detail.is_empty() {
                    completion.label.clone()
                } else {
                    format!("{} {}", completion.label, detail)
                };
                let mut spans = vec![CodeLabelSpan::code_range(0..name_len)];
                if !detail.is_empty() {
                    spans.push(CodeLabelSpan::literal(
                        format!("  {}", detail),
                        Some("comment".to_string()),
                    ));
                }
                Some(CodeLabel {
                    spans,
                    filter_range: (0..name_len).into(),
                    code,
                })
            }
            // Hypothesis introduced by an earlier tactic. Detail carries
            // the type ("h: π (x = y)").
            Some(zed::lsp::CompletionKind::Variable) => {
                let code = if detail.is_empty() {
                    completion.label.clone()
                } else {
                    format!("{} {}", completion.label, detail)
                };
                let mut spans = vec![CodeLabelSpan::code_range(0..name_len)];
                if !detail.is_empty() {
                    spans.push(CodeLabelSpan::literal(
                        format!("  {}", detail),
                        Some("comment".to_string()),
                    ));
                }
                Some(CodeLabel {
                    spans,
                    filter_range: (0..name_len).into(),
                    code,
                })
            }
            // Declared symbol. Detail is filled in lazily by
            // [completionItem/resolve]; the initial render lands here
            // with [detail = ""], then re-renders when resolution
            // completes.
            _ => {
                let prefix = "symbol ".len();
                if detail.is_empty() {
                    let code = format!("symbol {}", completion.label);
                    Some(CodeLabel {
                        spans: vec![
                            CodeLabelSpan::literal(
                                "symbol ", Some("keyword".to_string())),
                            CodeLabelSpan::code_range(
                                prefix..prefix + name_len),
                        ],
                        filter_range: (prefix..prefix + name_len).into(),
                        code,
                    })
                } else {
                    let code = format!(
                        "symbol {} : {}", completion.label, detail);
                    Some(CodeLabel {
                        spans: vec![
                            CodeLabelSpan::literal(
                                "symbol ", Some("keyword".to_string())),
                            CodeLabelSpan::code_range(
                                prefix..prefix + name_len),
                            CodeLabelSpan::literal(" : ", None),
                            CodeLabelSpan::literal(
                                detail, Some("type".to_string())),
                        ],
                        filter_range: (prefix..prefix + name_len).into(),
                        code,
                    })
                }
            }
        }
    }

}

zed::register_extension!(LambdaPiExtension);
