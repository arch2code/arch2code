#ifndef IDT_BFM_H_
#define IDT_BFM_H_
#include "systemc.h"
#include "idt_channel.h"
#include <variant>

template<typename V> struct idtBvWidth;
template<int N> struct idtBvWidth<sc_bv<N>> { static constexpr unsigned value = N; };
template<> struct idtBvWidth<bool> { static constexpr unsigned value = 1; };

template<typename P, unsigned DEF> constexpr unsigned idtPayloadW() {
    if constexpr (std::is_same_v<P, std::monostate>) return DEF; else return P::_bitWidth; }

// Verilated bridge; trailing bridge arguments default to the defaultWidth of the unbound optional parameter.
template<typename VL_S, typename VL_TY, typename VL_TS,
         typename VL_O1 = sc_bv<2>, typename VL_O2 = sc_bv<3>, typename VL_O3 = sc_bv<5>>
struct idt_hdl_if: public sc_interface {
    sc_signal<bool> vld;
    sc_signal<VL_S> s;
    sc_signal<VL_TY> ty;
    sc_signal<VL_TS> ts;
    sc_signal<VL_O1> o1;
    sc_signal<VL_O2> o2;
    sc_signal<VL_O3> o3;
    sc_signal<bool> rdy;
};

// Width checks: every bridge width must equal the payload width the SC side names.
template<typename S, typename TY, unsigned TYW, typename TS, unsigned TSW,
         typename VL_S, typename VL_TY, typename VL_TS, typename VL_O1, typename VL_O2, typename VL_O3,
         typename O1, typename O2, unsigned O2W, typename O3, unsigned O3W>
struct idt_bfm_checks {
    static_assert(S::_bitWidth == idtBvWidth<VL_S>::value, "bridge width of s != SC payload width");
    static_assert(TYW == idtBvWidth<VL_TY>::value, "bridge width of ty != SC type width");
    static_assert(TSW == idtBvWidth<VL_TS>::value, "bridge width of ts != SC typeStruct width");
    static_assert(idtPayloadW<O1, 2>() == idtBvWidth<VL_O1>::value, "bridge width of o1");
    static_assert(O2W == idtBvWidth<VL_O2>::value, "bridge width of o2");
    static_assert(O3W == idtBvWidth<VL_O3>::value, "bridge width of o3");
};

#define IDT_BFM_TPL \
template<typename S, typename TY, unsigned TYW, typename TS, unsigned TSW, \
         typename VL_S, typename VL_TY, typename VL_TS, \
         typename VL_O1 = sc_bv<2>, typename VL_O2 = sc_bv<3>, typename VL_O3 = sc_bv<5>, \
         typename O1 = std::monostate, typename O2 = std::monostate, unsigned O2W = 3, \
         typename O3 = std::monostate, unsigned O3W = 5>
#define IDT_BFM_BODY(CLS, PORT) \
class CLS: public sc_module, idt_bfm_checks<S,TY,TYW,TS,TSW,VL_S,VL_TY,VL_TS,VL_O1,VL_O2,VL_O3,O1,O2,O2W,O3,O3W> { \
public: \
    PORT<S,TY,TYW,TS,TSW,O1,O2,O2W,O3,O3W> if_p; \
    sc_port<idt_hdl_if<VL_S,VL_TY,VL_TS,VL_O1,VL_O2,VL_O3>> hdl_if_p; \
    sc_in<bool> clk; sc_in<bool> rst_n; \
    CLS(sc_module_name) {} \
};
IDT_BFM_TPL
IDT_BFM_BODY(idt_src_bfm, idt_out)
IDT_BFM_TPL
IDT_BFM_BODY(idt_dst_bfm, idt_in)
#endif
