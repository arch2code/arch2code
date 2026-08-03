"""Syntactic converter from Python-authored `eval` strings to the SV subset.

The legacy `eval:` constant expressions were authored in Python
(`($X - 1).bit_length()`, floor `//`, real `/ 2.0`). They do not parse under
the frozen SystemVerilog-subset grammar that `pysrc.evalExpr` now owns. This
module rewrites the Python-only constructs into SV-subset spelling without
touching anything already in-grammar.

The conversion is purely syntactic. The front-end is Python's own `ast`
(the source is literal Python), and rewrites are applied as targeted text
replacements over the original string so spacing, parentheses, and surrounding
characters are left byte-identical except for the spans that change.

Two public entry points:
  `convertExpr(pyExpr)`         pure expression converter, returns ConvertResult.
  `convertEvalsInFile(path)`    scans a YAML file's `eval` rows and rewrites the
                                CONVERTED ones in place (targeted text replace).

`valueType: real` evals (`$DWORD / 2.0`) cannot be rewritten by a syntactic
tool — converting them to a literal `value:` needs resolved symbol values — so
they are reported as NEEDS_MANUAL and never touched.

Python floor division (`//`) is likewise never auto-rewritten. `//` floors
toward -inf whereas SV `/` truncates toward zero; the two agree only for
non-negative operands, so a blind `//`->`/` rewrite silently corrupts the
ceiling idiom `-(-a//b)`. Every floor-division expression is reported as
NEEDS_MANUAL so a human rewrites it (e.g. positive ceiling as `(a + b - 1) / b`).
"""

import ast
from dataclasses import dataclass, field

import yaml

import pysrc.evalExpr as evalExpr


# Conversion outcome categories.
ALREADY_SV = "ALREADY_SV"     # already parses under the SV grammar; no change
CONVERTED = "CONVERTED"       # Python constructs rewritten to SV-subset spelling
NEEDS_MANUAL = "NEEDS_MANUAL"  # out-of-grammar; left untouched, flagged with reason


@dataclass(frozen=True)
class ConvertResult:
    category: str        # ALREADY_SV | CONVERTED | NEEDS_MANUAL
    expr: str            # resulting string (== input for ALREADY_SV / NEEDS_MANUAL)
    reason: str = ""     # populated for NEEDS_MANUAL


class EvalConvertError(Exception):
    """Internal converter failure: a rewrite produced a string that does not
    re-parse under the SV grammar. This is a converter bug, surfaced loudly
    rather than written to YAML."""


# Accept any bare symbol: the migration only cares whether an expression's
# *shape* is in-grammar, not whether its symbols resolve in a project. Symbol
# resolution is a create-time concern, not a syntactic one.
def _acceptAll(name):
    return name


# Binary operators the converter understands; all are already SV-valid and are
# copied through verbatim. Python floor division (`//`) is deliberately absent:
# it floors toward -inf while SV `/` truncates toward zero, so it is never
# auto-rewritten and is routed to NEEDS_MANUAL instead (see convertExpr).
_BINOPS = (
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
    ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr, ast.BitXor,
)
_UNARYOPS = (ast.UAdd, ast.USub, ast.Invert)


def convertExpr(pyExpr):
    """Convert a single Python `eval` expression string to the SV subset.

    Returns a ConvertResult. Idempotent: an already-SV string (including one
    this function just produced) returns ALREADY_SV unchanged.
    """
    # Step 1 - skip gate. If the string already parses under the SV grammar it
    # is in-subset; no rewrite. This makes the tool idempotent and minimal-diff
    # for free.
    try:
        evalExpr.parse(pyExpr, qualify=_acceptAll)
        return ConvertResult(ALREADY_SV, pyExpr)
    except evalExpr.EvalParseError:
        pass

    # Step 2 - placehold `$` -> `_` (both width 1, so all source columns stay
    # aligned) and parse with Python's `ast`. The resulting node offsets index
    # into the original string unchanged.
    placeheld = pyExpr.replace('$', '_')
    try:
        tree = ast.parse(placeheld, mode='eval')
    except SyntaxError as exc:
        return ConvertResult(NEEDS_MANUAL, pyExpr,
                             reason=f"not a parseable expression: {exc.msg}")

    # Step 2b - floor division is never auto-rewritten. Python `//` floors
    # toward -inf; SV `/` truncates toward zero, so blindly rewriting `//`->`/`
    # silently corrupts the ceiling idiom `-(-a//b)`. Walk the whole tree so
    # nested forms like `-(-(a)//b)` are caught, and route to NEEDS_MANUAL.
    if any(isinstance(n, ast.BinOp) and isinstance(n.op, ast.FloorDiv)
           for n in ast.walk(tree)):
        return ConvertResult(
            NEEDS_MANUAL, pyExpr,
            reason="Python '//' floors toward -inf; SV '/' truncates toward "
                   "zero. Rewrite by hand (e.g. positive ceiling as "
                   "(a + b - 1) / b).")

    # Step 3 - validate the tree is built only from convertible constructs.
    reason = _validate(tree.body, pyExpr)
    if reason is not None:
        return ConvertResult(NEEDS_MANUAL, pyExpr, reason=reason)

    # Step 4 - collect the rewrite spans and apply them right-to-left so earlier
    # offsets stay valid.
    spans = []
    _collectSpans(tree.body, pyExpr, spans)
    newExpr = _applySpans(pyExpr, spans)

    # Step 5 - the produced string must parse under the SV grammar. Failure is
    # a converter bug, not something to write to YAML.
    try:
        evalExpr.parse(newExpr, qualify=_acceptAll)
    except evalExpr.EvalParseError as exc:
        raise EvalConvertError(
            f"converted {pyExpr!r} to {newExpr!r}, which is not SV-subset: {exc.message}")

    return ConvertResult(CONVERTED, newExpr)


def _validate(node, src):
    """Walk the tree; return None if every node is convertible, else a reason
    string for the first out-of-grammar construct. The only function call
    permitted is a no-argument `.bit_length()`."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return "boolean literal is not in the SV subset"
        if isinstance(node.value, int):
            return None
        if isinstance(node.value, float):
            return "real literal"
        return f"unsupported literal {node.value!r}"
    if isinstance(node, ast.Name):
        return None
    if isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, _UNARYOPS):
            return f"unsupported unary operator {_opName(node.op)}"
        return _validate(node.operand, src)
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _BINOPS):
            return f"unsupported operator {_opName(node.op)}"
        return _validate(node.left, src) or _validate(node.right, src)
    if isinstance(node, ast.Call):
        if not _isBitLengthCall(node):
            return "unsupported function call"
        return _validate(node.func.value, src)
    if isinstance(node, ast.Attribute):
        # An Attribute that is not the func of a bit_length() call.
        return f"unsupported attribute .{node.attr}"
    return f"unsupported expression {type(node).__name__}"


def _isBitLengthCall(node):
    """True if `node` is exactly `<expr>.bit_length()` with no arguments."""
    return (isinstance(node, ast.Call)
            and not node.args and not node.keywords
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'bit_length')


def _opName(op):
    """Human-facing operator spelling for a NEEDS_MANUAL reason."""
    names = {
        ast.Pow: '**', ast.Add: '+', ast.Sub: '-', ast.Mult: '*',
        ast.Div: '/', ast.FloorDiv: '//', ast.Mod: '%',
        ast.LShift: '<<', ast.RShift: '>>',
        ast.BitAnd: '&', ast.BitOr: '|', ast.BitXor: '^',
        ast.UAdd: '+', ast.USub: '-', ast.Invert: '~',
    }
    return names.get(type(op), type(op).__name__)


def _src(node, src):
    """The original-string slice spanning `node`, carrying the developer's
    symbols and spacing through unchanged."""
    return src[node.col_offset:node.end_col_offset]


def _cStyleIntRespell(slice_):
    """SV-subset spelling of a C-style integer-literal source slice, or None if
    `slice_` is not one. Python accepts `0x`/`0o`/`0b` integer literals but the
    SV grammar rejects them, spelling based literals `'hFF` / `'b1010`. A C-style
    literal parses to a bare `ast.Constant` int with no operator for the span
    walk to key on, so its own source span is re-spelled here. Octal folds to
    hex, matching the eval IR's octal->hex normalization (`evalExpr`)."""
    if len(slice_) < 3 or slice_[0] != '0' or slice_[1] not in 'xXoObB':
        return None
    radix = {'x': 16, 'o': 8, 'b': 2}[slice_[1].lower()]
    value = int(slice_[2:].replace('_', ''), radix)
    return f"'b{value:b}" if radix == 2 else f"'h{value:x}"


def _collectSpans(node, src, spans):
    """Append `(start, end, replacement)` rewrite spans for every Python-only
    construct in the tree. `.bit_length()` calls and C-style integer literals
    are rewritten; everything else is copied verbatim. (Floor division is never
    reached here - it is routed to NEEDS_MANUAL up front in convertExpr.)

    A `.bit_length()` receiver is carried through by its verbatim source slice
    and is not descended into: a convertible construct nested inside a receiver
    would survive unrewritten and is caught by the Step-5 re-parse rather than
    silently mis-converted.
    """
    if isinstance(node, ast.Expression):
        _collectSpans(node.body, src, spans)
        return
    if _isBitLengthCall(node):
        recv = node.func.value
        if (isinstance(recv, ast.BinOp) and isinstance(recv.op, ast.Sub)
                and isinstance(recv.right, ast.Constant) and recv.right.value == 1
                and not isinstance(recv.right.value, bool)):
            # ($X - 1).bit_length()  ->  $clog2($X)
            replacement = f"$clog2({_src(recv.left, src)})"
        else:
            # e.bit_length()  ==  $clog2(e + 1)
            replacement = f"$clog2({_src(recv, src)} + 1)"
        spans.append((node.col_offset, node.end_col_offset, replacement))
        return
    if isinstance(node, ast.BinOp):
        _collectSpans(node.left, src, spans)
        _collectSpans(node.right, src, spans)
        return
    if isinstance(node, ast.UnaryOp):
        _collectSpans(node.operand, src, spans)
        return
    if (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool)):
        respelled = _cStyleIntRespell(_src(node, src))
        if respelled is not None:
            spans.append((node.col_offset, node.end_col_offset, respelled))
        return
    # Name / decimal Constant: nothing to rewrite.


def _applySpans(src, spans):
    """Apply rewrite spans to `src`, right-to-left. Spans must not overlap; an
    overlap means a nested rewrite the span model cannot express and is raised
    as a converter bug."""
    ordered = sorted(spans, key=lambda s: s[0], reverse=True)
    prevStart = len(src)
    result = src
    for start, end, replacement in ordered:
        if end > prevStart:
            raise EvalConvertError(
                f"overlapping rewrite spans in {src!r}; cannot convert automatically")
        result = result[:start] + replacement + result[end:]
        prevStart = start
    return result


# ---------------------------------------------------------------------------
# File driver
# ---------------------------------------------------------------------------

@dataclass
class EvalRow:
    line: int            # 1-based line of the `eval` value in the source file
    original: str        # the authored eval expression
    result: ConvertResult
    valueType: str = None  # the row's valueType, if any


@dataclass
class FileReport:
    path: str
    rows: list = field(default_factory=list)
    written: bool = False

    @property
    def converted(self):
        return [r for r in self.rows if r.result.category == CONVERTED]

    @property
    def manual(self):
        return [r for r in self.rows if r.result.category == NEEDS_MANUAL]


def convertEvalsInFile(path, write=False):
    """Scan one YAML file for `eval` rows and convert them.

    Each `eval` row is converted with `convertExpr`, except rows carrying
    `valueType: real`, which are routed to NEEDS_MANUAL directly (a syntactic
    tool cannot resolve them to a literal). When `write` is true, CONVERTED
    rows are rewritten in place by replacing the exact authored expression
    substring on its line, leaving every other character untouched. ALREADY_SV
    and NEEDS_MANUAL rows are never written.

    Returns a FileReport.
    """
    with open(path, 'r') as fh:
        text = fh.read()

    report = FileReport(path=path)
    for line0, expr, valueType in _findEvalRows(text):
        if valueType == 'real':
            result = ConvertResult(
                NEEDS_MANUAL, expr,
                reason="real-valued eval; resolve to a literal value: by hand")
        else:
            result = convertExpr(expr)
        report.rows.append(EvalRow(line=line0 + 1, original=expr,
                                   result=result, valueType=valueType))

    if write and report.converted:
        report.written = _writeConversions(path, text, report.converted)
    return report


def _findEvalRows(text):
    """Yield `(line0, exprValue, valueType)` for every mapping in the YAML text
    that carries an `eval` key. Line numbers are 0-based and taken from the
    `eval` value node's source mark. Covers both constant `eval` rows and enum
    `eval` fields, since the walk visits every mapping node."""
    rows = []
    for doc in yaml.compose_all(text, Loader=yaml.SafeLoader):
        _walkNode(doc, rows)
    return rows


def _walkNode(node, rows):
    if isinstance(node, yaml.MappingNode):
        evalNode = None
        valueType = None
        for keyNode, valueNode in node.value:
            if isinstance(keyNode, yaml.ScalarNode):
                if keyNode.value == 'eval':
                    evalNode = valueNode
                elif keyNode.value == 'valueType':
                    valueType = valueNode.value
        if evalNode is not None and isinstance(evalNode, yaml.ScalarNode):
            rows.append((evalNode.start_mark.line, evalNode.value, valueType))
        for _, valueNode in node.value:
            _walkNode(valueNode, rows)
    elif isinstance(node, yaml.SequenceNode):
        for child in node.value:
            _walkNode(child, rows)


def _writeConversions(path, text, convertedRows):
    """Rewrite CONVERTED rows by targeted text replace and write the file back.

    Replaces the first occurrence of the authored expression on its source
    line. The authored eval is a single-line scalar whose value appears
    verbatim on the line (inside its quotes), so a missing match means the
    file shape is unexpected and is raised rather than silently skipped."""
    lines = text.splitlines(keepends=True)
    for row in convertedRows:
        idx = row.line - 1
        old = row.original
        new = row.result.expr
        if old not in lines[idx]:
            raise EvalConvertError(
                f"{path}:{row.line}: authored eval {old!r} not found on its line")
        lines[idx] = lines[idx].replace(old, new, 1)
    with open(path, 'w') as fh:
        fh.write(''.join(lines))
    return True
