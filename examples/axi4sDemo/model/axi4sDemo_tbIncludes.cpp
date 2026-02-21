
// 
#include "axi4sDemo_tbIncludes.h"
// GENERATED_CODE_PARAM --context=axi4sDemo_tb.yaml
// GENERATED_CODE_BEGIN --template=structures --section=cppIncludes
#include "logging.h"
#include <algorithm>
#include "bitTwiddling.h"

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=cpp
// structures
bool data_t1_t::operator == (const data_t1_t & rhs) const {
    bool ret = true;
    ret = ret && (data.word[ 0 ] == rhs.data.word[ 0 ]);
    ret = ret && (data.word[ 1 ] == rhs.data.word[ 1 ]);
    ret = ret && (data.word[ 2 ] == rhs.data.word[ 2 ]);
    ret = ret && (data.word[ 3 ] == rhs.data.word[ 3 ]);
    return ( ret );
    }
std::string data_t1_t::prt(bool all) const
{
    return (std::format("data:0x{:016x}{:016x}{:016x}{:016x}",
       data.word[3],
       data.word[2],
       data.word[1],
       data.word[0]
    ));
}
void data_t1_t::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, data_t1_t::_byteWidth);
    pack_bits((uint64_t *)&_ret, 0, (uint64_t *)&data, 256);
}
void data_t1_t::unpack(const _packedSt &_src)
{
    uint16_t _pos{0};
    data.word[0] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
    _pos += 64;
    data.word[1] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
    _pos += 64;
    data.word[2] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
    _pos += 64;
    data.word[3] = ((_src[ _pos >> 6 ] >> (_pos & 63)));
}
sc_bv<data_t1_t::_bitWidth> data_t1_t::sc_pack(void) const
{
    sc_bv<data_t1_t::_bitWidth> packed_data;
    packed_data.range(63, 0) = data.word[0];
    packed_data.range(127, 64) = data.word[1];
    packed_data.range(191, 128) = data.word[2];
    packed_data.range(255, 192) = data.word[3];
    return packed_data;
}
void data_t1_t::sc_unpack(sc_bv<data_t1_t::_bitWidth> packed_data)
{
    data.word[0] = (uint64_t) packed_data.range(63, 0).to_uint64();
    data.word[1] = (uint64_t) packed_data.range(127, 64).to_uint64();
    data.word[2] = (uint64_t) packed_data.range(191, 128).to_uint64();
    data.word[3] = (uint64_t) packed_data.range(255, 192).to_uint64();
}
bool tid_t1_t::operator == (const tid_t1_t & rhs) const {
    bool ret = true;
    ret = ret && (tid == rhs.tid);
    return ( ret );
    }
std::string tid_t1_t::prt(bool all) const
{
    return (std::format("tid:0x{:01x}",
       (uint64_t) tid
    ));
}
void tid_t1_t::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, tid_t1_t::_byteWidth);
    _ret = tid;
}
void tid_t1_t::unpack(const _packedSt &_src)
{
    tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
}
sc_bv<tid_t1_t::_bitWidth> tid_t1_t::sc_pack(void) const
{
    sc_bv<tid_t1_t::_bitWidth> packed_data;
    packed_data.range(3, 0) = tid;
    return packed_data;
}
void tid_t1_t::sc_unpack(sc_bv<tid_t1_t::_bitWidth> packed_data)
{
    tid = (bv4_t) packed_data.range(3, 0).to_uint64();
}
bool tdest_t1_t::operator == (const tdest_t1_t & rhs) const {
    bool ret = true;
    ret = ret && (tid == rhs.tid);
    return ( ret );
    }
std::string tdest_t1_t::prt(bool all) const
{
    return (std::format("tid:0x{:01x}",
       (uint64_t) tid
    ));
}
void tdest_t1_t::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, tdest_t1_t::_byteWidth);
    _ret = tid;
}
void tdest_t1_t::unpack(const _packedSt &_src)
{
    tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
}
sc_bv<tdest_t1_t::_bitWidth> tdest_t1_t::sc_pack(void) const
{
    sc_bv<tdest_t1_t::_bitWidth> packed_data;
    packed_data.range(3, 0) = tid;
    return packed_data;
}
void tdest_t1_t::sc_unpack(sc_bv<tdest_t1_t::_bitWidth> packed_data)
{
    tid = (bv4_t) packed_data.range(3, 0).to_uint64();
}
bool tuser_t1_t::operator == (const tuser_t1_t & rhs) const {
    bool ret = true;
    ret = ret && (parity == rhs.parity);
    return ( ret );
    }
std::string tuser_t1_t::prt(bool all) const
{
    return (std::format("parity:0x{:04x}",
       (uint64_t) parity
    ));
}
void tuser_t1_t::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, tuser_t1_t::_byteWidth);
    _ret = parity;
}
void tuser_t1_t::unpack(const _packedSt &_src)
{
    parity = (bv16_t)((_src));
}
sc_bv<tuser_t1_t::_bitWidth> tuser_t1_t::sc_pack(void) const
{
    sc_bv<tuser_t1_t::_bitWidth> packed_data;
    packed_data.range(15, 0) = parity;
    return packed_data;
}
void tuser_t1_t::sc_unpack(sc_bv<tuser_t1_t::_bitWidth> packed_data)
{
    parity = (bv16_t) packed_data.range(15, 0).to_uint64();
}
bool data_t2_t::operator == (const data_t2_t & rhs) const {
    bool ret = true;
    ret = ret && (data == rhs.data);
    return ( ret );
    }
std::string data_t2_t::prt(bool all) const
{
    return (std::format("data:0x{:016x}",
       (uint64_t) data
    ));
}
void data_t2_t::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, data_t2_t::_byteWidth);
    _ret = data;
}
void data_t2_t::unpack(const _packedSt &_src)
{
    data = (bv64_t)((_src));
}
sc_bv<data_t2_t::_bitWidth> data_t2_t::sc_pack(void) const
{
    sc_bv<data_t2_t::_bitWidth> packed_data;
    packed_data.range(63, 0) = data;
    return packed_data;
}
void data_t2_t::sc_unpack(sc_bv<data_t2_t::_bitWidth> packed_data)
{
    data = (bv64_t) packed_data.range(63, 0).to_uint64();
}
bool tid_t2_t::operator == (const tid_t2_t & rhs) const {
    bool ret = true;
    ret = ret && (tid == rhs.tid);
    return ( ret );
    }
std::string tid_t2_t::prt(bool all) const
{
    return (std::format("tid:0x{:01x}",
       (uint64_t) tid
    ));
}
void tid_t2_t::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, tid_t2_t::_byteWidth);
    _ret = tid;
}
void tid_t2_t::unpack(const _packedSt &_src)
{
    tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
}
sc_bv<tid_t2_t::_bitWidth> tid_t2_t::sc_pack(void) const
{
    sc_bv<tid_t2_t::_bitWidth> packed_data;
    packed_data.range(3, 0) = tid;
    return packed_data;
}
void tid_t2_t::sc_unpack(sc_bv<tid_t2_t::_bitWidth> packed_data)
{
    tid = (bv4_t) packed_data.range(3, 0).to_uint64();
}
bool tdest_t2_t::operator == (const tdest_t2_t & rhs) const {
    bool ret = true;
    ret = ret && (tid == rhs.tid);
    return ( ret );
    }
std::string tdest_t2_t::prt(bool all) const
{
    return (std::format("tid:0x{:01x}",
       (uint64_t) tid
    ));
}
void tdest_t2_t::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, tdest_t2_t::_byteWidth);
    _ret = tid;
}
void tdest_t2_t::unpack(const _packedSt &_src)
{
    tid = (bv4_t)((_src) & ((1ULL << 4) - 1));
}
sc_bv<tdest_t2_t::_bitWidth> tdest_t2_t::sc_pack(void) const
{
    sc_bv<tdest_t2_t::_bitWidth> packed_data;
    packed_data.range(3, 0) = tid;
    return packed_data;
}
void tdest_t2_t::sc_unpack(sc_bv<tdest_t2_t::_bitWidth> packed_data)
{
    tid = (bv4_t) packed_data.range(3, 0).to_uint64();
}
bool tuser_t2_t::operator == (const tuser_t2_t & rhs) const {
    bool ret = true;
    ret = ret && (parity == rhs.parity);
    return ( ret );
    }
std::string tuser_t2_t::prt(bool all) const
{
    return (std::format("parity:0x{:01x}",
       (uint64_t) parity
    ));
}
void tuser_t2_t::pack(_packedSt &_ret) const
{
    memset(&_ret, 0, tuser_t2_t::_byteWidth);
    _ret = parity;
}
void tuser_t2_t::unpack(const _packedSt &_src)
{
    parity = (bv4_t)((_src) & ((1ULL << 4) - 1));
}
sc_bv<tuser_t2_t::_bitWidth> tuser_t2_t::sc_pack(void) const
{
    sc_bv<tuser_t2_t::_bitWidth> packed_data;
    packed_data.range(3, 0) = parity;
    return packed_data;
}
void tuser_t2_t::sc_unpack(sc_bv<tuser_t2_t::_bitWidth> packed_data)
{
    parity = (bv4_t) packed_data.range(3, 0).to_uint64();
}

// GENERATED_CODE_END
