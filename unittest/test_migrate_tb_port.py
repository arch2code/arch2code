#!/usr/bin/env python3
"""Unit tests for the testbench-family migration port (S4).

Two phases are covered, both driven for real over files staged on disk:

  pysrc.migrateBlockModulePort.portTbExternals  merges the legacy
      `<block>External.h`/`.cpp` pair into the scaffolded `<block>External.cppm`,
      carrying the legacy GENERATED_CODE_PARAM across.
  pysrc.migrateTbConfig.restructureTbConfigs    splits the legacy single
      `--template=tbConfig` region into prerequisites / class / registration.

The `.cppm` transplant TARGET and the `Config.cpp` marker/slot skeleton are both
obtained by CALLING the fresh scaffold templates (templates/fileGen/fileGen.py)
rather than by copying their text here, so a scaffold change cannot silently drift
away from what the port expects to find.

What is asserted, and why each matters:
  (a) PLACEMENT, not merely presence. Every ported slot must land in its own
      marker-delimited gap, and a relocated legacy `#include` must land in the
      GLOBAL MODULE FRAGMENT slot (above `export module`). Putting it in the
      preamble slot instead re-attaches its declarations to this module and breaks
      at LINK time against the plain `.cpp` that defines them - it compiles, so
      only a placement assertion catches it.
  (b) The PARAM carry-across. `--block=<blk>_tb --excludeInst=<dut>` is a
      documented user retarget that a fresh scaffold cannot know; losing it makes
      gen emit an External for the wrong block.
  (c) The no-silent-loss guard fires LOUDLY. A slot boundary the extraction cannot
      see must leave the legacy pair on disk and the target untouched, never a
      quietly shorter file (a prior wrapper migration silently dropped a
      setTimedLocal override that way).
  (d) Both phases are idempotent, and every refusal is non-destructive.

To exercise the DB-backed drivers without standing up a full projectCreate
database, each test stages a small synthetic project on disk and drives the phase
against a lightweight fake `prj` exposing exactly the attributes they read. The
files on disk are real; only the DB access surface is faked.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysrc.migrateBlockModulePort import (
    portTbExternals,
    portTbTops,
    _extractSlots,
    _buildPorted,
    _verifyNoLoss,
    BLOCK_SHAPE,
    TB_EXTERNAL_PORTED,
    TODO_PORT_SLOT0,
    TODO_PORT_UNPLACED,
    TODO_PORT_NO_CPPM,
    TODO_PORT_PARAM_SPLIT,
    TODO_PORT_NO_PARAM_LINE,
    TODO_PORT_TARGET_DAMAGED,
    TODO_PORT_STALE_VARIANT,
    TODO_PORT_TAIL_UNPLACED,
    TB_TOP_PORTED,
)
from pysrc.migrateTbConfig import (
    restructureTbConfigs,
    _isPrerequisite,
    PREREQ_INCLUDES,
    PREREQ_IMPORTS,
    TB_CONFIG_RESTRUCTURE,
    TODO_TBCONFIG_NO_REGISTRATION,
    TODO_TBCONFIG_DIRECTIVE,
)
from pysrc.migrateCommon import (_includeTarget, _importTarget, paramTail,
                                 paramVariant)
from templates.fileGen.fileGen import (tbExternal_cppm, tbConfig,
                                       blockModule_cppm, testBench_cppm)
from templates.systemc.testbench import tb_config_prerequisites

PASS = 0
FAIL = 0


def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS: {msg}")
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")


# ---------------------------------------------------------------------------
# Fake projectOpen handle
# ---------------------------------------------------------------------------

BLOCK = "myblk"
CONTEXT = "top.yaml"
PARAM_TAIL = f"--block={BLOCK}_tb --excludeInst=u_{BLOCK}"

# The current (post-S1) fileMap entries the phases resolve their targets through.
FILEMAP = {
    "tbExternal": {"name": "External", "ext": {"cppm": "cppm"},
                   "cond": {"hasTb": True}, "blockDir": True, "mode": "block",
                   "basePath": "tb"},
    "tbConfig": {"name": "Config", "ext": {"src": "cpp"},
                 "cond": {"hasTb": True}, "blockDir": True, "mode": "block",
                 "basePath": "tb"},
    "testBench": {"name": "Testbench", "ext": {"cppm": "cppm"},
                  "cond": {"hasTb": True}, "blockDir": True, "mode": "block",
                  "basePath": "tb"},
}

# The block's DECLARED variants, in declaration order, as projectOpen returns them.
# `make newmodule` seeds a tb top with the FIRST; the tb-top port carries whatever
# the legacy file named, and refuses a name that is not in this list.
DECLARED_VARIANTS = ["small", "large"]


class _FakeConfig:
    def __init__(self, values):
        self.values = values

    def getConfig(self, key):
        return self.values[key]


class _FakePrj:
    """The subset of a projectOpen handle the phases read.

    `hasOwnParams` is a DB fact the carried-variant check keys on: the generator only
    validates a `--variant=` against a block that owns `params:`, so a fixture has to
    be able to say either.
    """

    def __init__(self, root, hasOwnParams=True):
        self.hasOwnParams = hasOwnParams
        self.filemap = FILEMAP
        self.projectLayout = {"t": {"mode": "functional", "root": root,
                                    "segments": {"tb": {"path": os.path.join(root, "tb")}}}}
        self.contextOwningProject = {CONTEXT: "t"}
        self.config = _FakeConfig({"PROJECTNAME": "t"})
        self.data = {"blocks": {BLOCK: {"blockKey": BLOCK, "_context": CONTEXT,
                                        "dir": "", "block": BLOCK, "hasTb": 1}}}

    def getQualBlockVariants(self, qualBlock):
        return DECLARED_VARIANTS

    def getBlockConfigView(self, qualBlock):
        return {"hasOwnParams": self.hasOwnParams}


def _paths(root):
    tb = os.path.join(root, "tb", BLOCK)
    return {"h": os.path.join(tb, f"{BLOCK}External.h"),
            "cpp": os.path.join(tb, f"{BLOCK}External.cpp"),
            "cppm": os.path.join(tb, f"{BLOCK}External.cppm"),
            "config": os.path.join(tb, f"{BLOCK}Config.cpp"),
            "tbTopH": os.path.join(tb, f"{BLOCK}Testbench.h"),
            "tbTopCpp": os.path.join(tb, f"{BLOCK}Testbench.cpp"),
            "tbTopCppm": os.path.join(tb, f"{BLOCK}Testbench.cppm")}


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    return path


def _read(path):
    with open(path) as fh:
        return fh.read()


def _scaffoldData():
    return {"block": BLOCK, "variant": "",
            "fileGeneration": {"fileCopyrightStatement": "copyright test"}}


# ---------------------------------------------------------------------------
# Staged legacy testbench External
# ---------------------------------------------------------------------------

# Slot-0 carries the closed boilerplate set every measured External has, plus two
# genuinely external user headers: a plain one and a pimpl boundary whose
# definitions live in a plain .cpp. Both attached to the global module as header
# includes, so both must land in the GMF slot.
LEGACY_H = f"""#ifndef MYBLK_EXTERNAL_H
#define MYBLK_EXTERNAL_H
// copyright test

#include "systemc.h"
#include "logging.h"
#include "probe_plain.h"
#include "probe_pimpl.h"

// GENERATED_CODE_PARAM {PARAM_TAIL}
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import {BLOCK}.base;

class {BLOCK}External: public sc_module, public {BLOCK}Inverted {{

    logBlock log_;

// GENERATED_CODE_END

    void stimulusThread(void);
    probePlain probePlain_;
    sc_event probeEvent;
}};

#endif /* MYBLK_EXTERNAL_H */
"""

LEGACY_CPP = f"""import a2c.endOfTest;
#include "{BLOCK}External.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM {PARAM_TAIL}
// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import a2c.endOfTest;
#include "{BLOCK}External.h"

{BLOCK}External::{BLOCK}External(sc_module_name modulename) :
    {BLOCK}Inverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
   ,probeEvent("probeEvent")
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{{

    SC_THREAD(eotThread);
// GENERATED_CODE_END

    SC_THREAD(stimulusThread);
}}

void {BLOCK}External::stimulusThread(void)
{{
    probePlain_.bump();
}}
"""

# The three ported slot payloads, by the zone each must end up in.
CLASS_BODY_LINE = "    void stimulusThread(void);"
CTOR_INIT_LINE = '   ,probeEvent("probeEvent")'
CTOR_BODY_LINE = "    SC_THREAD(stimulusThread);"
TAIL_LINE = "    probePlain_.bump();"
# Every genuinely external top-of-file include relocates to the GMF user slot,
# whichever legacy file carried it: `probe_*.h` from the `.h`, and `workerThread.h`
# from the `.cpp` — no generated region names a `worker*` symbol, so a stimulus
# thread's prerequisite is user content, not framework baseline.
GMF_LINES = ('#include "probe_plain.h"', '#include "probe_pimpl.h"',
             '#include "workerThread.h"')
# The scaffold's seeded user-slot labels: the top of each user slot, below the
# generated region that owns the zone.
GMF_SLOT_LABEL = "// user #includes here"
PREAMBLE_SLOT_LABEL = "// user imports here"


def _stageExternal(root, hText=LEGACY_H, cppText=LEGACY_CPP):
    p = _paths(root)
    _write(p["h"], hText)
    _write(p["cpp"], cppText)
    _write(p["cppm"], tbExternal_cppm(None, None, _scaffoldData()))
    return p


GEN_END = "// GENERATED_CODE_END"

# The generated regions of a ported External `.cppm`, by the name its zone is
# asserted under.
EXTERNAL_MARKERS = (("--section=tbExternalModuleHeader", "gmf"),
                    ("--template=moduleExport", "export"),
                    ("--template=tbExternal --section=header", "class"),
                    ("--template=tbExternal --section=init", "init"),
                    ("--template=tbExternal --section=body", "body"))


def _regionBounds(lines, markers):
    """Map each named marker to the `<name>Begin`/`<name>End` line indices of its
    generated region: the BEGIN line carrying the marker text and the
    `GENERATED_CODE_END` that closes it.

    Both ends are needed because a user slot starts strictly BELOW its region's
    END. A band opened at the BEGIN index spans the generated region itself, so it
    would accept content the next `make gen` rewrites away."""
    z = dict()
    pending = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s == GEN_END:
            if pending is not None:
                z[pending + "End"] = i
                pending = None
            continue
        for marker, name in markers:
            if marker in s:
                z[name + "Begin"] = i
                pending = name
                break
    return z


def _zones(text):
    """Map each marker boundary of a ported `.cppm` to its 0-based line index, so a
    slot assertion can name the zone it expects rather than a line number."""
    lines = text.splitlines()
    return _regionBounds(lines, EXTERNAL_MARKERS), lines


def _slotLabel(lines, label):
    """Index of the seeded user-slot label line the scaffold writes below a
    generated region — the top of the user slot proper."""
    return next(i for i, line in enumerate(lines) if line.startswith(label))


def _lineIndex(lines, wanted):
    for i, line in enumerate(lines):
        if line.rstrip() == wanted:
            return i
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_external_slots_land_in_their_own_zones():
    print("test_external_slots_land_in_their_own_zones")
    with tempfile.TemporaryDirectory() as root:
        p = _stageExternal(root)
        report = portTbExternals(_FakePrj(root), write=True)

        kinds = [i.kind for i in report.applied]
        check(kinds == [TB_EXTERNAL_PORTED] and report.clean,
              "the External pair is ported with no manual TODO")
        check(not os.path.exists(p["h"]) and not os.path.exists(p["cpp"]),
              "the legacy pair is deleted once the transplant is written")

        text = _read(p["cppm"])
        z, lines = _zones(text)

        # (a) the relocated legacy includes are in the GMF USER slot: below the GMF
        # region's END and below its seeded label, and BEFORE `export module`. This
        # is the placement that preserves the global-module attachment they had as
        # header includes. The lower bound is the region END, not its BEGIN: the
        # region belongs to `tbExternalModuleHeader`, so a relocated include landing
        # inside it is silently erased by the next `make gen`.
        gmfSlot = _slotLabel(lines, GMF_SLOT_LABEL)
        check(z["gmfEnd"] < gmfSlot < z["exportBegin"],
              "the GMF user slot opens below the generated region, above export module")
        for gmf in GMF_LINES:
            idx = _lineIndex(lines, gmf)
            check(idx is not None and gmfSlot < idx < z["exportBegin"],
                  f"{gmf} lands in the global-module-fragment user slot")

        # the three ported user slots, each in its own marker-delimited gap, and each
        # below the END of the region that opens it rather than merely below its BEGIN
        classBody = _lineIndex(lines, CLASS_BODY_LINE)
        check(classBody is not None and classBody > z["classEnd"],
              "class-body content lands inside the class, after its region")
        classClose = next(i for i in range(classBody, len(lines))
                          if lines[i].rstrip() == "};")
        check(classClose < z["initBegin"],
              "class-body content stays above the class closing brace")

        ctorInit = _lineIndex(lines, CTOR_INIT_LINE)
        check(ctorInit is not None and z["initEnd"] < ctorInit < z["bodyBegin"],
              "constructor init-list content lands between the init and body regions")

        ctorBody = _lineIndex(lines, CTOR_BODY_LINE)
        tail = _lineIndex(lines, TAIL_LINE)
        check(ctorBody is not None and ctorBody > z["bodyEnd"],
              "constructor-body content lands after the body region")
        check(tail is not None and tail > ctorBody,
              "the out-of-line tail follows the constructor body")

        # (b) the legacy `--block`/`--excludeInst` retarget survives, with the
        # module-mode parameter appended.
        check(f"GENERATED_CODE_PARAM {PARAM_TAIL} --mode=module" in text,
              "the legacy GENERATED_CODE_PARAM is carried across with --mode=module")

        # no boilerplate is resurrected: the framework prerequisites and the
        # self-include are dropped, not relocated into a user slot.
        for dropped in ('#include "systemc.h"', '#include "logging.h"',
                        f'#include "{BLOCK}External.h"',
                        "import a2c.endOfTest;"):
            check(dropped not in text,
                  f"{dropped} is dropped (a generated region now owns it)")


def test_external_port_is_idempotent():
    print("test_external_port_is_idempotent")
    with tempfile.TemporaryDirectory() as root:
        p = _stageExternal(root)
        portTbExternals(_FakePrj(root), write=True)
        first = _read(p["cppm"])
        report = portTbExternals(_FakePrj(root), write=True)
        check(not report.applied and report.clean and not report.written,
              "a re-run over an already-ported block is a silent no-op")
        check(_read(p["cppm"]) == first, "the ported .cppm is unchanged by the re-run")


def test_stray_slot0_import_is_flagged_not_placed():
    print("test_stray_slot0_import_is_flagged_not_placed")
    with tempfile.TemporaryDirectory() as root:
        hText = LEGACY_H.replace('#include "probe_pimpl.h"\n',
                                 '#include "probe_pimpl.h"\nimport some.other;\n')
        p = _stageExternal(root, hText=hText)
        scaffold = _read(p["cppm"])
        report = portTbExternals(_FakePrj(root), write=True)

        kinds = [i.kind for i in report.manual]
        check(kinds == [TODO_PORT_SLOT0] and not report.applied,
              "a stray top-of-file import is reported, not guessed into a zone")
        check("import some.other;" in report.manual[0].message,
              "the report quotes the exact line it will not place")
        check(os.path.exists(p["h"]) and os.path.exists(p["cpp"]),
              "the legacy pair survives the refusal")
        check(_read(p["cppm"]) == scaffold, "the target .cppm is left untouched")


def test_unseen_slot_boundary_trips_the_no_loss_guard():
    print("test_unseen_slot_boundary_trips_the_no_loss_guard")
    with tempfile.TemporaryDirectory() as root:
        # A hand-edited class close the boundary finder cannot see. Without the
        # guard the class-body slot would silently vanish.
        hText = LEGACY_H.replace("    sc_event probeEvent;\n};\n",
                                 "    sc_event probeEvent;\n};  // end External\n")
        p = _stageExternal(root, hText=hText)
        scaffold = _read(p["cppm"])
        report = portTbExternals(_FakePrj(root), write=True)

        kinds = [i.kind for i in report.manual]
        check(kinds == [TODO_PORT_UNPLACED] and not report.applied,
              "an unseen slot boundary is reported as unplaced source, not dropped")
        check(CLASS_BODY_LINE.strip() in report.manual[0].message,
              "the report names the first line the port could not place")
        check(os.path.exists(p["h"]) and os.path.exists(p["cpp"]),
              "the legacy pair survives the guard's refusal")
        check(_read(p["cppm"]) == scaffold, "the target .cppm is left untouched")


def test_param_disagreement_and_missing_target_are_reported():
    print("test_param_disagreement_and_missing_target_are_reported")
    with tempfile.TemporaryDirectory() as root:
        cppText = LEGACY_CPP.replace(f"GENERATED_CODE_PARAM {PARAM_TAIL}",
                                     f"GENERATED_CODE_PARAM --block={BLOCK}", 1)
        _stageExternal(root, cppText=cppText)
        report = portTbExternals(_FakePrj(root), write=True)
        check([i.kind for i in report.manual] == [TODO_PORT_PARAM_SPLIT],
              "legacy .h/.cpp PARAM lines that disagree are reconciled by hand")

    with tempfile.TemporaryDirectory() as root:
        cppText = LEGACY_CPP.replace(f"// GENERATED_CODE_PARAM {PARAM_TAIL}\n", "", 1)
        _stageExternal(root, cppText=cppText)
        report = portTbExternals(_FakePrj(root), write=True)
        check([i.kind for i in report.manual] == [TODO_PORT_NO_PARAM_LINE],
              "a legacy file with no PARAM line at all is diagnosed as such, not as "
              "a disagreement")

    with tempfile.TemporaryDirectory() as root:
        p = _stageExternal(root)
        os.remove(p["cppm"])
        report = portTbExternals(_FakePrj(root), write=True)
        check([i.kind for i in report.manual] == [TODO_PORT_NO_CPPM],
              "a missing scaffolded .cppm target is reported, pair left alone")
        check(os.path.exists(p["h"]) and os.path.exists(p["cpp"]),
              "the legacy pair survives a missing target")

    with tempfile.TemporaryDirectory() as root:
        # A target that still carries a marker (so it passes the generated guard) but
        # has lost a region the transplant anchors on. Without the up-front check this
        # faults inside _buildPorted mid-loop, after earlier blocks were written.
        p = _stageExternal(root)
        damaged = _read(p["cppm"]).replace(
            "// GENERATED_CODE_BEGIN --template=tbExternal --section=init\n"
            "// GENERATED_CODE_END\n", "")
        _write(p["cppm"], damaged)
        report = portTbExternals(_FakePrj(root), write=True)
        check([i.kind for i in report.manual] == [TODO_PORT_TARGET_DAMAGED],
              "a target missing a transplant region is reported, not a traceback")
        check(os.path.exists(p["h"]) and os.path.exists(p["cpp"]),
              "the legacy pair survives a damaged target")


# ---------------------------------------------------------------------------
# tbConfig
# ---------------------------------------------------------------------------

LEGACY_CONFIG = f"""// copyright test

#include "systemc.h"
#include <string>

#include "instanceFactory.h"
#include "testBenchConfigFactory.h"
import a2c.endOfTest;
#include "testController.h"

// GENERATED_CODE_PARAM --block={BLOCK}
// GENERATED_CODE_BEGIN --template=tbConfig

class {BLOCK}Config : public testBenchConfigBase
{{
public:
    struct registerTestBenchConfig
    {{
    }};
    static registerTestBenchConfig registerTestBenchConfig_;
// GENERATED_CODE_END

    bool createTestBench(void) override
    {{
        return true;
    }}

}};
{BLOCK}Config::registerTestBenchConfig {BLOCK}Config::registerTestBenchConfig_;
"""


def _markerSkeleton(text):
    """The ordered marker and seeded-slot lines of a tbConfig file, i.e. its shape
    with all user and generated content removed."""
    return [ln.strip() for ln in text.splitlines()
            if "GENERATED_CODE" in ln or ln.startswith("// user ")
            or ln.startswith("// A plain translation unit")]


def test_tbconfig_three_edits_and_scaffold_shape():
    print("test_tbconfig_three_edits_and_scaffold_shape")
    with tempfile.TemporaryDirectory() as root:
        p = _paths(root)
        _write(p["config"], LEGACY_CONFIG)
        report = restructureTbConfigs(_FakePrj(root), write=True)
        check([i.kind for i in report.applied] == [TB_CONFIG_RESTRUCTURE]
              and report.clean,
              "the Config.cpp is restructured with no manual TODO")

        text = _read(p["config"])
        # edit 2: the bare region is renamed, or gen aborts with Unknown section ''
        check("--template=tbConfig --section=class" in text
              and "--template=tbConfig\n" not in text,
              "the bare tbConfig region is renamed to --section=class")
        # edit 1: the prerequisites region exists and the framework lines it emits
        # are gone, while genuine user content is kept
        check("--template=tbConfig --section=prerequisites" in text,
              "the prerequisites region is inserted")
        for dropped in ("#include <string>",
                        '#include "instanceFactory.h"',
                        '#include "testBenchConfigFactory.h"',
                        "import a2c.endOfTest;"):
            check(dropped not in text, f"{dropped} is dropped from the preamble")
        check('#include "testController.h"' in text,
              "a genuine user include is kept")
        # systemc.h is NOT a prerequisite the region emits, so a legacy copy is user
        # content: relocated below the seeded slot, not deleted.
        check('#include "systemc.h"' in text,
              "a legacy systemc.h is relocated, not dropped")
        # edit 3: the stranded out-of-class definition is replaced by the region
        check("--template=tbConfig --section=registration" in text,
              "the registration region is inserted")
        check("::registerTestBenchConfig_" not in text.split("--section=class")[-1]
              .split(GEN_END)[-1],
              "the stranded out-of-class registration definition is deleted")

        # the resulting marker/slot skeleton is the fresh scaffold's
        fresh = tbConfig(None, None, _scaffoldData())
        check(_markerSkeleton(text) == _markerSkeleton(fresh),
              "the restructured file's marker/slot skeleton matches a fresh scaffold")

        # user content order is preserved and the slot label precedes it
        lines = text.splitlines()
        slot = next(i for i, ln in enumerate(lines)
                    if ln.startswith("// user #includes and imports here"))
        userInc = next(i for i, ln in enumerate(lines)
                       if ln.strip() == '#include "testController.h"')
        check(slot < userInc, "the kept user include sits below the seeded slot label")

        report = restructureTbConfigs(_FakePrj(root), write=True)
        check(not report.applied and report.clean and not report.written,
              "a re-run over a three-section Config.cpp is a silent no-op")


def test_tbconfig_drop_set_matches_the_template():
    """The migrator's drop set and the `prerequisites` region's emission are the same
    list in two places. Gaining an entry in the template without gaining one here
    leaves a duplicate include behind; losing one drops a user line. Pinned by
    deriving the template's set from the template itself.

    The region also emits one PROJECT-DEPENDENT line per config context
    (`<context>VariantConfig.h`), which is deliberately NOT in the drop set: the
    header is include-guarded, so a legacy hand-added copy surviving in the user slot
    is a no-op, whereas dropping a user line by a name the migrator would have to
    derive per block is not. Both halves are pinned below."""
    print("test_tbconfig_drop_set_matches_the_template")
    noConfig = {"configIncludeContext": {}, "includeFiles": {}}
    emitted = tb_config_prerequisites(None, None, noConfig).splitlines()
    includes = tuple(h for h in (_includeTarget(ln.strip()) for ln in emitted)
                     if h is not None)
    imports = tuple(m for m in (_importTarget(ln.strip()) for ln in emitted)
                    if m is not None)
    check(includes == PREREQ_INCLUDES,
          "PREREQ_INCLUDES equals what tb_config_prerequisites emits")
    check(imports == PREREQ_IMPORTS,
          "PREREQ_IMPORTS equals what tb_config_prerequisites emits")
    check(len(emitted) == len(includes) + len(imports),
          "with no config context the region emits nothing but those includes and imports")

    withConfig = {
        "configIncludeContext": {"top.yaml": 0},
        "includeFiles": {"config_hdr": {"top.yaml": {"baseName": "topVariantConfig.h"}}},
    }
    emittedCfg = '#include "topVariantConfig.h"'
    check(emittedCfg in tb_config_prerequisites(None, None, withConfig).splitlines(),
          "a config context adds its VariantConfig header to the region")
    # Asserted through the migrator's PREDICATE, not the tuple: widening
    # _isPrerequisite to a pattern or suffix match would start dropping this user
    # line while a membership test on the tuple still passed.
    check(not _isPrerequisite(emittedCfg),
          "the migrator does not treat the VariantConfig header as a droppable prerequisite")


def test_tbconfig_preamble_directive_is_refused():
    """A preprocessor directive other than `#include` would change meaning when the
    relocation moves it below the prerequisites region, without changing text — the
    one loss the line-comparison guard cannot see. Refused instead."""
    print("test_tbconfig_preamble_directive_is_refused")
    with tempfile.TemporaryDirectory() as root:
        p = _paths(root)
        legacy = LEGACY_CONFIG.replace('#include "testController.h"\n',
                                       "#define SC_INCLUDE_DYNAMIC_PROCESSES\n"
                                       '#include "testController.h"\n')
        _write(p["config"], legacy)
        report = restructureTbConfigs(_FakePrj(root), write=True)
        check([i.kind for i in report.manual] == [TODO_TBCONFIG_DIRECTIVE]
              and not report.applied,
              "a preamble preprocessor directive is reported, not silently moved")
        check(_read(p["config"]) == legacy, "the file is left untouched")


def test_tbconfig_missing_registration_anchor_is_reported():
    print("test_tbconfig_missing_registration_anchor_is_reported")
    with tempfile.TemporaryDirectory() as root:
        p = _paths(root)
        legacy = LEGACY_CONFIG.replace(
            f"{BLOCK}Config::registerTestBenchConfig {BLOCK}Config::registerTestBenchConfig_;\n",
            "")
        _write(p["config"], legacy)
        report = restructureTbConfigs(_FakePrj(root), write=True)
        check([i.kind for i in report.manual] == [TODO_TBCONFIG_NO_REGISTRATION]
              and not report.applied,
              "a Config.cpp with no registration anchor is reported, not rewritten")
        check(_read(p["config"]) == legacy, "the file is left untouched")


# ---------------------------------------------------------------------------
# The other shape over the same mechanism
# ---------------------------------------------------------------------------

BLOCK_LEGACY_H = f"""#ifndef MYBLK_H
#define MYBLK_H
// copyright test

#include "systemc.h"
#include "probe_plain.h"
#include "sibling.h"

// GENERATED_CODE_PARAM --block={BLOCK}
// GENERATED_CODE_BEGIN --template=classDecl

class {BLOCK}: public {BLOCK}Base {{
// GENERATED_CODE_END
    // block implementation members
    void worker(void);
}};

#endif /* MYBLK_H */
"""

BLOCK_LEGACY_CPP = f"""// copyright test
#include "{BLOCK}.h"

// GENERATED_CODE_PARAM --block={BLOCK}
// GENERATED_CODE_BEGIN --template=constructor --section=init
{BLOCK}::{BLOCK}(sc_module_name blockName) :
    {BLOCK}Base("x")
// GENERATED_CODE_END
   ,userMember_(0)
// GENERATED_CODE_BEGIN --template=constructor --section=body
{{
// GENERATED_CODE_END
    SC_THREAD(worker);
}}

void {BLOCK}::worker(void) {{}}
"""


def test_block_shape_shares_the_same_transplant():
    """The block implementation family uses the same parameterized extraction and
    transplant as the testbench External, so its four slots, its sibling-header ->
    import conversion and its GMF relocation are asserted here too - the shape
    parameterization must not have changed the block path."""
    print("test_block_shape_shares_the_same_transplant")
    dropIncludes = BLOCK_SHAPE.dropIncludes + (f"{BLOCK}.h",)
    slots = _extractSlots(BLOCK_LEGACY_H, BLOCK_LEGACY_CPP, BLOCK_SHAPE,
                          dropIncludes, {"sibling.h": "sib.block"}, set())
    check(not _verifyNoLoss(slots, BLOCK_SHAPE, dropIncludes),
          "block extraction accounts for every code-bearing legacy line")
    check(slots.classBody == ["    void worker(void);"],
          "the scaffold class-body label is dropped and the member kept")
    check(slots.ctorInit == ["   ,userMember_(0)"], "the ctor init-list slot is captured")
    check(slots.ctorBody == ["    SC_THREAD(worker);"], "the ctor body slot is captured")
    check(slots.outOfLine == [f"void {BLOCK}::worker(void) {{}}"],
          "the out-of-line tail is captured")
    check(slots.userIncludes == ['#include "probe_plain.h"'],
          "a genuinely external header is relocated, systemc.h and the self-include are not")
    check(slots.siblingImports == ["import sib.block;"],
          "a sibling-block header include becomes an import")

    ported = _buildPorted(blockModule_cppm(None, None, _scaffoldData()), slots,
                          BLOCK_SHAPE)
    lines = ported.splitlines()
    z = _regionBounds(lines, (("--section=blockModuleHeader", "gmf"),
                              ("--template=moduleExport", "export"),
                              ("--template=classDecl", "class")))
    # Each band opens at its region's END, so neither placement can be satisfied by
    # content sitting inside the generated region above the slot.
    gmfSlot = _slotLabel(lines, GMF_SLOT_LABEL)
    preambleSlot = _slotLabel(lines, PREAMBLE_SLOT_LABEL)
    check(z["gmfEnd"] < gmfSlot and z["exportEnd"] < preambleSlot,
          "both user slots open below the generated region above them")
    gmf = _lineIndex(lines, '#include "probe_plain.h"')
    imp = _lineIndex(lines, "import sib.block;")
    check(gmf is not None and gmfSlot < gmf < z["exportBegin"],
          "the relocated block include lands in the global-module-fragment user slot")
    check(imp is not None and preambleSlot < imp < z["classBegin"],
          "the sibling import lands in the preamble user slot")


# ---------------------------------------------------------------------------
# Testbench top: DUT variant carry
# ---------------------------------------------------------------------------

# The legacy tb top is wholly generated apart from its PARAM line, so a staged pair
# needs only that line plus a marker; every measured instance's user slots are empty
# and the `.cppm` form has no include guard to carry.
def _stageTbTop(root, legacyTail, seededVariant):
    """Stage the legacy `<blk>Testbench.{h,cpp}` pair carrying `legacyTail` on its
    PARAM line (None for no PARAM line at all), plus the freshly scaffolded
    `<blk>Testbench.cppm` target seeded with `seededVariant` — obtained by CALLING
    the scaffold template, so the target is the shape newmodule really writes."""
    p = _paths(root)
    for key in ("tbTopH", "tbTopCpp"):
        param = f"// GENERATED_CODE_PARAM {legacyTail}\n" if legacyTail else ""
        _write(p[key], f"// copyright test\n{param}"
                       f"// GENERATED_CODE_BEGIN --template=testbench --section=header\n"
                       f"// GENERATED_CODE_END\n")
    data = dict(_scaffoldData())
    data["variant"] = seededVariant
    _write(p["tbTopCppm"], testBench_cppm(None, None, data))
    return p


def _stageExternalWithTail(root, tail):
    """Stage the legacy External pair with `tail` on both PARAM lines instead of the
    default `_tb` retarget."""
    return _stageExternal(root, LEGACY_H.replace(PARAM_TAIL, tail),
                          LEGACY_CPP.replace(PARAM_TAIL, tail))


def test_external_carries_a_declared_variant():
    """A valid non-default variant still ports.

    The External's tail is carried VERBATIM, which is the point of the phase; the
    variant check must not get in the way of a selection the block really declares.
    """
    print("test_external_carries_a_declared_variant")
    with tempfile.TemporaryDirectory() as root:
        p = _stageExternalWithTail(root, f"--block={BLOCK} --variant=large")
        report = portTbExternals(_FakePrj(root), write=True)

        check([i.kind for i in report.applied] == [TB_EXTERNAL_PORTED]
              and not report.manual,
              "a declared non-default variant ports cleanly")
        check(paramVariant(_read(p["cppm"])) == "large",
              "the declared variant is carried onto the .cppm")
        check(not os.path.exists(p["h"]) and not os.path.exists(p["cpp"]),
              "the legacy pair is deleted")


def test_external_retired_variant_is_refused():
    """A variant the block no longer declares is never stamped.

    Carrying the tail verbatim would put a retired variant on the target, which makes
    `gen` resolve the wrong config or fail - the same damage class the tb-top guard
    prevents, so the same report kind covers it.
    """
    print("test_external_retired_variant_is_refused")
    with tempfile.TemporaryDirectory() as root:
        p = _stageExternalWithTail(root, f"--block={BLOCK} --variant=retired")
        before = _read(p["cppm"])
        report = portTbExternals(_FakePrj(root), write=True)

        check([i.kind for i in report.manual] == [TODO_PORT_STALE_VARIANT]
              and not report.applied,
              "a retired variant is reported, nothing applied")
        check(os.path.exists(p["h"]) and os.path.exists(p["cpp"]),
              "both legacy files are left on disk")
        check(_read(p["cppm"]) == before, "the target .cppm is byte-identical")
        message = report.manual[0].message if report.manual else ""
        check("'retired'" in message and "small" in message and "large" in message,
              "the TODO names the retired selection and the declared variants")


def test_external_variant_check_skips_what_the_generator_does_not_resolve():
    """The check mirrors the generator, so it must skip where the generator skips.

    Two shapes must still port: the documented `_tb` retarget (the tail's `--block=`
    names a different block, whose variants are the ones actually resolved against),
    and a DUT that owns no `params:` (resolve_dut_variant_selection early-returns and
    passes the variant through to the instance factory unchecked). Refusing either
    would refuse a migration `make gen` accepts.
    """
    print("test_external_variant_check_skips_what_the_generator_does_not_resolve")
    with tempfile.TemporaryDirectory() as root:
        # retargeted --block plus a variant that is NOT declared by the ported block
        p = _stageExternalWithTail(
            root, f"--block={BLOCK}_tb --excludeInst=u_{BLOCK} --variant=retired")
        report = portTbExternals(_FakePrj(root), write=True)
        check([i.kind for i in report.applied] == [TB_EXTERNAL_PORTED]
              and not report.manual,
              "a retargeted --block is not validated against this block's variants")
        check(not os.path.exists(p["h"]), "the retargeted pair still ports")

    with tempfile.TemporaryDirectory() as root:
        p = _stageExternalWithTail(root, f"--block={BLOCK} --variant=retired")
        report = portTbExternals(_FakePrj(root, hasOwnParams=False), write=True)
        check([i.kind for i in report.applied] == [TB_EXTERNAL_PORTED]
              and not report.manual,
              "a block owning no params: is not variant-validated")
        check(not os.path.exists(p["h"]), "that pair still ports")

    with tempfile.TemporaryDirectory() as root:
        # the default in-tree shape: retargeted --block, no --variant at all
        p = _stageExternal(root)
        report = portTbExternals(_FakePrj(root), write=True)
        check([i.kind for i in report.applied] == [TB_EXTERNAL_PORTED]
              and not report.manual,
              "the ordinary no-variant retarget is untouched by the check")
        check(not os.path.exists(p["h"]), "that pair still ports")


def test_tb_top_carries_the_user_variant_and_deletes_the_pair():
    """The user's DUT variant survives the re-scaffold.

    `--variant=` on the legacy tb top's PARAM line is a user edit; newmodule seeds
    the block's FIRST declared variant ('small'). A legacy pair naming 'large' must
    end up with 'large' on the `.cppm` - deleting the pair without carrying it would
    silently point the testbench at another DUT variant.
    """
    print("test_tb_top_carries_the_user_variant_and_deletes_the_pair")
    with tempfile.TemporaryDirectory() as root:
        p = _stageTbTop(root, f"--block={BLOCK} --variant=large", "small")
        report = portTbTops(_FakePrj(root), write=True)

        check(paramVariant(_read(p["tbTopCppm"])) == "large",
              "the legacy --variant is carried onto the scaffolded .cppm")
        check(not os.path.exists(p["tbTopH"]) and not os.path.exists(p["tbTopCpp"]),
              "the legacy pair is deleted once the value is safely on the target")
        check([i.kind for i in report.applied] == [TB_TOP_PORTED] and not report.manual,
              "reported as an applied tb-top port with nothing left by hand")
        # Only the variant argument changes: the scaffold's own --block/--mode tokens
        # are what gen routes on and must survive the carry untouched.
        tail = paramTail(_read(p["tbTopCppm"]))
        check(f"--block={BLOCK}" in tail and "--mode=module" in tail,
              "the scaffold's other PARAM arguments are left exactly as written")


def test_tb_top_undeclared_variant_is_refused():
    """A stale selection is reported, never stamped.

    Migration can rename or remove a variant. Carrying a name the block no longer
    declares would make the next `gen` resolve the wrong config or fail, so the port
    refuses: target untouched, legacy pair left on disk for the operator.
    """
    print("test_tb_top_undeclared_variant_is_refused")
    with tempfile.TemporaryDirectory() as root:
        p = _stageTbTop(root, f"--block={BLOCK} --variant=retired", "small")
        before = _read(p["tbTopCppm"])
        report = portTbTops(_FakePrj(root), write=True)

        check(_read(p["tbTopCppm"]) == before, "the target .cppm is untouched")
        check(os.path.exists(p["tbTopH"]) and os.path.exists(p["tbTopCpp"]),
              "both legacy files are left on disk")
        kinds = [i.kind for i in report.manual]
        check(kinds == [TODO_PORT_STALE_VARIANT] and not report.applied,
              "reported as a stale-variant refusal and nothing applied")
        message = report.manual[0].message if report.manual else ""
        check("'retired'" in message and "small" in message and "large" in message,
              "the TODO names the stale selection and the variants the block declares")


def test_tb_top_without_a_variant_is_just_deleted():
    """The common case stays a plain delete-and-regenerate.

    A tb top naming no variant has nothing to carry, so the scaffold must be left
    exactly as written and the legacy pair simply removed. The following run is a
    no-op.
    """
    print("test_tb_top_without_a_variant_is_just_deleted")
    with tempfile.TemporaryDirectory() as root:
        p = _stageTbTop(root, f"--block={BLOCK}", "")
        before = _read(p["tbTopCppm"])
        report = portTbTops(_FakePrj(root), write=True)

        check(_read(p["tbTopCppm"]) == before,
              "the scaffolded .cppm is left byte-identical")
        check(not os.path.exists(p["tbTopH"]) and not os.path.exists(p["tbTopCpp"]),
              "the legacy pair is deleted")
        check([i.kind for i in report.applied] == [TB_TOP_PORTED] and not report.manual,
              "reported as an applied tb-top port")
        again = portTbTops(_FakePrj(root), write=True)
        check(not again.applied and not again.manual and not again.written,
              "a second run with the pair already gone is a no-op")


def test_tb_top_refuses_a_tail_argument_it_cannot_carry():
    """Only `--variant` is carried, so anything else on the line must be reported.

    The tb top's legacy line is `--block=<dut>` plus an optional `--variant=`; a
    fresh scaffold writes the `--block` back itself. Any other argument - a
    retargeted `--block`, an `--excludeInst`, or the space-spelled `--variant v`
    (which is two tokens, not a selection) - would vanish with the deleted pair, so
    the port refuses instead.
    """
    print("test_tb_top_refuses_a_tail_argument_it_cannot_carry")
    for tail, token in ((f"--block={BLOCK}_tb --excludeInst=u_{BLOCK}",
                         f"--block={BLOCK}_tb"),
                        (f"--block={BLOCK} --variant large", "--variant")):
        with tempfile.TemporaryDirectory() as root:
            p = _stageTbTop(root, tail, "small")
            before = _read(p["tbTopCppm"])
            report = portTbTops(_FakePrj(root), write=True)

            check([i.kind for i in report.manual] == [TODO_PORT_TAIL_UNPLACED]
                  and not report.applied,
                  f"tail {tail!r} is reported as unaccounted, nothing applied")
            check(os.path.exists(p["tbTopH"]) and os.path.exists(p["tbTopCpp"])
                  and _read(p["tbTopCppm"]) == before,
                  f"tail {tail!r} leaves the pair on disk and the target untouched")
            check(token in report.manual[0].message if report.manual else False,
                  f"the TODO names the argument it could not carry ({token})")


def test_tb_top_variant_disagreement_is_reported():
    """The two legacy files must agree on the DUT variant.

    Which one the user meant is a judgment call, so the port reports it exactly as
    the External port does for a whole-tail disagreement.
    """
    print("test_tb_top_variant_disagreement_is_reported")
    with tempfile.TemporaryDirectory() as root:
        p = _stageTbTop(root, f"--block={BLOCK} --variant=small", "small")
        _write(p["tbTopCpp"], _read(p["tbTopCpp"]).replace("--variant=small",
                                                          "--variant=large"))
        before = _read(p["tbTopCppm"])
        report = portTbTops(_FakePrj(root), write=True)

        check([i.kind for i in report.manual] == [TODO_PORT_PARAM_SPLIT]
              and not report.applied,
              "disagreeing legacy variants are reported as a PARAM split")
        check(os.path.exists(p["tbTopH"]) and os.path.exists(p["tbTopCpp"])
              and _read(p["tbTopCppm"]) == before,
              "the pair stays on disk and the target is untouched")


def test_tb_top_with_no_param_line_is_just_deleted():
    """A legacy pair carrying no PARAM line has no selection to lose."""
    print("test_tb_top_with_no_param_line_is_just_deleted")
    with tempfile.TemporaryDirectory() as root:
        p = _stageTbTop(root, None, "small")
        before = _read(p["tbTopCppm"])
        report = portTbTops(_FakePrj(root), write=True)

        check(not os.path.exists(p["tbTopH"]) and not os.path.exists(p["tbTopCpp"]),
              "the legacy pair is deleted")
        check(_read(p["tbTopCppm"]) == before,
              "the scaffold's own seeded variant is left in place")
        check([i.kind for i in report.applied] == [TB_TOP_PORTED] and not report.manual,
              "reported as an applied tb-top port")


def main():
    test_block_shape_shares_the_same_transplant()
    test_external_slots_land_in_their_own_zones()
    test_external_port_is_idempotent()
    test_stray_slot0_import_is_flagged_not_placed()
    test_unseen_slot_boundary_trips_the_no_loss_guard()
    test_param_disagreement_and_missing_target_are_reported()
    test_tbconfig_three_edits_and_scaffold_shape()
    test_tbconfig_drop_set_matches_the_template()
    test_tbconfig_preamble_directive_is_refused()
    test_tbconfig_missing_registration_anchor_is_reported()
    test_tb_top_carries_the_user_variant_and_deletes_the_pair()
    test_tb_top_undeclared_variant_is_refused()
    test_tb_top_without_a_variant_is_just_deleted()
    test_tb_top_refuses_a_tail_argument_it_cannot_carry()
    test_tb_top_variant_disagreement_is_reported()
    test_tb_top_with_no_param_line_is_just_deleted()
    test_external_carries_a_declared_variant()
    test_external_retired_variant_is_refused()
    test_external_variant_check_skips_what_the_generator_does_not_resolve()
    print(f"\nResult: {'PASS' if FAIL == 0 else 'FAIL'} "
          f"({PASS} checks, {FAIL} failures)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
