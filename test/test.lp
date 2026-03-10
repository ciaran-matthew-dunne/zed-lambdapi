// Comprehensive test file for zed-lambdapi syntax highlighting
// Exercises every grammar feature using the standard library

// ============================================
// Require/open (module system)
// ============================================
require open
  Stdlib.Set Stdlib.HOL Stdlib.Eq
  Stdlib.Prop Stdlib.Bool Stdlib.Classic
  Stdlib.Nat Stdlib.List;


/* ============================================
   Block comment: /* nested */ comments work
   ============================================ */

// ============================================
// Symbol declarations — all modifier combos
// ============================================

// Constant
constant symbol my_set : Set;
symbol foo : TYPE;

// Injective
injective symbol my_inj : τ nat → τ nat;

// Private
private symbol internal_helper : τ nat;

// Protected
protected symbol api_sym : τ nat → τ nat;


// Implicit arguments [...]
symbol first [a] : τ a → τ a → τ a;
rule first $x _ ↪ $x;

// ============================================
// Symbol definitions (≔)
// ============================================

symbol four ≔ _0 +1 +1 +1 +1;

// Lambda and let expressions
symbol id_nat ≔ λ (x : τ nat), x;

symbol use_let ≔
  let x ≔ _0 +1 +1 in
  let y ≔ x +1 in
  y;

// Pi types
symbol const_fn : Π (x : τ nat) (y : τ nat), τ nat;
rule const_fn $x _ ↪ $x;

// Explicit application with @
symbol explicit_example ≔ @first nat _0 (_0 +1);

// ============================================
// Inductive types
// ============================================

// Simple inductive
inductive Color : TYPE ≔
| red   : Color
| green : Color
| blue  : Color;

constant symbol color : Set;
rule τ color ↪ Color;

// Parameterized inductive
(a : Set) inductive Tree : TYPE ≔
| leaf : Tree a
| node : τ a → Tree a → Tree a → Tree a;

constant symbol tree : Set → Set;
rule τ (tree $a) ↪ Tree $a;

// ============================================
// Rules — single, with, sequential
// ============================================

// Single rule
symbol color_id : Color → Color;
rule color_id $c ↪ $c;

// Rules with 'with'
symbol double : τ nat → τ nat;
rule double _0 ↪ _0
with double ($n +1) ↪ (double $n) +1 +1;

// Sequential modifier
sequential symbol fib : τ nat → τ nat;
rule fib _0 ↪ _0;
rule fib (_0 +1) ↪ _0 +1;
rule fib ($n +1 +1) ↪ fib ($n +1) + fib $n;

// Pattern variables ($) and wildcards (_)
symbol tree_size [a] : Tree a → τ nat;
rule tree_size leaf ↪ _0
with tree_size (node _ $l $r) ↪ (tree_size $l) + (tree_size $r) +1;


// ============================================
// Notations — infix, prefix, postfix, quantifier
// ============================================

// Infix left
symbol my_add : τ nat → τ nat → τ nat;
notation my_add infix left 20;
rule _0 my_add $y ↪ $y
with ($x +1) my_add $y ↪ ($x my_add $y) +1;

// Prefix
symbol dbl_prefix : τ nat → τ nat;
notation dbl_prefix prefix 50;
rule dbl_prefix _0 ↪ _0;
rule dbl_prefix ($n +1) ↪ (dbl_prefix $n) +1 +1;

// Quantifier notation is set up by FOL (∀, ∃)

// ============================================
// Builtin declarations
// ============================================

// Builtin syntax (eq/refl/eqind already declared by stdlib)
constant symbol MySet : Set;
builtin "T" ≔ τ;

// ============================================
// Queries
// ============================================

assert ⊢ double (_0 +1 +1) ≡ _0 +1 +1 +1 +1;
assertnot ⊢ _0 ≡ _0 +1;
compute double (_0 +1 +1 +1);
type double;
print double;

// ============================================
// Escaped identifiers
// ============================================

symbol {|my symbol|} : τ nat → τ nat;
rule {|my symbol|} $n ↪ $n +1;

// ============================================
// Flags and settings
// ============================================

flag "print_implicits" on;
flag "print_implicits" off;

// ============================================
// Unification rules
// ============================================

unif_rule
  π $p ≡ Π x:$t, π $q.[x]
↪ [ $p ≡ `∀ x:$t, $q.[x] ];

// ============================================
// Coercion rules
// ============================================

coerce_rule
  coerce 𝔹 Prop $x ↪ istrue $x;

// ============================================
// Proofs — tactics showcase
// ============================================

// simplify + reflexivity
opaque symbol
  double_zero : π (double _0 = _0) ≔
begin
  simplify;
  reflexivity;
end;

// induction, assume, rewrite
opaque symbol
  add_0_r (n : τ nat) : π (n + _0 = n) ≔
begin
  induction
  { reflexivity; }
  { assume n ih;
    simplify;
    reflexivity };
end;


// apply, subproofs {}
opaque symbol and_comm [p q] : π (p ∧ q) → π (q ∧ p) ≔
begin
  assume p q h;
  apply ∧ᵢ
  { apply ∧ₑ₂ h }
  { apply ∧ₑ₁ h };
end;

// refine
opaque symbol or_comm [p q] :
  π (p ∨ q) → π (q ∨ p) ≔
begin
  assume p q h;
  refine ∨ₑ h _ _
  { assume hp; apply ∨ᵢ₂; apply hp }
  { assume hq; apply ∨ᵢ₁; apply hq };
end;

// have tactic
symbol A_ty : TYPE;
symbol B_ty : TYPE;
symbol b_val : B_ty;
symbol f_ab : B_ty → A_ty;

opaque symbol have_demo : A_ty ≔
begin
  have x : B_ty { apply b_val };
  apply f_ab;
  apply x;
end;

// symmetry
opaque symbol sym_example (n m : τ nat) : π (n = m) → π (m = n) ≔
begin
  assume n m h;
  symmetry;
  apply h;
end;

// Classical: double negation elimination via excluded middle
opaque symbol dne [p] : π (¬ (¬ p)) → π p ≔
begin
  assume p nnp;
  apply ∨ₑ (em p)
  { assume h; refine h }
  { assume np; apply ⊥ₑ; refine nnp np };
end;

// Proof with 'admitted' (incomplete proof, syntax test)
// symbol admitted_example : π (⊤) ≔ begin admitted;

// ============================================
// Stdlib types in action
// ============================================

// Boolean operations
symbol my_xor (a b : 𝔹) ≔
  (a or (not b)) and ((not a) or b);

// List operations
symbol my_list ≔
  _0 ∷ (_0 +1) ∷ (_0 +1 +1) ∷ □;
symbol my_length ≔ size my_list;
// ============================================
// Unicode operators and ASCII alternatives
// ============================================

// → (arrow), λ (lambda), Π (pi), ≔ (assign)
// ↪ (hook arrow), ≡ (equiv), ⊢ (turnstile)
// ∧ ∨ ¬ ⇒ ∀ ∃ ⊤ ⊥ (logical connectives)
// These are all exercised throughout this file.

// ============================================
// Associative/commutative modifiers
// ============================================

constant symbol G : TYPE;
associative commutative symbol op : G → G → G;
notation op infix 40;

// ============================================
// Integer literals and floats
// ============================================

// Integer literals (nat builtins if configured)
symbol int_test ≔ _0 +1 +1 +1 +1 +1;

// ============================================
// Qualified identifiers
// ============================================

// Qualified identifiers are tested in highlighting via the qualified_id rule
// (e.g. Stdlib.Set in the require statements above)

// ============================================
// Complex proof: addition associativity
// ============================================

opaque symbol plus_assoc (a b c : τ nat) :
  π ((a + b) + c = a + (b + c))
≔ begin
  induction
  { assume b c; simplify; reflexivity }
  { assume n ih b c;
    simplify;
    reflexivity };
end;

// ============================================
// Proof using rewrite with a hypothesis
// ============================================

opaque symbol eq_double (n m : τ nat) :
  π (n = m) → π (double n = double m)
≔ begin
  assume n m h;
  rewrite h;
  print;
  reflexivity;
end;

// Proof with symmetry and rewrite
opaque symbol eq_trans [a] (x y z : τ a) :
  π (x = y) → π (y = z) → π (x = z)
≔ begin
  assume a x y z h1 h2;
  rewrite h1;
  apply h2;
end;
