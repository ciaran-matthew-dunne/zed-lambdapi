; Keywords
[
  "abort"
  "admit"
  "admitted"
  "apply"
  "as"
  "assert"
  "assertnot"
  "associative"
  "assume"
  "begin"
  "builtin"
  "coerce_rule"
  "commutative"
  "compute"
  "constant"
  "end"
  "eval"
  "eval"
  "fail"
  "flag"
  "generalize"
  "have"
  "in"
  "induction"
  "inductive"
  "infix"
  "injective"
  "left"
  "let"
  "notation"
  "off"
  "on"
  "opaque"
  "open"
  "orelse"
  "postfix"
  "prefix"
  "print"
  "private"
  "protected"
  "prover"
  "prover_timeout"
  "quantifier"
  "refine"
  "reflexivity"
  "remove"
  "repeat"
  "require"
  "rewrite"
  "right"
  "rule"
  "search"
  "sequential"
  "set"
  "simplify"
  "solve"
  "symbol"
  "symmetry"
  "try"
  "type"
  "TYPE"
  "unif_rule"
  "verbose"
  "why3"
  "with"
] @keyword

; Operators
[
  "→"
  "->"
  "≔"
  ":="
  "≡"
  "=="
  "↪"
  "|->"
  "⊢"
  "|-"
  ":"
  ","
  ";"
  "."
  "|"
  "_"
  "`"
  "@"
  "$"
  "?"
  "+"
  "-"
] @operator

; Special symbols
[
  "λ"
  "\\"
  "Π"
  "forall"
] @keyword.function

; Delimiters
[
  "("
  ")"
  "["
  "]"
  "{"
  "}"
] @punctuation.bracket

; Identifiers
(uid) @variable
(param "_" @variable.builtin)
(param (uid) @variable.parameter)
(regular_id) @variable
(escaped_id) @variable

; Qualified identifiers
(qid) @variable
(qid_expl) @variable
(qualified_id) @variable
(path) @namespace

; Special identifiers
(meta_var) @variable.special
(pattern_var) @variable.special

; Type annotations
(param_list
  ":" @punctuation.delimiter
  (term) @type)

(symbol_command
  ":" @punctuation.delimiter
  (term) @type)

(let_term
  ":" @punctuation.delimiter
  (term) @type)

(constructor
  ":" @punctuation.delimiter
  (term) @type)

(inductive_def
  ":" @punctuation.delimiter
  (term) @type)

(binder
  ":" @punctuation.delimiter
  (term) @type)

(assert_query
  ":" @punctuation.delimiter
  (term) @type)

; Function/symbol definitions
(symbol_command
  "symbol" @keyword
  (uid) @function.definition)

(constructor
  (uid) @constructor)

(inductive_def
  (uid) @type.definition)

; Rules
(rule
  (term) @function.special
  (term) @function.special)

(unif_rule
  (equation) @function.special)

; Literals
(int) @number
(float) @number.float
(string) @string
(priority) @number

; Comments
(comment) @comment

; Proof tactics
(tactic
  [
    "admit"
    "apply"
    "assume"
    "eval"
    "fail"
    "generalize"
    "have"
    "induction"
    "orelse"
    "refine"
    "reflexivity"
    "remove"
    "repeat"
    "rewrite"
    "set"
    "simplify"
    "solve"
    "symmetry"
    "try"
    "why3"
  ] @keyword.function)

; Special tactic constructs
(tactic
  "have"
  (uid) @variable.definition
  ":"
  (term) @type)

(tactic
  "set"
  (uid) @variable.definition)

(tactic
  "generalize"
  (uid) @variable)

(tactic
  "assume"
  (param) @variable.parameter)

; Modifiers
(modifier) @keyword.modifier
(exposition) @keyword.modifier

; Builtin references
(builtin_command
  "builtin" @keyword
  (string) @string.special
  (qid) @function.builtin)

; Query types
(assert_query
  ["assert" "assertnot"] @keyword.function)
(compute_query "compute" @keyword.function)
(print_query "print" @keyword.function)
(proofterm_query) @keyword.function
(flag_query "flag" @keyword.function)
(prover_query "prover" @keyword.function)
(prover_timeout_query "prover_timeout" @keyword.function)
(verbose_query "verbose" @keyword.function)
(type_query "type" @keyword.function)
(search_query "search" @keyword.function)

; Debug operators
(debug_query
  ["+" "-"] @operator)

; Proof structure
(proof_end) @keyword
(proof "begin" @keyword)
(subproof ["{" "}"] @punctuation.bracket)

; Error highlighting for incomplete constructs
(ERROR) @error
