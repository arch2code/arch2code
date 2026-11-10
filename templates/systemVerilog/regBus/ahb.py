"""AHB-Lite front end for the generated register-bus router and register handler RTL.

It implements the API apb.py describes. AHB pipelines a transfer into an
address phase and a data phase, so both ends register the address phase and
run the core during the data phase, holding HREADYOUT low until the core
answers.

A transfer starts on HSEL & HTRANS[1] & HREADY, so NONSEQ and SEQ each start a
single transfer at the address they carry, and IDLE and BUSY get the
zero-wait OKAY the protocol requires. An error is the two-cycle response:
HRESP high with HREADYOUT low, then HRESP high with HREADYOUT high.
"""

from jinja2 import Template

BUS_NAME = 'AHB'
ERROR_NAME = 'HRESP ERROR'


def decoderUpstream(port, addrSt, dataSt, addrMask, clk, rst):
    lines = [f"{addrSt} ahb_addr;",
             f"assign ahb_addr = {addrSt}'({port}.haddr) & {addrSt}'(32'h{addrMask:_x});",
             Template(_upstream_j2_template).render(
                 port=port, addrSt=addrSt, dataSt=dataSt, clk=clk, rst=rst),
             '']
    return {'lines': lines,
            'addr': 'ahb_addr',
            'start': f"{port}.hsel & {port}.htrans[1] & {port}.hready",
            'accept': 'ahb_accept',
            'pending': 'ahb_dphase & ~hready_q & ~ahb_err2'}


def decoderDownstream(child, clk, rst):
    lines = [Template(_downstream_j2_template).render(child=child, clk=clk, rst=rst), '']
    return {'lines': lines,
            'selectNext': f"{child}_next_sel",
            'selected': f"{child}_sel",
            'ready': f"{child}_ready",
            'rdata': f"{child}.hrdata",
            'error': f"{child}.hresp"}


def decoderResponse(port, dataSt, clk, rst):
    return {'declLines': [f"logic {port}_next_hready, hready_q;",
                          f"{dataSt} {port}_next_hrdata, hrdata_q;",
                          f"logic {port}_next_hresp, hresp_q;",
                          "logic ahb_err2;"],
            'ready': f"{port}_next_hready",
            'rdata': f"{port}_next_hrdata",
            'error': f"{port}_next_hresp",
            'driveLines': Template(_response_j2_template).render(port=port, clk=clk, rst=rst).splitlines()}


def handlerAccess(port, addrSt, addrMask, clk, rst, errorResponses):
    lines = Template(_handler_j2_template).render(
        port=port, addrSt=addrSt, addrMask=addrMask, clk=clk, rst=rst,
        errorResponses=errorResponses).splitlines()
    return {'addrLines': lines,
            'addr': 'ahb_addr',
            'wdata': f"{port}.hwdata",
            'selectLines': ["logic wr_select;",
                            "logic rd_select;",
                            f"assign wr_select = ahb_core_select & ahb_write & ahb_word & {rst};",
                            f"assign rd_select = ahb_core_select & ~ahb_write & {rst};"],
            'readyWaitStateParam': 'AHB_READY_1WS'}


def handlerResponse(port, ready, rdata, error):
    return [f"// Update the {BUS_NAME} interface",
            f"assign ahb_ready = {ready} | ahb_subword_wr;",
            f"assign ahb_error = {error} | ahb_subword_err;",
            "assign ahb_complete = ahb_dphase & ahb_ready;",
            f"assign {port}.hrdata    = ahb_err2 ? ahb_err_hrdata : {rdata};",
            f"assign {port}.hreadyout = ~ahb_dphase | (ahb_complete & ~ahb_error) | ahb_err2;",
            f"assign {port}.hresp     = (ahb_complete & ahb_error) | ahb_err2;"]


# The router answers each transfer one cycle after the core, from the
# registered response, so an idle link reads HREADYOUT high. HRDATA holds from
# the response until the next one.
_upstream_j2_template = """\
//signals for interface {{ port }}
logic ahb_accept;
logic ahb_dphase;
{{ addrSt }} haddr_q;
`DFFEN_DOM({{ clk }}, {{ rst }}, haddr_q, {{ port }}.haddr, ahb_accept)
logic hwrite_q;
`DFFEN_DOM({{ clk }}, {{ rst }}, hwrite_q, {{ port }}.hwrite, ahb_accept)
logic [2:0] hsize_q;
`DFFEN_DOM({{ clk }}, {{ rst }}, hsize_q, {{ port }}.hsize, ahb_accept)
{{ dataSt }} hwdata_q;
`DFF_DOM({{ clk }}, {{ rst }}, hwdata_q, {{ port }}.hwdata)
`DFF_DOM({{ clk }}, {{ rst }}, ahb_dphase, ahb_accept | (ahb_dphase & ~{{ port }}.hreadyout))
"""

_downstream_j2_template = """\
//signals for interface {{ child }}
logic {{ child }}_sel;
logic {{ child }}_next_sel;
logic {{ child }}_aphase;
logic {{ child }}_ready;
`DFF_DOM({{ clk }}, {{ rst }}, {{ child }}_aphase, {{ child }}_next_sel)
assign {{ child }}_ready = {{ child }}_sel & ~{{ child }}_aphase & {{ child }}.hreadyout;
`SCFF_DOM({{ clk }}, {{ rst }}, {{ child }}_sel, {{ child }}_next_sel, {{ child }}_ready)

assign {{ child }}.hsel   = {{ child }}_aphase;
assign {{ child }}.htrans = {{ child }}_aphase ? 2'b10 : 2'b00;
assign {{ child }}.haddr  = haddr_q;
assign {{ child }}.hwrite = hwrite_q;
assign {{ child }}.hsize  = hsize_q;
assign {{ child }}.hwdata = hwdata_q;
assign {{ child }}.hready = {{ child }}.hreadyout;
"""

_response_j2_template = """\
`DFF_DOM({{ clk }}, {{ rst }}, hready_q, {{ port }}_next_hready)
`DFFEN_DOM({{ clk }}, {{ rst }}, hrdata_q, {{ port }}_next_hrdata, {{ port }}_next_hready)
`DFF_DOM({{ clk }}, {{ rst }}, hresp_q, {{ port }}_next_hresp)
`DFF_DOM({{ clk }}, {{ rst }}, ahb_err2, ahb_dphase & hready_q & hresp_q)
assign {{ port }}.hrdata    = hrdata_q;
assign {{ port }}.hreadyout = ~ahb_dphase | (hready_q & ~hresp_q) | ahb_err2;
assign {{ port }}.hresp     = (hready_q & hresp_q) | ahb_err2;"""

# The core runs while the data phase is open, except in the second cycle of an
# error response and in the first cycle of a transfer that follows another
# with no idle cycle between, which lets the core's memory read pipeline drain.
# HRDATA holds through both error cycles. A write of less than a word does not
# reach the core.
_handler_j2_template = """\
logic ahb_start;
assign ahb_start = {{ port }}.hsel & {{ port }}.htrans[1] & {{ port }}.hready;
{{ addrSt }} ahb_addr;
`DFFEN_DOM({{ clk }}, {{ rst }}, ahb_addr, {{ addrSt }}'({{ port }}.haddr) & {{ addrMask }}, ahb_start)
logic ahb_write, ahb_word;
`DFFEN_DOM({{ clk }}, {{ rst }}, ahb_write, {{ port }}.hwrite, ahb_start)
`DFFEN_DOM({{ clk }}, {{ rst }}, ahb_word, {{ port }}.hsize == 3'd2, ahb_start)
logic ahb_dphase, ahb_ready, ahb_error, ahb_complete, ahb_err2, ahb_back2back;
`DFF_DOM({{ clk }}, {{ rst }}, ahb_dphase, ahb_start | (ahb_dphase & ~{{ port }}.hreadyout))
`DFF_DOM({{ clk }}, {{ rst }}, ahb_err2, ahb_complete & ahb_error & ~ahb_err2)
`DFF_DOM({{ clk }}, {{ rst }}, ahb_back2back, ahb_start & ahb_dphase)
logic [$bits({{ port }}.hrdata)-1:0] ahb_err_hrdata;
`DFFEN_DOM({{ clk }}, {{ rst }}, ahb_err_hrdata, {{ port }}.hrdata, ahb_complete & ahb_error & ~ahb_err2)
logic ahb_core_select, ahb_subword_wr, ahb_subword_err;
assign ahb_core_select = ahb_dphase & ~ahb_err2 & ~ahb_back2back;
assign ahb_subword_wr  = ahb_core_select & ahb_write & ~ahb_word;
{%- if errorResponses %}
assign ahb_subword_err = ahb_subword_wr;
{%- else %}
assign ahb_subword_err = 1'b0;
{%- endif %}"""
