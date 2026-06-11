#!/usr/bin/env python3
"""Unit tests for the integer eval-expression evaluator (Stage E1).

Exercises each operator and unary, precedence/associativity flowing through
to numeric results, $clog2 over an expression, symbol resolution via the
resolve callback, truncating division toward zero with negative operands and
its matching `%` sign behavior, and divide/modulo-by-zero raising
EvalEvalError."""

import sys
import os

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.evalExpr import parse, evaluate, EvalEvalError


# Symbol values resolved by the create-time callback. Bare symbols qualify to
# "NAME/ip_test" in parse, so the resolve dict is keyed the same way.
_VALUES = {
    'A/ip_test': 1,
    'B/ip_test': 3,
    'N/ip_test': 0xF3,
    'MASK/ip_test': 0x0F,
    'IP_DATA_WIDTH/ip_test': 12,
    'DATA_BITS/ip_test': 20,
}

_KNOWN = {name.split('/')[0] for name in _VALUES}


def _qualify(name):
    return f"{name}/ip_test" if name in _KNOWN else None


def _resolve(key):
    return _VALUES[key]


def _eval(expr):
    return evaluate(parse(expr, qualify=_qualify), resolve=_resolve)


def _expect(expr, want):
    got = _eval(expr)
    if got != want:
        raise AssertionError(f"{expr!r}\n  expected {want}\n  got      {got}")


def _expectEvalError(expr):
    try:
        _eval(expr)
    except EvalEvalError:
        return
    raise AssertionError(f"expected EvalEvalError for {expr!r}")


def test_literals_and_bases():
    # The .base field is presentation only; the evaluated value is identical.
    _expect("255", 255)
    _expect("8'hFF", 255)
    _expect("'b1010", 10)
    _expect("4_095", 4095)
    return True


def test_binary_operators():
    _expect("2 + 3", 5)
    _expect("7 - 2", 5)
    _expect("3 * 4", 12)
    _expect("12 / 3", 4)
    _expect("17 % 5", 2)
    _expect("12 & 10", 8)
    _expect("12 | 1", 13)
    _expect("12 ^ 10", 6)
    _expect("1 << 4", 16)
    _expect("256 >> 2", 64)
    return True


def test_unary_operators():
    _expect("+5", 5)
    _expect("-5", -5)
    _expect("~0", -1)
    # Stacked unary.
    _expect("- -5", 5)
    return True


def test_precedence_to_value():
    # '*' binds tighter than '+': 1 + (3 * 2) = 7.
    _expect("$A + $B * 2", 7)
    # Parentheses regroup: (1 + 3) * 2 = 8.
    _expect("($A + $B) * 2", 8)
    # Shift lower than '+': (1 + 3) << 2 = 16.
    _expect("$A + $B << 2", 16)
    # Bitwise/shift combo: (0xF3 & ~0x0F) << 2 = 0xF0 << 2 = 0x3C0.
    _expect("($N & ~$MASK) << 2", 0x3C0)
    return True


def test_associativity_to_value():
    # Left-associative subtraction: (20 - 3) - 1 = 16.
    _expect("$DATA_BITS - $B - $A", 16)
    # Left-associative division: (20 / 3) / 2 = 6 / 2 = 3.
    _expect("$DATA_BITS / $B / 2", 3)
    return True


def test_clog2():
    # clog2(13) = 4.
    _expect("$clog2($IP_DATA_WIDTH + 1)", 4)
    # clog2 over a literal.
    _expect("$clog2(16)", 4)
    return True


def test_symbol_resolution():
    _expect("$IP_DATA_WIDTH", 12)
    _expect("$IP_DATA_WIDTH * 2", 24)
    # Round-up-to-bytes idiom with truncating division: 27 / 8 = 3.
    _expect("($DATA_BITS + 7) / 8", 3)
    return True


def test_truncating_division_negative():
    # SV/C++ truncate toward zero, not Python floor.
    _expect("-7 / 2", -3)
    _expect("7 / -2", -3)
    _expect("-7 / -2", 3)
    _expect("7 / 2", 3)
    return True


def test_modulo_sign_follows_dividend():
    # a % b == a - (a/b)*b, sign of the dividend.
    _expect("-7 % 2", -1)
    _expect("7 % -2", 1)
    _expect("-7 % -2", -1)
    _expect("7 % 2", 1)
    return True


def test_divide_by_zero():
    _expectEvalError("1 / 0")
    _expectEvalError("$A / (2 - 2)")
    return True


def test_modulo_by_zero():
    _expectEvalError("1 % 0")
    _expectEvalError("$A % (2 - 2)")
    return True


def test_negative_shift_count():
    _expectEvalError("1 << -1")
    _expectEvalError("8 >> -1")
    return True


def test_clog2_non_positive():
    _expectEvalError("$clog2(0)")
    _expectEvalError("$clog2(-1)")
    return True


_TESTS = [
    ("literals across bases", test_literals_and_bases),
    ("binary operators", test_binary_operators),
    ("unary operators", test_unary_operators),
    ("precedence flows to value", test_precedence_to_value),
    ("associativity flows to value", test_associativity_to_value),
    ("$clog2 over an expression", test_clog2),
    ("symbol resolution via callback", test_symbol_resolution),
    ("truncating division toward zero", test_truncating_division_negative),
    ("modulo sign follows dividend", test_modulo_sign_follows_dividend),
    ("divide-by-zero raises EvalEvalError", test_divide_by_zero),
    ("modulo-by-zero raises EvalEvalError", test_modulo_by_zero),
    ("negative shift raises EvalEvalError", test_negative_shift_count),
    ("non-positive $clog2 raises EvalEvalError", test_clog2_non_positive),
]


def main():
    print("=" * 70)
    print("TESTING EVAL EXPRESSION EVALUATOR (Stage E1)")
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
