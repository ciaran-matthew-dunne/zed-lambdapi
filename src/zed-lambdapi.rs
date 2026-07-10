use zed_extension_api::{
    self as zed,
    lsp::Completion, lsp::Symbol,
    CodeLabel, CodeLabelSpan, Result,
    DebugAdapterBinary, DebugConfig, DebugRequest, DebugScenario,
    DebugTaskDefinition,
    StartDebuggingRequestArguments, StartDebuggingRequestArgumentsRequest,
};

struct LambdaPiExtension;

/// The lp-goals companion tool (goals panel + LSP bridge), embedded in
/// the extension and materialized into the extension work dir when the
/// language server starts. Single source of truth: tools/lp-goals.
const LP_GOALS_SOURCE: &str = include_str!("../tools/lp-goals");

/// Write the embedded lp-goals script into the extension work dir
/// (which is the extension's cwd; Zed resolves the relative command
/// path against it). Rewrites only when the content changed, e.g.
/// after an extension update.
fn materialize_lp_goals() -> Result<String, String> {
    let path = "lp-goals".to_string();
    let needs_write = match std::fs::read_to_string(&path) {
        Ok(current) => current != LP_GOALS_SOURCE,
        Err(_) => true,
    };
    if needs_write {
        std::fs::write(&path, LP_GOALS_SOURCE)
            .map_err(|e| format!("failed to write lp-goals: {e}"))?;
        zed::make_file_executable(&path)?;
    }
    Ok(path)
}

/// Lambdapi binary path, optional --lib-root argument, optional
/// --map-dir flags, and shell environment.
type LambdapiEnv =
    (String, Option<String>, Vec<String>, Vec<(String, String)>);

/// Find lambdapi binary, --lib-root arg, and any --map-dir overrides
/// from worktree environment.
///
/// Set `LAMBDAPI_MAP_DIRS` in the worktree shell env to override
/// installed packages with in-tree paths.  Format is one or more
/// `MOD:DIR` entries separated by commas:
///   `LAMBDAPI_MAP_DIRS=pp2lp:/path/to/lp,foo:/path/to/foo`
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

    // Without LAMBDAPI_LIB_ROOT or an opam environment, omit --lib-root
    // and let lambdapi use its built-in default, so non-opam installs
    // (source builds, system packages) still get a working server.
    let lib_root = env
        .iter()
        .find(|(k, _)| k == "LAMBDAPI_LIB_ROOT")
        .or_else(|| env.iter().find(|(k, _)| k == "OPAM_SWITCH_PREFIX"))
        .map(|(_, v)| format!("--lib-root={}/lib/lambdapi/lib_root", v));

    let map_dirs: Vec<String> = env
        .iter()
        .find(|(k, _)| k == "LAMBDAPI_MAP_DIRS")
        .map(|(_, v)| {
            v.split(',')
                .map(str::trim)
                .filter(|s| !s.is_empty())
                .map(|s| format!("--map-dir={}", s))
                .collect()
        })
        .unwrap_or_default();

    Ok((lambdapi_path, lib_root, map_dirs, env))
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
        let (lambdapi_path, lib_root, map_dirs, env) = find_lambdapi(worktree)?;

        let mut args = vec!["lsp".to_string(), "--standard-lsp".to_string()];
        args.extend(lib_root);
        args.extend(map_dirs);

        // Launch the server through the embedded lp-goals bridge, a
        // transparent LSP proxy, so the terminal goals panel can
        // attach to this very session (same document state, unsaved
        // edits included). Set LAMBDAPI_NO_BRIDGE to launch lambdapi
        // directly; set LAMBDAPI_LP_GOALS to a script path to use a
        // development copy instead of the embedded one.
        //
        // The bridge is a Python script run via its shebang, so it
        // needs a Unix-like OS and python3 on PATH; anywhere that
        // doesn't hold, launch lambdapi directly instead.
        let (os, _arch) = zed::current_platform();
        let no_bridge = env.iter().any(|(k, _)| k == "LAMBDAPI_NO_BRIDGE")
            || matches!(os, zed::Os::Windows)
            || worktree.which("python3").is_none();
        if !no_bridge {
            let script = env
                .iter()
                .find(|(k, _)| k == "LAMBDAPI_LP_GOALS")
                .map(|(_, v)| Ok(v.clone()))
                .unwrap_or_else(materialize_lp_goals);
            // Fail open: if the script can't be materialized, run
            // lambdapi directly rather than breaking the LSP.
            if let Ok(script) = script {
                let mut bridge_args =
                    vec!["bridge".to_string(), "--".to_string(), lambdapi_path];
                bridge_args.extend(args);
                return Ok(zed::Command {
                    command: script,
                    args: bridge_args,
                    env,
                });
            }
        }

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

    // --- DAP (proof debugger) ----------------------------------------

    fn get_dap_binary(
        &mut self,
        _adapter_name: String,
        config: DebugTaskDefinition,
        user_provided_debug_adapter_path: Option<String>,
        worktree: &zed::Worktree,
    ) -> Result<DebugAdapterBinary, String> {
        let (lambdapi_path, lib_root, map_dirs, env) = find_lambdapi(worktree)?;
        let command = user_provided_debug_adapter_path.unwrap_or(lambdapi_path);
        let mut arguments = vec!["dap".to_string()];
        arguments.extend(lib_root);
        arguments.extend(map_dirs);
        Ok(DebugAdapterBinary {
            command: Some(command),
            arguments,
            envs: env,
            cwd: None,
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
    ) -> Result<StartDebuggingRequestArgumentsRequest, String> {
        // Lambdapi runs the type-checker in-process; there's nothing
        // to attach to, so every session is a launch.
        Ok(StartDebuggingRequestArgumentsRequest::Launch)
    }

    fn dap_config_to_scenario(
        &mut self,
        config: DebugConfig,
    ) -> Result<DebugScenario, String> {
        let launch = match config.request {
            DebugRequest::Launch(l) => l,
            DebugRequest::Attach(_) => {
                return Err(
                    "lambdapi adapter only supports `launch`".to_string()
                );
            }
        };
        let stop_on_entry = config.stop_on_entry.unwrap_or(true);
        let mut cfg = serde_json::Map::new();
        cfg.insert("program".into(), launch.program.into());
        cfg.insert("stopOnEntry".into(), stop_on_entry.into());
        // [debug] is lambdapi-specific and not in DebugConfig; users
        // who need it set it directly in `.zed/debug.json`.
        if let Some(cwd) = launch.cwd {
            cfg.insert("cwd".into(), cwd.into());
        }
        Ok(DebugScenario {
            label: config.label,
            adapter: config.adapter,
            build: None,
            config: serde_json::Value::Object(cfg).to_string(),
            tcp_connection: None,
        })
    }

    // --- LSP completion labelling ------------------------------------

    fn label_for_completion(
        &self,
        _language_server_id: &zed::LanguageServerId,
        completion: Completion,
    ) -> Option<CodeLabel> {
        let detail = completion.detail.as_deref().unwrap_or("");
        let name_len = completion.label.len();

        match completion.kind {
            // Tactic keyword (detail is a one-line description, always
            // present in the initial response) or hypothesis introduced
            // by an earlier tactic (detail carries the type,
            // "h: π (x = y)").
            Some(zed::lsp::CompletionKind::Keyword)
            | Some(zed::lsp::CompletionKind::Variable) => {
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
            // Module path (require/open and qualified-name
            // completion). Rendered as a literal, NOT as code: a bare
            // dotted path doesn't parse, and tree-sitter's error
            // recovery then finds keyword fragments inside the
            // identifiers ("on" in "Stdlib.Conj") and highlights
            // them.
            Some(zed::lsp::CompletionKind::Module) => {
                Some(CodeLabel {
                    spans: vec![CodeLabelSpan::literal(
                        completion.label.clone(),
                        None,
                    )],
                    filter_range: (0..name_len).into(),
                    code: String::new(),
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
