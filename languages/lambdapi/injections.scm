; Language injection rules for embedded content
; Comments can contain markdown for documentation
(comment) @injection.content
(#match? @injection.content "^//[/!]")
(#set! injection.language "markdown")
