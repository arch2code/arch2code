// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "mixedNestedIncludeIncludes.h"

// GENERATED_CODE_PARAM --context=mixedNestedInclude.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool dupTestSt::operator == (const dupTestSt & rhs) const {
    bool ret = true;
    ret = ret && (bob == rhs.bob);
    return ( ret );
    }
std::string dupTestSt::prt(bool all) const
{
    return (std::format("bob:0x{:04x}",
       (uint64_t) bob
    ));
}
void dupTestSt::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, dupTestSt::_byteWidth);
    _ret = bob;
}
void dupTestSt::unpack(const _packedSt &_src)
{
    bob = (dupTestT)((_src) & ((1ULL << 13) - 1));
}
sc_bv<13> dupTestSt::sc_pack(void) const
{
    sc_bv<13> packed_data;
    packed_data.range(12, 0) = bob;
    return packed_data;
}
void dupTestSt::sc_unpack(sc_bv<13> packed_data)
{
    bob = (dupTestT) packed_data.range(12, 0).to_uint64();
}

// GENERATED_CODE_END

