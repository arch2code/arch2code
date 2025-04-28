#ifndef ASYCHEVENT_H
#define ASYCHEVENT_H
#include "systemc.h"
#include <unistd.h>
#include <map>
// from https://forums.accellera.org/topic/29-async_request_update-example/

// the threadsafe event class is used to allow external threads to generate events in systemC
// is a wrapper for the async_request_update 
using namespace sc_core;


class ThreadSafeEvent : public sc_prim_channel {
public:
    ThreadSafeEvent(const char *name = ""): event(name), eventName(name) {} 

    void notify(sc_time delay_ = SC_ZERO_TIME) {
        this->delay = delay_;
        //std::cout << "ThreadSafeNotify " << eventName << endl; //temp debug
        async_request_update();
    }
    // use default_event to wait on
    const sc_event &default_event(void) const {
        return event;
    }
protected:
    virtual void update(void) {
        event.notify(delay);
        //std::cout << "ThreadSafeUpdate " << eventName << endl; //temp debug
    }
    sc_event event;
    sc_time delay;
    const char *eventName;  // keep our own copy of the eventname as the name() function does not appear to work correctly
};
//factory for pointers to thread safe events
class ThreadSafeEventFactory {
public:
    static std::shared_ptr<ThreadSafeEvent> newEvent(const char * name) 
    {
        auto &map = getMap();
        auto it = map.find(name);
        if (it == map.end()) {
            auto result = std::make_shared<ThreadSafeEvent>(name);
            map[name] = result;
            return result;
        } else {
            return it->second;
        }
    }
    static std::shared_ptr<ThreadSafeEvent> getEvent(const char * name) 
    {
        auto &map = getMap();
        auto it = map.find(name);
        if (it == map.end()) {
            return nullptr;
        }
        return it->second;
    }
private:
    static std::map<std::string, std::shared_ptr<ThreadSafeEvent>> & getMap() 
    {
        static std::map<std::string, std::shared_ptr<ThreadSafeEvent>> eventMap;
        return eventMap;
    }
};
#endif //ASYCHEVENT_H