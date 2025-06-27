; Tags for navigation and symbol indexing

; Symbol definitions
(symbol_command
  "symbol"
  (uid) @name) @definition.function

; Inductive type definitions
(inductive_def
  (uid) @name) @definition.class

; Constructor definitions
(constructor
  (uid) @name) @definition.method

; Rule definitions - using the left-hand side term as the name
(rule
  (term) @name) @definition.constant

; Coerce rule definitions
(coerce_rule_command
  (rule
    (term) @name)) @definition.constant

; Unification rule definitions
(unif_rule
  (equation
    (term) @name)) @definition.constant

; Notation definitions
(notation_command
  "notation"
  (qid) @name) @definition.operator

; Builtin definitions
(builtin_command
  "builtin"
  (qid) @name) @definition.function

; Let bindings (local definitions)
(let_term
  "let"
  (uid) @name) @definition.variable

; Opaque declarations
(opaque_command
  "opaque"
  (qid) @name) @reference.function

; Module imports
(require_command
  "require"
  (path) @name) @reference.module

(require_as_command
  "require"
  (path) @name
  "as"
  (uid) @name.alias) @reference.module
