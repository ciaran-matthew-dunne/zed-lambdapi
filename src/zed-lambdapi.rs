use zed_extension_api::{self as zed, Result};

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
        let lambdapi_path = worktree
            .which("lambdapi")
            .ok_or_else(|| "LambdaPi not found. Install with: opam install lambdapi")?;

        // Try to detect lib-root dynamically
        let lib_root = "--lib-root=/home/ciaran/.opam/default/lib/lambdapi/lib_root".to_string();

        let args = vec!["lsp".to_string(), lib_root, "--standard-lsp".to_string()];

        Ok(zed::Command {
            command: lambdapi_path,
            args,
            env: worktree.shell_env(),
        })
    }

    // fn language_server_initialization_options(
    //     &mut self,
    //     _language_server_id: &zed::LanguageServerId,
    //     _worktree: &zed::Worktree,
    // ) -> Result<Option<zed::serde_json::Value>> {
    //     // Add any initialization options for the language server
    //     Ok(None)
    // }

    // fn language_server_workspace_configuration(
    //     &mut self,
    //     _language_server_id: &zed::LanguageServerId,
    //     _worktree: &zed::Worktree,
    // ) -> Result<Option<zed::serde_json::Value>> {
    //     // Add workspace configuration if needed
    //     Ok(None)
    // }
}

zed::register_extension!(LambdaPiExtension);
