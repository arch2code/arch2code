"""Report hand-written SV that still names a generated module or package by
the project-qualified name it had before SV names followed file names
(`holoscan_mailbox` is now `mailbox`). `make gen` fixes generated references
only. DB-backed: both names are persisted. Report-only.
"""

import bisect
import itertools
import os
import re
from dataclasses import dataclass, field

from pysrc.migrateCommon import _read, isSkippedDir, userRegionLines
from pysrc.artifactPaths import fileMapCondMatch


TODO_STALE_SV_NAME = "TODO_STALE_SV_NAME"

# Hand-written SV and vendor Verilog both name generated modules and packages.
_SV_EXTS = (".sv", ".svh", ".v", ".vh")

# The suffix the SV generator once appended to the context identity to name a package.
_OLD_PACKAGE_SUFFIX = "_package"

# `endmodule : <label>`. The end-label re-stamp owns these labels, so they are
# not reported here.
_ENDLABEL_RE = re.compile(r"\bendmodule\s*:\s*[A-Za-z_]\w*")

# Where an SV statement can begin: a line start, after `;`, `)` (an `if`
# condition, an attribute's `*)`) or `:` (a case item, a statement label), after
# `begin`, `else` or `generate` and an optional block label, or after a
# conditional-compilation directive.
_STMT_START = (r"(?:^|[;):]|\b(?:begin|else|generate)\b(?:\s*:\s*[A-Za-z_]\w*\b)?"
               r"|`(?:ifn?def|elsif)[ \t]+\w+|`(?:else|endif)\b)")

# Reserved words that can follow a name where an instance name would stand.
_NOT_AN_INSTANCE = (r"(?:iff|within|intersect|throughout|and|or|implies|until|s_until"
                    r"|until_with|s_until_with|if|for|foreach|while|repeat|case|casex"
                    r"|casez|unique|unique0|priority|assert|assume|cover|restrict|wait"
                    r"|disable)\b")


@dataclass(frozen=True)
class ReportItem:
    kind: str
    location: str
    message: str


@dataclass
class StaleSvNameReport:
    projectName: str
    manual: list = field(default_factory=list)    # list[ReportItem]

    @property
    def clean(self):
        return not self.manual


def _renamedSvNames(prj):
    """Map each old SV module name, and separately each old package name, to
    (current name, what it names). An old name that is unchanged, or is still
    some emitted artifact's current name, is valid, so it is left out."""
    modules = dict()
    for blockRow in prj.data["blocks"].values():
        key = blockRow["blockKey"]
        owner = prj.contextOwningProject[blockRow["_context"]]
        if not fileMapCondMatch(prj.projectLayout[owner]["fileMap"]["rtlModule"],
                                prj.getBlockCondRow(key)):
            continue
        modules[prj.blockModuleName[key]] = (prj.blockSvModuleName[key],
                                             f"block '{blockRow['block']}' module")
    # Only contexts that emit a package; the rest (interface libraries, contexts
    # with no content) never had one. INCLUDEFILES has no package_sv key at all
    # when no context emits an SV package.
    packages = dict()
    for context in prj.config.getConfig("INCLUDEFILES").get("package_sv", {}):
        packages[prj.contextModuleIdentity[context] + _OLD_PACKAGE_SUFFIX] = (
            prj.contextSvPackageName[context],
            f"context '{prj.includeName[context]}' package")
    current = {new for new, _ in modules.values()} | {new for new, _ in packages.values()}

    def stale(renamed):
        return {old: entry for old, entry in renamed.items()
                if old != entry[0] and old not in current}
    return stale(modules), stale(packages)


def _namesRe(names):
    # Longest first, so a name that extends another (`p_a_package` vs `p_a`)
    # matches as itself.
    return "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))


def _codeOnly(text):
    """`text` with comments, string literals and `endmodule` labels blanked to
    spaces. Whitespace is kept, so line numbers still match."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if two == "//":
            end = text.find("\n", i)
            end = n if end < 0 else end
        elif two == "/*":
            end = text.find("*/", i + 2)
            end = n if end < 0 else end + 2
        elif c == '"':
            end = i + 1
            while end < n and text[end] not in '"\n':
                end += 2 if text[end] == "\\" else 1
            end = min(end + 1, n)
        else:
            i += 1
            continue
        for j in range(i, end):
            if not out[j].isspace():
                out[j] = " "
        i = end
    return _ENDLABEL_RE.sub(lambda m: re.sub(r"\S", " ", m.group(0)), "".join(out))


def reportStaleSvNames(prj):
    """Report every user-region reference to a pre-refactor SV name in the
    project tree's SV files. Returns a StaleSvNameReport."""
    projectName = prj.config.getConfig("PROJECTNAME")
    report = StaleSvNameReport(projectName=projectName)
    modules, packages = _renamedSvNames(prj)
    renamed = modules | packages
    if not renamed:
        return report
    anyRe = re.compile(r"\b(" + _namesRe(renamed) + r")\b")
    # A package is referenced as `p::`. A module is referenced as the type of an
    # instantiation at a statement start, followed by `#` (not `##`), or by an
    # instance name, any unpacked dimensions and `(`; and by name after
    # `module`, `macromodule` or a config `cell`. Whitespace after a name may
    # span lines.
    packageRe = re.compile(r"\b(" + _namesRe(packages) + r")\s*::") if packages else None
    moduleRe = re.compile(_STMT_START + r"[ \t]*\b(" + _namesRe(modules)
                          + r")\b\s*(?:#(?!#)|(?!" + _NOT_AN_INSTANCE
                          + r")[A-Za-z_]\w*\s*(?:\[[^\]]*\]\s*)*\()",
                          re.M) if modules else None
    definitionRe = re.compile(
        r"\b(?:(?:module|macromodule)\s+(?:(?:automatic|static)\s+)?|cell\s+(?:\w+\.)?)("
        + _namesRe(modules) + r")\b") if modules else None
    rootDir = prj.projectLayout[projectName]["root"]
    for dirpath, dirnames, filenames in os.walk(rootDir):
        dirnames[:] = sorted(d for d in dirnames if not isSkippedDir(d))
        for fn in sorted(filenames):
            if not fn.endswith(_SV_EXTS):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, rootDir)
            text = _read(path)
            if not anyRe.search(text):
                continue
            code = _codeOnly(text)
            # Line starts from the split userRegionLines uses, which also
            # breaks on `\f`, `\v` and Unicode line separators.
            starts = list(itertools.accumulate(
                (len(line) for line in code.splitlines(keepends=True)), initial=0))
            hits = dict()   # line index -> {offset: old name}
            for refRe in (packageRe, moduleRe, definitionRe):
                if refRe:
                    for m in refRe.finditer(code):
                        i = bisect.bisect_right(starts, m.start(1)) - 1
                        hits.setdefault(i, {})[m.start(1)] = m.group(1)
            for i, _ in userRegionLines(text):
                for _, old in sorted(hits.get(i, {}).items()):
                    new, what = renamed[old]
                    report.manual.append(ReportItem(
                        TODO_STALE_SV_NAME, f"{rel}:{i + 1}",
                        f"'{old}' is the old name of {what}; the "
                        f"generator now emits '{new}'. Rename the reference"))
    return report


def renderStaleSvNameReport(report):
    lines = [f"=== stale SV names in user code: {report.projectName} ==="]
    if report.clean:
        lines.append("  no user SV names a pre-refactor module or package; nothing to do")
        return "\n".join(lines)
    lines.append("  manual TODO:")
    for item in report.manual:
        lines.append(f"    {item.location}  {item.kind}  {item.message}")
    return "\n".join(lines)
