#ifndef IDTH_CHANNEL_H
#define IDTH_CHANNEL_H
#include <variant>
#include "clog2.h"
#include "rdy_vld_channel.h"
template<typename S, typename TS, unsigned TSW, typename O2 = std::monostate, unsigned O2W = 3>
using idth_channel = rdy_vld_channel<S>;
template<typename S, typename TS, unsigned TSW, typename O2 = std::monostate, unsigned O2W = 3>
using idth_in = rdy_vld_in<S>;
template<typename S, typename TS, unsigned TSW, typename O2 = std::monostate, unsigned O2W = 3>
using idth_out = rdy_vld_out<S>;
#endif
