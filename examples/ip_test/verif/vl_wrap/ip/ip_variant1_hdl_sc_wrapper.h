#ifndef IP_VARIANT1_HDL_SC_WRAPPER_H_
#define IP_VARIANT1_HDL_SC_WRAPPER_H_

// PROTOTYPE (P1) — ASSEMBLER-OWNED per-variant SC wrapper typedef.
//
// Hand-authored in the ASSEMBLER tree. Mirrors the variant0
// variant_class_template_spec section that the generator emits into the
// sub-project's ip_hdl_sc_wrapper.h, but for variant1 and owned here.
//
// - ip_hdl_sc_wrapper.h (sub-project-owned) provides the ip_hdl_sc_wrapper<>
//   class template and pulls in ipVariantConfig.h (which defines
//   ipVariant1Config). It lives in ip/verif/vl_wrap/ip, which is a
//   VL_WRAP_DIR and therefore already a -I include dir for the SC compile.
// - Vip_variant1_hdl_sv_wrapper.h is emitted by verilator into
//   verif/vl_wrap/obj_dir (also -I'd for the VL_DUT compile).
#include "ip_hdl_sc_wrapper.h"
#include "Vip_variant1_hdl_sv_wrapper.h"

using ip_variant1_hdl_sc_wrapper = ip_hdl_sc_wrapper<Vip_variant1_hdl_sv_wrapper, ipVariant1Config>;

#endif // IP_VARIANT1_HDL_SC_WRAPPER_H_
