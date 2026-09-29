#!/usr/bin/env python3
"""A channel parameterized by the assembling container's OWN parameter.

Three parties meet at a peer-to-peer connection: the channel (the interface the
container names in `connections:`) and each end's own declared `ports:`
interface. When both ends declare their own interface, both are adapted by a
generated thunker and neither can type the channel - the channel then carries
the container's class template parameter and resolves at the container's variant
binding.

The layout gate has to resolve it there too. Drawing the channel's configuration
from an endpoint evaluates a container-owned parameter at the constant's declared
default instead, which accepts a container variant that disagrees with every
endpoint: `make db`, `make gen` and the C++ compile are all clean and the payload
mis-shifts at run time, on the cells whose two adapters disagree about whether
the copy is whole-value or packed.

Three cells:

- the container's variant agrees with both endpoints -> accepted;
- the container's variant disagrees -> rejected at db time, with the disagreeing
  field, both structure declaration sites, and both sides' resolution provenance
  named;
- the container is instantiated at two variants, one agreeing and one not ->
  rejected, because every variant a container is built at is a configuration its
  channel is genuinely assembled in.
"""

import sys

from _addrctl_helpers import build_database, cleanup


def arch_yaml(container_variants):
    """A container owning the channel parameter, wrapping two endpoints whose
    ports are on their own literal-payload interfaces.

    `container_variants` maps variant label -> bound CH_WIDTH; one wrapper
    instance is emitted per entry. Both endpoint payloads are literal, so
    neither endpoint declares `params:` and neither can type the channel.
    """
    instances = '\n'.join(
        f"    uWrap{index}: {{ container: top, instanceType: wrap, "
        f"variant: {variant} }}"
        for index, variant in enumerate(container_variants))
    wrap_params = '\n'.join(
        f"        {variant}:\n            CH_WIDTH: {width}"
        for variant, width in container_variants.items())
    return f"""ipParameters:
    constants:
        CH_WIDTH: {{ value: 12, maxValue: 32, desc: "Channel pixel width owned by the container" }}
    types:
        chPixelT: {{ width: CH_WIDTH, maxBitwidth: 32, desc: "Parameterizable channel pixel" }}

types:
    tagT:      {{ width: 8, desc: "Sample tag at the low packed position" }}
    litPixelT: {{ width: 12, desc: "Literal endpoint pixel" }}

structures:
    chSt:
        tag:  {{ varType: tagT,     desc: "Sample tag" }}
        data: {{ varType: chPixelT, desc: "Pixel payload" }}
    epSt:
        tag:  {{ varType: tagT,      desc: "Sample tag" }}
        data: {{ varType: litPixelT, desc: "Pixel payload" }}

interfaces:
    chIf:
        desc: "Container-owned parameterized channel"
        interfaceType: push_ack
        structures:
            - {{ structure: chSt, structureType: data_t }}
    srcIf:
        desc: "Producer's own port interface"
        interfaceType: push_ack
        structures:
            - {{ structure: epSt, structureType: data_t }}
    dstIf:
        desc: "Consumer's own port interface"
        interfaceType: push_ack
        structures:
            - {{ structure: epSt, structureType: data_t }}

blocks:
    top:
        desc: "Top container"
        hasMdl: true
    wrap:
        desc: "Assembling container owning the channel parameter"
        params: [CH_WIDTH]
        hasMdl: true
    srcBlk:
        desc: "Producer on its own interface"
        hasMdl: true
        ports:
            out: {{ interface: srcIf, direction: src }}
    dstBlk:
        desc: "Consumer on its own interface"
        hasMdl: true
        ports:
            in: {{ interface: dstIf, direction: dst }}

instances:
    uTop: {{ container: top, instanceType: top }}
{instances}
    uSrc: {{ container: wrap, instanceType: srcBlk }}
    uDst: {{ container: wrap, instanceType: dstBlk }}

connections:
    - {{ interface: chIf, src: uSrc, srcport: out, dst: uDst, dstport: in }}

parameters:
    wrap:
{wrap_params}
"""


# The channel's own declaration and the endpoint's, the field that disagrees and
# both resolved widths, and the container block the channel was resolved at -
# which is the whole point: an endpoint-side resolution never names it.
REQUIRED_SUBSTRINGS = [
    "binds external interface chIf",
    "per-field _bitWidth must agree",
    "field index 1 of structureType 'data_t'",
    "_bitWidth 16",
    "_bitWidth 12",
    "structure 'chSt'",
    "structure 'epSt'",
    "parent side: interface 'chIf'",
    "resolved for block 'wrap'",
    "child side: interface 'srcIf'",
    "resolved for block 'srcBlk'",
]


def _check_rejected(label, variants):
    print(label)
    db_path, project_path, arch_paths, completed = build_database(
        arch_yaml(variants), expect_success=False)
    try:
        combined = completed.stdout + completed.stderr
        for needle in REQUIRED_SUBSTRINGS:
            if needle not in combined:
                print(f"FAIL: diagnostic missing substring '{needle}'.\n"
                      f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
                return False
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def _check_accepted(label):
    # The gate must not reject a design merely for owning the channel
    # parameter; build_database raises on an unexpected rejection.
    print(label)
    db_path, project_path, arch_paths = build_database(arch_yaml({'v0': 12}))
    try:
        print("PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def run_all_tests():
    ok = _check_accepted("agreeing container variant is accepted")
    ok = _check_rejected(
        "disagreeing container variant is rejected", {'v0': 16}) and ok
    ok = _check_rejected(
        "one disagreeing variant of two is rejected", {'v0': 12, 'v1': 16}) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
