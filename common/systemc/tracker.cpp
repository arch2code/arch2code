// copyright QiStor 2023

#include "systemc.h"

#include <string>
#include "tracker.h"
#include "logging.h"

void tracker_alloc(const char* name, int tag, const char* thread_string)
{
    static trackerCollection& tracker = trackerCollection::GetInstance();
    static logging& log = logging::GetInstance();
    std::stringstream ss;
    ss << "tracker DPI alloc " << name << " tag:0x" << std::hex << tag << " str: " << thread_string;
    log.logDirect(ss.str());
    tracker.alloc(name, tag, thread_string);
}

void tracker_dealloc(const char* name, int tag) {
    static trackerCollection& tracker = trackerCollection::GetInstance();
    static logging& log = logging::GetInstance();
    std::stringstream ss;
    ss << "tracker DPI dealloc " << name << " tag:0x" << std::hex << tag;
    log.logDirect(ss.str());
    tracker.dealloc(name, tag);
}
