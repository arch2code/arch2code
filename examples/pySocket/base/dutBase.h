#ifndef DUT_BASE_H
#define DUT_BASE_H

//

#include "systemc.h"

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "req_ack_channel.h"
#include "pySocketIncludes.h"

class dutBase : public virtual blockPortBase
{
public:
    virtual ~dutBase() = default;
    // dst ports
    // u_pySocket->test_req_ack: Req Ack Test interface
    req_ack_in< p2s_message_st, p2s_response_st > test_req_ack;


    dutBase(std::string name, const char * variant) :
        test_req_ack("test_req_ack")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test_req_ack->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test_req_ack->setLogging(verbosity);
    };
};
class dutInverted : public virtual blockPortBase
{
public:
    // dst ports
    // u_pySocket->test_req_ack: Req Ack Test interface
    req_ack_out< p2s_message_st, p2s_response_st > test_req_ack;


    dutInverted(std::string name) :
        test_req_ack(("test_req_ack"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test_req_ack->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test_req_ack->setLogging(verbosity);
    };
};
class dutChannels
{
public:
    // dst ports
    // Req Ack Test interface
    req_ack_channel< p2s_message_st, p2s_response_st > test_req_ack;


    dutChannels(std::string name, std::string srcName) :
    test_req_ack(("test_req_ack"+name).c_str(), srcName)
    {};
    void bind( dutBase *a, dutInverted *b)
    {
        a->test_req_ack( test_req_ack );
        b->test_req_ack( test_req_ack );
    };
};

// GENERATED_CODE_END
#endif //DUT_BASE_H
