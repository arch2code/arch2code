#!/usr/bin/env python3
"""Data contracts every shipped interface definition must satisfy.

Every rule here is a property of the interface library, which is
developer-authored, so they are checked here rather than on any execution path:
a malformed definition can only be introduced by editing the library, and this
suite catches it at that moment at zero cost per generator run. No rule needs to
see an interface that uses the definition, so none belongs in projectCreate.

Rule 1 - optional struct parameters are declared last.

An interface's struct-typed parameters are spelled as positional C++ template
arguments. Some hand-written templates splice another argument group into that
list: a BFM inserts its whole Verilated bridge group, a thunker inserts the
other side of a cross-interface bind. The generator produces those signatures by
splitting the declared parameter list at its first optional parameter
(`sc_split_payload_params` in pysrc/intf_gen_utils.py), which is only a split -
and not a reorder of what the author declared - while every optional parameter
is declared after every required one.

Rule 2 - an isEval hdlparam evaluates a required struct parameter.

An `hdlparams:` entry with `isEval` supplies the width of a signal the interface
always declares, and the generator has no way to omit that signal. An optional
parameter may be left unbound by any interface, and an unbound parameter carries
no structure and therefore no width, so evaluating one is unusable no matter
which interface binds what. Requiring the referenced parameter to be a required
one removes the case entirely, statically.

Rule 3 - every modport lists every declared signal.

The generator decides a blasted boundary port's direction by asking whether the
signal is in that modport's `inputs` group and calling it an output otherwise
(`sv_gen_modport_signal_blast` in pysrc/intf_gen_utils.py). A signal no group of
a modport mentions therefore still gets a direction, from that fallback rather
than from the definition, and on the modport where it should have been an input
the emitted wrapper declares an output and drives the assignment backwards.
Generation succeeds, so nothing but this rule reports it.

Rule 4 - an isEval hdlparam value has exactly one '.' separator.

The generator reads an isEval `value:` as `key, data = value.split('.')`, so a
value with any other number of separators aborts generation with a bare
unpacking ValueError naming neither the interface nor its file.

Rule 5 - every parameter declares `datatype: struct`.

`struct` is the only parameter datatype the generator recognises. A parameter
declaring anything else is skipped when the payload bindings are built
(`getIntfParamBindings` in pysrc/processYaml.py), so it silently vanishes from
the interface's positional C++ template arguments and from its SystemVerilog
parameter binding, shifting every later argument one place. Generation succeeds,
so nothing but this rule reports it.

Interface definition files are discovered by walking the interface trees, so a
newly authored interface is validated without anyone adding it to a list.
"""

import os
import shutil
import subprocess
import sys
import tempfile

import yaml as _pyyaml


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
import pysrc.yamlReadCache as yamlReadCache


# The shipped interface libraries. `pro` is a separate repository and is absent
# from a base-only checkout, so it is validated when present.
INTERFACE_ROOTS = (
    os.path.join(base_dir, 'interfaces'),
    os.path.join(os.path.dirname(base_dir), 'pro', 'interfaces'),
)


# A fixture project outside builder/base merges the pro project config, so its
# database carries every interface definition both libraries ship as system
# files. A project inside builder/base is deliberately base-only (see
# processYaml.mergeProjectConfig), which would leave the pro interfaces
# unvalidated.
ARCH_YAML = """blocks:
  top: {desc: "Top block"}

instances:
  uTop: {container: top, instanceType: top}
"""

# A definition that breaks the rule: the required struct parameter p_b is
# declared after the optional p_opt.
BAD_ARCH_YAML = """interface_defs:
  bad_order:
    parameters:
      p_a: {datatype: struct}
      p_opt: {datatype: struct, optional: true}
      p_b: {datatype: struct}
    signals:
      valid: bool
      ready: bool
      sig_a: p_a
    modports:
      src:
        inputs: ['ready']
        outputs: ['valid', 'sig_a']
      dst:
        inputs: ['valid', 'sig_a']
        outputs: ['ready']
    sc_channel:
      type: 'bad_order'
      multicycle_types: []

""" + ARCH_YAML

# A definition that breaks the hdlparam rule: the isEval hdlparam p_ustrb
# evaluates p_u, which is declared optional and so may be left unbound.
BAD_HDLPARAM_ARCH_YAML = """interface_defs:
  bad_hdlparam:
    parameters:
      p_a: {datatype: struct}
      p_u: {datatype: struct, optional: true}
    hdlparams:
      p_ustrb: {isEval: True, datatype: integer, value: 'p_u.to_bytes()'}
    signals:
      valid: bool
      ready: bool
      sig_a: p_a
      sig_ustrb: p_ustrb
    modports:
      src:
        inputs: ['ready']
        outputs: ['valid', 'sig_a', 'sig_ustrb']
      dst:
        inputs: ['valid', 'sig_a', 'sig_ustrb']
        outputs: ['ready']
    sc_channel:
      type: 'bad_hdlparam'
      multicycle_types: []

""" + ARCH_YAML

# A definition that breaks the modport rule: sig_a is declared, but modport dst
# lists it in neither group, so its direction comes from the generator's
# output fallback instead of from the definition.
BAD_MODPORT_ARCH_YAML = """interface_defs:
  bad_modport:
    parameters:
      p_a: {datatype: struct}
    signals:
      valid: bool
      ready: bool
      sig_a: p_a
    modports:
      src:
        inputs: ['ready']
        outputs: ['valid', 'sig_a']
      dst:
        inputs: ['valid']
        outputs: ['ready']
    sc_channel:
      type: 'bad_modport'
      multicycle_types: []

""" + ARCH_YAML

# A definition that breaks the hdlparam value rule: the isEval value names no
# expression to evaluate, so it carries no '.' for the generator to split on.
BAD_HDLPARAM_VALUE_ARCH_YAML = """interface_defs:
  bad_hdlparam_value:
    parameters:
      p_a: {datatype: struct}
    hdlparams:
      p_astrb: {isEval: True, datatype: integer, value: 'p_a'}
    signals:
      valid: bool
      ready: bool
      sig_a: p_a
      sig_astrb: p_astrb
    modports:
      src:
        inputs: ['ready']
        outputs: ['valid', 'sig_a', 'sig_astrb']
      dst:
        inputs: ['valid', 'sig_a', 'sig_astrb']
        outputs: ['ready']
    sc_channel:
      type: 'bad_hdlparam_value'
      multicycle_types: []

""" + ARCH_YAML

# A definition that breaks the datatype rule: p_b is misspelled as a non-struct
# datatype, so it is dropped from the payload bindings entirely.
BAD_DATATYPE_ARCH_YAML = """interface_defs:
  bad_datatype:
    parameters:
      p_a: {datatype: struct}
      p_b: {datatype: strcut}
    signals:
      valid: bool
      ready: bool
      sig_a: p_a
      sig_b: p_b
    modports:
      src:
        inputs: ['ready']
        outputs: ['valid', 'sig_a', 'sig_b']
      dst:
        inputs: ['valid', 'sig_a', 'sig_b']
        outputs: ['ready']
    sc_channel:
      type: 'bad_datatype'
      multicycle_types: []

""" + ARCH_YAML

PROJECT_YAML = """projectName: {name}
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - arch.yaml
"""


FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


def discover_interface_defs():
    """Map interface_type -> defining YAML file, walking the interface trees.

    Discovery rather than a list: an interface authored tomorrow is validated
    without this file being edited.
    """
    found = {}
    for root in INTERFACE_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for name in sorted(files):
                if not name.endswith('.yaml'):
                    continue
                path = os.path.join(dirpath, name)
                doc = _pyyaml.load(yamlReadCache.read(path),
                                   Loader=_pyyaml.CSafeLoader) or {}
                for interfaceType in (doc.get('interface_defs') or {}):
                    found[interfaceType] = path
    return found


def build_database(archText, name):
    """Build a fixture database outside builder/base. Returns (db, tmpdir)."""
    tmpdir = tempfile.mkdtemp(prefix='intf_def_contract_')
    projDir = os.path.join(tmpdir, 'proj')
    os.makedirs(projDir)
    with open(os.path.join(projDir, 'arch.yaml'), 'w') as f:
        f.write(archText)
    projectPath = os.path.join(projDir, f'{name}Project.yaml')
    with open(projectPath, 'w') as f:
        f.write(PROJECT_YAML.format(name=name))
    dbPath = os.path.join(tmpdir, f'{name}.db')
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    result = subprocess.run(
        [sys.executable, os.path.join(base_dir, 'arch2code.py'),
         '--yaml', projectPath, '--db', dbPath],
        capture_output=True, text=True, timeout=300, cwd=base_dir, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"failed to build fixture database:\n"
                           f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    return dbPath, tmpdir


def order_error(sourceFile, interfaceType, requiredParam, optionalParam):
    """The message an author sees. It has to be enough on its own.

    It names the file to edit, the parameter that is misplaced, the parameter it
    must move ahead of, and why the order is load bearing.
    """
    return (
        f"{sourceFile}: interface_defs '{interfaceType}' declares required struct "
        f"parameter '{requiredParam}' after optional struct parameter "
        f"'{optionalParam}'. Every optional struct parameter must be declared "
        f"last, after every required one. An interface's struct parameters are "
        f"emitted as positional C++ template arguments, and the generator builds "
        f"the BFM and thunker signatures by splitting that list at its first "
        f"optional parameter, so a required parameter declared after an optional "
        f"one is emitted in the optional group and lands in the wrong argument "
        f"position. Move '{requiredParam}' ahead of '{optionalParam}' in "
        f"{sourceFile}.")


def hdlparam_error(sourceFile, interfaceType, hdlparam, value, reason):
    """The message an author sees. It has to be enough on its own.

    It names the file to edit, the hdlparam, the parameter it evaluates and why
    that parameter cannot be the one it names.
    """
    return (
        f"{sourceFile}: interface_defs '{interfaceType}' hdlparam '{hdlparam}' "
        f"evaluates '{value}', which {reason}. An isEval hdlparam supplies the "
        f"width of a signal the interface always declares, and there is no way "
        f"to omit that signal, so the parameter it evaluates must always be "
        f"bound: it must be a required struct parameter. Fix the hdlparam, or "
        f"the parameter it names, in {sourceFile}.")


def modport_error(sourceFile, interfaceType, modport, signal):
    """The message an author sees. It has to be enough on its own.

    It names the file to edit, the modport that is short a signal, the signal it
    omits, and what the generator does with a signal no group mentions.
    """
    return (
        f"{sourceFile}: interface_defs '{interfaceType}' declares signal "
        f"'{signal}', which modport '{modport}' lists in neither its inputs nor "
        f"its outputs group. Every modport must list every declared signal in "
        f"one of its groups. The generator gives a blasted boundary port its "
        f"direction by asking whether the signal is in that modport's inputs "
        f"group and calling it an output otherwise, so a signal no group "
        f"mentions is emitted as an output of every modport, and on the modport "
        f"where it should have been an input the wrapper declares an output and "
        f"drives the assignment backwards. Add '{signal}' to modport "
        f"'{modport}' in {sourceFile}.")


def hdlparam_value_error(sourceFile, interfaceType, hdlparam, value, separators):
    """The message an author sees. It has to be enough on its own.

    It names the file to edit, the hdlparam, the value that cannot be read, and
    the shape the generator requires of it.
    """
    return (
        f"{sourceFile}: interface_defs '{interfaceType}' hdlparam '{hdlparam}' "
        f"has isEval value '{value}', which has {separators} '.' separator(s). "
        f"An isEval value must be spelled '<struct parameter>.<expression>', "
        f"with exactly one separator: the generator splits it on '.' into "
        f"exactly those two parts, to pick the parameter to read and the "
        f"expression to evaluate against it, so any other count aborts "
        f"generation with a bare unpacking ValueError that names neither this "
        f"interface nor this file. Fix the value of '{hdlparam}' in "
        f"{sourceFile}.")


def parameter_datatype_error(sourceFile, interfaceType, param, datatype):
    """The message an author sees. It has to be enough on its own.

    It names the file to edit, the parameter, the datatype it declares, and what
    silently happens to a parameter the generator does not recognise.
    """
    return (
        f"{sourceFile}: interface_defs '{interfaceType}' parameter '{param}' "
        f"declares datatype '{datatype}'. Every interface_defs parameter must "
        f"declare 'datatype: struct', the only parameter datatype the generator "
        f"recognises: a parameter declaring anything else is skipped when the "
        f"payload bindings are built, so it silently disappears from the "
        f"interface's positional C++ template arguments and from its "
        f"SystemVerilog parameter binding, and every argument declared after it "
        f"shifts one place. Fix the datatype of '{param}' in {sourceFile}.")


def check_modport_coverage(interfaceDefs, sourceFiles):
    """Modport coverage errors for every interface definition in sourceFiles.

    Modport groups are read as the generator reads them, through
    `modports -> modportGroups -> groups`, so a group named anything other than
    inputs/outputs still covers the signals it lists. A group declared as an
    empty list carries no `groups` rows at all, which the generator spells the
    same way (`... or {}` in `sv_gen_modport_signal_blast`).
    """
    errors = []
    for row in interfaceDefs.values():
        interfaceType = row['interface_type']
        if interfaceType not in sourceFiles:
            continue
        for modport, modportInfo in row['modports'].items():
            covered = set()
            for groupInfo in modportInfo['modportGroups'].values():
                covered.update(groupInfo['groups'] or {})
            for signal in row['signals']:
                if signal in covered:
                    continue
                errors.append(modport_error(sourceFiles[interfaceType],
                                            interfaceType, modport, signal))
    return errors


def check_hdlparam_values(interfaceDefs, sourceFiles):
    """isEval hdlparam value shape errors for every definition in sourceFiles.

    Only an isEval value is split by the generator, so only an isEval value has
    to carry the separator.
    """
    errors = []
    for row in interfaceDefs.values():
        interfaceType = row['interface_type']
        if interfaceType not in sourceFiles:
            continue
        for hdlparam, hdlparamInfo in (row['hdlparams'] or {}).items():
            if not hdlparamInfo['isEval']:
                continue
            value = hdlparamInfo['value']
            separators = value.count('.')
            if separators == 1:
                continue
            errors.append(hdlparam_value_error(sourceFiles[interfaceType],
                                               interfaceType, hdlparam, value,
                                               separators))
    return errors


def check_parameter_datatypes(interfaceDefs, sourceFiles):
    """Parameter datatype errors for every interface definition in sourceFiles."""
    errors = []
    for row in interfaceDefs.values():
        interfaceType = row['interface_type']
        if interfaceType not in sourceFiles:
            continue
        for param, paramInfo in (row['parameters'] or {}).items():
            if paramInfo['datatype'] == 'struct':
                continue
            errors.append(parameter_datatype_error(sourceFiles[interfaceType],
                                                   interfaceType, param,
                                                   paramInfo['datatype']))
    return errors


def check_hdlparam_parameters(interfaceDefs, sourceFiles):
    """isEval hdlparam errors for every interface definition in sourceFiles.

    An hdlparam `value:` is a small expression whose leading token names the
    struct parameter it reads; it is read here exactly as the generator reads it
    in `pysrc/intf_gen_utils.py`.
    """
    errors = []
    for row in interfaceDefs.values():
        interfaceType = row['interface_type']
        if interfaceType not in sourceFiles:
            continue
        parameters = row['parameters'] or {}
        for hdlparam, hdlparamInfo in (row['hdlparams'] or {}).items():
            if not hdlparamInfo['isEval']:
                continue
            value = hdlparamInfo['value']
            referenced = value.split('.')[0]
            paramInfo = parameters.get(referenced)
            if paramInfo is None or paramInfo['datatype'] != 'struct':
                reason = (f"names '{referenced}', which is not a struct "
                          f"parameter of that interface")
            elif paramInfo['optional']:
                reason = (f"names struct parameter '{referenced}', which is "
                          f"declared optional and so may be left unbound")
            else:
                continue
            errors.append(hdlparam_error(sourceFiles[interfaceType],
                                         interfaceType, hdlparam, value, reason))
    return errors


def check_parameter_order(interfaceDefs, sourceFiles):
    """Order errors for every interface definition in sourceFiles.

    interfaceDefs is the schema-loaded `interface_defs` data, so parameters are
    read as rows through the same contract the generator reads (declaration
    order, `datatype`, `optional`) rather than by re-reading the YAML text.
    """
    errors = []
    for row in interfaceDefs.values():
        interfaceType = row['interface_type']
        if interfaceType not in sourceFiles:
            continue
        optionalSeen = None
        for param, paramInfo in (row['parameters'] or {}).items():
            if paramInfo['datatype'] != 'struct':
                continue
            if paramInfo['optional']:
                if optionalSeen is None:
                    optionalSeen = param
            elif optionalSeen is not None:
                errors.append(order_error(sourceFiles[interfaceType],
                                          interfaceType, param, optionalSeen))
    return errors


def test_shipped_interface_defs(interfaceDefs, sourceFiles):
    print("\n[library] every shipped interface definition is discovered and loaded")
    check(bool(sourceFiles), "interface definition files are discovered on disk")

    loaded = {row['interface_type'] for row in interfaceDefs.values()}
    missing = sorted(set(sourceFiles) - loaded)
    check(not missing,
          "every discovered interface definition is loaded and therefore "
          f"validated (not loaded: {missing})")
    print(f"  validated {len(sourceFiles)} interface definition(s): "
          f"{', '.join(sorted(sourceFiles))}")

    print("\n[order] optional struct parameters are declared last")
    errors = check_parameter_order(interfaceDefs, sourceFiles)
    for error in errors:
        print(f"  {error}")
    check(not errors,
          "no shipped interface declares a required struct parameter after an "
          "optional one")

    print("\n[hdlparam] every isEval hdlparam evaluates a required struct parameter")
    errors = check_hdlparam_parameters(interfaceDefs, sourceFiles)
    for error in errors:
        print(f"  {error}")
    check(not errors,
          "no shipped interface has an isEval hdlparam evaluating a parameter "
          "that may be left unbound")

    print("\n[modport] every modport lists every declared signal")
    errors = check_modport_coverage(interfaceDefs, sourceFiles)
    for error in errors:
        print(f"  {error}")
    check(not errors,
          "no shipped interface leaves a declared signal out of one of its "
          "modports")

    print("\n[hdlparam] every isEval hdlparam value has exactly one separator")
    errors = check_hdlparam_values(interfaceDefs, sourceFiles)
    for error in errors:
        print(f"  {error}")
    check(not errors,
          "no shipped interface has an isEval hdlparam value the generator "
          "cannot split")

    print("\n[datatype] every parameter declares datatype struct")
    errors = check_parameter_datatypes(interfaceDefs, sourceFiles)
    for error in errors:
        print(f"  {error}")
    check(not errors,
          "no shipped interface declares a parameter with a datatype the "
          "generator does not recognise")


def test_misdeclared_interface_is_reported():
    """The check fires, and its message stands on its own."""
    print("\n[negative] a required parameter after an optional one is reported")
    try:
        dbPath, tmpdir = build_database(BAD_ARCH_YAML, 'badOrder')
    except RuntimeError as exc:
        check(False, f"mis-declared fixture must build a database: {exc}")
        return
    try:
        proj = projectOpen(dbPath)
        archPath = os.path.join(tmpdir, 'proj', 'arch.yaml')
        errors = check_parameter_order(proj.data['interface_defs'],
                                       {'bad_order': archPath})
        for error in errors:
            print(f"  {error}")
        if len(errors) != 1:
            check(False, f"exactly one order error is reported, got {len(errors)}")
            return
        message = errors[0]
        check(archPath in message, "the message names the file to edit")
        check("'bad_order'" in message, "the message names the interface")
        check("'p_b'" in message, "the message names the misplaced required parameter")
        check("'p_opt'" in message,
              "the message names the optional parameter it must move ahead of")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_hdlparam_on_optional_is_reported():
    """The check fires, and its message stands on its own."""
    print("\n[negative] an isEval hdlparam on an optional parameter is reported")
    try:
        dbPath, tmpdir = build_database(BAD_HDLPARAM_ARCH_YAML, 'badHdlparam')
    except RuntimeError as exc:
        check(False, f"mis-declared fixture must build a database: {exc}")
        return
    try:
        proj = projectOpen(dbPath)
        archPath = os.path.join(tmpdir, 'proj', 'arch.yaml')
        errors = check_hdlparam_parameters(proj.data['interface_defs'],
                                           {'bad_hdlparam': archPath})
        for error in errors:
            print(f"  {error}")
        if len(errors) != 1:
            check(False, f"exactly one hdlparam error is reported, got {len(errors)}")
            return
        message = errors[0]
        check(archPath in message, "the message names the file to edit")
        check("'bad_hdlparam'" in message, "the message names the interface")
        check("'p_ustrb'" in message, "the message names the hdlparam")
        check("'p_u'" in message,
              "the message names the optional parameter it evaluates")
        check("must always be bound" in message,
              "the message states why the parameter must be a required one")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_uncovered_signal_is_reported():
    """The check fires, and its message stands on its own."""
    print("\n[negative] a signal no modport group lists is reported")
    try:
        dbPath, tmpdir = build_database(BAD_MODPORT_ARCH_YAML, 'badModport')
    except RuntimeError as exc:
        check(False, f"mis-declared fixture must build a database: {exc}")
        return
    try:
        proj = projectOpen(dbPath)
        archPath = os.path.join(tmpdir, 'proj', 'arch.yaml')
        errors = check_modport_coverage(proj.data['interface_defs'],
                                        {'bad_modport': archPath})
        for error in errors:
            print(f"  {error}")
        if len(errors) != 1:
            check(False, f"exactly one modport error is reported, got {len(errors)}")
            return
        message = errors[0]
        check(archPath in message, "the message names the file to edit")
        check("'bad_modport'" in message, "the message names the interface")
        check("'dst'" in message, "the message names the modport that is short a signal")
        check("'sig_a'" in message, "the message names the uncovered signal")
        check("assignment backwards" in message,
              "the message states what the generator does with an uncovered signal")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_unsplittable_hdlparam_value_is_reported():
    """The check fires, and its message stands on its own."""
    print("\n[negative] an isEval value the generator cannot split is reported")
    try:
        dbPath, tmpdir = build_database(BAD_HDLPARAM_VALUE_ARCH_YAML,
                                        'badHdlparamValue')
    except RuntimeError as exc:
        check(False, f"mis-declared fixture must build a database: {exc}")
        return
    try:
        proj = projectOpen(dbPath)
        archPath = os.path.join(tmpdir, 'proj', 'arch.yaml')
        errors = check_hdlparam_values(proj.data['interface_defs'],
                                       {'bad_hdlparam_value': archPath})
        for error in errors:
            print(f"  {error}")
        if len(errors) != 1:
            check(False, f"exactly one value error is reported, got {len(errors)}")
            return
        message = errors[0]
        check(archPath in message, "the message names the file to edit")
        check("'bad_hdlparam_value'" in message, "the message names the interface")
        check("'p_astrb'" in message, "the message names the hdlparam")
        check("'p_a'" in message, "the message quotes the value it cannot read")
        check("<struct parameter>.<expression>" in message,
              "the message states the shape an isEval value must have")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_unrecognised_parameter_datatype_is_reported():
    """The check fires, and its message stands on its own."""
    print("\n[negative] a parameter with an unrecognised datatype is reported")
    try:
        dbPath, tmpdir = build_database(BAD_DATATYPE_ARCH_YAML, 'badDatatype')
    except RuntimeError as exc:
        check(False, f"mis-declared fixture must build a database: {exc}")
        return
    try:
        proj = projectOpen(dbPath)
        archPath = os.path.join(tmpdir, 'proj', 'arch.yaml')
        errors = check_parameter_datatypes(proj.data['interface_defs'],
                                           {'bad_datatype': archPath})
        for error in errors:
            print(f"  {error}")
        if len(errors) != 1:
            check(False, f"exactly one datatype error is reported, got {len(errors)}")
            return
        message = errors[0]
        check(archPath in message, "the message names the file to edit")
        check("'bad_datatype'" in message, "the message names the interface")
        check("'p_b'" in message, "the message names the parameter")
        check("'strcut'" in message, "the message quotes the datatype it rejects")
        check("shifts one place" in message,
              "the message states what a dropped parameter does to the arguments")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    print("=" * 72)
    print("TESTING INTERFACE DEFINITION DATA CONTRACTS")
    print("=" * 72)
    sourceFiles = discover_interface_defs()
    try:
        dbPath, tmpdir = build_database(ARCH_YAML, 'intfDefContract')
    except RuntimeError as exc:
        print(f"  FAIL: fixture project must build: {exc}")
        return 1
    try:
        proj = projectOpen(dbPath)
        test_shipped_interface_defs(proj.data['interface_defs'], sourceFiles)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    test_misdeclared_interface_is_reported()
    test_hdlparam_on_optional_is_reported()
    test_uncovered_signal_is_reported()
    test_unsplittable_hdlparam_value_is_reported()
    test_unrecognised_parameter_datatype_is_reported()

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all interface definition data contract checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
