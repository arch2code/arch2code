#ifndef LOG_H
#define LOG_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include <string>

enum loglevel_e {
    LOG_ALWAYS,    //Always sent to log for all verbosity levels
    LOG_IMPORTANT, //only important logging level
    LOG_NORMAL,    //normal logging level
    LOG_DEBUG      //most detailed logging level
};

enum verbosity_e {
    VERBOSITY_LOW,      // print only LOG_ALWAYS messages
    VERBOSITY_MEDIUM,   // ... also print LOG_IMPORTANT messages
    VERBOSITY_HIGH,     // ... also print LOG_NORMAL messages
    VERBOSITY_FULL,     // ... also print LOG_DEBUG messages
    VERBOSITY_UNKNOWN   // Unknown value in interface
};

//facade to hide the logging object
void log(const std::string &fname, const std::string &block, const std::string &logmsg, const loglevel_e loglevel=LOG_DEBUG);
void logDirect(const std::string &logmsg, const loglevel_e loglevel=LOG_NORMAL);
#define LOG(_block, _message) (_log(__func__, _block, _message))
#define LOG_LVL(_block, _message, _level) (_log(__func__, _block, _message, _level))

#endif //LOG_H 