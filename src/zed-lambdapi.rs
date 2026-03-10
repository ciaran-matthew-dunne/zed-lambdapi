use zed_extension_api::{
    self as zed, lsp::Symbol, CodeLabel, CodeLabelSpan, DebugAdapterBinary,
    DebugTaskDefinition, Result, StartDebuggingRequestArguments,
    StartDebuggingRequestArgumentsRequest,
};

struct LambdaPiExtension;

/// Find lambdapi binary and --lib-root arg from worktree environment.
fn find_lambdapi(
    worktree: &zed::Worktree,
) -> std::result::Result<(String, String, Vec<(String, String)>), String> {
    let env = worktree.shell_env();

    let lambdapi_path = env
        .iter()
        .find(|(k, _)| k == "LAMBDAPI_PATH")
        .map(|(_, v)| v.clone())
        .or_else(|| worktree.which("lambdapi"))
        .ok_or_else(|| "lambdapi not found. Install with: opam install lambdapi")?;

    let lib_root_prefix = env
        .iter()
        .find(|(k, _)| k == "LAMBDAPI_LIB_ROOT")
        .or_else(|| env.iter().find(|(k, _)| k == "OPAM_SWITCH_PREFIX"))
        .map(|(_, v)| v.clone())
        .ok_or_else(|| {
            "Neither LAMBDAPI_LIB_ROOT nor OPAM_SWITCH_PREFIX set. \
             Run: eval $(opam env)"
                .to_string()
        })?;
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

        // Use --standard-lsp: goal info comes from DAP / print diagnostics instead
        Ok(zed::Command {
            command: lambdapi_path,
            args: vec!["lsp".to_string(), "--standard-lsp".to_string(), lib_root],
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

    fn get_dap_binary(
        &mut self,
        _adapter_name: String,
        config: DebugTaskDefinition,
        _user_provided_debug_adapter_path: Option<String>,
        worktree: &zed::Worktree,
    ) -> std::result::Result<DebugAdapterBinary, String> {
        let (lambdapi_path, lib_root, env) = find_lambdapi(worktree)?;

        let config_json: serde_json::Value = serde_json::from_str(&config.config)
            .map_err(|e| format!("Invalid debug config JSON: {e}"))?;
        let program = config_json
            .get("program")
            .and_then(|v| v.as_str())
            .ok_or_else(|| "Missing 'program' in debug config".to_string())?
            .to_string();

        Ok(DebugAdapterBinary {
            command: Some(lambdapi_path),
            arguments: vec!["dap".to_string(), lib_root, program],
            envs: env,
            cwd: Some(worktree.root_path()),
            connection: None,
            request_args: StartDebuggingRequestArguments {
                configuration: config.config,
                request: StartDebuggingRequestArgumentsRequest::Launch,
            },
        })
    }

    fn dap_request_kind(
        &mut self,
        _adapter_name: String,
        _config: serde_json::Value,
    ) -> std::result::Result<StartDebuggingRequestArgumentsRequest, String> {
        Ok(StartDebuggingRequestArgumentsRequest::Launch)
    }
}

zed::register_extension!(LambdaPiExtension);
