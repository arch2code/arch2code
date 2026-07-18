#ifndef VL_WRAP_H_
#define VL_WRAP_H_

// GENERATED_CODE_PARAM --hierarchy
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=factory_register_vl_incl
#include "ipLeaf_hdl_sc_wrapper.h"
#include "ip_hdl_sc_wrapper.h"
#include "src_hdl_sc_wrapper.h"
#include "ipBridge_hdl_sc_wrapper.h"
#include "bridgeApbDecode_hdl_sc_wrapper.h"
#include "ip_top_hdl_sc_wrapper.h"
#include "apbDecode_hdl_sc_wrapper.h"
// GENERATED_CODE_END

// PROTOTYPE (P1) — assembler-owned variant1 SC wrapper typedef.
// The generator already emits the variant1 factory registration into
// vl_wrap.cpp (ip_variant1_hdl_sc_wrapper::registerBlock_("variant1")) but does
// NOT emit the ip_variant1_hdl_sc_wrapper typedef anywhere. This hand-authored
// include supplies it from the assembler tree. In P2 the generator would emit
// this include into the factory_register_vl_incl generated region above.
#include "ip_variant1_hdl_sc_wrapper.h"

#endif // VL_WRAP_H_
