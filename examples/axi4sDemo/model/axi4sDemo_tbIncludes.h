
#ifndef AXI4SDEMO_TBINCLUDES_H_
#define AXI4SDEMO_TBINCLUDES_H_
// 

#include "systemc.h"

// GENERATED_CODE_PARAM --context=axi4sDemo_tb.yaml
// GENERATED_CODE_BEGIN --template=headers --fileMapKey=include_hdr

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=constants
//constants

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=types
// types
typedef uint8_t bv4_t; // [4] Bit Vector 4 bits
typedef uint8_t bv8_t; // [8] Bit Vector 8 bits
typedef uint16_t bv16_t; // [16] Bit Vector 16 bits
typedef uint64_t bv64_t; // [64] Bit Vector 64 bits
struct bv256_t { uint64_t word[ 4 ]; }; // [256] Bit Vector 256 bits

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=includes --section=enums
// enums

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=structures
// structures
struct data_t1_t {
    bv256_t data; //

    data_t1_t() {}

    static constexpr uint16_t _bitWidth = 256;
    static constexpr uint16_t _byteWidth = 32;
    typedef uint64_t _packedSt[4];
    bool operator == (const data_t1_t & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const data_t1_t & v, const std::string & NAME ) {
        sc_trace(tf,v.data.word[ 0 ], NAME + ".data.word[ 0 ]");
        sc_trace(tf,v.data.word[ 1 ], NAME + ".data.word[ 1 ]");
        sc_trace(tf,v.data.word[ 2 ], NAME + ".data.word[ 2 ]");
        sc_trace(tf,v.data.word[ 3 ], NAME + ".data.word[ 3 ]");
    }
    inline friend ostream& operator << ( ostream& os,  data_t1_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<256> sc_pack(void) const;
    void sc_unpack(sc_bv<256> packed_data);
    explicit data_t1_t(sc_bv<256> packed_data) { sc_unpack(packed_data); }
    explicit data_t1_t(
        bv256_t data_) :
        data(data_)
    {}
    explicit data_t1_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tid_t1_t {
    bv4_t tid; //

    tid_t1_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const tid_t1_t & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const tid_t1_t & v, const std::string & NAME ) {
        sc_trace(tf,v.tid, NAME + ".tid");
    }
    inline friend ostream& operator << ( ostream& os,  tid_t1_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<4> sc_pack(void) const;
    void sc_unpack(sc_bv<4> packed_data);
    explicit tid_t1_t(sc_bv<4> packed_data) { sc_unpack(packed_data); }
    explicit tid_t1_t(
        bv4_t tid_) :
        tid(tid_)
    {}
    explicit tid_t1_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tdest_t1_t {
    bv4_t tid; //

    tdest_t1_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const tdest_t1_t & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const tdest_t1_t & v, const std::string & NAME ) {
        sc_trace(tf,v.tid, NAME + ".tid");
    }
    inline friend ostream& operator << ( ostream& os,  tdest_t1_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<4> sc_pack(void) const;
    void sc_unpack(sc_bv<4> packed_data);
    explicit tdest_t1_t(sc_bv<4> packed_data) { sc_unpack(packed_data); }
    explicit tdest_t1_t(
        bv4_t tid_) :
        tid(tid_)
    {}
    explicit tdest_t1_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tuser_t1_t {
    bv16_t parity; //

    tuser_t1_t() {}

    static constexpr uint16_t _bitWidth = 16;
    static constexpr uint16_t _byteWidth = 2;
    typedef uint16_t _packedSt;
    bool operator == (const tuser_t1_t & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const tuser_t1_t & v, const std::string & NAME ) {
        sc_trace(tf,v.parity, NAME + ".parity");
    }
    inline friend ostream& operator << ( ostream& os,  tuser_t1_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<16> sc_pack(void) const;
    void sc_unpack(sc_bv<16> packed_data);
    explicit tuser_t1_t(sc_bv<16> packed_data) { sc_unpack(packed_data); }
    explicit tuser_t1_t(
        bv16_t parity_) :
        parity(parity_)
    {}
    explicit tuser_t1_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct data_t2_t {
    bv64_t data; //

    data_t2_t() {}

    static constexpr uint16_t _bitWidth = 64;
    static constexpr uint16_t _byteWidth = 8;
    typedef uint64_t _packedSt;
    bool operator == (const data_t2_t & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const data_t2_t & v, const std::string & NAME ) {
        sc_trace(tf,v.data, NAME + ".data");
    }
    inline friend ostream& operator << ( ostream& os,  data_t2_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<64> sc_pack(void) const;
    void sc_unpack(sc_bv<64> packed_data);
    explicit data_t2_t(sc_bv<64> packed_data) { sc_unpack(packed_data); }
    explicit data_t2_t(
        bv64_t data_) :
        data(data_)
    {}
    explicit data_t2_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tid_t2_t {
    bv4_t tid; //

    tid_t2_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const tid_t2_t & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const tid_t2_t & v, const std::string & NAME ) {
        sc_trace(tf,v.tid, NAME + ".tid");
    }
    inline friend ostream& operator << ( ostream& os,  tid_t2_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<4> sc_pack(void) const;
    void sc_unpack(sc_bv<4> packed_data);
    explicit tid_t2_t(sc_bv<4> packed_data) { sc_unpack(packed_data); }
    explicit tid_t2_t(
        bv4_t tid_) :
        tid(tid_)
    {}
    explicit tid_t2_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tdest_t2_t {
    bv4_t tid; //

    tdest_t2_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const tdest_t2_t & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const tdest_t2_t & v, const std::string & NAME ) {
        sc_trace(tf,v.tid, NAME + ".tid");
    }
    inline friend ostream& operator << ( ostream& os,  tdest_t2_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<4> sc_pack(void) const;
    void sc_unpack(sc_bv<4> packed_data);
    explicit tdest_t2_t(sc_bv<4> packed_data) { sc_unpack(packed_data); }
    explicit tdest_t2_t(
        bv4_t tid_) :
        tid(tid_)
    {}
    explicit tdest_t2_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};
struct tuser_t2_t {
    bv4_t parity; //

    tuser_t2_t() {}

    static constexpr uint16_t _bitWidth = 4;
    static constexpr uint16_t _byteWidth = 1;
    typedef uint8_t _packedSt;
    bool operator == (const tuser_t2_t & rhs) const;
    inline friend void sc_trace(sc_trace_file *tf, const tuser_t2_t & v, const std::string & NAME ) {
        sc_trace(tf,v.parity, NAME + ".parity");
    }
    inline friend ostream& operator << ( ostream& os,  tuser_t2_t const & v ) {
        os << v.prt();
        return os;
    }
    std::string prt(bool all=false) const;
    static const char* getValueType(void) { return( "" );}
    inline uint64_t getStructValue(void) const { return( -1 );}
    void pack(_packedSt &_ret) const;
    void unpack(_packedSt &_src);
    sc_bv<4> sc_pack(void) const;
    void sc_unpack(sc_bv<4> packed_data);
    explicit tuser_t2_t(sc_bv<4> packed_data) { sc_unpack(packed_data); }
    explicit tuser_t2_t(
        bv4_t parity_) :
        parity(parity_)
    {}
    explicit tuser_t2_t(const _packedSt &packed_data) { unpack(const_cast<_packedSt&>(packed_data)); }

};

// GENERATED_CODE_END
#endif //AXI4SDEMO_TBINCLUDES_H_
