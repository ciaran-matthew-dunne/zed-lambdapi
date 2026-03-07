; Tags for navigation and symbol indexing

; Symbol declarations
(symbol_command
  "symbol"
  (uid) @name) @definition.function

; Symbol definitions
(symbol_def_command
  "symbol"
  (uid) @name) @definition.function

; Inductive type definitions
(inductive_def
  (uid) @name) @definition.class

; Constructor definitions
(constructor
  (uid) @name) @definition.method

; Rule definitions
(rule_command
  "rule") @definition.constant

; Notation definitions
(notation_command
  "notation"
  (qid) @name) @definition.constant

; Builtin definitions
(builtin_command
  "builtin"
  (qid) @name) @reference.implementation

; Let bindings (local definitions)
(let_term
  "let"
  (uid) @name) @definition.function

; Module imports
(require_command
  "require"
  (path) @name) @reference.module

(require_as_command
  "require"
  (path) @name) @reference.module
