#ifndef PYSOCKET_BASE_H
#define PYSOCKET_BASE_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "req_ack_channel.h"
#include "pySocket_tbIncludes.h"

class pySocketBase : public virtual blockPortBase
{
public:
    virtual ~pySocketBase() = default;
    // src ports
    // test_req_ack->u_dut: Req Ack Test interface
    req_ack_out< p2s_message_st, p2s_response_st > test_req_ack;
    // test2Python_req_ack->u_dut: Req Ack Test2Python interface
    req_ack_out< p2s_message_st, p2s_response_st > test2Python_req_ack;

    // dst ports
    // u_dut->dut2Python_req_ack: Req Ack Dut2Python interface
    req_ack_in< p2s_message_st, p2s_response_st > dut2Python_req_ack;


    pySocketBase(std::string name, const char * variant) :
        test_req_ack("test_req_ack")
        ,test2Python_req_ack("test2Python_req_ack")
        ,dut2Python_req_ack("dut2Python_req_ack")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test_req_ack->setTimed(nsec, mode);
        test2Python_req_ack->setTimed(nsec, mode);
        dut2Python_req_ack->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test_req_ack->setLogging(verbosity);
        test2Python_req_ack->setLogging(verbosity);
        dut2Python_req_ack->setLogging(verbosity);
    };
};
class pySocketInverted : public virtual blockPortBase
{
public:
    // src ports
    // test_req_ack->u_dut: Req Ack Test interface
    req_ack_in< p2s_message_st, p2s_response_st > test_req_ack;
    // test2Python_req_ack->u_dut: Req Ack Test2Python interface
    req_ack_in< p2s_message_st, p2s_response_st > test2Python_req_ack;

    // dst ports
    // u_dut->dut2Python_req_ack: Req Ack Dut2Python interface
    req_ack_out< p2s_message_st, p2s_response_st > dut2Python_req_ack;


    pySocketInverted(std::string name) :
        test_req_ack(("test_req_ack"+name).c_str())
        ,test2Python_req_ack(("test2Python_req_ack"+name).c_str())
        ,dut2Python_req_ack(("dut2Python_req_ack"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test_req_ack->setTimed(nsec, mode);
        test2Python_req_ack->setTimed(nsec, mode);
        dut2Python_req_ack->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test_req_ack->setLogging(verbosity);
        test2Python_req_ack->setLogging(verbosity);
        dut2Python_req_ack->setLogging(verbosity);
    };
};
class pySocketChannels
{
public:
    // src ports
    // Req Ack Test interface
    req_ack_channel< p2s_message_st, p2s_response_st > test_req_ack;
    // Req Ack Test2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > test2Python_req_ack;

    // dst ports
    // Req Ack Dut2Python interface
    req_ack_channel< p2s_message_st, p2s_response_st > dut2Python_req_ack;


    pySocketChannels(std::string name, std::string srcName) :
    test_req_ack(("test_req_ack"+name).c_str(), srcName)
    ,test2Python_req_ack(("test2Python_req_ack"+name).c_str(), srcName)
    ,dut2Python_req_ack(("dut2Python_req_ack"+name).c_str(), srcName)
    {};
    void bind( pySocketBase *a, pySocketInverted *b)
    {
        a->test_req_ack( test_req_ack );
        b->test_req_ack( test_req_ack );
        a->test2Python_req_ack( test2Python_req_ack );
        b->test2Python_req_ack( test2Python_req_ack );
        a->dut2Python_req_ack( dut2Python_req_ack );
        b->dut2Python_req_ack( dut2Python_req_ack );
    };
};

// GENERATED_CODE_END
#endif //PYSOCKET_BASE_H
