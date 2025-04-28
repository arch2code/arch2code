#ifndef INANDOUT_BASE_H
#define INANDOUT_BASE_H

#include "systemc.h"

// GENERATED_CODE_PARAM --block=inAndOut
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "pop_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "inAndOutIncludes.h"

class inAndOutBase : public virtual blockPortBase
{
public:
    virtual ~inAndOutBase() = default;
    // src ports
    // aStuffIf->uInAndOut0: An interface of type rdyVld
    rdy_vld_out< aSt > aOut;
    // bStuffIf->uInAndOut0: An interface of type reqAck
    req_ack_out< bSt, bBSt > bOut;
    // dStuffIf->uInAndOut0: An interface of type rdyAck
    pop_ack_out< dSt > dOut;

    // dst ports
    // uInAndOut0->aStuffIf: An interface of type rdyVld
    rdy_vld_in< aSt > aIn;
    // uInAndOut0->bStuffIf: An interface of type reqAck
    req_ack_in< bSt, bBSt > bIn;
    // uInAndOut0->dStuffIf: An interface of type rdyAck
    pop_ack_in< dSt > dIn;


    inAndOutBase(std::string name, const char * variant) :
        aOut("aOut")
        ,bOut("bOut")
        ,dOut("dOut")
        ,aIn("aIn")
        ,bIn("bIn")
        ,dIn("dIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        aOut->setTimed(nsec, mode);
        bOut->setTimed(nsec, mode);
        dOut->setTimed(nsec, mode);
        aIn->setTimed(nsec, mode);
        bIn->setTimed(nsec, mode);
        dIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        aOut->setLogging(verbosity);
        bOut->setLogging(verbosity);
        dOut->setLogging(verbosity);
        aIn->setLogging(verbosity);
        bIn->setLogging(verbosity);
        dIn->setLogging(verbosity);
    };
};
class inAndOutInverted : public virtual blockPortBase
{
public:
    // src ports
    // aStuffIf->uInAndOut0: An interface of type rdyVld
    rdy_vld_in< aSt > aOut;
    // bStuffIf->uInAndOut0: An interface of type reqAck
    req_ack_in< bSt, bBSt > bOut;
    // dStuffIf->uInAndOut0: An interface of type rdyAck
    pop_ack_in< dSt > dOut;

    // dst ports
    // uInAndOut0->aStuffIf: An interface of type rdyVld
    rdy_vld_out< aSt > aIn;
    // uInAndOut0->bStuffIf: An interface of type reqAck
    req_ack_out< bSt, bBSt > bIn;
    // uInAndOut0->dStuffIf: An interface of type rdyAck
    pop_ack_out< dSt > dIn;


    inAndOutInverted(std::string name) :
        aOut(("aOut"+name).c_str())
        ,bOut(("bOut"+name).c_str())
        ,dOut(("dOut"+name).c_str())
        ,aIn(("aIn"+name).c_str())
        ,bIn(("bIn"+name).c_str())
        ,dIn(("dIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        aOut->setTimed(nsec, mode);
        bOut->setTimed(nsec, mode);
        dOut->setTimed(nsec, mode);
        aIn->setTimed(nsec, mode);
        bIn->setTimed(nsec, mode);
        dIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        aOut->setLogging(verbosity);
        bOut->setLogging(verbosity);
        dOut->setLogging(verbosity);
        aIn->setLogging(verbosity);
        bIn->setLogging(verbosity);
        dIn->setLogging(verbosity);
    };
};
class inAndOutChannels
{
public:
    // src ports
    //   aStuffIf
    rdy_vld_channel< aSt > aOut;
    //   bStuffIf
    req_ack_channel< bSt, bBSt > bOut;
    //   dStuffIf
    pop_ack_channel< dSt > dOut;

    // dst ports
    //   aStuffIf
    rdy_vld_channel< aSt > aIn;
    //   bStuffIf
    req_ack_channel< bSt, bBSt > bIn;
    //   dStuffIf
    pop_ack_channel< dSt > dIn;


    inAndOutChannels(std::string name, std::string srcName) :
    aOut(("aOut"+name).c_str(), srcName)
    ,bOut(("bOut"+name).c_str(), srcName)
    ,dOut(("dOut"+name).c_str(), srcName)
    ,aIn(("aIn"+name).c_str(), srcName)
    ,bIn(("bIn"+name).c_str(), srcName)
    ,dIn(("dIn"+name).c_str(), srcName)
    {};
    void bind( inAndOutBase *a, inAndOutInverted *b)
    {
        a->aOut( aOut );
        b->aOut( aOut );
        a->bOut( bOut );
        b->bOut( bOut );
        a->dOut( dOut );
        b->dOut( dOut );
        a->aIn( aIn );
        b->aIn( aIn );
        a->bIn( bIn );
        b->bIn( bIn );
        a->dIn( dIn );
        b->dIn( dIn );
    };
};

// GENERATED_CODE_END


#endif //INANDOUT_BASE_H
