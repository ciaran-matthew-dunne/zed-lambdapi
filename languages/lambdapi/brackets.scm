; Bracket matching for Lambdapi

; Parentheses
("(" @open ")" @close)

; Square brackets
("[" @open "]" @close)

; Curly braces
("{" @open "}" @close)

; Escaped identifiers: {| |} is a single regex token (escaped_id),
; so bracket matching is not possible at the tree-sitter level.

; String quotes: " " is a single regex token (string),
; so bracket matching is not possible at the tree-sitter level.
