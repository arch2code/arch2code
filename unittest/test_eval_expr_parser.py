#!/usr/bin/env python3
"""Unit tests for the integer eval-expression parser and IR (Stage E0).

Exercises precedence, associativity, unary operators, parentheses, $clog2,
both $symbol forms, and rejection of out-of-grammar input (real literals,
sized literals, stray operators, unbalanced parentheses, unresolved
symbols)."""

import sys
import os

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.evalExpr import (
    parse, unparse, symbolKeys,
    Num, Sym, Unary, Bin, Clog2, EvalParseError,
)


# Bare symbols qualify to "NAME/ip_test"; unknown names are unresolved.
_KNOWN = {'A', 'B', 'C', 'N', 'MASK', 'W', 'IP_DATA_WIDTH', 'DATA_BITS'}


def _qualify(name):
    return f"{name}/ip_test" if name in _KNOWN else None


def _sym(name):
    return Sym(f"{name}/ip_test")


def _expect(expr, node):
    got = parse(expr, qualify=_qualify)
    if got != node:
        raise AssertionError(f"{expr!r}\n  expected {node}\n  got      {got}")


def _expectReject(expr):
    try:
        parse(expr, qualify=_qualify)
    except EvalParseError:
        return
    raise AssertionError(f"expected EvalParseError for {expr!r}")


def test_literals():
    # Unsized decimal (base 10 is the Num default).
    _expect("255", Num(255))
    _expect("4_095", Num(4095))
    # SV based literals: the authored radix is recorded so emitters can
    # re-spell the literal in the base the developer wrote.
    _expect("8'hFF", Num(255, 16))
    _expect("'hff", Num(255, 16))
    _expect("'b1010", Num(10, 2))
    _expect("12'd4095", Num(4095, 10))
    # Octal is accepted but recorded as hex (no clean C octal spelling).
    _expect("'o17", Num(15, 16))
    # Signedness marker is accepted and does not change the value or base.
    _expect("'shFF", Num(255, 16))
    # Underscore separators inside the value.
    _expect("16'hFF_FF", Num(0xFFFF, 16))


def test_symbol_forms():
    # Bare symbol is qualified via the callback.
    _expect("$IP_DATA_WIDTH", _sym('IP_DATA_WIDTH'))
    # Already-qualified ${name/context} parses directly; qualify not used.
    assert parse("${IP_DATA_WIDTH/ip_test}") == Sym("IP_DATA_WIDTH/ip_test")
    return True


def test_precedence():
    # '*' binds tighter than '+': multiply sits below the add.
    _expect("$A + $B * 2", Bin('+', _sym('A'), Bin('*', _sym('B'), Num(2))))
    # Shift is lower precedence than '+'.
    _expect("$A + $B << 2", Bin('<<', Bin('+', _sym('A'), _sym('B')), Num(2)))
    # Bitwise ordering: & tighter than ^ tighter than |.
    _expect("$A | $B ^ $C & 1",
            Bin('|', _sym('A'),
                Bin('^', _sym('B'), Bin('&', _sym('C'), Num(1)))))
    return True


def test_associativity():
    # Left-associative subtraction: (A - B) - C.
    _expect("$A - $B - $C",
            Bin('-', Bin('-', _sym('A'), _sym('B')), _sym('C')))
    # Left-associative division.
    _expect("$A / $B / $C",
            Bin('/', Bin('/', _sym('A'), _sym('B')), _sym('C')))
    return True


def test_unary():
    _expect("~$MASK", Unary('~', _sym('MASK')))
    _expect("-$A", Unary('-', _sym('A')))
    # Stacked unary operators.
    _expect("- -$A", Unary('-', Unary('-', _sym('A'))))
    # Unary binds tighter than binary multiply.
    _expect("$A * -$B", Bin('*', _sym('A'), Unary('-', _sym('B'))))
    return True


def test_parentheses():
    # Parentheses regroup: add now sits below the multiply.
    _expect("($A + $B) * 2",
            Bin('*', Bin('+', _sym('A'), _sym('B')), Num(2)))
    # Redundant parentheses collapse to the same tree as the bare form.
    _expect("(($A))", _sym('A'))
    return True


def test_clog2():
    _expect("$clog2($IP_DATA_WIDTH + 1)",
            Clog2(Bin('+', _sym('IP_DATA_WIDTH'), Num(1))))
    return True


def test_bitwise_shift_combo():
    # ($N & ~$MASK) << 2
    _expect("($N & ~$MASK) << 2",
            Bin('<<',
                Bin('&', _sym('N'), Unary('~', _sym('MASK'))),
                Num(2)))
    return True


def test_truncating_division_idiom_shape():
    # ($DATA_BITS + 7) / 8  -- shape only; evaluation is Stage E1.
    _expect("($DATA_BITS + 7) / 8",
            Bin('/', Bin('+', _sym('DATA_BITS'), Num(7)), Num(8)))
    return True


def test_reject_real_literal():
    _expectReject("1.5")
    _expectReject("$A + 2.0")
    _expectReject("1e3")
    return True


def test_reject_c_style_literal():
    # The authoring language is SV, so C-style prefixes are rejected.
    _expectReject("0x7f")
    _expectReject("0b1010")
    _expectReject("0o17")
    return True


def test_reject_xz_digits():
    # x / z digits are valid SV but have no integer value to evaluate.
    _expectReject("8'hxF")
    _expectReject("4'b1z0")
    _expectReject("'h?")
    return True


def test_reject_malformed_based_literal():
    _expectReject("8'q1")   # unknown base letter
    _expectReject("8'h")    # no value digits
    _expectReject("'hG")    # digit out of range for base
    return True


def test_reject_bad_syntax():
    _expectReject("")                 # empty
    _expectReject("$A +")             # dangling operator
    _expectReject("($A + $B")         # unbalanced paren
    _expectReject("$A $B")            # missing operator
    _expectReject("$A @ $B")          # unknown character
    _expectReject("$A < $B")          # single '<' is not an operator
    _expectReject("$clog2 $A")        # clog2 without parentheses
    return True


def test_reject_unresolved_symbol():
    # ZZZ is not in _KNOWN, so qualify returns None.
    _expectReject("$ZZZ + 1")
    return True


def test_reject_bare_symbol_without_qualifier():
    # qualify=None (the reload path) cannot resolve a bare symbol.
    try:
        parse("$A + 1", qualify=None)
    except EvalParseError:
        return True
    raise AssertionError("expected EvalParseError for bare symbol with qualify=None")


def _roundtrip(expr, canonical):
    """parse the user expression, assert its canonical unparse, and assert the
    canonical string re-parses (without a qualifier) to the identical tree."""
    node = parse(expr, qualify=_qualify)
    got = unparse(node)
    if got != canonical:
        raise AssertionError(f"{expr!r}\n  expected canonical {canonical!r}\n  got            {got!r}")
    reparsed = parse(got)
    if reparsed != node:
        raise AssertionError(f"round-trip mismatch for {expr!r}\n  node     {node}\n  reparsed {reparsed}")


def test_unparse_canonical():
    # Symbols qualify and persist in ${name/context} form; the worked
    # examples from plan-eval-symbolic-emission.md are the reference.
    _roundtrip("$IP_DATA_WIDTH * 2", "${IP_DATA_WIDTH/ip_test} * 2")
    _roundtrip("$clog2($IP_DATA_WIDTH + 1)", "$clog2(${IP_DATA_WIDTH/ip_test} + 1)")
    # Precedence is in the tree, not stored parens: no parens needed here.
    _roundtrip("$A + $B * 2", "${A/ip_test} + ${B/ip_test} * 2")
    # Parentheses are restored from precedence where grouping requires them.
    _roundtrip("($A + $B) * 2", "(${A/ip_test} + ${B/ip_test}) * 2")
    _roundtrip("($DATA_BITS + 7) / 8", "(${DATA_BITS/ip_test} + 7) / 8")
    _roundtrip("($N & ~$MASK) << 2", "(${N/ip_test} & ~${MASK/ip_test}) << 2")
    # Authored hex base is preserved as unsized SV hex; the width is dropped.
    _roundtrip("$A + 8'h20", "${A/ip_test} + 'h20")
    _roundtrip("'b1010 | $A", "'b1010 | ${A/ip_test}")
    return True


def test_unparse_associativity_parens():
    # Left-associative: a - (b - c) must keep parens on the right operand;
    # a - b - c must not gain any.
    _roundtrip("$A - $B - $C", "${A/ip_test} - ${B/ip_test} - ${C/ip_test}")
    _roundtrip("$A - ($B - $C)", "${A/ip_test} - (${B/ip_test} - ${C/ip_test})")
    return True


def test_symbol_keys():
    node = parse("($A + $B * 2) - $clog2($A + $MASK)", qualify=_qualify)
    assert symbolKeys(node) == {"A/ip_test", "B/ip_test", "MASK/ip_test"}
    assert symbolKeys(parse("255", qualify=_qualify)) == set()
    return True


_TESTS = [
    ("integer literals", test_literals),
    ("symbol forms (bare and qualified)", test_symbol_forms),
    ("operator precedence", test_precedence),
    ("left associativity", test_associativity),
    ("unary operators", test_unary),
    ("parentheses regrouping", test_parentheses),
    ("$clog2 over an expression", test_clog2),
    ("bitwise/shift combination", test_bitwise_shift_combo),
    ("truncating-division idiom shape", test_truncating_division_idiom_shape),
    ("unparse canonical serialization", test_unparse_canonical),
    ("unparse associativity parens", test_unparse_associativity_parens),
    ("symbolKeys resolution walk", test_symbol_keys),
    ("reject real literals", test_reject_real_literal),
    ("reject C-style literals", test_reject_c_style_literal),
    ("reject x/z digits", test_reject_xz_digits),
    ("reject malformed based literals", test_reject_malformed_based_literal),
    ("reject bad syntax", test_reject_bad_syntax),
    ("reject unresolved symbol", test_reject_unresolved_symbol),
    ("reject bare symbol without qualifier", test_reject_bare_symbol_without_qualifier),
]


def main():
    print("=" * 70)
    print("TESTING EVAL EXPRESSION PARSER (Stage E0)")
    print("=" * 70)

    all_ok = True
    for label, fn in _TESTS:
        try:
            fn()
            print(f"  PASS: {label}")
        except AssertionError as e:
            all_ok = False
            print(f"  FAIL: {label}\n        {e}")

    print(f"\nResult: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
