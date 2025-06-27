; Local variable definitions and references

; Function/symbol definitions
(symbol_command
  (uid) @definition.function)

; Variable definitions in parameters
(param_list
  (param
    (uid) @definition.parameter))

; Let bindings
(let_term
  (uid) @definition.variable)

; Pattern variables in tactics
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

; Special references
(term_id) @reference.variable
(meta_var) @reference.special
(pattern_var) @reference.special

; Parameter references
(param
  (uid) @reference.parameter)

; Scopes
[
  (source_file)
  (symbol_command)
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
