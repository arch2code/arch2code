//

// GENERATED_CODE_PARAM --block=dut --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "axi4_stream_channel.h"
#include "notify_ack_channel.h"
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"

export module pySocket_dut.base;
import pySocket_tb;
using namespace pySocket_tb_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class dutBase : public virtual blockPortBase
{
public:
    virtual ~dutBase() = default;
    // src ports
    // dut2Python_req_ack->u_pySocket: Req Ack Dut2Python interface
    req_ack_out< p2s_message_st, p2s_response_st > dut2Python_req_ack;
    // dut2Python_push_ack->u_pySocket: DUT-initiated push into Python
    push_ack_out< p2s_message_st > dut2Python_push_ack;
    // dut2Python_pop_ack->u_pySocket: DUT-initiated pop of data derived from the DUT push
    pop_ack_out< p2s_response_st > dut2Python_pop_ack;
    // dut2Python_notify_ack->u_pySocket: DUT-initiated notify into Python
    notify_ack_out< > dut2Python_notify_ack;
    // dut2Python_rdy_vld->u_pySocket: DUT-initiated rdy_vld write into Python
    rdy_vld_out< p2s_message_st > dut2Python_rdy_vld;
    // dut2Python_axi4_stream->u_pySocket: DUT-initiated AXI4-Stream into Python
    axi4_stream_out< p2s_message_st, axis_tid_st, axis_tdest_st > dut2Python_axi4_stream;

    // dst ports
    // u_pySocket->test_req_ack: Req Ack Test interface
    req_ack_in< p2s_message_st, p2s_response_st > test_req_ack;
    // u_pySocket->test2Python_req_ack: Req Ack Test2Python interface
    req_ack_in< p2s_message_st, p2s_response_st > test2Python_req_ack;
    // u_pySocket->test_push_ack: Python-initiated push into the DUT
    push_ack_in< p2s_message_st > test_push_ack;
    // u_pySocket->test_pop_ack: Python-initiated pop of data derived from the last push
    pop_ack_in< p2s_response_st > test_pop_ack;
    // u_pySocket->test_notify_ack: Python-initiated notify into the DUT
    notify_ack_in< > test_notify_ack;
    // u_pySocket->test_rdy_vld: Python-initiated rdy_vld write into the DUT
    rdy_vld_in< p2s_message_st > test_rdy_vld;
    // u_pySocket->test_axi4_stream: Python-initiated AXI4-Stream into the DUT
    axi4_stream_in< p2s_message_st, axis_tid_st, axis_tdest_st > test_axi4_stream;


    dutBase(std::string name, const char * variant) :
        dut2Python_req_ack("dut2Python_req_ack")
        ,dut2Python_push_ack("dut2Python_push_ack")
        ,dut2Python_pop_ack("dut2Python_pop_ack")
        ,dut2Python_notify_ack("dut2Python_notify_ack")
        ,dut2Python_rdy_vld("dut2Python_rdy_vld")
        ,dut2Python_axi4_stream("dut2Python_axi4_stream")
        ,test_req_ack("test_req_ack")
        ,test2Python_req_ack("test2Python_req_ack")
        ,test_push_ack("test_push_ack")
        ,test_pop_ack("test_pop_ack")
        ,test_notify_ack("test_notify_ack")
        ,test_rdy_vld("test_rdy_vld")
        ,test_axi4_stream("test_axi4_stream")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        dut2Python_req_ack->setTimed(nsec, mode);
        dut2Python_push_ack->setTimed(nsec, mode);
        dut2Python_pop_ack->setTimed(nsec, mode);
        dut2Python_notify_ack->setTimed(nsec, mode);
        dut2Python_rdy_vld->setTimed(nsec, mode);
        dut2Python_axi4_stream->setTimed(nsec, mode);
        test_req_ack->setTimed(nsec, mode);
        test2Python_req_ack->setTimed(nsec, mode);
        test_push_ack->setTimed(nsec, mode);
        test_pop_ack->setTimed(nsec, mode);
        test_notify_ack->setTimed(nsec, mode);
        test_rdy_vld->setTimed(nsec, mode);
        test_axi4_stream->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        dut2Python_req_ack->setLogging(verbosity);
        dut2Python_push_ack->setLogging(verbosity);
        dut2Python_pop_ack->setLogging(verbosity);
        dut2Python_notify_ack->setLogging(verbosity);
        dut2Python_rdy_vld->setLogging(verbosity);
        dut2Python_axi4_stream->setLogging(verbosity);
        test_req_ack->setLogging(verbosity);
        test2Python_req_ack->setLogging(verbosity);
        test_push_ack->setLogging(verbosity);
        test_pop_ack->setLogging(verbosity);
        test_notify_ack->setLogging(verbosity);
        test_rdy_vld->setLogging(verbosity);
        test_axi4_stream->setLogging(verbosity);
    };
};
export class dutInverted : public virtual blockPortBase
{
public:
    // src ports
    // dut2Python_req_ack->u_pySocket: Req Ack Dut2Python interface
    req_ack_in< p2s_message_st, p2s_response_st > dut2Python_req_ack;
    // dut2Python_push_ack->u_pySocket: DUT-initiated push into Python
    push_ack_in< p2s_message_st > dut2Python_push_ack;
    // dut2Python_pop_ack->u_pySocket: DUT-initiated pop of data derived from the DUT push
    pop_ack_in< p2s_response_st > dut2Python_pop_ack;
    // dut2Python_notify_ack->u_pySocket: DUT-initiated notify into Python
    notify_ack_in< > dut2Python_notify_ack;
    // dut2Python_rdy_vld->u_pySocket: DUT-initiated rdy_vld write into Python
    rdy_vld_in< p2s_message_st > dut2Python_rdy_vld;
    // dut2Python_axi4_stream->u_pySocket: DUT-initiated AXI4-Stream into Python
    axi4_stream_in< p2s_message_st, axis_tid_st, axis_tdest_st > dut2Python_axi4_stream;

    // dst ports
    // u_pySocket->test_req_ack: Req Ack Test interface
    req_ack_out< p2s_message_st, p2s_response_st > test_req_ack;
    // u_pySocket->test2Python_req_ack: Req Ack Test2Python interface
    req_ack_out< p2s_message_st, p2s_response_st > test2Python_req_ack;
    // u_pySocket->test_push_ack: Python-initiated push into the DUT
    push_ack_out< p2s_message_st > test_push_ack;
    // u_pySocket->test_pop_ack: Python-initiated pop of data derived from the last push
    pop_ack_out< p2s_response_st > test_pop_ack;
    // u_pySocket->test_notify_ack: Python-initiated notify into the DUT
    notify_ack_out< > test_notify_ack;
    // u_pySocket->test_rdy_vld: Python-initiated rdy_vld write into the DUT
    rdy_vld_out< p2s_message_st > test_rdy_vld;
    // u_pySocket->test_axi4_stream: Python-initiated AXI4-Stream into the DUT
    axi4_stream_out< p2s_message_st, axis_tid_st, axis_tdest_st > test_axi4_stream;


    dutInverted(std::string name) :
        dut2Python_req_ack(("dut2Python_req_ack"+name).c_str())
        ,dut2Python_push_ack(("dut2Python_push_ack"+name).c_str())
        ,dut2Python_pop_ack(("dut2Python_pop_ack"+name).c_str())
        ,dut2Python_notify_ack(("dut2Python_notify_ack"+name).c_str())
        ,dut2Python_rdy_vld(("dut2Python_rdy_vld"+name).c_str())
        ,dut2Python_axi4_stream(("dut2Python_axi4_stream"+name).c_str())
        ,test_req_ack(("test_req_ack"+name).c_str())
        ,test2Python_req_ack(("test2Python_req_ack"+name).c_str())
        ,test_push_ack(("test_push_ack"+name).c_str())
        ,test_pop_ack(("test_pop_ack"+name).c_str())
        ,test_notify_ack(("test_notify_ack"+name).c_str())
        ,test_rdy_vld(("test_rdy_vld"+name).c_str())
        ,test_axi4_stream(("test_axi4_stream"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        dut2Python_req_ack->setTimed(nsec, mode);
        dut2Python_push_ack->setTimed(nsec, mode);
        dut2Python_pop_ack->setTimed(nsec, mode);
        dut2Python_notify_ack->setTimed(nsec, mode);
        dut2Python_rdy_vld->setTimed(nsec, mode);
        dut2Python_axi4_stream->setTimed(nsec, mode);
        test_req_ack->setTimed(nsec, mode);
        test2Python_req_ack->setTimed(nsec, mode);
        test_push_ack->setTimed(nsec, mode);
        test_pop_ack->setTimed(nsec, mode);
        test_notify_ack->setTimed(nsec, mode);
        test_rdy_vld->setTimed(nsec, mode);
        test_axi4_stream->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        dut2Python_req_ack->setLogging(verbosity);
        dut2Python_push_ack->setLogging(verbosity);
        dut2Python_pop_ack->setLogging(verbosity);
        dut2Python_notify_ack->setLogging(verbosity);
        dut2Python_rdy_vld->setLogging(verbosity);
        dut2Python_axi4_stream->setLogging(verbosity);
        test_req_ack->setLogging(verbosity);
        test2Python_req_ack->setLogging(verbosity);
        test_push_ack->setLogging(verbosity);
        test_pop_ack->setLogging(verbosity);
        test_notify_ack->setLogging(verbosity);
        test_rdy_vld->setLogging(verbosity);
        test_axi4_stream->setLogging(verbosity);
    };
};
export class dutChannels
{
public:
    // src ports
    // Req Ack Dut2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > dut2Python_req_ack;
    // DUT-initiated push into Python
    push_ack_channel< p2s_message_st > dut2Python_push_ack;
    // DUT-initiated pop of data derived from the DUT push
    pop_ack_channel< p2s_response_st > dut2Python_pop_ack;
    // DUT-initiated notify into Python
    notify_ack_channel< > dut2Python_notify_ack;
    // DUT-initiated rdy_vld write into Python
    rdy_vld_channel< p2s_message_st > dut2Python_rdy_vld;
    // DUT-initiated AXI4-Stream into Python
    axi4_stream_channel< p2s_message_st, axis_tid_st, axis_tdest_st > dut2Python_axi4_stream;

    // dst ports
    // Req Ack Test interface
    req_ack_channel< p2s_message_st, p2s_response_st > test_req_ack;
    // Req Ack Test2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > test2Python_req_ack;
    // Python-initiated push into the DUT
    push_ack_channel< p2s_message_st > test_push_ack;
    // Python-initiated pop of data derived from the last push
    pop_ack_channel< p2s_response_st > test_pop_ack;
    // Python-initiated notify into the DUT
    notify_ack_channel< > test_notify_ack;
    // Python-initiated rdy_vld write into the DUT
    rdy_vld_channel< p2s_message_st > test_rdy_vld;
    // Python-initiated AXI4-Stream into the DUT
    axi4_stream_channel< p2s_message_st, axis_tid_st, axis_tdest_st > test_axi4_stream;


    dutChannels(std::string name, std::string srcName) :
    dut2Python_req_ack(("dut2Python_req_ack"+name).c_str(), srcName)
    ,dut2Python_push_ack(("dut2Python_push_ack"+name).c_str(), srcName)
    ,dut2Python_pop_ack(("dut2Python_pop_ack"+name).c_str(), srcName)
    ,dut2Python_notify_ack(("dut2Python_notify_ack"+name).c_str(), srcName)
    ,dut2Python_rdy_vld(("dut2Python_rdy_vld"+name).c_str(), srcName)
    ,dut2Python_axi4_stream(("dut2Python_axi4_stream"+name).c_str(), srcName, "api_list_size", 16, "")
    ,test_req_ack(("test_req_ack"+name).c_str(), srcName)
    ,test2Python_req_ack(("test2Python_req_ack"+name).c_str(), srcName)
    ,test_push_ack(("test_push_ack"+name).c_str(), srcName)
    ,test_pop_ack(("test_pop_ack"+name).c_str(), srcName)
    ,test_notify_ack(("test_notify_ack"+name).c_str(), srcName)
    ,test_rdy_vld(("test_rdy_vld"+name).c_str(), srcName)
    ,test_axi4_stream(("test_axi4_stream"+name).c_str(), srcName, "api_list_size", 16, "")
    {};
    void bind( dutBase *a, dutInverted *b)
    {
        a->dut2Python_req_ack( dut2Python_req_ack );
        b->dut2Python_req_ack( dut2Python_req_ack );
        a->dut2Python_push_ack( dut2Python_push_ack );
        b->dut2Python_push_ack( dut2Python_push_ack );
        a->dut2Python_pop_ack( dut2Python_pop_ack );
        b->dut2Python_pop_ack( dut2Python_pop_ack );
        a->dut2Python_notify_ack( dut2Python_notify_ack );
        b->dut2Python_notify_ack( dut2Python_notify_ack );
        a->dut2Python_rdy_vld( dut2Python_rdy_vld );
        b->dut2Python_rdy_vld( dut2Python_rdy_vld );
        a->dut2Python_axi4_stream( dut2Python_axi4_stream );
        b->dut2Python_axi4_stream( dut2Python_axi4_stream );
        a->test_req_ack( test_req_ack );
        b->test_req_ack( test_req_ack );
        a->test2Python_req_ack( test2Python_req_ack );
        b->test2Python_req_ack( test2Python_req_ack );
        a->test_push_ack( test_push_ack );
        b->test_push_ack( test_push_ack );
        a->test_pop_ack( test_pop_ack );
        b->test_pop_ack( test_pop_ack );
        a->test_notify_ack( test_notify_ack );
        b->test_notify_ack( test_notify_ack );
        a->test_rdy_vld( test_rdy_vld );
        b->test_rdy_vld( test_rdy_vld );
        a->test_axi4_stream( test_axi4_stream );
        b->test_axi4_stream( test_axi4_stream );
    };
};

// GENERATED_CODE_END
