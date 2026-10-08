#ifndef IDTH_BFM_H_
#define IDTH_BFM_H_
#include "systemc.h"
#include "idth_channel.h"
#include "idt_bfm.h"
template<typename VL_S, typename VL_TS, typename VL_SB, typename VL_O2 = sc_bv<3>>
struct idth_hdl_if: public sc_interface {
    sc_signal<bool> vld;
    sc_signal<VL_S> s;
    sc_signal<VL_SB> sb;
    sc_signal<VL_TS> ts;
    sc_signal<VL_O2> o2;
    sc_signal<bool> rdy;
};
template<typename S, typename TS, unsigned TSW, typename VL_S, typename VL_TS, typename VL_SB,
         typename VL_O2, typename O2, unsigned O2W>
struct idth_bfm_checks {
    static_assert(S::_bitWidth == idtBvWidth<VL_S>::value, "bridge width of s != SC payload width");
    static_assert((S::_bitWidth + 7) / 8 == idtBvWidth<VL_SB>::value, "bridge width of hdlparam sb != bytes of s");
    static_assert(TSW == idtBvWidth<VL_TS>::value, "bridge width of ts != SC typeStruct width");
    static_assert(O2W == idtBvWidth<VL_O2>::value, "bridge width of o2");
};
#define IDTH_BFM_TPL \
template<typename S, typename TS, unsigned TSW, typename VL_S, typename VL_TS, typename VL_SB, \
         typename VL_O2 = sc_bv<3>, typename O2 = std::monostate, unsigned O2W = 3>
#define IDTH_BFM_BODY(CLS, PORT) \
class CLS: public sc_module, idth_bfm_checks<S,TS,TSW,VL_S,VL_TS,VL_SB,VL_O2,O2,O2W> { \
public: \
    PORT<S,TS,TSW,O2,O2W> if_p; \
    sc_port<idth_hdl_if<VL_S,VL_TS,VL_SB,VL_O2>> hdl_if_p; \
    sc_in<bool> clk; sc_in<bool> rst_n; \
    CLS(sc_module_name) {} \
};
IDTH_BFM_TPL
IDTH_BFM_BODY(idth_src_bfm, idth_out)
IDTH_BFM_TPL
IDTH_BFM_BODY(idth_dst_bfm, idth_in)
#endif
