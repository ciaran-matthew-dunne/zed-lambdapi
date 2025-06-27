; Code folding rules for LambdaPi

; Fold proof blocks
(proof) @fold

; Fold subproofs
(subproof) @fold

; Fold multi-line commands
(symbol_command) @fold
(inductive_command) @fold
(rule_command) @fold
(builtin_command) @fold
(coerce_rule_command) @fold
(unif_rule_command) @fold
(notation_command) @fold

; Fold let expressions
(let_term) @fold

; Fold parameter lists when they span multiple lines
(param_list
  "("
  ")" @fold.stop) @fold

(param_list
  "["
  "]" @fold.stop) @fold

; Fold environments
(env) @fold

; Fold wrapped and explicit terms
(wrapped_term) @fold
(explicit_term) @fold

; Fold inductive definitions
(inductive_def) @fold

; Fold binders
(binder) @fold

; Fold comments
(comment) @fold

; Fold complex terms
(term
  (arrow)) @fold

; Fold equation lists in unif rules
(unif_rule
  "["
  "]" @fold.stop) @fold
