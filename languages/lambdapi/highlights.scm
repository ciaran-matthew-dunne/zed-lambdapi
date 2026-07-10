; ============================================
; LambdaPi Syntax Highlighting for Zed
; ============================================
; Zed uses LAST-MATCH-WINS precedence, so generic fallbacks go first
; and specific overrides go last.
;
; Zedoki palette mapping:
;   @keyword       — red/pink (#ff6188)  — commands, tactics, flags
;   @attribute     — cyan italic (#78dce8) — modifiers, notation directives
;   @constant      — purple (#ab9df2)    — TYPE
;   @function      — green (#a9dc76)     — symbol/definition names
;   @constructor   — red/pink (#ff6188)  — inductive constructors
;   @type          — cyan (#78dce8)      — inductive type names
;   @comment       — gray italic (#727072)
;   @string        — yellow (#ffd866)    — "...", module path prefixes
;   @variable      — white (#fcfcfa)     — identifiers
;   @label         — orange (#fc9867)    — pattern vars ($x)
;   @variable.special — purple (#ab9df2) — wildcards, metavars
;   @punctuation   — muted gray (#939293)

; ============================================
; COMMENTS
; ============================================

(comment) @comment

; ============================================
; GENERIC FALLBACKS (lowest precedence)
; ============================================

(uid) @variable
(escaped_id) @variable

; ============================================
; KEYWORDS — red/pink
; ============================================

; Core commands
[
  "symbol"
  "inductive"
  "require"
  "open"
  "rule"
  "with"
  "let"
  "in"
  "as"
  "begin"
  "notation"
  "unif_rule"
  "coerce_rule"
  "builtin"
] @keyword

; Proof end keywords
(proof_end) @keyword

; Queries
[
  "assert"
  "assertnot"
  "compute"
  "print"
  "debug"
  "search"
  "type"
  "prover"
  "prover_timeout"
] @keyword

(proofterm_query) @keyword

; Flags
[
  "flag"
  "verbose"
] @keyword

; ============================================
; MODIFIERS — cyan italic
; ============================================

[
  "constant"
  "opaque"
  "injective"
  "sequential"
  "associative"
  "commutative"
  "private"
  "protected"
] @attribute

; Notation modifiers
[
  "left"
  "right"
  "infix"
  "prefix"
  "postfix"
  "quantifier"
] @attribute

; Flag values
[
  "on"
  "off"
] @attribute

; ============================================
; TACTICS — red/pink
; ============================================

[
  "admit"
  "apply"
  "assume"
  "change"
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
] @keyword

; ============================================
; OPERATORS & BINDERS — muted gray
; ============================================

(arrow) @punctuation.delimiter
(assign) @punctuation.delimiter
(equiv) @punctuation.delimiter
(hook_arrow) @punctuation.delimiter
(lambda) @punctuation.delimiter
(pi) @punctuation.delimiter
(turnstile) @punctuation.delimiter

; ============================================
; LITERALS
; ============================================

(int) @number
(float) @number
(string) @string

; ============================================
; PUNCTUATION — muted gray
; ============================================

[
  ","
  ";"
  ":"
  "|"
  "."
  "`"
  "@"
] @punctuation.delimiter

[
  "("
  ")"
  "["
  "]"
  "{"
  "}"
] @punctuation.bracket

; ============================================
; SPECIFIC OVERRIDES (highest precedence)
; ============================================
; Everything below here overrides the generic fallbacks above.

; --- Types — purple ---

"TYPE" @constant

; --- Inductive constructors — red/pink ---

(constructor
  (uid) @constructor)

; --- Builtin bindings (builtin "T" ≔ τ) ---

(builtin_command
  (string) @string.special)

(flag_query
  (string) @string.special)

; --- Variables in binding positions ---
; (let/have/set/generalize binders need no extra pattern: their keywords
; are covered by the keyword arrays above and their (uid) by the fallback)

(param
  (uid) @variable.parameter)

; --- Special variables — purple ---

"_" @variable.special

(meta_var
  "?" @variable.special)

(pattern_var
  "$" @label
  (identifier
    (regular_id) @label))

(pattern_var
  "$" @label
  (identifier
    (escaped_id) @label))

; --- Module paths ---

; Qualified names: Stdlib.Nat → module prefix parts yellow, final part
; white. Three separate patterns (instead of one sibling pattern) avoid
; combinatorial sub-matches on paths with 3+ segments. The last pattern
; marks exactly the prefix segments (each id_part immediately followed
; by a dot); the final segment keeps @variable from the first pattern.
(qualified_id
  (id_part) @variable)

(qualified_id
  "." @punctuation.delimiter)

(qualified_id
  (id_part) @string
  . ".")
