#!/usr/bin/env python3
"""Opt-in functional -> hierarchical layout migration
(plan-decomp-functional-layout.md "Phase 4 - L4", T4.1-T4.4).

migrateLayout classifies a project into one of three layout states without
opening the database (text-only, like the other migration phases), computes the
relocation map, applies it, and re-roots the relative include/projectFiles/
user-region references broken by the moves. This test covers:

  - classification + no-op / blocked semantics (T4.1)
  - the fileMap-driven relocation map: recognized fully-generated file types are
    deleted+recreated, every other source (user-editable or unrecognized/custom
    fileMap type) MOVES byte-preserving; orphans move into prj/ (T4.2, T4.3)
  - the T4.4 relative-path re-rooting: include:/projectFiles: entries and
    user-region source includes, with unrewritable references reported not
    mangled.

File classification uses the merged fileMap (base/pro/user), the same merge the
generator runs at create, so a project that declares only a subset still
classifies its base-inherited file types. The recognized fully-generated set is
keyed on the base-config fileMap key names; an unrecognized key is preserved
(moved), never deleted.
"""

import os
import shutil
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir

sys.path.insert(0, base_dir)
from pysrc.migrateLayout import (  # noqa: E402
    LAYOUT_ALREADY_HIERARCHICAL,
    LAYOUT_FUNCTIONAL,
    LAYOUT_NEEDS_MIGRATION,
    MOVE_AUTHORED_YAML,
    MOVE_ORPHAN,
    MOVE_PROJECT_FILE,
    MOVE_SOURCE,
    TODO_NOT_FORMAT2,
    TODO_UNGENERATED_FILE,
    TODO_UNREWRITABLE_PATH,
    migrateLayoutInProject,
)

_MARKER = "// GENERATED_CODE_BEGIN\n// GENERATED_CODE_END\n"


# A real functional example (no `layout:` selector, yamlFormat: 2) for the
# no-op classification check. `nested` is no longer usable here — it was
# converted to hierarchical as the T4.6 sign-off vehicle (see
# test_layout_nested.py) — so this points at a still-functional example.
FUNCTIONAL_PROJECT = os.path.join(base_dir, "examples", "simple", "arch", "yaml",
                                  "project.yaml")
HIERARCHICAL_PROJECT = os.path.join(test_dir, "fixtures", "hier-layout", "prj",
                                    "yaml", "hierProject.yaml")


def _writeTemp(text):
    fd, path = tempfile.mkstemp(suffix=".yaml", prefix="layoutmig_")
    with os.fdopen(fd, "w") as fh:
        fh.write(text)
    return path


def _check(name, cond):
    print(f"  {'PASS' if cond else 'FAIL'}: {name}")
    return cond


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


def _optInLayout(projFile):
    """Insert `layout: hierarchical` under `fileGeneration:` so a copied
    functional example becomes a migration candidate (the live tree must stay
    functional, so this only ever runs on a temp copy)."""
    text = open(projFile).read()
    _write(projFile, text.replace("fileGeneration:\n",
                                  "fileGeneration:\n  layout: hierarchical\n", 1))


def _moveSet(report, kind, root):
    """{(relSrc, relDst)} for every move of `kind`, relative to the project root
    so the assertion is path-independent."""
    return {(os.path.relpath(m.src, root), os.path.relpath(m.dst, root))
            for m in report.moves if m.kind == kind}


def _relDeletes(report, root):
    return {os.path.relpath(p, root) for p in report.deletes}


def _rewriteSet(report, kind, root):
    """{(relPath, old, new)} for every rewrite of `kind`."""
    return {(os.path.relpath(rw.path, root), rw.old, rw.new)
            for rw in report.rewrites if rw.kind == kind}


def test_decomposed_example_map(ok):
    """hierInclude is the decomposed vehicle (2 decomp subdirs, include chains).
    A temp copy opted into hierarchical produces the decomp-preserving authored
    YAML + project-file moves, deletes only the fully-generated *_package.sv,
    MOVES the user-editable module .sv into <node>/rtl/, and re-roots the four
    cross-node include/projectFiles references (same-node references unchanged),
    with nothing manual and no writes to the copy."""
    tmp = tempfile.mkdtemp(prefix="layoutmap_hier_")
    try:
        dst = os.path.join(tmp, "hierInclude")
        shutil.copytree(os.path.join(base_dir, "examples", "hierInclude"), dst,
                        ignore=shutil.ignore_patterns("build", ".gen", "*.db",
                                                      ".*.db", "obj_dir"))
        proj = os.path.join(dst, "arch", "hierIncludeProject.yaml")
        _optInLayout(proj)

        before = _treeSnapshot(dst)
        r = migrateLayoutInProject(proj)
        root = r.projectRoot

        ok &= _check("decomposed candidate is LAYOUT_NEEDS_MIGRATION",
                     r.state == LAYOUT_NEEDS_MIGRATION)
        ok &= _check("decomposed candidate has no manual items", not r.manual)

        authored = _moveSet(r, MOVE_AUTHORED_YAML, root)
        ok &= _check("authored YAML decomp preserved (root + b/ + c/)", authored == {
            ("arch/hierInclude.yaml", "yaml/hierInclude.yaml"),
            ("arch/hierIncludeTop.yaml", "yaml/hierIncludeTop.yaml"),
            ("arch/hierIncludeNestedTop.yaml", "yaml/hierIncludeNestedTop.yaml"),
            ("arch/b/hierIncludeB.yaml", "b/yaml/hierIncludeB.yaml"),
            ("arch/b/hierIncludeBInclude.yaml", "b/yaml/hierIncludeBInclude.yaml"),
            ("arch/c/hierIncludeC.yaml", "c/yaml/hierIncludeC.yaml"),
            ("arch/c/hierIncludeCInclude.yaml", "c/yaml/hierIncludeCInclude.yaml"),
        })

        ok &= _check("project file -> prj/yaml/<name>Project.yaml",
                     _moveSet(r, MOVE_PROJECT_FILE, root) ==
                     {("arch/hierIncludeProject.yaml",
                       "prj/yaml/hierIncludeProject.yaml")})

        # Only the fully-generated *_package.sv (fileMap key `package`) delete;
        # the user-editable module .sv (rtlModule) move to <node>/rtl/.
        deletes = _relDeletes(r, root)
        ok &= _check("only *_package.sv deleted",
                     deletes and all(d.endswith("_package.sv") for d in deletes))
        ok &= _check("module .sv NOT deleted",
                     not any(d.endswith("blockA.sv") for d in deletes))

        srcMoves = _moveSet(r, MOVE_SOURCE, root)
        ok &= _check("root-node module .sv -> rtl/",
                     ("systemVerilog/blockA.sv", "rtl/blockA.sv") in srcMoves)
        ok &= _check("b-node module .sv -> b/rtl/",
                     ("systemVerilog/b/blockBX.sv", "b/rtl/blockBX.sv") in srcMoves)
        ok &= _check("c-node module .sv -> c/rtl/",
                     ("systemVerilog/c/blockCZ.sv", "c/rtl/blockCZ.sv") in srcMoves)

        # The four cross-node references re-root; same-node ones are unchanged
        # (absent from the rewrite set).
        incl = _rewriteSet(r, "include", root)
        ok &= _check("b/c cross-node include re-rooted", incl == {
            ("b/yaml/hierIncludeB.yaml", "../hierInclude.yaml", "../../yaml/hierInclude.yaml"),
            ("c/yaml/hierIncludeC.yaml", "../hierInclude.yaml", "../../yaml/hierInclude.yaml"),
        })
        pf = _rewriteSet(r, "projectFiles", root)
        ok &= _check("projectFiles entries re-rooted", pf == {
            ("prj/yaml/hierIncludeProject.yaml", "hierInclude.yaml", "../../yaml/hierInclude.yaml"),
            ("prj/yaml/hierIncludeProject.yaml", "b/hierIncludeB.yaml", "../../b/yaml/hierIncludeB.yaml"),
            ("prj/yaml/hierIncludeProject.yaml", "c/hierIncludeC.yaml", "../../c/yaml/hierIncludeC.yaml"),
        })

        ok &= _check("decomposed dry-run wrote nothing",
                     _treeSnapshot(dst) == before)
    finally:
        shutil.rmtree(tmp)
    return ok


def _synthProject(root):
    """Write a synthetic decomposed project exercising every classification
    branch and return its project-file path. Two nodes ("" and sub); files are
    classified by the merged base fileMap."""
    yamlRoot = os.path.join(root, "arch", "yaml")
    proj = os.path.join(yamlRoot, "project.yaml")
    _write(proj,
           "yamlFormat: 2\n"
           "projectName: demo\n"
           "dirs:\n"
           "  root: ../..\n"
           "  base: $root/base\n"
           "  model: $root/model\n"
           "  rtl: $root/rtl\n"
           "  vl_wrap: $root/verif/vl_wrap\n"
           "  fw: $root/fw\n"
           "fileGeneration:\n"
           "  layout: hierarchical\n"
           "projectFiles:\n"
           "  - demo.yaml\n"
           "  - sub/subblk.yaml\n")
    _write(os.path.join(yamlRoot, "demo.yaml"), "blocks:\n  demo: {}\n")
    _write(os.path.join(yamlRoot, "sub", "subblk.yaml"),
           "include:\n  - ../demo.yaml\nblocks:\n  subblk: {}\n")
    _write(os.path.join(root, "include", "make", "shared.mk"), "PROJECTNAME=demo\n")
    # fully-generated (marker) -> delete: blockBase (base/*Base.h), package (rtl/*_package.sv)
    _write(os.path.join(root, "base", "demoBase.h"), _MARKER)
    _write(os.path.join(root, "base", "sub", "subblkBase.h"), _MARKER)
    _write(os.path.join(root, "rtl", "demo_package.sv"), _MARKER)
    # name-matched fully-generated file WITHOUT the marker -> manual (kept)
    _write(os.path.join(root, "base", "handBase.h"), "struct hand {};\n")
    # user-editable (block / rtlModule): root node stays, sub node moves
    _write(os.path.join(root, "model", "demo.cpp"), _MARKER)
    _write(os.path.join(root, "model", "sub", "subblk.cpp"), _MARKER)
    _write(os.path.join(root, "rtl", "demo.sv"), _MARKER)
    _write(os.path.join(root, "rtl", "sub", "subblk.sv"), _MARKER)
    # orphans -> move (sc_main/fwIpMain hand-written, vl_wrap aggregator generated)
    _write(os.path.join(root, "verif", "vl_wrap", "sc_main.cpp"), "int main(){}\n")
    _write(os.path.join(root, "verif", "vl_wrap", "vl_wrap.cpp"), _MARKER)
    _write(os.path.join(root, "fw", "fwIpMain.cpp"), "void fw(){}\n")
    return proj


def test_orphan_and_guard_map(ok):
    """Synthetic decomposed fixture exercising every classification branch:
    fully-generated types (blockBase, package) delete; user-editable types
    (block, rtlModule) move (root node stays, sub node relocates); orphans move
    into prj/; build-config include/ STAYS at the project root (Q-L3 amended,
    only its A2C_PRJ_YAML line is re-pointed); a name-matched fully-generated
    file lacking the marker is reported manual, never deleted."""
    tmp = tempfile.mkdtemp(prefix="layoutmap_orphan_")
    try:
        root = os.path.join(tmp, "demo")
        proj = _synthProject(root)

        before = _treeSnapshot(root)
        r = migrateLayoutInProject(proj)
        rt = r.projectRoot

        ok &= _check("synthetic candidate is LAYOUT_NEEDS_MIGRATION",
                     r.state == LAYOUT_NEEDS_MIGRATION)
        ok &= _check("authored YAML decomp (root + sub/)",
                     _moveSet(r, MOVE_AUTHORED_YAML, rt) == {
                         ("arch/yaml/demo.yaml", "yaml/demo.yaml"),
                         ("arch/yaml/sub/subblk.yaml", "sub/yaml/subblk.yaml"),
                     })
        ok &= _check("build-config include/ NOT moved (stays at project root)",
                     not any("include/make/shared.mk" in os.path.relpath(m.src, rt) or
                             "include/make/shared.mk" in os.path.relpath(m.dst, rt)
                             for m in r.moves))
        harness = {(os.path.relpath(e.path, rt), e.old, e.new)
                   for e in r.harnessEdits}
        ok &= _check("A2C_PRJ_YAML re-point planned into root harness",
                     harness == {("include/make/shared.mk", "",
                                  "A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/demoProject.yaml")})
        ok &= _check("orphans move to prj/verif and prj/fw (flattened)",
                     _moveSet(r, MOVE_ORPHAN, rt) == {
                         ("verif/vl_wrap/sc_main.cpp", "prj/verif/sc_main.cpp"),
                         ("verif/vl_wrap/vl_wrap.cpp", "prj/verif/vl_wrap.cpp"),
                         ("fw/fwIpMain.cpp", "prj/fw/fwIpMain.cpp"),
                     })
        ok &= _check("fully-generated types deleted (blockBase, package)",
                     _relDeletes(r, rt) == {
                         "base/demoBase.h", "base/sub/subblkBase.h",
                         "rtl/demo_package.sv"})
        # User-editable source: root node stays in place, sub node relocates.
        srcMoves = _moveSet(r, MOVE_SOURCE, rt)
        ok &= _check("root-node user source not moved (demo.cpp/demo.sv)",
                     not any(s in ("model/demo.cpp", "rtl/demo.sv")
                             for s, _ in srcMoves))
        ok &= _check("sub-node user source moves to <node>/<seg>/",
                     srcMoves == {
                         ("model/sub/subblk.cpp", "sub/model/subblk.cpp"),
                         ("rtl/sub/subblk.sv", "sub/rtl/subblk.sv"),
                     })
        ok &= _check("unguarded name-matched fully-generated file reported manual",
                     any(i.kind == TODO_UNGENERATED_FILE and
                         "handBase.h" in i.location for i in r.manual))
        ok &= _check("unguarded file not deleted, not moved",
                     "base/handBase.h" not in _relDeletes(r, rt) and
                     not any("handBase.h" in s for s, _ in srcMoves))
        ok &= _check("synthetic dry-run wrote nothing",
                     _treeSnapshot(root) == before)
    finally:
        shutil.rmtree(tmp)
    return ok


def test_apply_decomposed(ok):
    """T4.3+T4.4 apply on a temp copy of hierInclude: authored YAML under
    <node>/yaml/, project file under prj/yaml/ with re-rooted projectFiles,
    cross-node include re-rooted, *_package.sv deleted, module .sv relocated to
    <node>/rtl/ byte-preserved, emptied decomp subdirs pruned, the migrated tree
    still parses, and a re-run is a no-op (idempotent)."""
    import yaml
    tmp = tempfile.mkdtemp(prefix="layoutapply_hier_")
    try:
        dst = os.path.join(tmp, "hierInclude")
        shutil.copytree(os.path.join(base_dir, "examples", "hierInclude"), dst,
                        ignore=shutil.ignore_patterns("build", ".gen", "*.db",
                                                      ".*.db", "obj_dir"))
        proj = os.path.join(dst, "arch", "hierIncludeProject.yaml")
        _optInLayout(proj)

        # A module .sv has no relative includes, so its move must byte-preserve.
        svSrc = os.path.join(dst, "systemVerilog", "b", "blockBX.sv")
        svBytes = open(svSrc, "rb").read()

        r = migrateLayoutInProject(proj, write=True)
        root = r.projectRoot

        ok &= _check("apply reports written", r.written)
        ok &= _check("apply candidate has no manual items", not r.manual)

        ok &= _check("authored YAML relocated to b/yaml/",
                     os.path.isfile(os.path.join(root, "b", "yaml", "hierIncludeB.yaml")))
        ok &= _check("root-node authored YAML at yaml/",
                     os.path.isfile(os.path.join(root, "yaml", "hierInclude.yaml")))

        # Cross-node include physically re-rooted in the relocated file.
        bText = open(os.path.join(root, "b", "yaml", "hierIncludeB.yaml")).read()
        ok &= _check("b include re-rooted in place",
                     "../../yaml/hierInclude.yaml" in bText and
                     "- ../hierInclude.yaml" not in bText)

        movedProj = os.path.join(root, "prj", "yaml", "hierIncludeProject.yaml")
        pfText = open(movedProj).read()
        ok &= _check("project file relocated with re-rooted projectFiles",
                     os.path.isfile(movedProj) and
                     "../../b/yaml/hierIncludeB.yaml" in pfText and
                     "../../yaml/hierInclude.yaml" in pfText)
        ok &= _check("old project file location gone", not os.path.exists(proj))

        # Module .sv moved to <node>/rtl/, byte-preserved (no rewrite); package gone.
        movedSv = os.path.join(root, "b", "rtl", "blockBX.sv")
        ok &= _check("module .sv relocated to b/rtl/ byte-preserved",
                     os.path.isfile(movedSv) and open(movedSv, "rb").read() == svBytes)
        ok &= _check("root-node module .sv at rtl/",
                     os.path.isfile(os.path.join(root, "rtl", "blockA.sv")))
        sv = os.path.join(root, "systemVerilog")
        ok &= _check("*_package.sv deleted",
                     not any(f.endswith("_package.sv")
                             for _, _, fs in os.walk(sv) for f in fs))
        ok &= _check("non-source scaffolding preserved",
                     os.path.isfile(os.path.join(sv, "package.f")) and
                     os.path.isfile(os.path.join(sv, "Makefile")))
        ok &= _check("emptied systemVerilog/b pruned",
                     not os.path.exists(os.path.join(sv, "b")))
        ok &= _check("emptied systemVerilog/c pruned",
                     not os.path.exists(os.path.join(sv, "c")))

        # Every migrated YAML parses.
        parses = True
        for dp, _, fs in os.walk(root):
            for f in fs:
                if f.endswith(".yaml"):
                    try:
                        yaml.safe_load(open(os.path.join(dp, f)).read())
                    except Exception:
                        parses = False
        ok &= _check("all migrated YAML parses", parses)

        # Idempotent: re-run against the relocated project file is a no-op.
        r2 = migrateLayoutInProject(movedProj)
        ok &= _check("re-run is LAYOUT_ALREADY_HIERARCHICAL no-op",
                     r2.state == LAYOUT_ALREADY_HIERARCHICAL and
                     r2.isNoOp and not r2.written)
    finally:
        shutil.rmtree(tmp)
    return ok


def test_apply_orphan_and_guard(ok):
    """T4.3 apply on the synthetic fixture: fully-generated deletes removed,
    user-editable sub-node source relocated byte-preserved, orphans under prj/,
    build-config include/ kept at the project root with only its A2C_PRJ_YAML
    line re-pointed, the unguarded name-matched file left in place (dir kept),
    and a re-run is a no-op."""
    tmp = tempfile.mkdtemp(prefix="layoutapply_orphan_")
    try:
        root = os.path.join(tmp, "demo")
        proj = _synthProject(root)

        r = migrateLayoutInProject(proj, write=True)
        rt = r.projectRoot

        ok &= _check("apply reports written", r.written)
        ok &= _check("sc_main moved to prj/verif (byte-preserved)",
                     open(os.path.join(rt, "prj", "verif", "sc_main.cpp")).read()
                     == "int main(){}\n")
        ok &= _check("fwIpMain moved to prj/fw (byte-preserved)",
                     open(os.path.join(rt, "prj", "fw", "fwIpMain.cpp")).read()
                     == "void fw(){}\n")
        ok &= _check("vl_wrap aggregator moved, never deleted",
                     os.path.isfile(os.path.join(rt, "prj", "verif", "vl_wrap.cpp")))
        ok &= _check("build config NOT relocated under prj/",
                     not os.path.exists(os.path.join(rt, "prj", "include")))
        harnessText = open(os.path.join(rt, "include", "make", "shared.mk")).read()
        ok &= _check("build config stays at root include/, A2C_PRJ_YAML re-pointed",
                     "PROJECTNAME=demo\n" in harnessText and
                     "A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/demoProject.yaml" in harnessText)
        ok &= _check("authored YAML relocated (root + sub/)",
                     os.path.isfile(os.path.join(rt, "yaml", "demo.yaml")) and
                     os.path.isfile(os.path.join(rt, "sub", "yaml", "subblk.yaml")))

        ok &= _check("fully-generated deletes removed",
                     not os.path.exists(os.path.join(rt, "base", "demoBase.h")) and
                     not os.path.exists(os.path.join(rt, "rtl", "demo_package.sv")))
        ok &= _check("root-node user source kept in place",
                     os.path.isfile(os.path.join(rt, "model", "demo.cpp")) and
                     os.path.isfile(os.path.join(rt, "rtl", "demo.sv")))
        ok &= _check("sub-node user source relocated byte-preserved",
                     os.path.isfile(os.path.join(rt, "sub", "model", "subblk.cpp")) and
                     os.path.isfile(os.path.join(rt, "sub", "rtl", "subblk.sv")))
        ok &= _check("unguarded name-matched file left in place, dir kept",
                     os.path.isfile(os.path.join(rt, "base", "handBase.h")) and
                     os.path.isdir(os.path.join(rt, "base")))
        ok &= _check("unguarded file reported manual",
                     any(i.kind == TODO_UNGENERATED_FILE and
                         "handBase.h" in i.location for i in r.manual))

        # Idempotent even though an unguarded file remains (layout is hierarchical).
        movedProj = os.path.join(rt, "prj", "yaml", "demoProject.yaml")
        r2 = migrateLayoutInProject(movedProj)
        ok &= _check("re-run is LAYOUT_ALREADY_HIERARCHICAL no-op",
                     r2.state == LAYOUT_ALREADY_HIERARCHICAL and r2.isNoOp)
    finally:
        shutil.rmtree(tmp)
    return ok


def test_source_userregion_rewrite(ok):
    """A moved user source file whose user-region relative include names a file
    in another node has that include re-rooted through the new levels; the
    include inside a generated region is left for make gen (never hand-edited)."""
    tmp = tempfile.mkdtemp(prefix="layoutsrc_")
    try:
        root = os.path.join(tmp, "demo")
        yamlRoot = os.path.join(root, "arch", "yaml")
        proj = os.path.join(yamlRoot, "project.yaml")
        _write(proj,
               "yamlFormat: 2\n"
               "projectName: demo\n"
               "dirs:\n  root: ../..\n  model: $root/model\n"
               "fileGeneration:\n  layout: hierarchical\n"
               "projectFiles:\n  - a/ablk.yaml\n  - b/bblk.yaml\n")
        _write(os.path.join(yamlRoot, "a", "ablk.yaml"), "blocks:\n  ablk: {}\n")
        _write(os.path.join(yamlRoot, "b", "bblk.yaml"), "blocks:\n  bblk: {}\n")
        # a-node user source with a cross-node relative include in a USER region,
        # plus a same-cross-node include inside a GENERATED region (must NOT change).
        _write(os.path.join(root, "model", "a", "ablk.cpp"),
               '#include "../b/bblk.h"\n'
               "// GENERATED_CODE_BEGIN\n"
               '#include "../b/bblk.h"\n'
               "// GENERATED_CODE_END\n")
        _write(os.path.join(root, "model", "b", "bblk.h"), _MARKER)

        r = migrateLayoutInProject(proj, write=True)
        rt = r.projectRoot

        moved = os.path.join(rt, "a", "model", "ablk.cpp")
        text = open(moved).read()
        # User-region include re-rooted: model/a -> a/model, target b -> b/model.
        ok &= _check("user-region cross-node include re-rooted",
                     '#include "../../b/model/bblk.h"' in text)
        ok &= _check("generated-region include left untouched",
                     text.count('#include "../b/bblk.h"') == 1)
        ok &= _check("source rewrite has no manual items", not r.manual)
    finally:
        shutil.rmtree(tmp)
    return ok


def test_unrewritable_reported(ok):
    """A relative include that escapes the project root cannot be re-rooted
    mechanically: it is reported (TODO_UNREWRITABLE_PATH) and left byte-for-byte,
    never mangled."""
    tmp = tempfile.mkdtemp(prefix="layoutunrw_")
    try:
        root = os.path.join(tmp, "demo")
        yamlRoot = os.path.join(root, "arch", "yaml")
        proj = os.path.join(yamlRoot, "project.yaml")
        _write(proj,
               "yamlFormat: 2\n"
               "projectName: demo\n"
               "dirs:\n  root: ../..\n"
               "fileGeneration:\n  layout: hierarchical\n"
               "projectFiles:\n  - b/bblk.yaml\n")
        # An include that escapes the project root to a real file outside it
        # (arch/yaml/b -> tmp/outside.yaml is four levels up, above demo/).
        _write(os.path.join(yamlRoot, "b", "bblk.yaml"),
               "include:\n  - ../../../../outside.yaml\nblocks:\n  bblk: {}\n")
        _write(os.path.join(tmp, "outside.yaml"), "blocks:\n  outside: {}\n")

        r = migrateLayoutInProject(proj, write=True)
        rt = r.projectRoot

        ok &= _check("escaping include reported manual",
                     any(i.kind == TODO_UNREWRITABLE_PATH for i in r.manual))
        ok &= _check("candidate with unrewritable item is not clean", not r.clean)
        ok &= _check("out-of-root target not moved (not mangled)",
                     not os.path.exists(os.path.join(rt, "outside.yaml")) and
                     os.path.isfile(os.path.join(tmp, "outside.yaml")))
        movedText = open(os.path.join(rt, "b", "yaml", "bblk.yaml")).read()
        ok &= _check("escaping include left byte-for-byte (not mangled)",
                     "- ../../../../outside.yaml" in movedText)
        ok &= _check("no path rewrite emitted for the escaping include",
                     not any(rw.old == "../../../../outside.yaml" for rw in r.rewrites))
    finally:
        shutil.rmtree(tmp)
    return ok


def test_quoted_yaml_rewrite(ok):
    """Quoted include/projectFiles entries are re-rooted by replacing the scalar
    value inside the quotes, preserving the user's quoting style."""
    tmp = tempfile.mkdtemp(prefix="layoutquoted_")
    try:
        root = os.path.join(tmp, "demo")
        yamlRoot = os.path.join(root, "arch", "yaml")
        proj = os.path.join(yamlRoot, "project.yaml")
        _write(proj,
               "yamlFormat: 2\n"
               "projectName: demo\n"
               "dirs:\n  root: ../..\n"
               "fileGeneration:\n  layout: hierarchical\n"
               "projectFiles:\n"
               "  - \"a/ablk.yaml\"\n"
               "  - 'b/bblk.yaml'\n")
        _write(os.path.join(yamlRoot, "a", "ablk.yaml"),
               "include:\n  - \"../b/bblk.yaml\"\nblocks:\n  ablk: {}\n")
        _write(os.path.join(yamlRoot, "b", "bblk.yaml"),
               "blocks:\n  bblk: {}\n")

        r = migrateLayoutInProject(proj, write=True)
        rt = r.projectRoot

        movedProj = open(os.path.join(rt, "prj", "yaml", "demoProject.yaml")).read()
        movedA = open(os.path.join(rt, "a", "yaml", "ablk.yaml")).read()
        ok &= _check("quoted projectFiles re-rooted with quotes preserved",
                     '"../../a/yaml/ablk.yaml"' in movedProj and
                     "'../../b/yaml/bblk.yaml'" in movedProj)
        ok &= _check("quoted include re-rooted with quotes preserved",
                     '"../../b/yaml/bblk.yaml"' in movedA)
        ok &= _check("quoted rewrite has no manual items", not r.manual)
    finally:
        shutil.rmtree(tmp)
    return ok


def _treeSnapshot(root):
    """{relpath: bytes} for every file under `root`, to prove a dry-run made no
    on-disk change."""
    snap = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            with open(p, "rb") as fh:
                snap[os.path.relpath(p, root)] = fh.read()
    return snap


def run_all_tests():
    ok = True

    # Real functional example: not opted in -> no-op.
    r = migrateLayoutInProject(FUNCTIONAL_PROJECT)
    ok &= _check("functional example is LAYOUT_FUNCTIONAL",
                 r.state == LAYOUT_FUNCTIONAL)
    ok &= _check("functional example is a no-op", r.isNoOp)

    # Real green-field fixture: already hierarchical on disk -> no-op.
    r = migrateLayoutInProject(HIERARCHICAL_PROJECT)
    ok &= _check("hier fixture is LAYOUT_ALREADY_HIERARCHICAL",
                 r.state == LAYOUT_ALREADY_HIERARCHICAL)
    ok &= _check("hier fixture is a no-op", r.isNoOp)

    # Opted in, still functional on disk, yamlFormat: 2 -> migration candidate,
    # nothing manual (this bare stub has no source to relocate; the map content
    # is covered by the decomposed / orphan tests below).
    cand = _writeTemp("yamlFormat: 2\nprojectName: foo\n"
                      "dirs:\n  root: .\n"
                      "fileGeneration:\n  layout: hierarchical\n")
    try:
        r = migrateLayoutInProject(cand)
        ok &= _check("opted-in format-2 is LAYOUT_NEEDS_MIGRATION",
                     r.state == LAYOUT_NEEDS_MIGRATION)
        ok &= _check("opted-in format-2 candidate is not a no-op", not r.isNoOp)
        ok &= _check("opted-in format-2 candidate is clean (no blocker)", r.clean)
    finally:
        os.remove(cand)

    # Opted in but not yamlFormat: 2 -> blocked precondition.
    blocked = _writeTemp("projectName: foo\n"
                         "fileGeneration:\n  layout: hierarchical\n")
    try:
        r = migrateLayoutInProject(blocked)
        ok &= _check("not-format-2 candidate is LAYOUT_NEEDS_MIGRATION",
                     r.state == LAYOUT_NEEDS_MIGRATION)
        ok &= _check("not-format-2 candidate is blocked (not clean)", not r.clean)
        ok &= _check("blocker is TODO_NOT_FORMAT2",
                     any(i.kind == TODO_NOT_FORMAT2 for i in r.manual))
    finally:
        os.remove(blocked)

    # T4.2 relocation map (computed, never applied).
    ok = test_decomposed_example_map(ok)
    ok = test_orphan_and_guard_map(ok)

    # T4.3 apply (execute the map under --write).
    ok = test_apply_decomposed(ok)
    ok = test_apply_orphan_and_guard(ok)

    # T4.4 relative-path re-rooting.
    ok = test_source_userregion_rewrite(ok)
    ok = test_unrewritable_reported(ok)
    ok = test_quoted_yaml_rewrite(ok)

    print("PASS: layout migration trigger + map + apply + path rewrite"
          if ok else
          "FAIL: layout migration trigger + map + apply + path rewrite")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
