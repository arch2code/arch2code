#ifndef CONSUMER_BASE_H
#define CONSUMER_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "helloWorldTopIncludes.h"

class consumerBase : public virtual blockPortBase
{
public:
    virtual ~consumerBase() = default;
    // dst ports
    // uProducer->test_rdy_vld: Ready Valid Test interface
    rdy_vld_in< data_st > test_rdy_vld;
    // uProducer->test_req_ack: Req Ack Test interface
    req_ack_in< data_st, data_st > test_req_ack;
    // uProducer->test_push_ack: Valid Ack Test interface
    push_ack_in< data_st > test_push_ack;
    // uProducer->test_pop_ack: Ready Ack Test interface
    pop_ack_in< data_st > test_pop_ack;


    consumerBase(std::string name, const char * variant) :
        test_rdy_vld("test_rdy_vld")
        ,test_req_ack("test_req_ack")
        ,test_push_ack("test_push_ack")
        ,test_pop_ack("test_pop_ack")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test_rdy_vld->setTimed(nsec, mode);
        test_req_ack->setTimed(nsec, mode);
        test_push_ack->setTimed(nsec, mode);
        test_pop_ack->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test_rdy_vld->setLogging(verbosity);
        test_req_ack->setLogging(verbosity);
        test_push_ack->setLogging(verbosity);
        test_pop_ack->setLogging(verbosity);
    };
};
class consumerInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uProducer->test_rdy_vld: Ready Valid Test interface
    rdy_vld_out< data_st > test_rdy_vld;
    // uProducer->test_req_ack: Req Ack Test interface
    req_ack_out< data_st, data_st > test_req_ack;
    // uProducer->test_push_ack: Valid Ack Test interface
    push_ack_out< data_st > test_push_ack;
    // uProducer->test_pop_ack: Ready Ack Test interface
    pop_ack_out< data_st > test_pop_ack;


    consumerInverted(std::string name) :
        test_rdy_vld(("test_rdy_vld"+name).c_str())
        ,test_req_ack(("test_req_ack"+name).c_str())
        ,test_push_ack(("test_push_ack"+name).c_str())
        ,test_pop_ack(("test_pop_ack"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        test_rdy_vld->setTimed(nsec, mode);
        test_req_ack->setTimed(nsec, mode);
        test_push_ack->setTimed(nsec, mode);
        test_pop_ack->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        test_rdy_vld->setLogging(verbosity);
        test_req_ack->setLogging(verbosity);
        test_push_ack->setLogging(verbosity);
        test_pop_ack->setLogging(verbosity);
    };
};
class consumerChannels
{
public:
    // dst ports
    // Ready Valid Test interface
    rdy_vld_channel< data_st > test_rdy_vld;
    // Req Ack Test interface
    req_ack_channel< data_st, data_st > test_req_ack;
    // Valid Ack Test interface
    push_ack_channel< data_st > test_push_ack;
    // Ready Ack Test interface
    pop_ack_channel< data_st > test_pop_ack;


    consumerChannels(std::string name, std::string srcName) :
    test_rdy_vld(("test_rdy_vld"+name).c_str(), srcName)
    ,test_req_ack(("test_req_ack"+name).c_str(), srcName)
    ,test_push_ack(("test_push_ack"+name).c_str(), srcName)
    ,test_pop_ack(("test_pop_ack"+name).c_str(), srcName)
    {};
    void bind( consumerBase *a, consumerInverted *b)
    {
        a->test_rdy_vld( test_rdy_vld );
        b->test_rdy_vld( test_rdy_vld );
        a->test_req_ack( test_req_ack );
        b->test_req_ack( test_req_ack );
        a->test_push_ack( test_push_ack );
        b->test_push_ack( test_push_ack );
        a->test_pop_ack( test_pop_ack );
        b->test_pop_ack( test_pop_ack );
    };
};

// GENERATED_CODE_END

#endif //CONSUMER_BASE_H
