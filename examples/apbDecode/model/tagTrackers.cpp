
#include <vector>
#include <string>
#include <boost/assert.hpp>
#include <format>
#include "logging.h"
#include "tagTrackers.h"

std::string cmdIdInfo::prt(void)
{
    std::string s = std::format("dummy:0x{:x}", dummy );
    return(s);
}


std::string tagInfo::prt(void)
{
    const int shortDump=8;
    std::string s;
    std::string dump;
    if (cmdId != -1)
    {
        s = std::format("Type:{} cmdId:0x{:x}", tagType, cmdId );
    } else {
        s = "Type:" + tagType;
    }
    if (buff != nullptr)
    {
        if (buffLen < shortDump)
        {
            for(int i=0; i<shortDump; i++)
            {
                dump = std::format("{} {:x}", dump, *(buff+i) );
            }
            dump = " Data:[" + dump + "]";
        } else {
            dump = std::format(" Data:[{:x} {:x} {:x} {:x} {:x} {:x} {:x} {:x}..]", *(buff), *(buff+1), *(buff+2), *(buff+3), *(buff+4), *(buff+5), *(buff+6), *(buff+7));
        }
        s = s + dump;
    }

    return(s);
};
