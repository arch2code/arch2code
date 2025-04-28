#ifndef PORTBASE_H
#define PORTBASE_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "trackerBase.h"
#include "log.h"
#include "blockBase.h"
#include "stringPingPong.h"

enum portType { PORTTYPE_IN, PORTTYPE_OUT, PORTTYPE_ANY };
// common functions to be overridden in the implementation
struct portBase  
{
public:
    virtual void setMultiDriver(std::string name, std::function<std::string(const uint64_t &value)> prt = nullptr) = 0;
    virtual std::shared_ptr<trackerBase> getTracker(void) = 0;
    virtual void setTeeBusy(bool busy) = 0;
    virtual void setTandem(void) = 0;
    virtual void setLogging(verbosity_e verbosity) = 0;
    virtual void setTimed(int nsec, timedDelayMode mode) = 0;
    virtual void setCycleTransaction(portType type_=PORTTYPE_ANY) {};
    virtual void setTimedDelayPtr(std::shared_ptr<timedDelayBase> pTimedDelay) {};
    virtual portBase* getPort(void) { return this; }
    virtual void setLogQueue(std::shared_ptr<stringPingPong> logQueue) {};
};


#endif //(PORTBASE_H)
