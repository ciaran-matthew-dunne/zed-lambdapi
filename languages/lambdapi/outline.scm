; Code outline/structure for Lambdapi

; Symbol declarations
(symbol_command
  (modifier)* @context
  "symbol" @context
  (uid) @name) @item

; Symbol definitions
(symbol_def_command
  (modifier)* @context
  "symbol" @context
  (uid) @name) @item

; Inductive type definitions
(inductive_def
  (uid) @name) @item

; Constructor definitions
(constructor
  (uid) @name) @item

; Rule definitions
(rule_command
  "rule" @context
  (rule)) @item

(rule
  (term) @name
  (hook_arrow) @context
  (term) @context) @item

; Coerce rule definitions
(coerce_rule_command
  "coerce_rule" @context
  (rule
    (term) @name)) @item

; Unification rule definitions
(unif_rule_command
  "unif_rule" @context) @item

; Notation definitions
(notation_command
  "notation" @context
  (qid) @name
  (notation) @context) @item

; Builtin definitions
(builtin_command
  "builtin" @context
  (string) @name
  (qid) @name) @item

; Let bindings in proofs
(let_term
  "let" @context
  (uid) @name) @item

; Query commands
(query_command
  (query) @name) @item

; Comments as documentation
(comment) @annotation
