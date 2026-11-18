"""APB front end for the generated register-bus router and register handler RTL.

A front end owns every line that names a protocol signal. It turns the bus
into a neutral access, and the shared cores in regBusDecodeModule.py and
moduleRegs.py decode that access. An interface type with addressBus: true
names its front end in svRegBusFrontEnd:.

Router (one bus type for the whole decode tree, upstream and downstream):
  decoderUpstream   captures the request. The core reads `addr`, starts a
                    decode when `start` is true, drives `accept` high on that
                    cycle, and answers an unmapped access while `pending`.
  decoderDownstream drives one child from the captured request while the
                    core holds its `selectNext`. `selected` stays high until
                    the child answers on `ready`, `rdata` and `error`.
  decoderResponse   declares the core's next response `ready`, `rdata` and
                    `error`, and registers them onto the upstream bus.

Handler:
  handlerAccess     declares `addr`, names the write data `wdata`, and drives
                    the core's `wr_select` and `rd_select`, held until the
                    core answers. `readyWaitStateParam` names the module
                    parameter that registers the answer. `clk` is for a
                    front end that registers the access, and
                    `errorResponses` for one that answers some accesses
                    itself. APB uses neither.
  handlerResponse   drives the bus from the core's ready, read data and error.
"""

from jinja2 import Template

BUS_NAME = 'APB'
ERROR_NAME = 'PSLVERR'


def decoderUpstream(port, addrSt, dataSt, addrMask, clk, rst):
    lines = [f"{addrSt} apb_addr;",
             f"assign apb_addr = {addrSt}'({port}.paddr) & {addrSt}'(32'h{addrMask:_x});",
             Template(_upstream_j2_template).render(
                 port=port, addrSt=addrSt, dataSt=dataSt, clk=clk, rst=rst),
             '']
    return {'lines': lines,
            'addr': 'apb_addr',
            'start': f"{port}.psel & ~trans_active",
            'accept': 'set_trans_active',
            'pending': 'trans_active & ~pready'}


def decoderDownstream(child, clk, rst):
    lines = [Template(_downstream_j2_template).render(child=child, clk=clk, rst=rst), '']
    return {'lines': lines,
            'selectNext': f"{child}_next_psel",
            'selected': f"{child}_psel",
            'ready': f"{child}.pready",
            'rdata': f"{child}.prdata",
            'error': f"{child}.pslverr"}


def decoderResponse(port, dataSt, clk, rst):
    return {'declLines': [f"logic {port}_next_pready;",
                          f"{dataSt} {port}_next_prdata, prdata;",
                          f"logic {port}_next_pslverr, pslverr;"],
            'ready': f"{port}_next_pready",
            'rdata': f"{port}_next_prdata",
            'error': f"{port}_next_pslverr",
            'driveLines': [f"`DFF_DOM({clk}, {rst}, pready, {port}_next_pready)",
                           f"`DFF_DOM({clk}, {rst}, prdata, {port}_next_prdata)",
                           f"`DFF_DOM({clk}, {rst}, pslverr, {port}_next_pslverr)",
                           f"assign {port}.pready  = pready;",
                           f"assign {port}.prdata  = prdata;",
                           f"assign {port}.pslverr = pslverr;"]}


def handlerAccess(port, addrSt, addrMask, clk, rst, errorResponses):
    return {'addrLines': [f"{addrSt} apb_addr;",
                          f"assign apb_addr = {addrSt}'({port}.paddr) & {addrMask};"],
            'addr': 'apb_addr',
            'wdata': f"{port}.pwdata",
            'selectLines': ["logic wr_select;",
                            "logic rd_select;",
                            f"assign wr_select = {port}.psel & {port}.penable & {port}.pwrite & {rst};",
                            f"assign rd_select = {port}.psel & {port}.penable & !{port}.pwrite & {rst};"],
            'readyWaitStateParam': 'APB_READY_1WS'}


def handlerResponse(port, ready, rdata, error):
    return [f"// Update the {BUS_NAME} interface",
            f"assign {port}.prdata  = {rdata};",
            f"assign {port}.pready  = {ready};",
            f"assign {port}.pslverr = {error};"]


_upstream_j2_template = """\
//signals for interface {{ port }}
{{ addrSt }} paddr_q;
`DFF_DOM({{ clk }}, {{ rst }}, paddr_q, {{ port }}.paddr)
{{ dataSt }} pwdata_q;
`DFF_DOM({{ clk }}, {{ rst }}, pwdata_q, {{ port }}.pwdata)
logic penable_q;
`DFF_DOM({{ clk }}, {{ rst }}, penable_q, {{ port }}.penable)
logic pwrite_q;
`DFF_DOM({{ clk }}, {{ rst }}, pwrite_q, {{ port }}.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF_DOM({{ clk }}, {{ rst }}, trans_active, set_trans_active, pready)
"""

_downstream_j2_template = """\
//signals for interface {{ child }}
logic {{ child }}_psel;
logic {{ child }}_next_psel;
`SCFF_DOM({{ clk }}, {{ rst }}, {{ child }}_psel, {{ child }}_next_psel, {{ child }}.pready)

assign {{ child }}.paddr   = paddr_q;
assign {{ child }}.penable = penable_q & {{ child }}_psel;
assign {{ child }}.psel    = {{ child }}_psel;
assign {{ child }}.pwrite  = pwrite_q;
assign {{ child }}.pwdata  = pwdata_q;
"""
