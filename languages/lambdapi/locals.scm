; Local variable definitions and references

; Symbol definitions
(symbol_command
  (uid) @definition.function)

(symbol_def_command
  (uid) @definition.function)

; Variable definitions in parameters
(param_list
  (param
    (uid) @definition.parameter))

; Let bindings
(let_term
  (uid) @definition.variable)

; Tactic variable bindings
(tactic
  "assume"
  (param
    (uid) @definition.variable))

(tactic
  "have"
  (uid) @definition.variable)

(tactic
  "generalize"
  (uid) @definition.variable)

(tactic
  "set"
  (uid) @definition.variable)

; Inductive type definitions
(inductive_def
  (uid) @definition.type)

(constructor
  (uid) @definition.constructor)

; Variable references
(uid) @reference.variable
(qid) @reference.variable
(qid_expl) @reference.variable
(term_id) @reference.variable

; Special references
(meta_var) @reference.special
(pattern_var) @reference.special

; Parameter references
(param
  (uid) @reference.parameter)

; Scopes
[
  (source_file)
  (symbol_command)
  (symbol_def_command)
  (let_term)
  (proof)
  (subproof)
  (binder)
  (param_list)
  (inductive_command)
  (rule_command)
] @scope

; Scope boundaries for let bindings
(let_term
  "in" @scope.boundary)
