; Code outline/structure for Lambdapi

; Symbol definitions
; Theorem definitions (opaque symbols with proofs)
(symbol_command
  (modifier)* @context
  "symbol" @context
  (uid) @name
  (param_list)*
  ":"
  (term)
) @item

; really, we should have 'inductive_command' here as well??

; Inductive type definitions
(inductive_def
  (uid) @name
  (param_list)*
  (term)) @item

; Constructor definitions
(constructor
  (uid) @name
  (param_list)*
  (term) @context) @item

(rule_command
  "rule" @context
  (rule)
) @item

; Rule definitions
(rule
  ((term) @name
   (hook_arrow) @context
   (term) @name
  )
) @item

; Coerce rule definitions
(coerce_rule_command
  "coerce_rule" @context
  (rule
    (term) @name)) @item

; Unification rule definitions
(unif_rule_command
  "unif_rule" @context
  (unif_rule)
) @item

(unif_rule
  (equation
    (term) @name)) @item

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
  (uid) @name
  (param_list)*
  (term)?) @item

; Query commands
(query_command
  (query) @name) @item

; Proof structure
; (proof
;   "begin" @name) @item

; Comments as documentation
(comment) @annotation
