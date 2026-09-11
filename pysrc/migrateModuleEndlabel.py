"""Re-stamp the USER-owned `endmodule: <label>` of each RTL block module file to
the project-qualified module name.

The SystemVerilog module begin-declaration is generator-owned
(`moduleInterfacesInstances`) and now emits the project-qualified module name
(`blockModuleName`). The matching `endmodule: <label>` in such a file is
scaffolded OUTSIDE the generated region (the user writes the module body and
closes it), so `make gen` never rewrites it. This one-time re-stamp aligns the
user end-label with the qualified begin-label; without it Verilator raises
`%Error-ENDLABEL`.

DB-backed, like migrateProjectParam: the qualified name is
`qualify(blockName, owningProject)` and the owner (`contextOwningProject`) exists
only after `make db`, so this runs in the `migrateYaml.py --sweep` phase. A
fully-generated RTL block (`moduleRegs` / `apbDecodeModule`) closes its module
INSIDE the generated region, so it carries no user end-label and is left
untouched. Idempotent (a file already carrying the qualified label is a no-op)
and owner-gated (a composed build never rewrites a referenced child's file).
"""

import os
import re
from dataclasses import dataclass, field

from pysrc.migrateCommon import _read, _write, _isGenerated, _loc, userRegionLines
from pysrc.artifactPaths import expandNewModulePath, fileMapCondMatch


# Applied-edit kind.
MODULE_ENDLABEL_RESTAMP = "MODULE_ENDLABEL_RESTAMP"

# A labelled `endmodule` line: leading indent + keyword + label + trailing space.
_ENDLABEL_RE = re.compile(r"^(\s*endmodule\s*:\s*)([A-Za-z_]\w*)(\s*)$")


@dataclass(frozen=True)
class ReportItem:
    kind: str
    location: str
    message: str


@dataclass
class ModuleEndlabelReport:
    projectName: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False

    @property
    def clean(self):
        return not self.manual


def _restampEndlabel(text, qualified):
    """Rewrite the user-region `endmodule: <label>` to `endmodule: <qualified>`.

    Returns (found, newText):
      (True, <text>)  a user-region labelled endmodule was rewritten
      (True, None)    it already reads the qualified label (idempotent no-op)
      (False, None)   no user-region labelled endmodule (generator-owned inside a
                      region, unlabelled, or absent) — nothing to re-stamp
    """
    userIdx = {i for i, _ in userRegionLines(text)}
    lines = text.splitlines(keepends=True)
    for i, raw in enumerate(lines):
        if i not in userIdx:
            continue
        stripped = raw.rstrip("\r\n")
        m = _ENDLABEL_RE.match(stripped)
        if not m:
            continue
        if m.group(2) == qualified:
            return True, None
        newline = raw[len(stripped):]  # preserve original line ending
        lines[i] = f"{m.group(1)}{qualified}{m.group(3)}{newline}"
        return True, "".join(lines)
    return False, None


def restampModuleEndlabel(prj, write=False):
    """Re-stamp the user `endmodule:` label of every RTL block file this project
    owns to the qualified module name. Returns a ModuleEndlabelReport."""
    projectName = prj.config.getConfig("PROJECTNAME")
    report = ModuleEndlabelReport(projectName=projectName)
    rtlDef = prj.filemap["rtlModule"]
    layout = prj.projectLayout[projectName]
    wrote = False
    for blockRow in prj.data["blocks"].values():
        # Only re-stamp files this build owns; a referenced child's RTL is
        # re-stamped by the child project's own migration (mirrors the
        # project/context re-stamp owner guard).
        if prj.contextOwningProject[blockRow["_context"]] != projectName:
            continue
        if not fileMapCondMatch(rtlDef, blockRow):
            continue
        filePath = expandNewModulePath(rtlDef, blockRow["dir"], blockRow["block"],
                                       blockRow["block"], layout, missingDirOk=True)
        qualified = prj.blockModuleName[blockRow["blockKey"]]
        for ext in rtlDef["ext"]:
            path = filePath + "." + rtlDef["ext"][ext]
            if not os.path.exists(path) or not _isGenerated(path):
                continue
            found, newText = _restampEndlabel(_read(path), qualified)
            if not found or newText is None:
                continue  # generator-owned/unlabelled endmodule, or already qualified
            report.applied.append(ReportItem(
                MODULE_ENDLABEL_RESTAMP, _loc(path, 0),
                f"re-stamped {os.path.basename(path)} endmodule label to "
                f"'{qualified}'"))
            if write:
                _write(path, newText)
                wrote = True
    report.written = wrote
    return report


def renderModuleEndlabelReport(report, write):
    lines = [f"=== module endmodule-label re-stamp: {report.projectName} ==="]
    if not report.applied:
        lines.append("  no user-owned RTL endmodule label to re-stamp; nothing to do")
        return "\n".join(lines)
    verb = "re-stamped" if write else "would re-stamp (dry-run; re-run with --write)"
    for item in report.applied:
        lines.append(f"  {verb}: {item.message}")
    return "\n".join(lines)
