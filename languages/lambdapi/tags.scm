; Tags for navigation and symbol indexing

; Symbol definitions
(symbol_command
  "symbol"
  (uid) @name) @definition.function

; Builtin definitions
(builtin_command
  "builtin"
  (qid) @name) @reference.implementation

; Let bindings (local definitions)
(let_term
  "let"
  (uid) @name) @definition.function
