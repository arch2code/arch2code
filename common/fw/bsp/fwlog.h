#ifndef FWLOG_H
#define FWLOG_H

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "log.h"
#include "logging.h"
#include <boost/format.hpp>

//facade to hide the logging object

void fwlog(const std::string &logmsg, const loglevel_e loglevel=LOG_NORMAL);

template<typename... Args>
void fwlog(const loglevel_e loglevel, const char* fmt, Args... args) {
    static logBlock log("FW");
    // Use boost::format to format the string
    std::string f_logmsg = (boost::format(fmt) % ... % args).str();
    // Print the formatted string
    log.logPrint(f_logmsg, loglevel);
}

template<typename... Args>
void fwlog(const char* fmt, Args... args) {
    fwlog(LOG_NORMAL, fmt, args...);
}

#endif //FWLOG_H 