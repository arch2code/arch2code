"""
sv_model.py — SystemVerilog code generation models

Mapped from IEEE 1800-2017 Annex A BNF grammar.
Scope: interface declarations, module declarations, and hierarchical
instantiations (modules and interfaces).

Direction of use: populate models from a database / YAML, call .render()
to emit LRM-compliant SystemVerilog source text.
"""

from __future__ import annotations

from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

# ─── Rendering helpers ────────────────────────────────────────────────────────

_INDENT = "    "  # 4-space per LRM examples


def _ind(n: int) -> str:
    return _INDENT * n


def _inline_comment(text: Optional[str]) -> str:
    return f"  // {text}" if text else ""


def _with_sep(rendered: str, sep: str) -> str:
    """Place ``sep`` before any inline comment so commas precede ``//``."""
    marker = "  // "
    if sep and marker in rendered:
        idx = rendered.index(marker)
        return rendered[:idx] + sep + rendered[idx:]
    return rendered + sep


_COMPACT_LINE_MAX: int = 100


def set_compact_line_max(n: int) -> None:
    """Set the column limit used by _render_inst when deciding between a
    compact one-liner and the standard multi-line format."""
    global _COMPACT_LINE_MAX
    _COMPACT_LINE_MAX = n


def _render_inst(
    indent: int,
    type_name: str,
    params: list,
    inst_label: str,
    ports: list,
    comment: Optional[str],
) -> str:
    """Render a module/interface instantiation.

    When ``comment`` is set it is emitted as a ``// …`` line immediately
    before the instantiation (at the same indentation level).

    Emits a one-liner when no sub-item carries its own comment and the
    resulting line fits within ``_COMPACT_LINE_MAX``; otherwise falls back
    to the standard multi-line format.
    """
    pad = _ind(indent)
    comment_prefix = f"{pad}// {comment}\n" if comment else ""

    # ── attempt compact one-liner ────────────────────────────────────────────
    no_sub_comments = not any(item.comment for item in list(params) + list(ports))
    if no_sub_comments:
        params_str = ", ".join(p.render(0) for p in params)
        ports_str = ", ".join(p.render(0) for p in ports)
        if params_str:
            candidate = f"{pad}{type_name} #({params_str}) {inst_label} ({ports_str});"
        else:
            candidate = f"{pad}{type_name} {inst_label} ({ports_str});"
        if len(candidate) <= _COMPACT_LINE_MAX:
            return comment_prefix + candidate

    # ── multi-line fallback ──────────────────────────────────────────────────
    lines: list[str] = []
    if params:
        lines.append(f"{pad}{type_name} #(")
        for i, p in enumerate(params):
            sep = "," if i < len(params) - 1 else ""
            lines.append(_with_sep(p.render(indent + 1), sep))
        lines.append(f"{pad}) {inst_label} (")
    else:
        lines.append(f"{pad}{type_name} {inst_label} (")
    for i, p in enumerate(ports):
        sep = "," if i < len(ports) - 1 else ""
        lines.append(_with_sep(p.render(indent + 1), sep))
    lines.append(f"{pad});")
    return comment_prefix + "\n".join(lines)


def _begin_end(
    header: str,
    body: str,
    label: Optional[str],
    indent: int,
    comment: Optional[str] = None,
) -> str:
    """
    Render a ``begin [ : label ] … end [ : label ]`` block.

    The *header* is the keyword line prefix (e.g. ``"always_ff @(posedge clk)"``).
    The *body* text is re-indented to ``indent + 1``; blank lines are preserved
    without trailing whitespace.  The optional ``comment`` is placed inline on
    the opening keyword line.
    """
    pad = _ind(indent)
    inner = _ind(indent + 1)
    label_sfx = f" : {label}" if label else ""
    lines = [f"{pad}{header} begin{label_sfx}" + _inline_comment(comment)]
    for line in body.splitlines():
        stripped = line.rstrip()
        lines.append(f"{inner}{stripped}" if stripped else "")
    lines.append(f"{pad}end{label_sfx}")
    return "\n".join(lines)


def _begin_end_items(
    header: str,
    body: List[Any],
    label: Optional[str],
    indent: int,
    comment: Optional[str] = None,
) -> str:
    """
    Same as ``_begin_end``, but *body* is a list of ``SvNode`` instances rendered
    at ``indent + 1`` (each node's ``render`` output is appended line-wise).
    """
    pad = _ind(indent)
    inner = indent + 1
    label_sfx = f" : {label}" if label else ""
    lines = [f"{pad}{header} begin{label_sfx}" + _inline_comment(comment)]
    for item in body:
        for line in item.render(inner).splitlines():
            stripped = line.rstrip()
            lines.append(stripped if stripped else "")
    lines.append(f"{pad}end{label_sfx}")
    return "\n".join(lines)


# ─── Base class ───────────────────────────────────────────────────────────────


class SvNode(BaseModel):
    """
    Base for every AST node.

    - ``comment``: optional inline ``// comment`` appended to the node's
      primary output line.
    - ``render(indent)`` emits the BNF construct as LRM-formatted text.
    """

    model_config = ConfigDict(extra="forbid")

    comment: Optional[str] = Field(
        default=None,
        description="Inline // comment appended to this node's primary line.",
    )

    def render(self, indent: int = 0) -> str:  # pragma: no cover
        raise NotImplementedError(type(self).__name__)


# ─── Dimensions (A.2.5) ───────────────────────────────────────────────────────


class PackedDim(SvNode):
    """
    packed_dimension (A.2.5) ::= [ msb : lsb ]

    Example: ``[DATA_WIDTH-1:0]``
    """

    msb: str
    lsb: str = "0"

    def render(self, indent: int = 0) -> str:
        return f"[{self.msb}:{self.lsb}]"


class UnpackedDim(SvNode):
    """
    unpacked_dimension (A.2.5) ::= [ msb : lsb ] | [ size ]

    Use ``size`` as a shorthand for ``[size]`` (e.g. array lengths).
    """

    msb: Optional[str] = None
    lsb: Optional[str] = None
    size: Optional[str] = None

    def render(self, indent: int = 0) -> str:
        if self.size is not None:
            return f"[{self.size}]"
        return f"[{self.msb}:{self.lsb}]"


# ─── Header parameters (A.2.1.1) ─────────────────────────────────────────────


class ParamDecl(SvNode):
    """
    parameter_declaration (A.2.1.1):
        ``parameter data_type_or_implicit list_of_param_assignments``

    Used inside the module ``#( … )`` parameter port list.
    """

    name: str
    data_type: str = "int"
    default: Optional[str] = None

    def render(self, indent: int = 0) -> str:
        base = f"parameter {self.data_type} {self.name}"
        if self.default is not None:
            base += f" = {self.default}"
        return base + _inline_comment(self.comment)


# ─── Port declarations (A.1.3 / A.2.1.3) ─────────────────────────────────────

Direction = Literal["input", "output", "inout", "ref"]

# Net types (§6.5) — synthesised from multiple drivers; cannot hold state.
# A signal declared with one of these types is a *net* and may NOT be connected
# to a ``ref`` port (§23.2.2.3).
NetType = Literal[
    "wire", "tri", "wand", "wor", "triand", "trior",
    "tri0", "tri1", "supply0", "supply1", "uwire",
    # Variable / data types (§6.2, §6.4) — hold state; legal for ``ref`` ports.
    "logic", "reg", "bit",
    "byte", "shortint", "int", "longint", "integer", "time",
    "real", "shortreal", "realtime",
]

# Private sets used by validate_instance_connections for §23.2.2.3 checks.
_NET_TYPES: frozenset[str] = frozenset({
    "wire", "tri", "wand", "wor", "triand", "trior",
    "tri0", "tri1", "supply0", "supply1", "uwire",
})
_VARIABLE_TYPES: frozenset[str] = frozenset({
    "logic", "reg", "bit",
    "byte", "shortint", "int", "longint", "integer", "time",
    "real", "shortreal", "realtime",
})

# Signing modifier (§6.2.2) — placed between the type keyword and packed dims:
#   ``logic signed [7:0] data``
Signing = Literal["signed", "unsigned"]


class PortDecl(SvNode):
    """
    ansi_port_declaration (A.1.3):
        ``[ port_direction ] [ net_type ] [ signing ] { packed_dim } identifier { unpacked_dim }``

    ``net_type=None`` omits the type keyword (inherits from previous port or
    uses the module default net type per LRM §23.2.2.3).

    ``signing`` inserts ``signed`` / ``unsigned`` between the type keyword and
    the first packed dimension (§6.2.2).  Unsigned is the default for all net
    types and for ``logic``/``bit``; ``signed`` is the default for ``int``,
    ``shortint``, ``longint``, ``byte``, ``integer`` — omit the field when the
    LRM default is intended.

    ``ref`` ports must connect to variables, not nets (§23.2.2.3).

    **Unpacked array ports (§23.3.3.5)**

    One or more ``unpacked_dims`` make this an *unpacked array port*.  The
    packed dimensions (if any) describe the element type; the unpacked
    dimensions describe how many elements there are::

        input logic [7:0] data [0:3]   # 4-element array of byte-wide ports
            ^^^^^^^^^^^^ packed        ^^^^^  unpacked

    When such a port is connected in an array-of-instances context, the LRM
    distributes array elements across instances automatically (§23.3.3.5).
    Use ``IndexedSlice`` in the connecting ``PortConn.expression`` when an
    explicit per-element selection is required (e.g. ``data_arr[i][7:0]``).
    """

    kind: Literal["port"] = "port"
    direction: Direction
    net_type: Optional[NetType] = "logic"
    signing: Optional[Signing] = None
    packed_dims: List[PackedDim] = []
    name: str
    unpacked_dims: List[UnpackedDim] = []
    default: Optional[str] = None

    def render(self, indent: int = 0) -> str:
        parts: list[str] = [self.direction]
        if self.net_type:
            parts.append(self.net_type)
        if self.signing:
            parts.append(self.signing)
        parts.extend(d.render() for d in self.packed_dims)
        parts.append(self.name)
        parts.extend(d.render() for d in self.unpacked_dims)
        base = " ".join(parts)
        if self.default is not None:
            base += f" = {self.default}"
        return base + _inline_comment(self.comment)


# ─── Modports (§25.5) / interface-typed module ports ───────────────────────────


class ModportPortDecl(SvNode):
    """
    One port direction entry inside a ``modport`` declaration.

    Example: ``output req``
    """

    direction: Direction
    name: str

    def render(self, indent: int = 0) -> str:
        return f"{self.direction} {self.name}"


class ModportDecl(SvNode):
    """
    modport_declaration (§25.5):

        ``modport modport_identifier ( { modport_ports_declaration } ) ;``

    Example: ``modport master_mp(output req, input ack);``
    """

    kind: Literal["modport"] = "modport"
    name: str
    ports: List[ModportPortDecl]

    def render(self, indent: int = 0) -> str:
        inner = ", ".join(p.render() for p in self.ports)
        return (
            f"{_ind(indent)}modport {self.name}({inner});"
            + _inline_comment(self.comment)
        )


class InterfacePortDecl(SvNode):
    """
    A module port whose type is an interface, optionally restricted by modport.

    Examples::

        my_if.master_mp bus
        my_if bus
        my_if.slave_mp chan [0:3]
    """

    kind: Literal["iface_port"] = "iface_port"
    interface_name: str
    modport_name: Optional[str] = None
    name: str
    unpacked_dims: List[UnpackedDim] = []

    def render(self, indent: int = 0) -> str:
        if self.modport_name:
            base = f"{self.interface_name}.{self.modport_name} {self.name}"
        else:
            base = f"{self.interface_name} {self.name}"
        base += "".join(d.render() for d in self.unpacked_dims)
        return base + _inline_comment(self.comment)


# Plain union (no ``discriminator``): YAML/JSON inputs often omit ``kind`` on
# ports; ``PortDecl`` supplies ``kind="port"`` by default.  ``InterfacePortDecl``
# is tried when ``PortDecl`` fails (e.g. ``interface_name`` present).
ModulePortItem = Union[PortDecl, InterfacePortDecl]


# ─── Module body items ────────────────────────────────────────────────────────
#
# Each concrete body-item class carries a ``kind`` Literal field used as the
# Pydantic discriminator so that YAML/JSON round-trips work without ambiguity.


class LocalparamDecl(SvNode):
    """
    local_parameter_declaration (A.2.1.1):
        ``localparam data_type_or_implicit list_of_param_assignments ;``
    """

    kind: Literal["localparam"] = "localparam"
    data_type: str = "int"
    name: str
    value: str

    def render(self, indent: int = 0) -> str:
        base = f"{_ind(indent)}localparam {self.data_type} {self.name} = {self.value};"
        return base + _inline_comment(self.comment)


class NetDecl(SvNode):
    """
    net_declaration / data_declaration (A.2.1.3):
        ``net_type [ signing ] { packed_dim } identifier { unpacked_dim } [ = initial ] ;``

    Covers all net types (``wire``, ``tri``, …) and variable/data types
    (``logic``, ``reg``, ``bit``, integer types, …) as enumerated in §6.2–6.5.

    ``signing`` inserts ``signed`` / ``unsigned`` between the type keyword and
    the first packed dimension (§6.2.2).
    """

    kind: Literal["net"] = "net"
    net_type: NetType = "logic"
    signing: Optional[Signing] = None
    packed_dims: List[PackedDim] = []
    name: str
    unpacked_dims: List[UnpackedDim] = []
    initial_value: Optional[str] = None

    def render(self, indent: int = 0) -> str:
        parts: list[str] = [self.net_type]
        if self.signing:
            parts.append(self.signing)
        parts.extend(d.render() for d in self.packed_dims)
        parts.append(self.name)
        parts.extend(d.render() for d in self.unpacked_dims)
        base = f"{_ind(indent)}{' '.join(parts)}"
        if self.initial_value is not None:
            base += f" = {self.initial_value}"
        return base + ";" + _inline_comment(self.comment)


class TypedVarDecl(SvNode):
    """
    Data declaration with a free-form type expression (user-defined type,
    ``parameter type`` name, typedef, etc.).

    Used when ``NetDecl.net_type`` (a closed ``Literal``) cannot express the
    type, e.g. ``DATA_T data_in;`` inside a type-parameterized interface.

    Example: ``my_struct_t payload [3:0];``
    """

    kind: Literal["typed_var"] = "typed_var"
    user_type: str
    name: str
    unpacked_dims: List[UnpackedDim] = []

    def render(self, indent: int = 0) -> str:
        parts: list[str] = [self.user_type, self.name]
        parts.extend(d.render() for d in self.unpacked_dims)
        base = f"{_ind(indent)}{' '.join(parts)};"
        return base + _inline_comment(self.comment)


# ─── Module instantiation (A.4.1) ─────────────────────────────────────────────


class ParamConn(SvNode):
    """
    named_parameter_assignment (A.4.1):
        ``. parameter_identifier ( param_expression )``
    """

    param: str
    value: str

    def render(self, indent: int = 0) -> str:
        return f"{_ind(indent)}.{self.param}({self.value})" + _inline_comment(self.comment)


class SvExpr(BaseModel):
    """
    Base for inline expression nodes used inside port/parameter connections.

    Intentionally does **not** carry a ``comment`` field — expressions are
    always inlined into a larger construct and cannot hold standalone comments.
    """

    model_config = ConfigDict(extra="forbid")

    def render(self) -> str:  # pragma: no cover
        raise NotImplementedError(type(self).__name__)


# ─── Port-connection expression types (A.4.1 / A.8) ──────────────────────────
#
# These replace the former ``Optional[str]`` in ``PortConn`` so that every
# connected value refers to a structurally declared object in the hierarchy
# (a net/port by name, a bit-select or part-select of one, or a concatenation
# of such references).  Raw constant strings are intentionally excluded — use
# ``NetDecl`` / ``PortDecl`` names, not magic literals.
#
# Recursive self-reference in ``Concatenation`` requires ``model_rebuild()``
# at the bottom of this file.


class SignalRef(SvExpr):
    """
    Simple reference to a declared net, variable, or port by name.

    Example: ``clk``, ``data_in``, ``MY_PARAM``
    """

    kind: Literal["signal"] = "signal"
    name: str

    def render(self) -> str:
        return self.name


class BitSelect(SvExpr):
    """
    Single-bit select: ``name[index]``

    ``index`` is a constant expression string (e.g. ``"3"`` or ``"i"``).
    """

    kind: Literal["bit_select"] = "bit_select"
    name: str
    index: str

    def render(self) -> str:
        return f"{self.name}[{self.index}]"


class PartSelect(SvExpr):
    """
    Part-select: ``name[msb:lsb]``

    Example: ``data[7:0]``
    """

    kind: Literal["part_select"] = "part_select"
    name: str
    msb: str
    lsb: str

    def render(self) -> str:
        return f"{self.name}[{self.msb}:{self.lsb}]"


class IndexedSlice(SvExpr):
    """
    Two-level select: ``name[index][msb:lsb]``

    Selects one element of an unpacked array and then a packed range within
    that element.  This is the canonical expression form when connecting a
    specific element of an array port to an instance port in an array-of-
    instances context (§23.3.3.5).

    Example: ``data_arr[2][7:0]`` — element 2, bits 7 down to 0.

    For a plain unpacked-element select without a further packed range, use
    ``BitSelect`` (``name[index]``).
    """

    kind: Literal["indexed_slice"] = "indexed_slice"
    name: str
    index: str   # constant expression for the unpacked dimension
    msb: str
    lsb: str

    def render(self) -> str:
        return f"{self.name}[{self.index}][{self.msb}:{self.lsb}]"


class ConstantExpr(SvExpr):
    """
    A literal constant value emitted verbatim.

    Use for numeric literals (``1'b0``, ``8'hFF``), parameter expressions
    (``WIDTH-1``), or any other constant that is not a declared signal name.

    Examples::

        ConstantExpr(value="1'b0")      → ``1'b0``
        ConstantExpr(value="8'hFF")     → ``8'hFF``
    """

    kind: Literal["constant"] = "constant"
    value: str

    def render(self) -> str:
        return self.value


class VerbatimExpr(SvExpr):
    """
    Arbitrary expression text (casts, operators, function calls, etc.).

    Use in ``AssignStatement.rhs`` (or ``lvalue``) when the value cannot be
    built from ``SignalRef``, ``Concatenation``, and other structured nodes.
    The string is emitted unchanged—reserve for expressions that are valid
    SystemVerilog on the corresponding side of ``=``.

    In YAML/JSON you may give ``AssignStatement.rhs`` as a plain string; it
    is normalized to ``verbatim`` automatically.

    Prefer structured ``PortConnExpr`` where possible so connectivity checks
    and tooling can resolve signal names.
    """

    kind: Literal["verbatim"] = "verbatim"
    text: str

    def render(self) -> str:
        return self.text


class InterfaceRef(SvExpr):
    """
    Reference to an interface instance (or interface port) by identifier.

    Example: ``bus_if`` — used on the RHS of ``.port(expr)`` for interface
    connections and for distributing whole unpacked arrays of interfaces
    (§23.3.3.5).
    """

    kind: Literal["iface_ref"] = "iface_ref"
    name: str

    def render(self) -> str:
        return self.name


class InterfaceIndexedRef(SvExpr):
    """
    Single element of an unpacked array of interface instances.

    Example: ``bus_if[2]`` or ``bus_if[i]``
    """

    kind: Literal["iface_indexed"] = "iface_indexed"
    name: str
    index: str

    def render(self) -> str:
        return f"{self.name}[{self.index}]"


class Concatenation(SvExpr):
    """
    Concatenation: ``{ part0, part1, … }``

    Parts are themselves ``PortConnExpr`` values, enabling nested
    concatenations such as ``{a, b[3:0], {c, d}}``.

    Because ``PortConnExpr`` is a forward reference, call
    ``Concatenation.model_rebuild()`` after ``PortConnExpr`` is defined.
    """

    kind: Literal["concat"] = "concat"
    parts: List[PortConnExpr]  # type: ignore[name-defined]  # forward ref

    def render(self) -> str:
        return "{" + ", ".join(p.render() for p in self.parts) + "}"


# Discriminated union — Pydantic selects the right class from ``kind``.
# ``IndexedSlice`` must appear before ``PartSelect`` in the union so that the
# discriminator (``kind``) is unambiguous even though both carry ``msb``/``lsb``.
# ``ConstantExpr`` covers literal values (``1'b0``, ``8'hFF``, …) that are not
# declared signal names; ``VerbatimExpr`` is for arbitrary expression text.
# Both are valid in assign RHS/LHS; for port connections prefer structured refs.
PortConnExpr = Annotated[
    Union[
        SignalRef,
        BitSelect,
        PartSelect,
        IndexedSlice,
        Concatenation,
        ConstantExpr,
        VerbatimExpr,
        InterfaceRef,
        InterfaceIndexedRef,
    ],
    Field(discriminator="kind"),
]


class PortConn(SvNode):
    """
    named_port_connection (A.4.1):
        ``. port_identifier [ ( [ expression ] ) ]``

    ``expression=None`` produces an unconnected port: ``.port()``.

    The ``expression`` field accepts only typed connection objects
    (``SignalRef``, ``BitSelect``, ``PartSelect``, ``Concatenation``) rather
    than a bare string, so that every connected value can be traced back to a
    declared object in the hierarchy.
    """

    port: str
    expression: Optional[PortConnExpr] = None

    def render(self, indent: int = 0) -> str:
        expr = "" if self.expression is None else self.expression.render()
        return f"{_ind(indent)}.{self.port}({expr})" + _inline_comment(self.comment)


class ModuleInst(SvNode):
    """
    module_instantiation (A.4.1):
        ``module_identifier [ #( list_of_parameter_assignments ) ]``
        ``name_of_instance ( [ list_of_port_connections ] ) ;``

    ``name_of_instance`` is defined in A.4.1 as::

        instance_identifier { unpacked_dimension }

    Supplying ``instance_dims`` creates an **array of instances** (§23.3.3.5).
    Each unpacked dimension adds one axis to the instance array::

        logic_cell u_cells [7:0] ( .a(a_bus), .y(y_bus) );
        // → 8 instances, LRM distributes port connections across the array

    Connection distribution rules (§23.3.3.5):

    - A port of width W connected by an expression of width W is *replicated*
      to every instance in the array.
    - A port of width W connected by an expression of width N×W (where N is
      the total number of instances) is *distributed* — each instance receives
      its own W-bit slice.
    - Unpacked-array signals may be connected directly; the LRM assigns
      element ``[i]`` of the signal to instance ``[i]``.

    Use ``IndexedSlice`` in ``PortConn.expression`` when you need to connect
    a specific element-plus-range (``sig[i][msb:lsb]``) explicitly.

    The ``comment`` field is rendered on the closing ``);`` line.
    """

    kind: Literal["inst"] = "inst"
    module_name: str
    instance_name: str
    instance_dims: List[UnpackedDim] = []
    parameters: List[ParamConn] = []
    ports: List[PortConn] = []

    def render(self, indent: int = 0) -> str:
        inst_label = self.instance_name
        if self.instance_dims:
            inst_label += " " + " ".join(d.render() for d in self.instance_dims)
        return _render_inst(indent, self.module_name, self.parameters, inst_label, self.ports, self.comment)


class InterfaceInst(SvNode):
    """
    interface_instantiation (§25.3):

        ``interface_identifier [ #( parameter_assignments ) ]``
        ``instance_identifier { unpacked_dimension } ( [ port_connections ] ) ;``

    Syntax mirrors ``ModuleInst``; binds the interface's own ports (e.g. clk).
    """

    kind: Literal["iface_inst"] = "iface_inst"
    interface_name: str
    instance_name: str
    instance_dims: List[UnpackedDim] = []
    parameters: List[ParamConn] = []
    ports: List[PortConn] = []

    def render(self, indent: int = 0) -> str:
        inst_label = self.instance_name
        if self.instance_dims:
            inst_label += " " + " ".join(d.render() for d in self.instance_dims)
        return _render_inst(indent, self.interface_name, self.parameters, inst_label, self.ports, self.comment)


# ─── Escape hatches ───────────────────────────────────────────────────────────


class RawStatement(SvNode):
    """
    Verbatim text block.  Use for constructs not yet modelled (always blocks,
    assign statements, assertions, …).  Each line is re-indented to ``indent``.
    """

    kind: Literal["raw"] = "raw"
    text: str

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        lines = [pad + line for line in self.text.splitlines()]
        return "\n".join(lines) + _inline_comment(self.comment)


def _coerce_procedural_body(value: object) -> object:
    """Allow a single multi-line string (YAML / legacy) as one ``RawStatement``."""
    if isinstance(value, str):
        return [RawStatement(text=value)]
    return value


class CommentBlock(SvNode):
    """
    A standalone comment line or block.

    ``block=False`` (default): emits one ``// …`` line per input line.
    ``block=True``: emits a single ``/* … */`` block comment.
    """

    kind: Literal["comment_block"] = "comment_block"
    text: str
    block: bool = False

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        if self.block:
            return f"{pad}/* {self.text} */"
        return "\n".join(f"{pad}// {line}" for line in self.text.splitlines())


# ─── Sensitivity list event (A.6.7) ───────────────────────────────────────────


class SensitivityEvent(BaseModel):
    """
    One event inside an event_control sensitivity list (A.6.7):

    .. code-block:: bnf

        event_expression ::=
            [ edge_identifier ] expression
            | event_expression or event_expression

        edge_identifier ::= posedge | negedge | edge

    Set ``edge=None`` for a level-sensitive (combinational) entry; the signal
    name is emitted without an edge qualifier.

    Examples::

        SensitivityEvent(edge="posedge", signal="clk")   → ``posedge clk``
        SensitivityEvent(signal="rst_n")                 → ``rst_n``
    """

    model_config = ConfigDict(extra="forbid")

    edge: Optional[Literal["posedge", "negedge", "edge"]] = None
    signal: str

    def render(self) -> str:
        return f"{self.edge} {self.signal}" if self.edge else self.signal


# ─── Continuous assignment (A.6.1) ────────────────────────────────────────────


class AssignStatement(SvNode):
    """
    continuous_assign (A.6.1):

    .. code-block:: bnf

        continuous_assign ::=
            assign [ drive_strength ] [ delay3 ] list_of_net_assignments ;

        net_assignment ::= net_lvalue = expression

    ``lvalue`` is the assign target; ``rhs`` is the right-hand side. Either
    field uses structured ``PortConnExpr`` nodes, or ``rhs`` may be a plain
    string in the input (coerced to ``VerbatimExpr``) for casts and operators.

    ``delay`` is an optional delay value emitted as ``#delay`` (e.g. ``"1"``).

    Examples::

        assign full = fifo_full;
        assign #2 data_out = pipe_q;
    """

    kind: Literal["assign"] = "assign"
    lvalue: PortConnExpr
    rhs: PortConnExpr
    delay: Optional[str] = None

    @field_validator("rhs", mode="before")
    @classmethod
    def _rhs_coerce_str(cls, v: object) -> object:
        if isinstance(v, str):
            return {"kind": "verbatim", "text": v}
        return v

    @field_validator("lvalue", mode="before")
    @classmethod
    def _lvalue_coerce_str(cls, v: object) -> object:
        if isinstance(v, str):
            return {"kind": "verbatim", "text": v}
        return v

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        delay_part = f" #{self.delay}" if self.delay else ""
        base = f"{pad}assign{delay_part} {self.lvalue.render()} = {self.rhs.render()};"
        return base + _inline_comment(self.comment)


# ─── Procedural blocks (A.6.4) ────────────────────────────────────────────────


class AlwaysComb(SvNode):
    """
    always_construct (A.6.4) — combinational process:

    .. code-block:: bnf

        always_construct ::= always_comb seq_block

    The simulator automatically infers the sensitivity list from the ``body``
    nodes; no explicit ``@(…)`` clause is emitted.

    The ``body`` field is a list of procedural nodes (``RawStatement``,
    ``CommentBlock``, nested ``always_*`` / ``initial`` / ``final`` blocks,
    etc.).  A single multi-line string is still accepted at validation time
    and coerced to one ``RawStatement``.
    """

    kind: Literal["always_comb"] = "always_comb"
    label: Optional[str] = None
    body: Annotated[
        List["ProceduralBodyItem"],
        BeforeValidator(_coerce_procedural_body),
    ] = Field(default_factory=list)

    def render(self, indent: int = 0) -> str:
        return _begin_end_items(
            "always_comb", self.body, self.label, indent, self.comment
        )


class AlwaysLatch(SvNode):
    """
    always_construct (A.6.4) — latch-inference process:

    .. code-block:: bnf

        always_construct ::= always_latch seq_block

    Use when the intent is to infer a level-sensitive latch.  Synthesis tools
    warn if the body does not imply a latch.

    ``body`` uses the same ``ProceduralBodyItem`` list shape as ``AlwaysComb``
    (see that class).
    """

    kind: Literal["always_latch"] = "always_latch"
    label: Optional[str] = None
    body: Annotated[
        List["ProceduralBodyItem"],
        BeforeValidator(_coerce_procedural_body),
    ] = Field(default_factory=list)

    def render(self, indent: int = 0) -> str:
        return _begin_end_items(
            "always_latch", self.body, self.label, indent, self.comment
        )


class AlwaysFf(SvNode):
    """
    always_construct (A.6.4) — registered / clocked process:

    .. code-block:: bnf

        always_construct ::= always_ff clocking_event seq_block

        clocking_event ::= @ ( event_expression )
        event_expression ::=
            [ edge_identifier ] expression
            | event_expression or event_expression

    The ``sensitivity`` list is rendered as a comma/or-separated event
    expression, e.g.::

        sensitivity:
          - edge: posedge
            signal: clk
          - edge: negedge
            signal: rst_n
        →  always_ff @(posedge clk or negedge rst_n)

    Synthesis tools enforce that every assignment in the body is a
    non-blocking (``<=``) assignment.
    """

    kind: Literal["always_ff"] = "always_ff"
    sensitivity: List[SensitivityEvent]
    label: Optional[str] = None
    body: Annotated[
        List["ProceduralBodyItem"],
        BeforeValidator(_coerce_procedural_body),
    ] = Field(default_factory=list)

    def render(self, indent: int = 0) -> str:
        sens = " or ".join(e.render() for e in self.sensitivity)
        return _begin_end_items(
            f"always_ff @({sens})", self.body, self.label, indent, self.comment
        )


class AlwaysBlock(SvNode):
    """
    always_construct (A.6.4) — plain always with explicit event_control (A.6.7):

    .. code-block:: bnf

        always_construct ::= always statement
        statement        ::= procedural_timing_control_statement
        procedural_timing_control_statement ::=
            event_control statement_or_null

    When ``sensitivity_star=True`` (or ``sensitivity`` is empty) emits
    ``always @(*)``; otherwise the list items are joined with ``or``::

        always @(posedge clk or data_in)

    Prefer ``always_comb`` / ``always_ff`` / ``always_latch`` for new designs;
    use this class only for legacy or mixed-sensitivity constructs.
    """

    kind: Literal["always"] = "always"
    sensitivity: List[SensitivityEvent] = []
    sensitivity_star: bool = False
    label: Optional[str] = None
    body: Annotated[
        List["ProceduralBodyItem"],
        BeforeValidator(_coerce_procedural_body),
    ] = Field(default_factory=list)

    def render(self, indent: int = 0) -> str:
        if self.sensitivity_star or not self.sensitivity:
            clk_expr = "@(*)"
        else:
            sens = " or ".join(e.render() for e in self.sensitivity)
            clk_expr = f"@({sens})"
        return _begin_end_items(
            f"always {clk_expr}", self.body, self.label, indent, self.comment
        )


class InitialBlock(SvNode):
    """
    initial_construct (A.6.4):

    .. code-block:: bnf

        initial_construct ::= initial statement_or_null

    Executes once at time zero.  Used for testbench stimulus, memory
    initialisation, or simulation-only reset sequences.

    .. note::
        ``initial`` blocks are not synthesisable.  Use ``always_ff`` with a
        reset condition for synthesisable register initialisation.
    """

    kind: Literal["initial"] = "initial"
    label: Optional[str] = None
    body: Annotated[
        List["ProceduralBodyItem"],
        BeforeValidator(_coerce_procedural_body),
    ] = Field(default_factory=list)

    def render(self, indent: int = 0) -> str:
        return _begin_end_items("initial", self.body, self.label, indent, self.comment)


class FinalBlock(SvNode):
    """
    final_construct (A.6.4):

    .. code-block:: bnf

        final_construct ::= final function_statement

    Runs exactly once at the end of simulation (time infinity).  Typically
    used for end-of-test reporting or resource cleanup.

    .. note::
        ``final`` blocks are not synthesisable.
    """

    kind: Literal["final"] = "final"
    label: Optional[str] = None
    body: Annotated[
        List["ProceduralBodyItem"],
        BeforeValidator(_coerce_procedural_body),
    ] = Field(default_factory=list)

    def render(self, indent: int = 0) -> str:
        return _begin_end_items("final", self.body, self.label, indent, self.comment)


class SeqBlock(SvNode):
    """
    seq_block (A.6.3) — a named or unnamed ``begin`` … ``end`` block.

    .. code-block:: bnf

        seq_block ::=
            begin [ : block_identifier ]
                { block_item_declaration }
                { statement_or_null }
            end [ : block_identifier ]

    A ``SeqBlock`` may appear anywhere a procedural statement is legal (inside
    ``always_*``, ``initial``, or ``final`` bodies, or nested inside another
    ``SeqBlock``).  It is the only valid way to nest a ``begin``/``end`` group
    inside a procedural body.
    """

    kind: Literal["seq_block"] = "seq_block"
    label: Optional[str] = None
    body: Annotated[
        List["ProceduralBodyItem"],
        BeforeValidator(_coerce_procedural_body),
    ] = Field(default_factory=list)

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        inner = indent + 1
        label_sfx = f" : {self.label}" if self.label else ""
        lines = [f"{pad}begin{label_sfx}" + _inline_comment(self.comment)]
        for item in self.body:
            for line in item.render(inner).splitlines():
                stripped = line.rstrip()
                lines.append(stripped if stripped else "")
        lines.append(f"{pad}end{label_sfx}")
        return "\n".join(lines)


# Recursive procedural statement list for ``always_*``, ``initial``, ``final``,
# and nested ``SeqBlock`` bodies.  Only constructs that are valid *statements*
# inside a ``begin``/``end`` block are included — module-level constructs such
# as ``always_*`` / ``initial`` / ``final`` are intentionally excluded.

ProceduralBodyItem = Annotated[
    Union[
        RawStatement,
        CommentBlock,
        SeqBlock,
    ],
    Field(discriminator="kind"),
]


# ─── Generate constructs (A.4.2) ──────────────────────────────────────────────
#
# GenerateFor, GenerateIf, and GenerateRegion bodies are typed as
# ``List[ModuleBodyItem]`` — a forward reference resolved by model_rebuild()
# at the bottom of this file.


class GenerateFor(SvNode):
    """
    loop_generate_construct (A.4.2):

    .. code-block:: bnf

        loop_generate_construct ::=
            for ( genvar_initialization ; genvar_expression ; genvar_iteration )
            generate_block

        genvar_initialization ::=
            [ genvar ] genvar_identifier = constant_expression

        generate_block ::=
            generate_item
            | [ : label ] begin [ : label ] { generate_item } end [ : label ]

    ``var`` is the genvar identifier (the ``genvar`` keyword is always emitted
    inline).  ``init``, ``condition``, and ``step`` are constant-expression
    strings rendered directly into the ``for(…)`` header.

    The ``body`` accepts any ``ModuleBodyItem``  — net declarations, instances,
    assign statements, always blocks, or nested generate constructs.

    Example::

        for (genvar i = 0; i < N; i++) begin : gen_lanes
            lane_proc u_lane_i ( ... );
        end : gen_lanes
    """

    kind: Literal["generate_for"] = "generate_for"
    var: str
    init: str
    condition: str
    step: str
    label: Optional[str] = None
    body: List["ModuleBodyItem"]  # type: ignore[name-defined]  # forward ref

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        label_sfx = f" : {self.label}" if self.label else ""
        header = (
            f"for (genvar {self.var} = {self.init}; {self.condition}; {self.step})"
        )
        lines = [f"{pad}{header} begin{label_sfx}" + _inline_comment(self.comment)]
        for item in self.body:
            lines.append(item.render(indent + 1))
        lines.append(f"{pad}end{label_sfx}")
        return "\n".join(lines)


class GenerateIf(SvNode):
    """
    if_generate_construct (A.4.2):

    .. code-block:: bnf

        if_generate_construct ::=
            if ( constant_expression ) generate_block [ else generate_block ]

    ``then_body`` is always required; ``else_body`` is optional.  Each branch
    may carry an independent ``begin : label`` identifier.

    Example::

        if (USE_FAST_PATH) begin : gen_fast
            fast_cell u_fast ( ... );
        end : gen_fast
        else begin : gen_slow
            slow_cell u_slow ( ... );
        end : gen_slow
    """

    kind: Literal["generate_if"] = "generate_if"
    condition: str
    then_label: Optional[str] = None
    then_body: List["ModuleBodyItem"]  # type: ignore[name-defined]
    else_label: Optional[str] = None
    else_body: Optional[List["ModuleBodyItem"]] = None  # type: ignore[name-defined]

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        then_sfx = f" : {self.then_label}" if self.then_label else ""
        lines = [
            f"{pad}if ({self.condition}) begin{then_sfx}"
            + _inline_comment(self.comment)
        ]
        for item in self.then_body:
            lines.append(item.render(indent + 1))
        lines.append(f"{pad}end{then_sfx}")
        if self.else_body is not None:
            else_sfx = f" : {self.else_label}" if self.else_label else ""
            lines.append(f"{pad}else begin{else_sfx}")
            for item in self.else_body:
                lines.append(item.render(indent + 1))
            lines.append(f"{pad}end{else_sfx}")
        return "\n".join(lines)


class GenerateRegion(SvNode):
    """
    generate_region (A.4.2):

    .. code-block:: bnf

        generate_region ::= generate { generate_item } endgenerate

    Optional explicit wrapper that groups generate constructs under a
    ``generate … endgenerate`` keyword pair.  The keywords are optional in
    IEEE 1800-2017 but are commonly required by older tools and improve
    readability when multiple constructs are grouped.

    The ``body`` accepts any ``ModuleBodyItem``, including nested generate
    constructs.
    """

    kind: Literal["generate"] = "generate"
    body: List["ModuleBodyItem"]  # type: ignore[name-defined]

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        lines = [f"{pad}generate" + _inline_comment(self.comment)]
        for item in self.body:
            lines.append(item.render(indent + 1))
        lines.append(f"{pad}endgenerate")
        return "\n".join(lines)


class IfaceGenerateFor(SvNode):
    """
    ``for (…) generate`` inside an ``interface`` body (same rules as ``GenerateFor``
    but items are ``InterfaceBodyItem`` — e.g. modports, nets, nested generate).
    """

    kind: Literal["iface_generate_for"] = "iface_generate_for"
    var: str
    init: str
    condition: str
    step: str
    label: Optional[str] = None
    body: List["InterfaceBodyItem"]  # type: ignore[name-defined]

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        label_sfx = f" : {self.label}" if self.label else ""
        header = (
            f"for (genvar {self.var} = {self.init}; {self.condition}; {self.step})"
        )
        lines = [f"{pad}{header} begin{label_sfx}" + _inline_comment(self.comment)]
        for item in self.body:
            lines.append(item.render(indent + 1))
        lines.append(f"{pad}end{label_sfx}")
        return "\n".join(lines)


class IfaceGenerateIf(SvNode):
    """Conditional generate inside an interface body."""

    kind: Literal["iface_generate_if"] = "iface_generate_if"
    condition: str
    then_label: Optional[str] = None
    then_body: List["InterfaceBodyItem"]  # type: ignore[name-defined]
    else_label: Optional[str] = None
    else_body: Optional[List["InterfaceBodyItem"]] = None  # type: ignore[name-defined]

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        then_sfx = f" : {self.then_label}" if self.then_label else ""
        lines = [
            f"{pad}if ({self.condition}) begin{then_sfx}"
            + _inline_comment(self.comment)
        ]
        for item in self.then_body:
            lines.append(item.render(indent + 1))
        lines.append(f"{pad}end{then_sfx}")
        if self.else_body is not None:
            else_sfx = f" : {self.else_label}" if self.else_label else ""
            lines.append(f"{pad}else begin{else_sfx}")
            for item in self.else_body:
                lines.append(item.render(indent + 1))
            lines.append(f"{pad}end{else_sfx}")
        return "\n".join(lines)


class IfaceGenerateRegion(SvNode):
    """``generate … endgenerate`` wrapper inside an interface body."""

    kind: Literal["iface_generate"] = "iface_generate"
    body: List["InterfaceBodyItem"]  # type: ignore[name-defined]

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        lines = [f"{pad}generate" + _inline_comment(self.comment)]
        for item in self.body:
            lines.append(item.render(indent + 1))
        lines.append(f"{pad}endgenerate")
        return "\n".join(lines)


InterfaceBodyItem = Annotated[
    Union[
        LocalparamDecl,
        NetDecl,
        TypedVarDecl,
        AssignStatement,
        AlwaysComb,
        AlwaysLatch,
        AlwaysFf,
        AlwaysBlock,
        InitialBlock,
        FinalBlock,
        IfaceGenerateFor,
        IfaceGenerateIf,
        IfaceGenerateRegion,
        ModportDecl,
        RawStatement,
        CommentBlock,
    ],
    Field(discriminator="kind"),
]


class InterfaceDecl(SvNode):
    """
    interface_declaration (§25.3):

        ``interface [ lifetime ] interface_identifier … endinterface``

    ANSI-style header with optional ``package_import_declaration`` items (Annex A),
    then optional parameter port list and interface ports (e.g. clocking inputs),
    followed by interface items (nets, modports, …).

    ``imports`` holds one ``package_import_item`` string per line (after the
    ``import`` keyword), e.g. ``"my_pkg::*"`` renders as ``import my_pkg::*;``.
    """

    kind: Literal["interface"] = "interface"
    name: str
    timescale: Optional[str] = None
    imports: List[str] = []
    parameters: List[ParamDecl] = []
    ports: List[PortDecl] = []
    body: List[InterfaceBodyItem] = []
    emit_end: bool = True # emit `endinterface` per LRM §A.1.3
    end_label: bool = True # emit `endinterface : {self.name}` per LRM §A.1.3

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        inner = _ind(indent + 1)
        lines: list[str] = []

        if self.timescale:
            lines.append(f"`timescale {self.timescale}")

        if self.comment:
            lines.append(f"{pad}// {self.comment}")

        have_imports = bool(self.imports)
        if have_imports:
            lines.append(f"{pad}interface {self.name}")
            for clause in self.imports:
                lines.append(f"{inner}import {clause};")

        if self.parameters:
            if have_imports:
                lines.append(f"{pad}#(")
            else:
                lines.append(f"{pad}interface {self.name} #(")
            for i, p in enumerate(self.parameters):
                sep = "," if i < len(self.parameters) - 1 else ""
                lines.append(_with_sep(inner + p.render(), sep))
            if self.ports:
                lines.append(f"{pad}) (")
            else:
                lines.append(f"{pad});")
        else:
            if self.ports:
                if have_imports:
                    lines.append(f"{pad}(")
                else:
                    lines.append(f"{pad}interface {self.name} (")
            else:
                if have_imports:
                    lines.append(f"{pad};")
                else:
                    lines.append(f"{pad}interface {self.name};")

        if self.ports:
            for i, p in enumerate(self.ports):
                sep = "," if i < len(self.ports) - 1 else ""
                lines.append(_with_sep(inner + p.render(), sep))
            lines.append(f"{pad});")

        _IFACE_BLOCK_TYPES = (
            AlwaysComb,
            AlwaysLatch,
            AlwaysFf,
            AlwaysBlock,
            InitialBlock,
            FinalBlock,
            IfaceGenerateFor,
            IfaceGenerateIf,
            IfaceGenerateRegion,
        )
        if self.body:
            lines.append("")
            for i, item in enumerate(self.body):
                lines.append(item.render(indent + 1))
                if i < len(self.body) - 1:
                    next_item = self.body[i + 1]
                    if isinstance(item, _IFACE_BLOCK_TYPES) or isinstance(
                        next_item, _IFACE_BLOCK_TYPES
                    ):
                        lines.append("")

        if self.body:
            lines.append("")
        if self.emit_end:
            lines.append(f"{pad}endinterface : {self.name}" if self.end_label else f"{pad}endinterface")

        return "\n".join(lines)


# ─── Discriminated union for body items ───────────────────────────────────────
#
# Pydantic uses the ``kind`` field value as the discriminator key so that
# model_validate() selects the right class without trying every branch.

ModuleBodyItem = Annotated[
    Union[
        LocalparamDecl,
        NetDecl,
        TypedVarDecl,
        ModuleInst,
        InterfaceInst,
        AssignStatement,
        AlwaysComb,
        AlwaysLatch,
        AlwaysFf,
        AlwaysBlock,
        InitialBlock,
        FinalBlock,
        GenerateFor,
        GenerateIf,
        GenerateRegion,
        RawStatement,
        CommentBlock,
    ],
    Field(discriminator="kind"),
]


# ─── Module declaration (A.1.2 / A.1.3) ──────────────────────────────────────


class ModuleDecl(SvNode):
    """
    module_declaration with ANSI-style header (A.1.2 / A.1.3):

    Per Annex A, the header may include ``package_import_declaration`` entries
    after ``module`` ``module_identifier`` and before the optional parameter
    port list ``#( … )`` and ANSI port list ``( … )``.

    ``imports`` holds one ``package_import_item`` string per line (text after
    the ``import`` keyword), e.g. ``"shared_types_package::*"`` becomes
    ``import shared_types_package::*;``.

    When ``imports`` is empty, rendering matches the historical single-line
    ``module name #(` / ``module name (` / ``module name;`` forms for backward
    compatibility.

    The ``comment`` field is rendered as a ``//`` line immediately before the
    ``module`` keyword, serving as a module-level description comment.
    """

    kind: Literal["module"] = "module"
    name: str
    timescale: Optional[str] = None
    imports: List[str] = []
    parameters: List[ParamDecl] = []
    ports: List[ModulePortItem] = []
    body: List[ModuleBodyItem] = []
    emit_end: bool = True # emit `endmodule` per LRM §A.1.2
    end_label: bool = True  # emit `: name` after endmodule per LRM §A.1.2

    def render(self, indent: int = 0) -> str:
        pad = _ind(indent)
        inner = _ind(indent + 1)
        lines: list[str] = []

        # ── `timescale compiler directive ─────────────────────────────────────
        if self.timescale:
            lines.append(f"`timescale {self.timescale}")

        # ── optional module-level description comment ─────────────────────────
        if self.comment:
            lines.append(f"{pad}// {self.comment}")

        have_imports = bool(self.imports)
        if have_imports:
            lines.append(f"{pad}module {self.name}")
            for clause in self.imports:
                lines.append(f"{inner}import {clause};")

        # ── #( parameter_port_list ) and start of port list ───────────────────
        if self.parameters:
            if have_imports:
                lines.append(f"{pad}#(")
            else:
                lines.append(f"{pad}module {self.name} #(")
            for i, p in enumerate(self.parameters):
                sep = "," if i < len(self.parameters) - 1 else ""
                lines.append(_with_sep(inner + p.render(), sep))
            if self.ports:
                lines.append(f"{pad}) (")
            else:
                lines.append(f"{pad});")
        else:
            if self.ports:
                if have_imports:
                    lines.append(f"{pad}(")
                else:
                    lines.append(f"{pad}module {self.name} (")
            else:
                if have_imports:
                    lines.append(f"{pad};")
                else:
                    lines.append(f"{pad}module {self.name};")

        # ── list_of_port_declarations ─────────────────────────────────────────
        if self.ports:
            for i, p in enumerate(self.ports):
                sep = "," if i < len(self.ports) - 1 else ""
                lines.append(_with_sep(inner + p.render(), sep))
            lines.append(f"{pad});")

        # ── module body items ─────────────────────────────────────────────────
        _BLOCK_TYPES = (
            ModuleInst,
            InterfaceInst,
            AlwaysComb, AlwaysLatch, AlwaysFf, AlwaysBlock,
            InitialBlock, FinalBlock,
            GenerateFor, GenerateIf, GenerateRegion,
        )
        if self.body:
            lines.append("")
            rendered_body = [item.render(indent + 1) for item in self.body]
            for i, (item, rendered) in enumerate(zip(self.body, rendered_body)):
                lines.append(rendered)
                if i < len(self.body) - 1:
                    next_item = self.body[i + 1]
                    next_rendered = rendered_body[i + 1]
                    if isinstance(item, _BLOCK_TYPES) or isinstance(next_item, _BLOCK_TYPES):
                        # Omit blank line between consecutive compact (single-line,
                        # no comment) instances; keep it in all other cases.
                        curr_compact = (
                            isinstance(item, (ModuleInst, InterfaceInst))
                            and "\n" not in rendered
                        )
                        next_compact = (
                            isinstance(next_item, (ModuleInst, InterfaceInst))
                            and "\n" not in next_rendered
                        )
                        if not (curr_compact and next_compact):
                            lines.append("")

        # ── endmodule [ : identifier ] ────────────────────────────────────────
        if self.body:
            lines.append("")
        if self.emit_end:
            lines.append(f"{pad}endmodule : {self.name}" if self.end_label else f"{pad}endmodule")

        return "\n".join(lines)

    def declared_signal_names(self) -> set[str]:
        """
        Return the set of every name that is legal on the *right-hand side* of a
        ``PortConn.expression`` inside this module.

        Includes:
        - All ANSI port names (``PortDecl.name``)
        - All net/variable declaration names (``NetDecl.name`` in ``body``)
        - All parameter names (``ParamDecl.name``) — parameters are visible as
          constant expressions and may legitimately drive parameter ports of
          child instances.
        - All localparam names (``LocalparamDecl.name``) — same rationale.

        Does **not** descend into child ``ModuleInst`` items; call this method
        on the specific ``ModuleDecl`` that contains the instance being checked.
        """
        names: set[str] = set()
        for p in self.ports:
            names.add(p.name)
        names.update(p.name for p in self.parameters)
        for item in self.body:
            if isinstance(item, NetDecl):
                names.add(item.name)
            elif isinstance(item, LocalparamDecl):
                names.add(item.name)
            elif isinstance(item, TypedVarDecl):
                names.add(item.name)
            elif isinstance(item, InterfaceInst):
                names.add(item.instance_name)
        return names

    def validate_instance_connections(
        self,
        inst: ModuleInst,
        child_decl: Optional[ModuleDecl] = None,
    ) -> list[str]:
        """
        Check that every named ``PortConn`` expression in ``inst`` references a
        name declared in this module.  Returns a list of error strings (empty
        when all connections are valid).

        Pass ``child_decl`` (the ``ModuleDecl`` of the instantiated module) to
        enable additional §23.2.2.3 checks:

        - A ``ref`` port may only connect to a variable-type signal (one
          declared with ``logic``, ``reg``, ``bit``, or an integer type).
          Connecting it to a net type (``wire``, ``tri``, …) is illegal.

        **Array-of-instances (§23.3.3.5):** when ``inst.instance_dims`` is
        non-empty the instance is an array.  This method still verifies that
        every referenced signal name is declared in the parent module.  Full
        width-distribution checking (whether the connected expression is W wide
        for replication, or N×W wide for distribution) requires width metadata
        on ``NetDecl`` / ``PortDecl`` and is not performed here.

        Usage::

            errors = parent.validate_instance_connections(u_child, child_decl)
            if errors:
                raise ValueError("\\n".join(errors))
        """
        valid = self.declared_signal_names()

        # Map signal name → NetDecl for net-type look-ups (ref port check).
        parent_nets: dict[str, NetDecl] = {
            item.name: item
            for item in self.body
            if isinstance(item, NetDecl)
        }
        # Map port name → PortDecl for the child module (ref direction check).
        child_ports: dict[str, PortDecl] = (
            {
                p.name: p
                for p in child_decl.ports
                if isinstance(p, PortDecl)
            }
            if child_decl
            else {}
        )

        errors: list[str] = []

        def _root_name(expr: PortConnExpr) -> Optional[str]:
            """Return the base signal name for any named expression."""
            if isinstance(
                expr,
                (SignalRef, BitSelect, PartSelect, IndexedSlice, InterfaceRef, InterfaceIndexedRef),
            ):
                return expr.name
            return None

        def _check_expr(expr: PortConnExpr, port_name: str) -> None:
            if isinstance(
                expr,
                (
                    SignalRef,
                    BitSelect,
                    PartSelect,
                    IndexedSlice,
                    InterfaceRef,
                    InterfaceIndexedRef,
                ),
            ):
                if expr.name not in valid:
                    errors.append(
                        f"{inst.instance_name}.{port_name}: "
                        f"'{expr.name}' is not declared in module '{self.name}'"
                    )
            elif isinstance(expr, Concatenation):
                for part in expr.parts:
                    _check_expr(part, port_name)

        def _check_ref_port(conn: PortConn) -> None:
            """§23.2.2.3 — ref ports require a variable, not a net."""
            port_decl = child_ports.get(conn.port)
            if port_decl is None or port_decl.direction != "ref":
                return
            if conn.expression is None:
                return
            sig_name = _root_name(conn.expression)
            if sig_name is None:
                return  # concatenation in ref port — caught elsewhere
            net = parent_nets.get(sig_name)
            if net is not None and net.net_type in _NET_TYPES:
                errors.append(
                    f"{inst.instance_name}.{conn.port}: 'ref' port connected to "
                    f"net '{sig_name}' (type '{net.net_type}'); "
                    f"§23.2.2.3 requires a variable type "
                    f"(logic, reg, bit, integer, …)"
                )

        for conn in inst.ports:
            if conn.expression is not None:
                _check_expr(conn.expression, conn.port)
            if child_decl:
                _check_ref_port(conn)

        return errors


# ─── Top-level design file ────────────────────────────────────────────────────


class SvDesign(BaseModel):
    """
    Root object representing a single ``.sv`` file.

    A design file contains an optional file-level description (rendered as a
    ``//`` header block), zero or more interface declarations, and one or more
    module declarations.
    """

    model_config = ConfigDict(extra="forbid")

    description: Optional[str] = None
    interfaces: List[InterfaceDecl] = []
    modules: List[ModuleDecl]

    def render(self) -> str:
        """Render the entire ``.sv`` file as a string."""
        sections: list[str] = []

        if self.description:
            header = "\n".join(f"// {line}" for line in self.description.splitlines())
            sections.append(header)

        sections.extend(i.render() for i in self.interfaces)
        sections.extend(m.render() for m in self.modules)
        return "\n\n".join(sections) + "\n"


# ─── Post-definition rebuilds ─────────────────────────────────────────────────
#
# ``Concatenation.parts`` uses ``PortConnExpr``, the generate constructs use
# ``ModuleBodyItem``, and the procedural block classes use ``ProceduralBodyItem``
# via ``SeqBlock`` — all forward references resolved here.

Concatenation.model_rebuild()
SeqBlock.model_rebuild()
AlwaysComb.model_rebuild()
AlwaysLatch.model_rebuild()
AlwaysFf.model_rebuild()
AlwaysBlock.model_rebuild()
InitialBlock.model_rebuild()
FinalBlock.model_rebuild()
GenerateFor.model_rebuild()
GenerateIf.model_rebuild()
GenerateRegion.model_rebuild()
IfaceGenerateFor.model_rebuild()
IfaceGenerateIf.model_rebuild()
IfaceGenerateRegion.model_rebuild()