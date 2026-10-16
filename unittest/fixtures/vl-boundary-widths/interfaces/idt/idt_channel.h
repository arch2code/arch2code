#ifndef IDT_CHANNEL_H
#define IDT_CHANNEL_H
#include <variant>
#include "clog2.h"
#include "rdy_vld_channel.h"
// Test protocol: the channel carries the required struct S only; the other
// positional arguments exist so the generator's argument list is exercised.
template<typename S, typename TY, unsigned TYW, typename TS, unsigned TSW,
         typename O1 = std::monostate, typename O2 = std::monostate, unsigned O2W = 3,
         typename O3 = std::monostate, unsigned O3W = 5>
using idt_channel = rdy_vld_channel<S>;
template<typename S, typename TY, unsigned TYW, typename TS, unsigned TSW,
         typename O1 = std::monostate, typename O2 = std::monostate, unsigned O2W = 3,
         typename O3 = std::monostate, unsigned O3W = 5>
using idt_in = rdy_vld_in<S>;
template<typename S, typename TY, unsigned TYW, typename TS, unsigned TSW,
         typename O1 = std::monostate, typename O2 = std::monostate, unsigned O2W = 3,
         typename O3 = std::monostate, unsigned O3W = 5>
using idt_out = rdy_vld_out<S>;
#endif
