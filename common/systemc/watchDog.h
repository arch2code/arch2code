#ifndef WATCHDOG_H
#define WATCHDOG_H
// copyright QiStor 2025
#include "systemc.h"
class watchDog
{
public:
    static bool tickled;
    static bool enabled;
    static sc_time timeout;
    static bool isTimeout;
    static uint64_t enablers;
    static uint64_t enableVotes;
    static void registerEnabler(void) {enablers++;}; // to enable or disable the watchdog you must be an enabler
    static void tickleWatchdog(void) {tickled = true;}; // tickle the watchdog to prevent timeout
    static bool watchDogIsExpired(void) {return isTimeout;};
    static void enableWatchdog(void); // must be called by all enablers to enable the watchdog
    static void disableWatchdog(void); 
};

// Watchdog process body, spawned once per run by sc_main so a design that
// registers an enabler is protected without declaring a block.
void watchDogHandler(void);

#endif //WATCHDOG_H
