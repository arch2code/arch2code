//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=producer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module simple_producer.base;
import simple;
using namespace simple_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class producerBase : public virtual blockPortBase
{
public:
    virtual ~producerBase() = default;
    // src ports
    // tag->u_consumer: tag interface
    push_ack_out< tag_st > tag0;
    // tag->u_consumer: tag interface
    push_ack_out< tag_st > tag1;


    producerBase(std::string name, const char * variant) :
        tag0("tag0")
        ,tag1("tag1")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        tag0->setTimed(nsec, mode);
        tag1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        tag0->setLogging(verbosity);
        tag1->setLogging(verbosity);
    };
};
export class producerInverted : public virtual blockPortBase
{
public:
    // src ports
    // tag->u_consumer: tag interface
    push_ack_in< tag_st > tag0;
    // tag->u_consumer: tag interface
    push_ack_in< tag_st > tag1;


    producerInverted(std::string name) :
        tag0(("tag0"+name).c_str())
        ,tag1(("tag1"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        tag0->setTimed(nsec, mode);
        tag1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        tag0->setLogging(verbosity);
        tag1->setLogging(verbosity);
    };
};
export class producerChannels
{
public:
    // src ports
    // tag interface
    push_ack_channel< tag_st > tag0;
    // tag interface
    push_ack_channel< tag_st > tag1;


    producerChannels(std::string name, std::string srcName) :
    tag0(("tag0"+name).c_str(), srcName)
    ,tag1(("tag1"+name).c_str(), srcName)
    {};
    void bind( producerBase *a, producerInverted *b)
    {
        a->tag0( tag0 );
        b->tag0( tag0 );
        a->tag1( tag1 );
        b->tag1( tag1 );
    };
};

// GENERATED_CODE_END
