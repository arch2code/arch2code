#!/usr/bin/env python3
"""Unit tests for the Python->SV `eval` converter (Stage E1.5 core).

Exercises `convertExpr` per conversion rule, numeric equivalence between the
original Python expression and the converted SV expression, idempotency, the
ALREADY_SV skip gate, NEEDS_MANUAL reporting, and the file driver's targeted
in-place rewrite (every non-eval byte preserved)."""

import os
import re
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.evalExpr import parse, evaluate
from pysrc.evalPyToSv import (
    convertExpr, convertEvalsInFile,
    ALREADY_SV, CONVERTED, NEEDS_MANUAL,
)


def _expectConvert(pyExpr, svExpr):
    got = convertExpr(pyExpr)
    if got.category != CONVERTED:
        raise AssertionError(f"{pyExpr!r}: expected CONVERTED, got {got.category} ({got.reason})")
    if got.expr != svExpr:
        raise AssertionError(f"{pyExpr!r}\n  expected {svExpr!r}\n  got      {got.expr!r}")


def _expectAlreadySv(expr):
    got = convertExpr(expr)
    if got.category != ALREADY_SV:
        raise AssertionError(f"{expr!r}: expected ALREADY_SV, got {got.category} ({got.reason})")
    if got.expr != expr:
        raise AssertionError(f"{expr!r}: ALREADY_SV must not change the string, got {got.expr!r}")


def _expectManual(expr, reasonSubstr=None):
    got = convertExpr(expr)
    if got.category != NEEDS_MANUAL:
        raise AssertionError(f"{expr!r}: expected NEEDS_MANUAL, got {got.category}")
    if got.expr != expr:
        raise AssertionError(f"{expr!r}: NEEDS_MANUAL must not rewrite, got {got.expr!r}")
    if reasonSubstr is not None and reasonSubstr not in got.reason:
        raise AssertionError(f"{expr!r}: reason {got.reason!r} missing {reasonSubstr!r}")


# Conversion rules, drawn from the repo inventory in
# plan-eval-python-to-sv-migration.md.

def test_bit_length_minus_one():
    # ($X - 1).bit_length()  ->  $clog2($X), no/with spacing, real symbol names.
    _expectConvert("($MEMORYA_WORDS-1).bit_length()", "$clog2($MEMORYA_WORDS)")
    _expectConvert("($NUM_LINE_BUFFERS-1).bit_length()", "$clog2($NUM_LINE_BUFFERS)")
    _expectConvert("($N - 1).bit_length()", "$clog2($N)")
    return True


def test_bit_length_general():
    # ($X).bit_length()  ->  $clog2($X + 1)
    _expectConvert("($DWORD).bit_length()", "$clog2($DWORD + 1)")
    _expectConvert("($DEBAYER_DIMENSION).bit_length()", "$clog2($DEBAYER_DIMENSION + 1)")
    return True


def test_floordiv():
    # floor // -> /, with the surrounding spacing left intact.
    _expectConvert("$HORIZONTAL_SIZE // $PIXELS_PER_CLOCK",
                   "$HORIZONTAL_SIZE / $PIXELS_PER_CLOCK")
    _expectConvert("($DEBAYER_DIMENSION-1)//2", "($DEBAYER_DIMENSION-1)/2")
    _expectConvert("($DEBAYER_DIMENSION - 1) // 2", "($DEBAYER_DIMENSION - 1) / 2")
    return True


def test_combination():
    # A bit_length inside a larger expression; the surrounding text is verbatim.
    _expectConvert("($A-1).bit_length() + 1", "$clog2($A) + 1")
    # A bit_length feeding a floor-divide: two non-overlapping rewrites.
    _expectConvert("($A-1).bit_length() // 2", "$clog2($A) / 2")
    return True


def test_already_sv():
    # Rows the inventory says are already in-grammar must be left untouched.
    for expr in [
        "$BITS_PER_PIXEL_COLOR + 1",
        "(1 << $BITS_PER_PIXEL_COLOR) - 1",
        "$A + $B - 1",
        "$IP_DATA_WIDTH",
        "$TESTCONST1+4",
        "$IP_DATA_WIDTH * 2",
        "$clog2($IP_DATA_WIDTH + 1)",
    ]:
        _expectAlreadySv(expr)
    return True


def test_needs_manual():
    # Real literals, exponent, and unsupported calls/operators are reported,
    # never rewritten.
    _expectManual("$DWORD / 2.0", reasonSubstr="real literal")
    _expectManual("$A ** 2", reasonSubstr="**")
    _expectManual("$A % 2 if $B else 1")  # ternary is out of grammar
    _expectManual("foo($A)", reasonSubstr="function call")
    return True


def test_idempotency():
    # Converting an already-converted string is a no-op (ALREADY_SV).
    for pyExpr in [
        "($MEMORYA_WORDS-1).bit_length()",
        "($DWORD).bit_length()",
        "$HORIZONTAL_SIZE // $PIXELS_PER_CLOCK",
        "($A-1).bit_length() // 2",
    ]:
        once = convertExpr(pyExpr)
        assert once.category == CONVERTED, pyExpr
        twice = convertExpr(once.expr)
        if twice.category != ALREADY_SV or twice.expr != once.expr:
            raise AssertionError(
                f"not idempotent: {pyExpr!r} -> {once.expr!r} -> {twice.category}/{twice.expr!r}")
    return True


# The strongest check: the converted SV expression evaluates to the same
# integer as the original Python expression over several symbol assignments.

def _evalPython(pyExpr, values):
    """Evaluate the original Python eval string, mirroring the legacy mechanism
    ($SYM -> a Python variable)."""
    pyText = re.sub(r'\$([A-Za-z_][A-Za-z0-9_]*)', r'\1', pyExpr)
    return eval(pyText, {}, dict(values))


def _evalSv(svExpr, values):
    """Evaluate the converted SV string through the real E1 evaluator."""
    node = parse(svExpr, qualify=lambda name: name)
    return evaluate(node, resolve=lambda key: values[key])


def test_numeric_equivalence():
    cases = [
        "($MEMORYA_WORDS-1).bit_length()",
        "($DWORD).bit_length()",
        "$HORIZONTAL_SIZE // $PIXELS_PER_CLOCK",
        "($DEBAYER_DIMENSION-1)//2",
        "($A-1).bit_length() // 2",
    ]
    # Symbol assignments: include powers of two and non-powers; all positive so
    # $clog2 arguments are valid and Python floor // matches SV truncation.
    assignments = [
        {"MEMORYA_WORDS": 8, "DWORD": 32, "HORIZONTAL_SIZE": 1920,
         "PIXELS_PER_CLOCK": 4, "DEBAYER_DIMENSION": 5, "A": 8},
        {"MEMORYA_WORDS": 9, "DWORD": 33, "HORIZONTAL_SIZE": 1921,
         "PIXELS_PER_CLOCK": 3, "DEBAYER_DIMENSION": 8, "A": 17},
        {"MEMORYA_WORDS": 2, "DWORD": 1, "HORIZONTAL_SIZE": 100,
         "PIXELS_PER_CLOCK": 7, "DEBAYER_DIMENSION": 2, "A": 2},
    ]
    for pyExpr in cases:
        result = convertExpr(pyExpr)
        assert result.category == CONVERTED, pyExpr
        for values in assignments:
            want = _evalPython(pyExpr, values)
            got = _evalSv(result.expr, values)
            if want != got:
                raise AssertionError(
                    f"{pyExpr!r} -> {result.expr!r} with {values}: python={want} sv={got}")
    return True


# File driver: targeted in-place rewrite preserving every other byte.

_FIXTURE = (
    "constants:\n"
    '  A_LOG2: {eval: "($A-1).bit_length()", desc: "log2 of A"}\n'
    '  ENTRIES: {eval: "$H // $PPC", desc: "entries per line"}  # trailing comment\n'
    '  ALREADY: {eval: "$A + 1", desc: "already SV"}\n'
    '  REAL_HALF: {eval: "$A / 2.0", valueType: real, desc: "real eval"}\n'
)


def test_file_roundtrip():
    with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False) as fh:
        path = fh.name
        fh.write(_FIXTURE)
    try:
        report = convertEvalsInFile(path, write=True)
        assert report.written, "expected a write"
        # Two CONVERTED rows, one NEEDS_MANUAL (the real eval); ALREADY_SV not
        # reported as either.
        assert len(report.converted) == 2, [r.original for r in report.converted]
        assert len(report.manual) == 1, [r.original for r in report.manual]
        assert report.manual[0].original == "$A / 2.0"

        with open(path) as f:
            out = f.read()
        expected = (
            "constants:\n"
            '  A_LOG2: {eval: "$clog2($A)", desc: "log2 of A"}\n'
            '  ENTRIES: {eval: "$H / $PPC", desc: "entries per line"}  # trailing comment\n'
            '  ALREADY: {eval: "$A + 1", desc: "already SV"}\n'
            '  REAL_HALF: {eval: "$A / 2.0", valueType: real, desc: "real eval"}\n'
        )
        if out != expected:
            raise AssertionError(f"file rewrite mismatch:\n--- got ---\n{out}\n--- want ---\n{expected}")

        # Idempotent: a second pass converts nothing and does not write.
        report2 = convertEvalsInFile(path, write=True)
        assert not report2.converted, "second pass should convert nothing"
        assert not report2.written, "second pass should not write"
        with open(path) as f:
            assert f.read() == expected, "second pass must not change the file"
    finally:
        os.unlink(path)
    return True


_TESTS = [
    ("($X-1).bit_length() -> $clog2($X)", test_bit_length_minus_one),
    ("($X).bit_length() -> $clog2($X + 1)", test_bit_length_general),
    ("floor // -> /", test_floordiv),
    ("bit_length combined with other constructs", test_combination),
    ("already-SV rows skipped unchanged", test_already_sv),
    ("out-of-grammar rows reported NEEDS_MANUAL", test_needs_manual),
    ("conversion is idempotent", test_idempotency),
    ("converted SV is numerically equivalent", test_numeric_equivalence),
    ("file driver targeted in-place rewrite", test_file_roundtrip),
]


def main():
    print("=" * 70)
    print("TESTING PYTHON->SV EVAL CONVERTER (Stage E1.5)")
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
