#ifndef DUT_BASE_H
#define DUT_BASE_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "req_ack_channel.h"
#include "pySocket_tbIncludes.h"

class dutBase : public virtual blockPortBase
{
public:
    virtual ~dutBase() = default;
    // src ports
    // dut2Python_req_ack->u_pySocket: Req Ack Dut2Python interface
    req_ack_out< p2s_message_st, p2s_response_st > dut2Python_req_ack;

    // dst ports
    // u_pySocket->test_req_ack: Req Ack Test interface
    req_ack_in< p2s_message_st, p2s_response_st > test_req_ack;
    // u_pySocket->test2Python_req_ack: Req Ack Test2Python interface
    req_ack_in< p2s_message_st, p2s_response_st > test2Python_req_ack;


    dutBase(std::string name, const char * variant) :
        dut2Python_req_ack("dut2Python_req_ack")
        ,test_req_ack("test_req_ack")
        ,test2Python_req_ack("test2Python_req_ack")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        dut2Python_req_ack->setTimed(nsec, mode);
        test_req_ack->setTimed(nsec, mode);
        test2Python_req_ack->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        dut2Python_req_ack->setLogging(verbosity);
        test_req_ack->setLogging(verbosity);
        test2Python_req_ack->setLogging(verbosity);
    };
};
class dutInverted : public virtual blockPortBase
{
public:
    // src ports
    // dut2Python_req_ack->u_pySocket: Req Ack Dut2Python interface
    req_ack_in< p2s_message_st, p2s_response_st > dut2Python_req_ack;

    // dst ports
    // u_pySocket->test_req_ack: Req Ack Test interface
    req_ack_out< p2s_message_st, p2s_response_st > test_req_ack;
    // u_pySocket->test2Python_req_ack: Req Ack Test2Python interface
    req_ack_out< p2s_message_st, p2s_response_st > test2Python_req_ack;


    dutInverted(std::string name) :
        dut2Python_req_ack(("dut2Python_req_ack"+name).c_str())
        ,test_req_ack(("test_req_ack"+name).c_str())
        ,test2Python_req_ack(("test2Python_req_ack"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        dut2Python_req_ack->setTimed(nsec, mode);
        test_req_ack->setTimed(nsec, mode);
        test2Python_req_ack->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        dut2Python_req_ack->setLogging(verbosity);
        test_req_ack->setLogging(verbosity);
        test2Python_req_ack->setLogging(verbosity);
    };
};
class dutChannels
{
public:
    // src ports
    // Req Ack Dut2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > dut2Python_req_ack;

    // dst ports
    // Req Ack Test interface
    req_ack_channel< p2s_message_st, p2s_response_st > test_req_ack;
    // Req Ack Test2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > test2Python_req_ack;


    dutChannels(std::string name, std::string srcName) :
    dut2Python_req_ack(("dut2Python_req_ack"+name).c_str(), srcName)
    ,test_req_ack(("test_req_ack"+name).c_str(), srcName)
    ,test2Python_req_ack(("test2Python_req_ack"+name).c_str(), srcName)
    {};
    void bind( dutBase *a, dutInverted *b)
    {
        a->dut2Python_req_ack( dut2Python_req_ack );
        b->dut2Python_req_ack( dut2Python_req_ack );
        a->test_req_ack( test_req_ack );
        b->test_req_ack( test_req_ack );
        a->test2Python_req_ack( test2Python_req_ack );
        b->test2Python_req_ack( test2Python_req_ack );
    };
};

// GENERATED_CODE_END
#endif //DUT_BASE_H
