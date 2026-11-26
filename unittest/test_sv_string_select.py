#!/usr/bin/env python3
"""No SystemVerilog ?: picks between two string literals.

VCS types `cond ? "a" : "bb"` as a packed vector, not a string, so %s prints
the shorter literal right-justified with leading spaces; Xcelium prints it
as written. A string'() cast on an arm does not change that on VCS.
a2c_select_str() in a2c_uvm_pkg.sv returns a string on both.

The check reads every SV file in the base tree except the Verilator-only
benches under unittest/, and the SV text the generators emit: each Python
string in templates/systemVerilog/*.py and pysrc/systemVerilogGenerator*.py,
with an f-string's replacement fields read as identifiers. Comments are
skipped, and a ? or : inside a string literal is text. Run on its own, the
file first proves the scanner on planted cases.
"""

import ast
import glob
import os
import re
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

SV_SUFFIXES = ('.sv', '.svh', '.v', '.vh')
FIX = 'use a2c_select_str(cond, "a", "b") from a2c_uvm_pkg, which VCS and Xcelium both type as string'

# A character that continues an expression after an operand. An arm whose
# literal is followed by one of these is part of a larger expression.
CONTINUES = set('+-*/%&|^<>=!.[\'')


def mask(src):
    """src with comments blanked and each string literal's body replaced by
    x, so offsets and newlines still match src. `" is a macro's string
    delimiter, not a literal."""
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        if src.startswith('`"', i) or src.startswith('`\\`"', i):
            i += 2 if src[i + 1] == '"' else 4
        elif src.startswith('//', i):
            j = src.find('\n', i)
            j = n if j < 0 else j
            out[i:j] = ' ' * (j - i)
            i = j
        elif src.startswith('/*', i):
            j = src.find('*/', i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != '\n':
                    out[k] = ' '
            i = j
        elif src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"' and src[j] != '\n':
                j += 2 if src[j] == '\\' else 1
            for k in range(i + 1, min(j, n)):
                if out[k] != '\n':
                    out[k] = 'x'
            i = j + 1
        else:
            i += 1
    return ''.join(out)


# A string literal, bare, in parentheses or in a string'() cast.
STRING = r'(?:"x*"|string\s*\'\s*\(\s*"x*"\s*\))'
LITERAL = re.compile(r'\s*(\(\s*)*' + STRING + r'(\s*\))*\s*$')


def is_literal(arm):
    m = LITERAL.match(arm)
    return bool(m) and arm.count('(') == arm.count(')')


def true_arm_end(m, i):
    """Index of the : that ends the true arm starting at i, or -1."""
    depth = 0
    while i < len(m):
        c = m[i]
        if m.startswith('::', i):
            i += 2
            continue
        if c in '([{':
            depth += 1
        elif c in ')]}':
            if depth == 0:
                return -1
            depth -= 1
        elif c == ';' and depth == 0:
            return -1
        elif c == ':' and depth == 0:
            return i
        i += 1
    return -1


def false_arm_is_literal(m, i):
    """Whether the false arm starting at i is a string literal, possibly in
    parentheses, that nothing after it extends."""
    match = re.compile(r'\s*((?:\(\s*)*)' + STRING).match(m, i)
    if not match:
        return False
    j = match.end()
    opened = match.group(1).count('(')
    while opened:
        k = j
        while k < len(m) and m[k].isspace():
            k += 1
        if k >= len(m) or m[k] != ')':
            return False
        j = k + 1
        opened -= 1
    while j < len(m) and m[j].isspace():
        j += 1
    return j >= len(m) or m[j] not in CONTINUES


def literal_selects(src):
    """(line, text) of each ?: in src whose arms are both string literals."""
    m = mask(src)
    found = []
    for q in re.finditer(r'\?', m):
        p = q.start()
        colon = true_arm_end(m, p + 1)
        if colon < 0 or not is_literal(m[p + 1:colon]) or not false_arm_is_literal(m, colon + 1):
            continue
        line = src.count('\n', 0, p) + 1
        end = src.find('\n', p)
        found.append((line, ' '.join(src[src.rfind('\n', 0, p) + 1:end if end >= 0 else None].split())))
    return found


def sv_files(root, skip_dirs=()):
    """Every SV file under root, outside .git and the directories named."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames
                             if d != '.git' and os.path.join(dirpath, d) not in skip_dirs)
        files += [os.path.join(dirpath, f) for f in sorted(filenames) if f.endswith(SV_SUFFIXES)]
    return files


def python_strings(path):
    """(line, text) of each string in a Python file, an f-string's
    replacement fields read as an identifier."""
    tree = ast.parse(open(path).read(), path)
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            parts = [v.value if isinstance(v, ast.Constant) else 'a2c_field' for v in node.values]
            yield node.lineno, ''.join(parts)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value


def template_selects(path):
    """(line, text) of each literal-literal ?: in the SV a Python
    generator file holds, by the line of the Python string."""
    found = []
    for lineno, text in python_strings(path):
        found += [(lineno + line - 1, snippet) for line, snippet in literal_selects(text)]
    return found


def scan(sv_paths, template_paths):
    """'path:line: text' of every literal-literal ?: found."""
    hits = []
    for path in sv_paths:
        hits += [f'{path}:{line}: {text}' for line, text in literal_selects(open(path, errors='replace').read())]
    for path in template_paths:
        hits += [f'{path}:{line}: {text}' for line, text in template_selects(path)]
    return hits


# (SV text, number of literal-literal ?: in it)
PLANTED = (
    ('s = c ? "a" : "bb";', 1),
    ('s = c ? ("a") : ( "bb" );', 1),
    ('$display("%s", c ? "src"\n                  : "dst");', 1),
    ('f(c ? "a" : "b", 2);', 1),
    ('s = {x, c ? "a" : "b"};', 1),
    ('s = c1 ? "a" : c2 ? "b" : "c";', 1),
    ('s = a ? b ? "x" : "y" : "z";', 1),
    ('`define PICK(c) c ? "on" : "off"\n', 1),
    ('s = c ? "a?" : "b:c";', 1),
    ('s = c ? "a\\"" : "b";', 1),
    ('// s = c ? "a" : "b";', 0),
    ('/* s = c ? "a" :\n "b"; */', 0),
    ('$display("c ? \\"a\\" : \\"b\\"");', 0),
    ('s = a2c_select_str(c, "a", "b");', 0),
    ('s = c ? name : "b";', 0),
    ('s = c ? "a" : name;', 0),
    ('s = c ? string\'("a") : string\'("b");', 1),
    ('s = c ? string\'("") : "s";', 1),
    ('s = c ? string\'(name) : "s";', 0),
    ('s = c ? "a" : "b" == t;', 0),
    ('x = pkg::f(c) ? pkg::A : pkg::B;', 0),
    ('casez (v) 4\'b1??0: y = 1; endcase', 0),
    ('`define Q(x) `"x`"\ns = c ? `Q(a) : "b";', 0),
)


def prove_scanner():
    """Whether the scanner finds exactly the planted cases."""
    ok = True
    for text, want in PLANTED:
        got = len(literal_selects(text))
        if got != want:
            print(f'FAIL: scanner found {got} literal-literal ?: in {text!r}, not {want}')
            ok = False
    template = 'lines = [f"    assign {name} = {sel} ? \\"{a}\\" : \\"{b}\\";", "s = c ? x : y;"]\n'
    tmp = os.path.join(test_dir, f'.planted_template_{os.getpid()}.py')
    try:
        with open(tmp, 'w') as f:
            f.write(template)
        got = template_selects(tmp)
    finally:
        os.remove(tmp)
    if [line for line, _ in got] != [1]:
        print(f'FAIL: scanner found {got} in a template string holding one literal-literal ?:')
        ok = False
    if ok:
        print(f'PASS: the scanner finds the {sum(w for _, w in PLANTED) + 1} planted literal-literal ?: '
              f'and none of the {sum(1 for _, w in PLANTED if not w)} look-alikes')
    return ok


def report(hits, checked, where):
    if hits:
        for hit in hits:
            print(f'FAIL: {hit}')
        print(f'FAIL: {len(hits)} ?: in {where} pick between two string literals; {FIX}')
        return False
    print(f'PASS: no literal-literal ?: in {checked} files of {where}')
    return True


def main():
    ok = prove_scanner()
    sv = sv_files(base_dir, skip_dirs=(os.path.join(base_dir, 'unittest'),))
    templates = sorted(glob.glob(os.path.join(base_dir, 'templates', 'systemVerilog', '*.py'))
                       + glob.glob(os.path.join(base_dir, 'pysrc', 'systemVerilogGenerator*.py')))
    if not sv or not templates:
        print(f'FAIL: found {len(sv)} SV files and {len(templates)} SV generator files')
        ok = False
    ok = report(scan(sv, templates), len(sv) + len(templates),
                'the base SV library, examples and SV generators') and ok
    print('ALL TESTS PASSED' if ok else 'SOME TESTS FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
