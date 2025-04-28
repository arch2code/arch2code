#ifndef INTERFACEBASE_H
#define INTERFACEBASE_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "logging.h"
#include "tracker.h"
#include "synchLock.h"
#include <string>
#include "timedDelay.h"
#include "stringPingPong.h"

enum INTERFACE_AUTO_MODE { INTERFACE_AUTO_OFF, INTERFACE_AUTO_ALLOC, INTERFACE_AUTO_DEALLOC };

struct interfaceBase
{
public:
    logBlock log_;
    bool autoAlloc=false; // if true, add tag to tracker automatically
    bool autoDeAlloc=false; // if true, remove tag from tracker automatically
    std::shared_ptr<trackerBase> tracker_;  // can hold any tracker
    std::shared_ptr<synchLock<uint64_t>> synchLock_;
    const char * module_;
    const std::string blockName_;
    bool locking_ = false;
    bool teeBusy_ = false;
    bool isDebugLog = false;
    std::shared_ptr<timedDelayBase> m_delay;
    std::shared_ptr<stringPingPong> m_logQueue = nullptr;

public:
    interfaceBase(const char * module, std::string block, INTERFACE_AUTO_MODE autoMode ) :
        log_(std::string(module), block),
        module_(module),
        blockName_(block),
        m_delay(std::make_shared<timedDelay> (module))
    {
        switch (autoMode)
        {
        case INTERFACE_AUTO_OFF:
            autoAlloc = false;
            autoDeAlloc = false;
            break;
        case INTERFACE_AUTO_ALLOC:
            autoAlloc = true;
            autoDeAlloc = false;
            break;
        case INTERFACE_AUTO_DEALLOC:
            autoAlloc = false;
            autoDeAlloc = true;
            break;
        default:
            autoAlloc = false;
            autoDeAlloc = false;
            break;
        }
    };
    void setTracker(const char * type)
    {
        trackerCollection &trackers = trackerCollection::GetInstance();
        tracker_=trackers.getTracker(type);
    }
    virtual void setTracker( std::shared_ptr<trackerBase> pTracker)
    {
        tracker_ = pTracker;
    }
    void setLogging(verbosity_e verbosity) // allow interface level override of logging
    {
        log_.setVerbosity(verbosity);
        isDebugLog = log_.isMatch(LOG_DEBUG);
    }
    void setLogQueue(std::shared_ptr<stringPingPong> logQueue)
    {
        Q_ASSERT_CTX(tracker_ == nullptr, __func__, "Cannot set log queue when tracker is in use");
        m_logQueue = logQueue;
    }
    void interfaceLog(std::string const &s, uint64_t const tag)
    {
        if (tracker_ != nullptr)
        {
            if (!tracker_->is_valid(tag))
            {
                log_.logPrint(fmt::format("Invalid tracker tag:0x{:x} interface data:{}", tag, s), LOG_IMPORTANT);
                Q_ASSERT_CTX(false, fmt::format("{}.{}", blockName_, module_), "Invalid tracker interface data");
            }
            if (autoAlloc) {
                tracker_->autoAlloc(tag, s);
            }
            log_.logPrint(tracker_->prt( tag, s, log_.getLogPrefix() ), LOG_NORMAL);
            if (autoDeAlloc) {
                tracker_->autoDealloc(tag);
            }
        } else {
            if (m_logQueue != nullptr) {
                if (!m_logQueue->isEmpty()) {
                    log_.logPrint(m_logQueue->pop() + s, LOG_NORMAL);
                } else {
                    log_.logPrint(s, LOG_NORMAL);
                }
            } else {
                log_.logPrint(s, LOG_NORMAL);
            }
        }
    }
    inline bool isLocking(void)
    {
        return locking_;
    }
    // set multidriver when you have multiple threads using the same interface that require locking
    void setMultiDriver(std::string name, std::function<std::string(const uint64_t &value)> prt = nullptr)
    {
        cout << "setMultiDriver " << name << endl;
        synchLock_ = synchLockFactory<>::getInstance().newLock(name, "Mutex");
        if (prt != nullptr) {
            synchLock_->setPrt(prt);
        }
        locking_ = true;
    }
    void teeStatus(void)
    {
        if (teeBusy_)
        {
            log_.logPrint(fmt::format("Tee for {} has one side, waiting for other", module_  ) );
        }
    }
    // in tandem mode if either autoalloc or autodealloc- do both to neutralize the ref counting
    void setTandem(void)
    {
        if (autoAlloc || autoDeAlloc)
        {
            autoAlloc = true;
            autoDeAlloc = true;
        }
    }
    void setTimed(int nsec, timedDelayMode mode)
    {
        m_delay->setTimed(nsec, mode);
    }

    void delay(bool waitOnZero=false)
    {
        m_delay->delay(waitOnZero);
    }
    void setTimedDelayPtr(std::shared_ptr<timedDelayBase> pDelay)
    {
        m_delay = pDelay;
    }
};


#endif //(INTERFACEBASE_H)
