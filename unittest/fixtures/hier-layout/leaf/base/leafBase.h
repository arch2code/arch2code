#ifndef LEAF_BASE_H
#define LEAF_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=leaf
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "push_ack_channel.h"
import core;
using namespace core_ns;

class leafBase : public virtual blockPortBase
{
public:
    virtual ~leafBase() = default;
    // src ports
    // datIf->u_leaf1: data interface
    push_ack_out< dat_st > dOut;

    // dst ports
    // u_gen->datIf: data interface
    push_ack_in< dat_st > dIn;


    leafBase(std::string name, const char * variant) :
        dOut("dOut")
        ,dIn("dIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        dOut->setTimed(nsec, mode);
        dIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        dOut->setLogging(verbosity);
        dIn->setLogging(verbosity);
    };
};
class leafInverted : public virtual blockPortBase
{
public:
    // src ports
    // datIf->u_leaf1: data interface
    push_ack_in< dat_st > dOut;

    // dst ports
    // u_gen->datIf: data interface
    push_ack_out< dat_st > dIn;


    leafInverted(std::string name) :
        dOut(("dOut"+name).c_str())
        ,dIn(("dIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        dOut->setTimed(nsec, mode);
        dIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        dOut->setLogging(verbosity);
        dIn->setLogging(verbosity);
    };
};
class leafChannels
{
public:
    // src ports
    // data interface
    push_ack_channel< dat_st > dOut;

    // dst ports
    // data interface
    push_ack_channel< dat_st > dIn;


    leafChannels(std::string name, std::string srcName) :
    dOut(("dOut"+name).c_str(), srcName)
    ,dIn(("dIn"+name).c_str(), srcName)
    {};
    void bind( leafBase *a, leafInverted *b)
    {
        a->dOut( dOut );
        b->dOut( dOut );
        a->dIn( dIn );
        b->dIn( dIn );
    };
};

// GENERATED_CODE_END
#endif //LEAF_BASE_H
