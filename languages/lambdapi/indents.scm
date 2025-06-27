; Indentation rules for LambdaPi

; Indent inside blocks and groupings
[
  (proof)
  (subproof)
  (param_list)
  (wrapped_term)
  (explicit_term)
  (env)
] @indent

; Indent inside command bodies
(symbol_command
  "symbol" @indent)

(inductive_command
  "inductive" @indent)

(inductive_def
  ":" @indent)

(constructor
  ":" @indent)

(let_term
  "let" @indent)

(let_term
  "in" @indent)

; Indent after rule arrows
(rule
  (hook_arrow) @indent)

(unif_rule
  (hook_arrow) @indent)

; Indent in binders
(binder
  "," @indent)

; Indent after type annotations
(param_list
  ":" @indent)

; Indent inside proof tactics
(proof_step) @indent

(tactic
  "have" @indent)

(tactic
  "apply" @indent)

(tactic
  "refine" @indent)

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

; Align certain constructs
(rule
  (hook_arrow) @align)

(equation
  (equiv) @align)

(symbol_command
  (assign) @align)

(let_term
  (assign) @align)

(inductive_def
  (assign) @align)

; Branch points for alignment
[
  ";"
  "|"
  "with"
] @branch

; Indent continuation lines
(term
  (arrow) @indent.always)

; Special handling for multi-line terms
(saterm) @indent.auto

; Don't indent at the top level
(source_file) @indent.zero
