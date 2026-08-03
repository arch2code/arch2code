"""Language-neutral parser and IR for integer `eval` constant expressions.

This module owns the tokenizer, the in-house precedence-climbing (Pratt)
parser, and the IR node classes for the integer SystemVerilog
constant-expression subset described in
`builder/base/plan-eval-symbolic-emission.md`.

The grammar covers SystemVerilog integer literals (unsized decimal and
SV based literals such as `8'hFF`, `'hFF`, `'b1010`, `12'd9`), arithmetic
`+ - * / %`, bitwise `& | ^ ~`, logical shifts `<< >>`, relational
`< <= > >=`, equality `== !=`, the ternary conditional `?:`, `$clog2`,
`$symbol` references, and parentheses. Every operator has a direct, identical
SV/C++/C spelling, so the emitters pass it through 1:1. The authoring language
is SV, so literals are spelled in SV: C-style `0x` / `0o` / `0b` prefixes,
`x` / `z` digits, real literals, and out-of-grammar operators are all rejected
at parse time.

This module owns the language-neutral core: parsing into the IR (`parse`),
numeric evaluation (`evaluate`), canonical serialization for persistence
(`unparse`), and the symbol-resolution walk (`symbolKeys`). The per-language
emitters that translate the canonical string to SystemVerilog / C++ / firmware
text live in the template layer, not here.
"""

import re
from dataclasses import dataclass

import pysrc.arch2codeHelper


# IR nodes. Pure data, walked externally by the evaluator and emitters.
# Frozen so they are hashable and compare structurally, which makes parser
# results directly assertable in tests.

@dataclass(frozen=True)
class Num:
    value: int
    base: int = 10  # authored radix (10, 16, 2) for emitter re-spelling;
                    # octal is normalized to 16 (C has no clean octal form)


@dataclass(frozen=True)
class Sym:
    key: str  # qualified symbol key, e.g. "IP_DATA_WIDTH/ip_test"


@dataclass(frozen=True)
class Unary:
    op: str   # one of '+' '-' '~'
    operand: object


@dataclass(frozen=True)
class Bin:
    op: str   # one of '+' '-' '*' '/' '%' '&' '|' '^' '<<' '>>'
    lhs: object
    rhs: object


@dataclass(frozen=True)
class Clog2:
    operand: object


@dataclass(frozen=True)
class Cond:
    # Ternary conditional `cond ? then : otherwise`. `cond` evaluates as a
    # boolean (nonzero is true), matching the shared SV/C++/C spelling emitted
    # verbatim by the per-language emitters.
    cond: object
    then: object
    otherwise: object


class EvalParseError(Exception):
    """Raised for user-facing parse failures: bad syntax, real or sized
    literals, or an unresolved bare symbol. Carries the source column so
    callers can point at the offending text."""

    def __init__(self, message, col):
        super().__init__(message)
        self.message = message
        self.col = col


# Binary-operator precedence. Higher binds tighter. The SV and C++ orderings
# coincide for this subset, so one table serves the parser, `unparse`, and the
# per-language emitters. All binary operators are left-associative. Relational
# and equality bind looser than the shifts and tighter than the bitwise ops,
# matching the shared SV/C++ ordering; the ternary conditional binds looser than
# every binary operator and is parsed as its own right-associative layer.
PRECEDENCE = {
    '|': 1,
    '^': 2,
    '&': 3,
    '==': 4, '!=': 4,
    '<': 5, '<=': 5, '>': 5, '>=': 5,
    '<<': 6, '>>': 6,
    '+': 7, '-': 7,
    '*': 8, '/': 8, '%': 8,
}

# Prefix unary operators.
_UNARY_OPS = {'+', '-', '~'}

# A decimal run shaped like a real (scientific notation). The decimal-point
# form is caught separately by testing for '.'. Used only to produce a
# targeted "real literals are not supported" diagnostic.
_REAL_RE = re.compile(r'[0-9][0-9_]*[eE][+-]?[0-9]+')

# SV based-literal bases: base letter -> (radix, valid digit set).
_BASE_INFO = {
    'b': (2, set('01')),
    'o': (8, set('01234567')),
    'd': (10, set('0123456789')),
    'h': (16, set('0123456789abcdefABCDEF')),
}

# Unknown/high-impedance digits, valid SV but not evaluable to an integer.
_XZ = set('xXzZ?')


def _tokenize(text):
    """Turn the expression string into a list of (type, value, col) tokens,
    terminated by a sticky ('EOF', None, col) sentinel."""
    toks = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in ' \t\n\r':
            i += 1
            continue
        if c == '(':
            toks.append(('LPAREN', '(', i))
            i += 1
            continue
        if c == ')':
            toks.append(('RPAREN', ')', i))
            i += 1
            continue
        if c == '<':
            if text[i:i + 2] == '<<':
                toks.append(('OP', '<<', i))
                i += 2
                continue
            if text[i:i + 2] == '<=':
                toks.append(('OP', '<=', i))
                i += 2
                continue
            toks.append(('OP', '<', i))
            i += 1
            continue
        if c == '>':
            if text[i:i + 2] == '>>':
                toks.append(('OP', '>>', i))
                i += 2
                continue
            if text[i:i + 2] == '>=':
                toks.append(('OP', '>=', i))
                i += 2
                continue
            toks.append(('OP', '>', i))
            i += 1
            continue
        if c == '=':
            if text[i:i + 2] == '==':
                toks.append(('OP', '==', i))
                i += 2
                continue
            raise EvalParseError("'=' is not a valid operator; did you mean '=='?", i)
        if c == '!':
            if text[i:i + 2] == '!=':
                toks.append(('OP', '!=', i))
                i += 2
                continue
            raise EvalParseError("'!' is not a valid operator; did you mean '!='?", i)
        if c == '?':
            toks.append(('QUESTION', '?', i))
            i += 1
            continue
        if c == ':':
            toks.append(('COLON', ':', i))
            i += 1
            continue
        if c in '+-*/%&|^~':
            toks.append(('OP', c, i))
            i += 1
            continue
        if c == "'":
            # Unsized based literal, e.g. 'hFF.
            i = _tokenizeBased(text, i, i, toks)
            continue
        if c == '$':
            i = _tokenizeSymbol(text, i, toks)
            continue
        if c.isdigit():
            i = _tokenizeNumber(text, i, toks)
            continue
        raise EvalParseError(f"unexpected character {c!r}", i)
    toks.append(('EOF', None, n))
    return toks


def _tokenizeSymbol(text, i, toks):
    """Tokenize a `$`-prefixed token starting at `i`. Accepts the bare
    `$NAME` form, the qualified `${name/context}` form, and the `$clog2`
    function name. Returns the index past the token."""
    n = len(text)
    j = i + 1
    if j < n and text[j] == '{':
        close = text.find('}', j + 1)
        if close == -1:
            raise EvalParseError("unterminated ${...} symbol", i)
        key = text[j + 1:close]
        if not key:
            raise EvalParseError("empty ${} symbol", i)
        toks.append(('SYM_Q', key, i))
        return close + 1
    m = j
    while m < n and (text[m].isalnum() or text[m] == '_'):
        m += 1
    word = text[j:m]
    if not word:
        raise EvalParseError("expected a symbol name after '$'", i)
    if word == 'clog2':
        toks.append(('CLOG2', 'clog2', i))
    else:
        toks.append(('SYM_B', word, i))
    return m


def _tokenizeNumber(text, i, toks):
    """Tokenize an integer literal starting at `i` (a digit). This is either
    a sized based literal (the leading digits are the width, e.g. `8'hFF`) or
    an unsized decimal (`123`). Returns the index past the token. Rejects
    real literals and C-style `0x` / `0o` / `0b` forms."""
    n = len(text)
    m = i
    while m < n and (text[m].isdigit() or text[m] == '_'):
        m += 1
    if m < n and text[m] == "'":
        # Sized based literal: the leading run is the declared width, which
        # does not affect the evaluated integer value (the IR models
        # unbounded integers, so no bit-width truncation).
        return _tokenizeBased(text, i, m, toks)
    # Unsized decimal. Extend over any trailing alnum/'.' so malformed,
    # real, and C-style inputs can be diagnosed rather than silently split.
    while m < n and (text[m].isalnum() or text[m] == '_' or text[m] == '.'):
        m += 1
    raw = text[i:m]
    if re.match(r'0[xXoObB]', raw):
        raise EvalParseError(
            f"C-style literals are not supported; use SV form (e.g. 'hFF): {raw!r}", i)
    if '.' in raw or _REAL_RE.fullmatch(raw):
        raise EvalParseError(f"real literals are not supported: {raw!r}", i)
    try:
        value = int(raw.replace('_', ''), 10)
    except ValueError:
        raise EvalParseError(f"invalid integer literal: {raw!r}", i)
    toks.append(('NUM', (value, 10), i))
    return m


def _tokenizeBased(text, litStart, apos, toks):
    """Tokenize an SV based literal whose `'` is at `apos`. `litStart` is the
    literal's first character (the width, or `apos` for an unsized literal)
    and is used as the token column. Returns the index past the token."""
    n = len(text)
    j = apos + 1
    if j < n and text[j] in 'sS':  # signedness marker; irrelevant to the value
        j += 1
    if j >= n or text[j] not in 'bBoOdDhH':
        raise EvalParseError("expected a base letter (b/o/d/h) after \"'\"", apos)
    radix, digits = _BASE_INFO[text[j].lower()]
    j += 1
    valChars = []
    while j < n and (text[j].isalnum() or text[j] == '_' or text[j] == '?'):
        ch = text[j]
        if ch == '_':
            j += 1
            continue
        if ch in _XZ:
            raise EvalParseError("x / z digits cannot be evaluated to an integer", j)
        if ch not in digits:
            raise EvalParseError(f"invalid digit {ch!r} for a base-{radix} literal", j)
        valChars.append(ch)
        j += 1
    if not valChars:
        raise EvalParseError("based literal has no value digits", apos)
    value = int(''.join(valChars), radix)
    # Octal is recorded as hex: C has no clean octal spelling (`017` is
    # error-prone), so an octal-authored literal emits and persists as hex.
    base = 16 if radix == 8 else radix
    toks.append(('NUM', (value, base), litStart))
    return j


class _Parser:
    """Precedence-climbing parser over a token list."""

    def __init__(self, toks, qualify):
        self.toks = toks
        self.pos = 0
        self.qualify = qualify

    def _peek(self):
        return self.toks[self.pos]

    def _advance(self):
        tok = self.toks[self.pos]
        if tok[0] != 'EOF':
            self.pos += 1
        return tok

    def parse(self):
        node = self._ternary()
        tok = self._peek()
        if tok[0] != 'EOF':
            raise EvalParseError(f"unexpected token {tok[1]!r}", tok[2])
        return node

    def _ternary(self):
        # The conditional binds looser than every binary operator and is
        # right-associative (`a ? b : c ? d : e` == `a ? b : (c ? d : e)`), so
        # the branches recurse back into `_ternary` while the condition is a
        # full binary expression.
        cond = self._expr(0)
        if self._peek()[0] == 'QUESTION':
            self._advance()
            then = self._ternary()
            colon = self._advance()
            if colon[0] != 'COLON':
                raise EvalParseError("expected ':' in conditional expression", colon[2])
            return Cond(cond, then, self._ternary())
        return cond

    def _expr(self, minPrec):
        left = self._unary()
        while True:
            tok = self._peek()
            if tok[0] == 'OP' and tok[1] in PRECEDENCE and PRECEDENCE[tok[1]] >= minPrec:
                op = tok[1]
                self._advance()
                # Left-associative: parse the right operand at one level
                # tighter so equal-precedence operators group leftward.
                right = self._expr(PRECEDENCE[op] + 1)
                left = Bin(op, left, right)
            else:
                break
        return left

    def _unary(self):
        tok = self._peek()
        if tok[0] == 'OP' and tok[1] in _UNARY_OPS:
            self._advance()
            return Unary(tok[1], self._unary())
        return self._atom()

    def _atom(self):
        tok = self._advance()
        typ = tok[0]
        if typ == 'NUM':
            value, base = tok[1]
            return Num(value, base)
        if typ == 'SYM_Q':
            return Sym(tok[1])
        if typ == 'SYM_B':
            if self.qualify is None:
                raise EvalParseError(
                    f"cannot resolve bare symbol ${tok[1]} without a qualifier", tok[2])
            key = self.qualify(tok[1])
            if key is None:
                raise EvalParseError(f"unresolved symbol: ${tok[1]}", tok[2])
            return Sym(key)
        if typ == 'CLOG2':
            lparen = self._advance()
            if lparen[0] != 'LPAREN':
                raise EvalParseError("expected '(' after $clog2", lparen[2])
            inner = self._ternary()
            rparen = self._advance()
            if rparen[0] != 'RPAREN':
                raise EvalParseError("expected ')' to close $clog2(", rparen[2])
            return Clog2(inner)
        if typ == 'LPAREN':
            inner = self._ternary()
            rparen = self._advance()
            if rparen[0] != 'RPAREN':
                raise EvalParseError("expected ')'", rparen[2])
            return inner
        if typ == 'EOF':
            raise EvalParseError("unexpected end of expression", tok[2])
        raise EvalParseError(f"unexpected token {tok[1]!r}", tok[2])


def parse(text, qualify=None):
    """Parse an integer eval expression string into an IR node.

    Two symbol token forms are accepted:
      `$NAME`           bare; `qualify(NAME)` is called to obtain the
                        qualified key, or None if unresolved (validation
                        folds into parsing).
      `${name/context}` already-qualified; parsed straight to Sym(key) with
                        `qualify` never invoked (the canonical/reload form).

    `$clog2(...)` is the function. Integer literals are SystemVerilog
    literals: unsized decimal or SV based literals (`8'hFF`, `'hFF`,
    `'b1010`, `12'd9`). Raises EvalParseError on bad syntax, real literals,
    `x` / `z` digits, C-style `0x` prefixes, or an unresolved bare symbol.
    """
    return _Parser(_tokenize(text), qualify).parse()


def needsParens(parentOp, child, side):
    """Whether `child` (the `side` operand, 'left' or 'right', of a binary
    `parentOp`) must be parenthesized to preserve the tree's grouping when
    re-emitted. Precedence is grammar, shared by `unparse` and the per-language
    emitters; all binary operators are left-associative."""
    if isinstance(child, Cond):
        # The conditional binds looser than every binary operator, so a Cond
        # operand of a binary op is always wrapped regardless of side.
        return True
    if not isinstance(child, Bin):
        # Atoms, unary operators, and $clog2 all bind at least as tightly as
        # any binary operator, so they never need wrapping.
        return False
    parentPrec = PRECEDENCE[parentOp]
    childPrec = PRECEDENCE[child.op]
    if childPrec < parentPrec:
        return True
    if childPrec == parentPrec:
        # Left-associative: a - (b - c) must keep its parens; a - b - c need not.
        return side == 'right'
    return False


def _unparseNum(node):
    """Spell a Num in unsized SV based form for its authored radix. The
    authored bit width is not reproduced (the IR models unbounded integers)."""
    if node.base == 16:
        return f"'h{node.value:x}"
    if node.base == 2:
        return f"'b{node.value:b}"
    return str(node.value)


def unparse(node):
    """Serialize an IR node to its canonical SV-subset string for persistence.

    Symbols are emitted in already-qualified `${name/context}` form (so a
    later `parse` needs no qualifier), literals in unsized SV based form for
    their authored radix, operators with normalized single-space padding, and
    parentheses restored from operator precedence via `needsParens`. The
    invariant `parse(unparse(node)) == node` holds, so create-time evaluation
    and template-layer emission cannot diverge on tree shape. Total over
    well-formed trees: it trusts its input and performs no validation."""
    if isinstance(node, Num):
        return _unparseNum(node)
    if isinstance(node, Sym):
        return '${' + node.key + '}'
    if isinstance(node, Unary):
        operand = unparse(node.operand)
        if isinstance(node.operand, Bin):
            operand = f"({operand})"
        return node.op + operand
    if isinstance(node, Bin):
        lhs = unparse(node.lhs)
        if needsParens(node.op, node.lhs, 'left'):
            lhs = f"({lhs})"
        rhs = unparse(node.rhs)
        if needsParens(node.op, node.rhs, 'right'):
            rhs = f"({rhs})"
        return f"{lhs} {node.op} {rhs}"
    if isinstance(node, Cond):
        # Only a Cond condition needs wrapping: `_expr` never parses a bare
        # conditional, so a nested Cond in the condition slot would otherwise
        # re-parse wrong. Branches recurse through `_ternary` and stay bare.
        cond = unparse(node.cond)
        if isinstance(node.cond, Cond):
            cond = f"({cond})"
        return f"{cond} ? {unparse(node.then)} : {unparse(node.otherwise)}"
    return f"$clog2({unparse(node.operand)})"  # Clog2


def symbolKeys(node):
    """Return the set of qualified symbol keys referenced by the IR tree.

    A symbol-resolution walk, distinct from numeric evaluation: it enumerates
    the `Sym` referents (e.g. for create-time parameterizable detection)
    without resolving any of them to a value."""
    if isinstance(node, Sym):
        return {node.key}
    if isinstance(node, Num):
        return set()
    if isinstance(node, Unary):
        return symbolKeys(node.operand)
    if isinstance(node, Bin):
        return symbolKeys(node.lhs) | symbolKeys(node.rhs)
    if isinstance(node, Cond):
        return symbolKeys(node.cond) | symbolKeys(node.then) | symbolKeys(node.otherwise)
    return symbolKeys(node.operand)  # Clog2


class EvalEvalError(Exception):
    """Raised for runtime evaluation failures surfaced as create-time user
    diagnostics."""


def _truncDiv(a, b):
    """Integer division truncating toward zero, matching SystemVerilog and
    C++ (not Python floor `//`). Done by magnitude with the sign applied so
    large integers keep full precision (`int(a / b)` would not)."""
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def evaluate(node, resolve):
    """Evaluate an IR node to a Python int using SystemVerilog integer
    constant-expression semantics.

    `resolve(symKey)` returns the int to substitute for a `Sym`'s qualified
    key. Division truncates toward zero and `%` follows that truncated
    quotient (`a % b == a - (a/b)*b`, sign of the dividend); divide-by-zero
    raises EvalEvalError. `$clog2` uses `arch2codeHelper.clog2`. The `.base`
    field on `Num` is presentation only and is ignored here.
    """
    if isinstance(node, Num):
        return node.value
    if isinstance(node, Sym):
        return resolve(node.key)
    if isinstance(node, Unary):
        operand = evaluate(node.operand, resolve)
        if node.op == '+':
            return operand
        if node.op == '-':
            return -operand
        return ~operand  # '~', the only remaining unary operator
    if isinstance(node, Bin):
        lhs = evaluate(node.lhs, resolve)
        rhs = evaluate(node.rhs, resolve)
        op = node.op
        if op == '+':
            return lhs + rhs
        if op == '-':
            return lhs - rhs
        if op == '*':
            return lhs * rhs
        if op == '/':
            if rhs == 0:
                raise EvalEvalError("division by zero")
            return _truncDiv(lhs, rhs)
        if op == '%':
            if rhs == 0:
                raise EvalEvalError("modulo by zero")
            return lhs - _truncDiv(lhs, rhs) * rhs
        if op == '&':
            return lhs & rhs
        if op == '|':
            return lhs | rhs
        if op == '^':
            return lhs ^ rhs
        # Relational and equality yield a 0/1 int, matching SV/C++ where a
        # comparison is an integer usable as a ternary condition.
        if op == '<':
            return int(lhs < rhs)
        if op == '<=':
            return int(lhs <= rhs)
        if op == '>':
            return int(lhs > rhs)
        if op == '>=':
            return int(lhs >= rhs)
        if op == '==':
            return int(lhs == rhs)
        if op == '!=':
            return int(lhs != rhs)
        if op == '<<':
            if rhs < 0:
                raise EvalEvalError("negative shift count")
            return lhs << rhs
        if rhs < 0:
            raise EvalEvalError("negative shift count")
        return lhs >> rhs  # '>>', the only remaining binary operator
    if isinstance(node, Cond):
        # Nonzero condition selects the `then` branch (SV/C++ truthiness).
        if evaluate(node.cond, resolve) != 0:
            return evaluate(node.then, resolve)
        return evaluate(node.otherwise, resolve)
    operand = evaluate(node.operand, resolve)  # Clog2
    if operand <= 0:
        raise EvalEvalError("$clog2 argument must be positive")
    return pysrc.arch2codeHelper.clog2(operand)
