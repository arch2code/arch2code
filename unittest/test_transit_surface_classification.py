#!/usr/bin/env python3
"""What a connection's interface says about the blocks its ends belong to.

`calcBlockConfigInfo` walks every block's reachable surface to decide two
different things: whether the block TOUCHES parameterizable declarations at all
(transit), and whether it OWNS them, which requires it to be a C++ class
template. Both answers come from the interface the block itself declares for the
port an end terminates, not from the connection's: an end whose declared
interface differs is bridged by a generated thunker and never names the
connection's declaration. An end that declares no port of that name inherits the
connection's interface top-down, and that one IS its own surface.

The cells:

- a literal-ported endpoint on a parameterized channel is accepted, and is not
  flagged parameterizable, so no Config, no variant structs and no trampoline
  registrar are emitted for it;
- a params-less container transiting a parameterizable channel IS flagged
  parameterizable but is not a class template, so no trampoline registrar
  appears in the emitted artifact set;
- a parameterized endpoint's config context is its own file, so a variant
  binding declared there is selected rather than relocating to the assembler;
- a block whose `params:` are backed by ipParameters constants reached through
  `include:` takes the declaring file of those constants as its config context,
  since they are its Config struct's fields;
- an end with no declared port inherits the connection's interface, so a
  parameterizable connection puts it on that block's own surface (a guard on the
  fallback arm, which the old and new rules answer identically);
- a params-less container assembling a parameterizable channel that no end can
  type is rejected at db time, because the channel would spell a `Config` that
  is in scope nowhere.
"""

import os
import sys
import tempfile

from _addrctl_helpers import cleanup, find_block, make_project, run_arch2code

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen


# The endpoint IP: a producer and a consumer in a literal and a parameterized
# spelling, each on an interface this file owns. Kept in its own file so the
# config-context cell can tell the IP's file from the assembler's.
IP_YAML = """ipParameters:
    constants:
        EP_WIDTH: { value: 12, maxValue: 32, desc: "Endpoint pixel width" }
    types:
        epPixelT: { width: EP_WIDTH, maxBitwidth: 32, desc: "Parameterizable endpoint pixel" }

types:
    tagT:      { width: 8,  desc: "Sample tag at the low packed position" }
    litPixelT: { width: 12, desc: "Literal endpoint pixel" }

structures:
    epLitSt:
        tag:  { varType: tagT,       desc: "Sample tag" }
        data: { varType: litPixelT,  desc: "Literal pixel payload" }
    epParSt:
        tag:  { varType: tagT,       desc: "Sample tag" }
        data: { varType: epPixelT,   desc: "Parameterizable pixel payload" }

interfaces:
    srcLitIf:
        desc: "Producer port interface, literal payload"
        interfaceType: push_ack
        structures:
            - { structure: epLitSt, structureType: data_t }
    srcParIf:
        desc: "Producer port interface, parameterizable payload"
        interfaceType: push_ack
        structures:
            - { structure: epParSt, structureType: data_t }
    dstLitIf:
        desc: "Consumer port interface, literal payload"
        interfaceType: push_ack
        structures:
            - { structure: epLitSt, structureType: data_t }
    dstParIf:
        desc: "Consumer port interface, parameterizable payload"
        interfaceType: push_ack
        structures:
            - { structure: epParSt, structureType: data_t }

blocks:
    srcLit:
        desc: "Producer whose own port payload is literal"
        hasMdl: true
        ports:
            out: { interface: srcLitIf, direction: src }
    srcPar:
        desc: "Producer whose own port payload is parameterizable"
        params: [EP_WIDTH]
        hasMdl: true
        ports:
            out: { interface: srcParIf, direction: src }
    dstLit:
        desc: "Consumer whose own port payload is literal"
        hasMdl: true
        ports:
            in: { interface: dstLitIf, direction: dst }
    dstPar:
        desc: "Consumer whose own port payload is parameterizable"
        params: [EP_WIDTH]
        hasMdl: true
        ports:
            in: { interface: dstParIf, direction: dst }

parameters:
    srcPar:
        v0:
            EP_WIDTH: 12
    dstPar:
        v0:
            EP_WIDTH: 12
"""


def assembler_yaml(ip_basename, consumer, container_params=True, channel='own',
                   producer='srcLit'):
    """An assembler wrapping one cell of the endpoint IP.

    `producer` and `consumer` pick the endpoint blocks, so the same assembler
    covers the literal-ported and the parameterized-ported end at either end of
    the channel. `container_params` decides
    whether the container is a class template, i.e. whether anything is left to
    type the channel once every end is adapted. `channel` selects the connection
    interface: the assembler's own parameterized declaration ('own', so both
    ends are adapted) or the consumer IP's own ('ip', so the consumer end binds
    directly and elects the channel's Config).
    """
    ownChannel = channel == 'own'
    params = "        params: [CH_WIDTH]\n" if container_params else ""
    wrap_variant = ", variant: v0" if container_params else ""
    wrap_binding = ("    wrap:\n        v0:\n            CH_WIDTH: 12\n"
                    if container_params else "")
    # The assembler's own channel constant must be consumed by a block param
    # declared in the same file (_validateIpParametersLinkage). The container
    # does that when it is a class template; otherwise an uninstantiated carrier
    # block supplies the link.
    channelDecls = """
ipParameters:
    constants:
        CH_WIDTH: { value: 12, maxValue: 16, desc: "Channel pixel width owned by the assembler" }
    types:
        chPixelT: { width: CH_WIDTH, maxBitwidth: 16, desc: "Parameterizable channel pixel" }

types:
    chTagT: { width: 8, desc: "Channel tag at the low packed position" }

structures:
    chSt:
        tag:  { varType: chTagT,   desc: "Sample tag" }
        data: { varType: chPixelT, desc: "Pixel payload" }

interfaces:
    chIf:
        desc: "Assembler-owned parameterized channel"
        interfaceType: push_ack
        structures:
            - { structure: chSt, structureType: data_t }
""" if ownChannel else ""
    carrier = """    carrier:
        desc: "Uninstantiated carrier so the channel parameter has a same-file block param"
        params: [CH_WIDTH]
        hasMdl: false
""" if ownChannel and not container_params else ""
    carrier_binding = ("    carrier:\n        v0:\n            CH_WIDTH: 12\n"
                       if carrier else "")
    consumer_variant = ", variant: v0" if consumer == 'dstPar' else ""
    producer_variant = (", variant: v0"
                        if producer in ('srcPar', 'tbSrc', 'inferred') else "")
    # A producer declared HERE, in the assembler's file, whose `params:` are
    # backed by the IP's ipParameters constants reached through include: - the
    # testbench stimulus shape. Its port is on the IP's literal interface, so
    # nothing but its own params makes it parameterizable.
    tb_src = """    tbSrc:
        desc: "Producer declared in the assembler's file over the IP's parameters"
        params: [EP_WIDTH]
        hasMdl: true
        ports:
            out: { interface: srcLitIf, direction: src }
""" if producer == 'tbSrc' else ""
    tb_src_binding = ("    tbSrc:\n        v0:\n            EP_WIDTH: 12\n"
                      if producer == 'tbSrc' else "")
    # A producer that declares NO ports at all: top-down inference gives its
    # port the connection's own interface, which is therefore its own surface.
    if producer == 'inferred':
        tb_src = """    inferredSrc:
        desc: "Producer with no ports: declaration, typed top-down by the connection"
        params: [CH_WIDTH]
        hasMdl: true
"""
        tb_src_binding = "    inferredSrc:\n        v0:\n            CH_WIDTH: 12\n"
    channelIf = 'chIf' if ownChannel else 'dstParIf'
    producerBlock = 'inferredSrc' if producer == 'inferred' else producer
    bindings = wrap_binding + carrier_binding + tb_src_binding
    parameters = f"\nparameters:\n{bindings}" if bindings else ""
    return f"""include:
    - {ip_basename}
{channelDecls}
blocks:
    top:
        desc: "Top container"
        hasMdl: true
    wrap:
        desc: "Assembling container of the one cell"
{params}        hasMdl: true
{tb_src}{carrier}
instances:
    uTop:  {{ container: top,  instanceType: top }}
    uWrap: {{ container: top,  instanceType: wrap{wrap_variant} }}
    uSrc:  {{ container: wrap, instanceType: {producerBlock}{producer_variant} }}
    uDst:  {{ container: wrap, instanceType: {consumer}{consumer_variant} }}

connections:
    - {{ interface: {channelIf}, src: uSrc, srcport: out, dst: uDst, dstport: in }}
{parameters}"""


def build_cell(consumer, container_params=True, channel='own',
               producer='srcLit', expect_success=True):
    """Write the IP file and an assembler that includes it, then build.

    The assembler's `include:` needs the IP file's temp basename, which
    make_project only settles once it has written the file, so the assembler is
    emitted as a placeholder and rewritten with the resolved name.
    """
    project_path, arch_paths = make_project(
        [('assembler', 'PLACEHOLDER'), ('ip', IP_YAML)],
        top_instance='uTop', project_name='transit_test')
    ip_basename = os.path.basename(arch_paths[1])
    with open(arch_paths[0], 'w') as f:
        f.write(assembler_yaml(ip_basename, consumer, container_params, channel,
                               producer))
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    result = run_arch2code(project_path, db_path)
    if expect_success and result.returncode != 0:
        cleanup([project_path, db_path] + arch_paths)
        raise AssertionError(
            f"arch2code.py failed unexpectedly:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    if (not expect_success) and result.returncode == 0:
        cleanup([project_path, db_path] + arch_paths)
        raise AssertionError(
            f"arch2code.py succeeded unexpectedly:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return db_path, project_path, arch_paths, result


def test_literal_endpoint_on_parameterized_channel():
    """An end whose own declared port is literal has no parameterizable own
    surface, whatever the channel it is attached to is declared as."""
    print("literal-ported endpoint on a parameterized channel")
    db_path, project_path, arch_paths, _ = build_cell('dstLit')
    try:
        prj = projectOpen(db_path)
        ok = True
        for name in ('srcLit', 'dstLit'):
            _, row = find_block(prj, name)
            if row['isParameterizable']:
                print(f"FAIL: block '{name}' flagged isParameterizable from a "
                      f"channel its own port does not declare")
                ok = False
            if row['defaultConfig'] or row['configContext']:
                print(f"FAIL: block '{name}' carries a config context "
                      f"('{row['configContext']}') it owns nothing in")
                ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


def test_no_registrar_for_paramsless_transit_container():
    """The container transits a parameterizable channel, so it stays flagged
    parameterizable - but it is not a class template, and the trampoline
    registrar exists only to pick a template instantiation.

    Asserted on the emitted artifact set (the build manifest's generated-source
    enumeration, which is the same file set newModule scaffolds) rather than on
    the cond predicate, because the point of the gate is that the file stops
    being emitted."""
    print("params-less transit container gets no trampoline registrar")
    db_path, project_path, arch_paths, _ = build_cell(
        'dstPar', container_params=False, channel='ip')
    try:
        prj = projectOpen(db_path)
        emitted = {os.path.basename(f)
                   for f in prj.config.getConfig('BUILDMANIFEST')['scGenFiles']}
        ok = True
        for name, expected in (('wrap', False), ('dstPar', True)):
            registrar = f'{name}Registrar.cppm'
            if (registrar in emitted) != expected:
                print(f"FAIL: '{registrar}' emitted={registrar in emitted}, "
                      f"expected {expected}. Emitted set: {sorted(emitted)}")
                ok = False
        _, wrapRow = find_block(prj, 'wrap')
        if not wrapRow['isParameterizable']:
            print("FAIL: the transit container lost its isParameterizable flag; "
                  "this cell no longer covers the shape it was written for")
            ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


def test_endpoint_config_context_stays_in_its_own_file():
    """A parameterized channel must not relocate an endpoint's config context to
    the assembler's file: the endpoint's parameterizable declarations, and the
    variant binding that selects among them, live in the IP's own file."""
    print("parameterized endpoint keeps its own file as its config context")
    db_path, project_path, arch_paths, _ = build_cell('dstPar', producer='srcPar')
    try:
        prj = projectOpen(db_path)
        _, row = find_block(prj, 'dstPar')
        ipContext = os.path.basename(arch_paths[1])
        ok = True
        if os.path.basename(row['configContext']) != ipContext:
            print(f"FAIL: dstPar configContext is '{row['configContext']}', "
                  f"expected the IP file '{ipContext}'")
            ok = False
        # The v0 descriptor the IP's own binding declares must be the block's
        # own, not a foreign one: a relocated context makes the IP's binding
        # foreign to the context owner and no descriptor is selected at all, so
        # the instance falls back to a default Config carrying no EP_WIDTH.
        blockKey, _ = find_block(prj, 'dstPar')
        descriptors = prj.getBlockConfigView(blockKey)['variantConfigs']
        v0 = [d for d in descriptors if d['variant'] == 'v0']
        if len(v0) != 1:
            print(f"FAIL: dstPar has {len(v0)} v0 Config descriptors, expected 1")
            ok = False
        elif v0[0]['isForeign']:
            print("FAIL: dstPar's v0 descriptor is FOREIGN, so the IP's own "
                  "binding is not the one in force")
            ok = False
        elif 'EP_WIDTH' not in v0[0]['values']:
            print(f"FAIL: dstPar's v0 Config carries {sorted(v0[0]['values'])}, "
                  f"not its own EP_WIDTH")
            ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


def test_included_parameters_keep_their_declaring_file():
    """A block declares `params:` in one file and the ipParameters constants
    backing them live in another, reached by `include:`. The Config struct's
    fields are those constants, so the config context is the file that declares
    them, not the file the `params:` list sits in."""
    print("block params backed by an included IP keep the IP's config context")
    db_path, project_path, arch_paths, _ = build_cell('dstLit', producer='tbSrc')
    try:
        prj = projectOpen(db_path)
        _, row = find_block(prj, 'tbSrc')
        ipContext = os.path.basename(arch_paths[1])
        ok = True
        if os.path.basename(row['configContext']) != ipContext:
            print(f"FAIL: tbSrc configContext is '{row['configContext']}', "
                  f"expected the IP file '{ipContext}' that declares EP_WIDTH")
            ok = False
        blockKey, _ = find_block(prj, 'tbSrc')
        descriptors = prj.getBlockConfigView(blockKey)['variantConfigs']
        v0 = [d for d in descriptors if d['variant'] == 'v0']
        if len(v0) != 1:
            print(f"FAIL: tbSrc has {len(v0)} v0 Config descriptors, expected 1")
            ok = False
        elif 'EP_WIDTH' not in v0[0]['values']:
            print(f"FAIL: tbSrc's v0 Config carries {sorted(v0[0]['values'])}, "
                  f"not the backing EP_WIDTH constant")
            ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


def test_undeclared_port_fallback_still_takes_the_connection_interface():
    """FALLBACK-PATH GUARD, not a regression test for the surface/transit fix.

    An end whose block declares no port of that name has its port typed
    top-down by the connection, so the connection's interface IS that block's
    own surface. The old walk credited the connection's interface to every end
    unconditionally, so it produced the same answer for this shape and this cell
    passes against the un-fixed generator too - by construction, because the
    fallback arm is exactly where the old and new rules agree. It is kept to stop
    the fix from regressing top-down inference, and it is deliberately NOT
    counted as evidence that the fix works."""
    print("end with no declared port still takes the connection's own surface")
    db_path, project_path, arch_paths, _ = build_cell('dstLit', producer='inferred')
    try:
        prj = projectOpen(db_path)
        _, row = find_block(prj, 'inferredSrc')
        assemblerContext = os.path.basename(arch_paths[0])
        ok = True
        if not row['isParameterizable']:
            print("FAIL: inferredSrc is not flagged parameterizable, so the "
                  "top-down inference fallback did not credit it with the "
                  "connection's interface")
            ok = False
        if os.path.basename(row['configContext']) != assemblerContext:
            print(f"FAIL: inferredSrc configContext is '{row['configContext']}', "
                  f"expected the assembler file '{assemblerContext}' that "
                  f"declares the channel")
            ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


REJECTION_SUBSTRINGS = [
    "Block 'wrap' assembles channel",
    "parameterizable interface 'chIf'",
    "uSrc.out",
    "uDst.in",
    "nothing supplies the Config",
    "declares no params:",
]


def test_untypeable_channel_is_rejected():
    """Every end adapted and no container template parameter leaves the channel
    payload with no Config at all; the emitted C++ names an undeclared one."""
    print("parameterizable channel with no Config source is rejected")
    db_path, project_path, arch_paths, result = build_cell(
        'dstLit', container_params=False, expect_success=False)
    try:
        combined = result.stdout + result.stderr
        ok = True
        for needle in REJECTION_SUBSTRINGS:
            if needle not in combined:
                print(f"FAIL: diagnostic missing substring '{needle}'.\n"
                      f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
                ok = False
        if ok:
            print("PASS")
        return ok
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    ok = test_literal_endpoint_on_parameterized_channel()
    ok = test_no_registrar_for_paramsless_transit_container() and ok
    ok = test_endpoint_config_context_stays_in_its_own_file() and ok
    ok = test_included_parameters_keep_their_declaring_file() and ok
    ok = test_undeclared_port_fallback_still_takes_the_connection_interface() and ok
    ok = test_untypeable_channel_is_rejected() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
