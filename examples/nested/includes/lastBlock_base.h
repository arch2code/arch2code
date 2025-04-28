#ifndef LASTBLOCK_BASE_H
#define LASTBLOCK_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=lastBlock
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "rdy_vld_channel.h"
#include "nestedTopIncludes.h"

class lastBlockBase : public virtual blockPortBase
{
public:
    virtual ~lastBlockBase() = default;
    // src ports
    // gamma->uFirst: Test interface gamma
    rdy_vld_out< test_st > response;

    // dst ports
    // uSecond->beta: Test interface beta
    rdy_vld_in< test_st > beta;


    lastBlockBase(std::string name, const char * variant) :
        response("response")
        ,beta("beta")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        response->setTimed(nsec, mode);
        beta->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        response->setLogging(verbosity);
        beta->setLogging(verbosity);
    };
};
class lastBlockInverted : public virtual blockPortBase
{
public:
    // src ports
    // gamma->uFirst: Test interface gamma
    rdy_vld_in< test_st > response;

    // dst ports
    // uSecond->beta: Test interface beta
    rdy_vld_out< test_st > beta;


    lastBlockInverted(std::string name) :
        response(("response"+name).c_str())
        ,beta(("beta"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        response->setTimed(nsec, mode);
        beta->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        response->setLogging(verbosity);
        beta->setLogging(verbosity);
    };
};
class lastBlockChannels
{
public:
    // src ports
    //   gamma
    rdy_vld_channel< test_st > response;

    // dst ports
    //   beta
    rdy_vld_channel< test_st > beta;


    lastBlockChannels(std::string name, std::string srcName) :
    response(("response"+name).c_str(), srcName)
    ,beta(("beta"+name).c_str(), srcName)
    {};
    void bind( lastBlockBase *a, lastBlockInverted *b)
    {
        a->response( response );
        b->response( response );
        a->beta( beta );
        b->beta( beta );
    };
};

// GENERATED_CODE_END

#endif //LASTBLOCK_BASE_H
