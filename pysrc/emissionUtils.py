from dataclasses import dataclass
from typing import Callable

import pysrc.evalExpr as evalExpr


def _svNumLiteral(node):
    """Re-spell a Num in its authored, unsized SystemVerilog base: decimal
    as-is, hex as 'hFF, binary as 'b1010. The authored bit width is not
    reproduced (the eval IR models unbounded integers)."""
    if node.base == 16:
        return f"'h{node.value:x}"
    if node.base == 2:
        return f"'b{node.value:b}"
    return str(node.value)


def _cNumLiteral(node):
    """Re-spell a Num in its authored base as a C literal: decimal as-is, hex
    as 0x.., binary as 0b.. (octal was normalized to hex at parse). The
    authored bit width is not reproduced (the eval IR models unbounded
    integers)."""
    if node.base == 16:
        return f"0x{node.value:x}"
    if node.base == 2:
        return f"0b{node.value:b}"
    return str(node.value)


@dataclass(frozen=True)
class EmitLang:
    """Per-language spelling for eval-expression and width-expression
    emission. The emission walks are language-neutral; only these leaves
    differ between SystemVerilog and C/C++."""
    clog2: str            # log2 builtin name: "$clog2" (SV) | "clog2" (C)
    numLiteral: Callable  # base-aware integer-literal speller for a Num node


SV = EmitLang(clog2="$clog2", numLiteral=_svNumLiteral)
C = EmitLang(clog2="clog2", numLiteral=_cNumLiteral)


def _emitNode(node, symSpelling, lang):
    """Walk one eval-IR node to target text. Operators pass through 1:1 (the
    frozen grammar is the SV/C++ common subset); $clog2 uses lang.clog2; a Num
    is re-spelled by lang.numLiteral; a Sym is spelled by
    symSpelling(qualifiedKey); parentheses are restored from operator
    precedence via evalExpr.needsParens."""
    if isinstance(node, evalExpr.Num):
        return lang.numLiteral(node)
    if isinstance(node, evalExpr.Sym):
        return symSpelling(node.key)
    if isinstance(node, evalExpr.Unary):
        operand = _emitNode(node.operand, symSpelling, lang)
        if isinstance(node.operand, evalExpr.Bin):
            operand = f"({operand})"
        return node.op + operand
    if isinstance(node, evalExpr.Bin):
        lhs = _emitNode(node.lhs, symSpelling, lang)
        if evalExpr.needsParens(node.op, node.lhs, 'left'):
            lhs = f"({lhs})"
        rhs = _emitNode(node.rhs, symSpelling, lang)
        if evalExpr.needsParens(node.op, node.rhs, 'right'):
            rhs = f"({rhs})"
        return f"{lhs} {node.op} {rhs}"
    return f"{lang.clog2}({_emitNode(node.operand, symSpelling, lang)})"  # Clog2


def emitExpr(evalCanonical, symSpelling, lang):
    """Translate a persisted canonical eval expression into a target-language
    expression string for `lang`.

    The canonical string is already qualified, so it is parsed with
    qualify=None; this reload parse is total and trusts its input (a failure
    here is an internal invariant violation, not a user diagnostic). Each Sym
    is spelled by symSpelling(qualifiedKey); operators, the log2 builtin,
    literals, and grouping are emitted by walking the IR."""
    return _emitNode(evalExpr.parse(evalCanonical, qualify=None), symSpelling, lang)


def typeWidthExpr(value, lang, constSpelling, literalWidth):
    """Build a type's bit-range width expression for `lang`.

    The decision tree is language-neutral:
      widthLog2 with constant C:        <clog2>(C+1)
      widthLog2minus1 with constant C:  <clog2>(C)
      width with constant C:            C
      literal:                          literalWidth(value)
    isSigned + log2 appends +1. Only the leaves vary by site/language and are
    supplied by the caller: lang.clog2, constSpelling(constKey) for a width
    constant reference, and literalWidth(value) for the literal fallback.

    Parameterized (per-variant) widths need no special case: a width backed by
    a parameterizable constant resolves through constSpelling to that constant's
    symbol (a module-local SV param/localparam, or the per-variant Config member
    in C++), so the emitted range stays symbolic rather than frozen to a literal.
    """
    signedExtra = '+1' if value['isSigned'] else ''

    wl2Key = value['widthLog2Key']
    if wl2Key:
        return f"{lang.clog2}({constSpelling(wl2Key)}+1){signedExtra}"
    wl2 = value['widthLog2']
    if wl2 != '':
        return f"{lang.clog2}({wl2}+1){signedExtra}"

    wl2m1Key = value['widthLog2minus1Key']
    if wl2m1Key:
        return f"{lang.clog2}({constSpelling(wl2m1Key)}){signedExtra}"
    wl2m1 = value['widthLog2minus1']
    if wl2m1 != '':
        return f"{lang.clog2}({wl2m1}){signedExtra}"

    widthKey = value['widthKey']
    if widthKey:
        return constSpelling(widthKey)
    return literalWidth(value)
