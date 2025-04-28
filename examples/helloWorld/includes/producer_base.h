#ifndef PRODUCER_BASE_H
#define PRODUCER_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "pop_ack_channel.h"
#include "push_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "helloWorldTopIncludes.h"

class producerBase : public virtual blockPortBase
{
public:
    virtual ~producerBase() = default;
    // src ports
    // test_rdy_vld->uConsumer: Ready Valid Test interface
    rdy_vld_out< data_st > test_rdy_vld;
    // test_req_ack->uConsumer: Req Ack Test interface
    req_ack_out< data_st, data_st > test_req_ack;
    // test_push_ack->uConsumer: Valid Ack Test interface
    push_ack_out< data_st > test_push_ack;
    // test_pop_ack->uConsumer: Ready Ack Test interface
    pop_ack_out< data_st > test_pop_ack;

    // dst ports


    producerBase(std::string name, const char * variant) :
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
class producerInverted : public virtual blockPortBase
{
public:
    // src ports
    // test_rdy_vld->uConsumer: Ready Valid Test interface
    rdy_vld_in< data_st > test_rdy_vld;
    // test_req_ack->uConsumer: Req Ack Test interface
    req_ack_in< data_st, data_st > test_req_ack;
    // test_push_ack->uConsumer: Valid Ack Test interface
    push_ack_in< data_st > test_push_ack;
    // test_pop_ack->uConsumer: Ready Ack Test interface
    pop_ack_in< data_st > test_pop_ack;

    // dst ports


    producerInverted(std::string name) :
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
class producerChannels
{
public:
    // src ports
    //   test_rdy_vld
    rdy_vld_channel< data_st > test_rdy_vld;
    //   test_req_ack
    req_ack_channel< data_st, data_st > test_req_ack;
    //   test_push_ack
    push_ack_channel< data_st > test_push_ack;
    //   test_pop_ack
    pop_ack_channel< data_st > test_pop_ack;

    // dst ports


    producerChannels(std::string name, std::string srcName) :
    test_rdy_vld(("test_rdy_vld"+name).c_str(), srcName)
    ,test_req_ack(("test_req_ack"+name).c_str(), srcName)
    ,test_push_ack(("test_push_ack"+name).c_str(), srcName)
    ,test_pop_ack(("test_pop_ack"+name).c_str(), srcName)
    {};
    void bind( producerBase *a, producerInverted *b)
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

#endif //PRODUCER_BASE_H
