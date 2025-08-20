#ifndef TAGTRACKER_H
#define TAGTRACKER_H

#include <vector>
#include <string>
#include <format>



class cmdIdInfo
{
public:
    int dummy;
    std::string prt(void);
};

class tagInfo
{
public:
    tagInfo() : cmdId(-1), buff(nullptr), buffLen(0) {}
    tagInfo(const std::string tagType_) : cmdId(-1), buff(nullptr), buffLen(0), tagType(tagType_) {}
    int cmdId;          //-1 for invalid cmdId
    u_int8_t *buff;     //backdoor data transfer
    uint64_t buffLen;
    std::string tagType;
    std::string prt(void);
};






#endif //(TAGTRACKER_H)