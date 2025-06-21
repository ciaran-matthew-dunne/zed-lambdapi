; highlights.scm — Tree-sitter highlight queries for LambdaPi

;; Capture comments, strings, and numbers
[(comment)     @comment]
[(string)      @string]
[(integer)     @constant.numeric]
; ["El" @type]

;; Identifiers and qualified identifiers
[(uid)         @variable]
[(qid)         @variable.special]
[(path)        @function]
[(term_id)     @function]

(param) @function
"require" @function
"open" @function

;; Keywords and language constructs
[
  ; Modifiers
  "sequential"  @keyword
  "constant"    @keyword
  "commutative" @keyword
  "injective"   @keyword
  "opaque"      @keyword

  ; Commands
  "symbol"    @keyword
  "inductive" @keyword
  "rule"      @keyword
  "with"      @keyword
  "builtin"   @keyword
  "coerce_rule" @keyword
  "unif_rule" @keyword
  "notation"  @keyword

  ; Proof delimiters
  "begin"     @keyword
  "abort"     @keyword
  "admitted"  @keyword
  "end"       @keyword

  "assert" @keyword
  "assertnot" @keyword
  "compute" @keyword
  "print" @keyword
  "debug" @keyword
  "flag" @keyword
  "prover" @keyword
  "prover_timeout" @keyword
  "verbose" @keyword
  "type" @keyword
  "search" @keyword
  ]

[
    "infix" @attribute
    "postfix" @attribute
    "prefix" @attribute
    "quantifier" @attribute
]

; Operators
[
  "→" @punctuation
  "↪" @punctuation
  "≔" @punctuation
  "≡" @punctuation
  "⊢" @punctuation
]


;; Punctuation
[
  "("  @punctuation.bracket
  ")"  @punctuation.bracket
  "["  @punctuation.bracket
  "]"  @punctuation.bracket
  "{"  @punctuation.bracket
  "}"  @punctuation.bracket
  ","  @punctuation.delimiter
  ":"  @punctuation.delimiter
  ";"  @punctuation.delimiter
]
