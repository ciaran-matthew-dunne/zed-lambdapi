; Syntax overrides for Lambdapi

; String scope
(string) @string

; Comment scope (inclusive to handle line comments properly)
(comment) @comment.inclusive

; Inside proofs, different completion behavior might be desired
(proof) @proof
(subproof) @proof

; Pattern variable contexts (where $ is significant)
(rule) @pattern
(unif_rule) @pattern

; Term contexts where unicode symbols are common
(term) @term
(aterm) @term
(saterm) @term
(bterm) @term
