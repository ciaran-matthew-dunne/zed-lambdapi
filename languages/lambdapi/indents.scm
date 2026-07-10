; Indentation rules for Lambdapi
;
; NOTE: Zed skips @indent captures whose node spans a single line, so
; captures must target container nodes that can span multiple lines,
; not individual keyword/operator tokens.

; Blocks and groupings
[
  (proof)
  (subproof)
  (param_list)
  (wrapped_term)
  (explicit_term)
  (env)
] @indent

; Multi-line commands
[
  (symbol_command)
  (symbol_def_command)
  (inductive_command)
  (rule_command)
  (builtin_command)
  (coerce_rule_command)
  (unif_rule_command)
  (notation_command)
] @indent

; Multi-line terms
(let_term) @indent
(binder) @indent

; Proof steps (tactic plus its subproofs)
(proof_step) @indent

; Dedent on closing brackets and keywords
[
  ")"
  "]"
  "}"
  "end"
  "in"
  "admitted"
  "abort"
] @outdent
