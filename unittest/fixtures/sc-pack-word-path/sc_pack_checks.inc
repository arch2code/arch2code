// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Per-struct fill and oracle for test_sc_pack_word_path.py. Included once inside
// each emission flavour's namespace, so the unqualified struct names resolve to
// that flavour's rendering. Field positions are spelled out by hand.

static void fill(tinySt &x) { x.x = rnd(3); x.y = srnd(5); }
static sc_bv<tinySt::_bitWidth> expect(const tinySt &x)
{
    sc_bv<tinySt::_bitWidth> bv;
    put(bv, 0, 5, x.y);
    put(bv, 5, 3, x.x);
    return bv;
}

static void fill(smallSt &x) { x.a = rnd(4); x.s = srnd(5); x.b = rnd(8); }
static sc_bv<smallSt::_bitWidth> expect(const smallSt &x)
{
    sc_bv<smallSt::_bitWidth> bv;
    put(bv, 0, 8, x.b);
    put(bv, 8, 5, x.s);
    put(bv, 13, 4, x.a);
    return bv;
}

static void fill(exact64St &x) { x.hi = rnd(24); x.lo = srnd(40); }
static sc_bv<exact64St::_bitWidth> expect(const exact64St &x)
{
    sc_bv<exact64St::_bitWidth> bv;
    put(bv, 0, 40, x.lo);
    put(bv, 40, 24, x.hi);
    return bv;
}

static void fill(innerSt &x) { x.x = rnd(4); x.y = srnd(3); }
static sc_bv<innerSt::_bitWidth> expect(const innerSt &x)
{
    sc_bv<innerSt::_bitWidth> bv;
    put(bv, 0, 3, x.y);
    put(bv, 3, 4, x.x);
    return bv;
}

static void fill(nestSt &x)
{
    x.top = rnd(3);
    for (auto &e : x.inner) fill(e);
    fill(x.tail);
}
static sc_bv<nestSt::_bitWidth> expect(const nestSt &x)
{
    sc_bv<nestSt::_bitWidth> bv;
    bv.range(16, 0) = expect(x.tail);
    for (unsigned i = 0; i < 3; i++) {
        bv.range(17 + 7 * i + 6, 17 + 7 * i) = expect(x.inner[i]);
    }
    put(bv, 38, 3, x.top);
    return bv;
}

static void fill(wideSt &x) { x.hi = rnd(4); rndWide(x.w, 100); x.lo = srnd(7); }
static sc_bv<wideSt::_bitWidth> expect(const wideSt &x)
{
    sc_bv<wideSt::_bitWidth> bv;
    put(bv, 0, 7, x.lo);
    putWide(bv, 7, 100, x.w);
    put(bv, 107, 4, x.hi);
    return bv;
}

static void fill(bigNestSt &x)
{
    for (auto &e : x.inners) fill(e);
    x.flag = rnd(1);
}
static sc_bv<bigNestSt::_bitWidth> expect(const bigNestSt &x)
{
    sc_bv<bigNestSt::_bitWidth> bv;
    put(bv, 0, 1, x.flag);
    for (unsigned i = 0; i < 5; i++) {
        bv.range(1 + 17 * i + 16, 1 + 17 * i) = expect(x.inners[i]);
    }
    return bv;
}

static void fill(arrSt &x)
{
    for (auto &e : x.v) e = rnd(12);
    x.z = srnd(5);
}
static sc_bv<arrSt::_bitWidth> expect(const arrSt &x)
{
    sc_bv<arrSt::_bitWidth> bv;
    put(bv, 0, 5, x.z);
    for (unsigned i = 0; i < 7; i++) {
        put(bv, 5 + 12 * i, 12, x.v[i]);
    }
    return bv;
}

static void fill(deepSt &x) { fill(x.n); fill(x.w); }
static sc_bv<deepSt::_bitWidth> expect(const deepSt &x)
{
    sc_bv<deepSt::_bitWidth> bv;
    bv.range(110, 0) = expect(x.w);
    bv.range(151, 111) = expect(x.n);
    return bv;
}

static void fill(lowNestSt &x) { rndWide(x.w, 100); fill(x.tail); }
static sc_bv<lowNestSt::_bitWidth> expect(const lowNestSt &x)
{
    sc_bv<lowNestSt::_bitWidth> bv;
    bv.range(16, 0) = expect(x.tail);
    putWide(bv, 17, 100, x.w);
    return bv;
}

static void fill(log2NSt &x) { x.b = rnd(4); x.a = rnd(5); }
static sc_bv<log2NSt::_bitWidth> expect(const log2NSt &x)
{
    sc_bv<log2NSt::_bitWidth> bv;
    put(bv, 0, 5, x.a);
    put(bv, 5, 4, x.b);
    return bv;
}

static void fill(aliasSt &x) { x.hi = rnd(8); x.addr = rnd(55); fill(x.n); }
static sc_bv<aliasSt::_bitWidth> expect(const aliasSt &x)
{
    sc_bv<aliasSt::_bitWidth> bv;
    bv.range(8, 0) = expect(x.n);
    put(bv, 9, 55, x.addr);
    put(bv, 64, 8, x.hi);
    return bv;
}

static void fill(nHighSt &x) { fill(x.n); x.lo = rnd(64); }
static sc_bv<nHighSt::_bitWidth> expect(const nHighSt &x)
{
    sc_bv<nHighSt::_bitWidth> bv;
    put(bv, 0, 64, x.lo);
    bv.range(72, 64) = expect(x.n);
    return bv;
}

static void fill(wordHighSt &x) { fill(x.n); x.lo = rnd(64); }
static sc_bv<wordHighSt::_bitWidth> expect(const wordHighSt &x)
{
    sc_bv<wordHighSt::_bitWidth> bv;
    put(bv, 0, 64, x.lo);
    bv.range(127, 64) = expect(x.n);
    return bv;
}

static void fill(pix4St &x) { for (auto &e : x.pixels) e = rnd(8); }
static sc_bv<pix4St::_bitWidth> expect(const pix4St &x)
{
    sc_bv<pix4St::_bitWidth> bv;
    for (unsigned i = 0; i < 4; i++) {
        put(bv, 8 * i, 8, x.pixels[i]);
    }
    return bv;
}

static void fill(pix2St &x) { for (auto &e : x.p) e = rnd(8); }
static sc_bv<pix2St::_bitWidth> expect(const pix2St &x)
{
    sc_bv<pix2St::_bitWidth> bv;
    put(bv, 0, 8, x.p[0]);
    put(bv, 8, 8, x.p[1]);
    return bv;
}

static void fill(csiSt &x) { x.fv = rnd(1); x.lv = rnd(1); fill(x.data); }
static sc_bv<csiSt::_bitWidth> expect(const csiSt &x)
{
    sc_bv<csiSt::_bitWidth> bv;
    bv.range(31, 0) = expect(x.data);
    put(bv, 32, 1, x.lv);
    put(bv, 33, 1, x.fv);
    return bv;
}

static void fill(csiUnSt &x) { x.fv = rnd(1); fill(x.data); x.lv = rnd(1); }
static sc_bv<csiUnSt::_bitWidth> expect(const csiUnSt &x)
{
    sc_bv<csiUnSt::_bitWidth> bv;
    put(bv, 0, 1, x.lv);
    bv.range(32, 1) = expect(x.data);
    put(bv, 33, 1, x.fv);
    return bv;
}

static void fill(pixWideSt &x) { fill(x.a); rndWide(x.w, 100); fill(x.b); }
static sc_bv<pixWideSt::_bitWidth> expect(const pixWideSt &x)
{
    sc_bv<pixWideSt::_bitWidth> bv;
    bv.range(15, 0) = expect(x.b);
    putWide(bv, 16, 100, x.w);
    bv.range(131, 116) = expect(x.a);
    return bv;
}

template <uint32_t P_W>
static void fill(pSt_v<P_W> &x) { x.pa = rnd(P_W); x.pb = srnd(5); }
template <uint32_t P_W>
static sc_bv<pSt_v<P_W>::_bitWidth> expect(const pSt_v<P_W> &x)
{
    sc_bv<pSt_v<P_W>::_bitWidth> bv;
    put(bv, 0, 5, x.pb);
    put(bv, 5, P_W, x.pa);
    return bv;
}

template <uint32_t A_N, uint32_t P_W>
static void fill(pArrSt_v<A_N, P_W> &x)
{
    for (auto &e : x.px) e = rnd(P_W);
    x.pz = rnd(4);
}
template <uint32_t A_N, uint32_t P_W>
static sc_bv<pArrSt_v<A_N, P_W>::_bitWidth> expect(const pArrSt_v<A_N, P_W> &x)
{
    sc_bv<pArrSt_v<A_N, P_W>::_bitWidth> bv;
    put(bv, 0, 4, x.pz);
    for (unsigned i = 0; i < A_N; i++) {
        put(bv, 4 + P_W * i, P_W, x.px[i]);
    }
    return bv;
}

template <uint32_t PW_W, uint32_t P_W>
static void fill(pWideSt_v<PW_W, P_W> &x) { x.hi = rnd(3); rndWide(x.pw, PW_W); x.ps = srnd(P_W); }
template <uint32_t PW_W, uint32_t P_W>
static sc_bv<pWideSt_v<PW_W, P_W>::_bitWidth> expect(const pWideSt_v<PW_W, P_W> &x)
{
    sc_bv<pWideSt_v<PW_W, P_W>::_bitWidth> bv;
    put(bv, 0, P_W, x.ps);
    putWide(bv, P_W, PW_W, x.pw);
    put(bv, P_W + PW_W, 3, x.hi);
    return bv;
}

template <uint32_t PW_W>
static void fill(pWArrSt_v<PW_W> &x)
{
    for (auto &e : x.pw) rndWide(e, PW_W);
    x.z = rnd(2);
}
template <uint32_t PW_W>
static sc_bv<pWArrSt_v<PW_W>::_bitWidth> expect(const pWArrSt_v<PW_W> &x)
{
    sc_bv<pWArrSt_v<PW_W>::_bitWidth> bv;
    put(bv, 0, 2, x.z);
    for (unsigned i = 0; i < 2; i++) {
        putWide(bv, 2 + PW_W * i, PW_W, x.pw[i]);
    }
    return bv;
}

template <uint32_t A_N, uint32_t PW_W, uint32_t P_W>
static void fill(pNestSt_v<A_N, PW_W, P_W> &x)
{
    for (auto &e : x.inner) fill(e);
    fill(x.plain);
    fill(x.pw);
}
template <uint32_t A_N, uint32_t PW_W, uint32_t P_W>
static sc_bv<pNestSt_v<A_N, PW_W, P_W>::_bitWidth> expect(const pNestSt_v<A_N, PW_W, P_W> &x)
{
    constexpr unsigned wideW = pWideSt_v<PW_W, P_W>::_bitWidth;
    constexpr unsigned innerW = pSt_v<P_W>::_bitWidth;
    sc_bv<pNestSt_v<A_N, PW_W, P_W>::_bitWidth> bv;
    bv.range(wideW - 1, 0) = expect(x.pw);
    bv.range(wideW + 16, wideW) = expect(x.plain);
    for (unsigned i = 0; i < A_N; i++) {
        unsigned lo = wideW + 17 + innerW * i;
        bv.range(lo + innerW - 1, lo) = expect(x.inner[i]);
    }
    return bv;
}

template <uint32_t P_W>
static void fill(pStrSt_v<P_W> &x) { x.a = rnd(8); x.p = srnd(P_W); x.b = rnd(40); }
template <uint32_t P_W>
static sc_bv<pStrSt_v<P_W>::_bitWidth> expect(const pStrSt_v<P_W> &x)
{
    sc_bv<pStrSt_v<P_W>::_bitWidth> bv;
    put(bv, 0, 40, x.b);
    put(bv, 40, P_W, x.p);
    put(bv, 40 + P_W, 8, x.a);
    return bv;
}

template <uint32_t M_W>
static void fill(awbLikeSt_v<M_W> &x) { x.r = rnd(M_W); x.g = rnd(M_W); x.b = rnd(M_W); }
template <uint32_t M_W>
static sc_bv<awbLikeSt_v<M_W>::_bitWidth> expect(const awbLikeSt_v<M_W> &x)
{
    sc_bv<awbLikeSt_v<M_W>::_bitWidth> bv;
    put(bv, 0, M_W, x.b);
    put(bv, M_W, M_W, x.g);
    put(bv, 2 * M_W, M_W, x.r);
    return bv;
}

template <uint32_t Q_W>
static void fill(pMisSt_v<Q_W> &x) { fill(x.n); x.q = rnd(Q_W); }
template <uint32_t Q_W>
static sc_bv<pMisSt_v<Q_W>::_bitWidth> expect(const pMisSt_v<Q_W> &x)
{
    sc_bv<pMisSt_v<Q_W>::_bitWidth> bv;
    put(bv, 0, Q_W, x.q);
    bv.range(Q_W + 63, Q_W) = expect(x.n);
    return bv;
}

template <uint32_t Q_W>
static void fill(pMisNSt_v<Q_W> &x) { x.hi = rnd(8); fill(x.n); x.q = rnd(Q_W); }
template <uint32_t Q_W>
static sc_bv<pMisNSt_v<Q_W>::_bitWidth> expect(const pMisNSt_v<Q_W> &x)
{
    sc_bv<pMisNSt_v<Q_W>::_bitWidth> bv;
    put(bv, 0, Q_W, x.q);
    bv.range(Q_W + 8, Q_W) = expect(x.n);
    put(bv, Q_W + 9, 8, x.hi);
    return bv;
}

template <uint32_t N_A>
static void fill(pHoldSt_v<N_A> &x)
{
    for (auto &e : x.b.a) e = rnd(8);
    x.lo = rnd(3);
}
template <uint32_t N_A>
static sc_bv<pHoldSt_v<N_A>::_bitWidth> expect(const pHoldSt_v<N_A> &x)
{
    sc_bv<pHoldSt_v<N_A>::_bitWidth> bv;
    put(bv, 0, 3, x.lo);
    for (unsigned i = 0; i < N_A; i++) {
        put(bv, 3 + 8 * i, 8, x.b.a[i]);
    }
    return bv;
}

template <uint32_t W2>
static void fill(pW2St_v<W2> &x) { x.hi = rnd(3); rndWide(x.w, W2); x.lo = rnd(5); }
template <uint32_t W2>
static sc_bv<pW2St_v<W2>::_bitWidth> expect(const pW2St_v<W2> &x)
{
    sc_bv<pW2St_v<W2>::_bitWidth> bv;
    put(bv, 0, 5, x.lo);
    putWide(bv, 5, W2, x.w);
    put(bv, 5 + W2, 3, x.hi);
    return bv;
}

template <uint32_t N_ONE>
static void fill(pOneArrSt_v<N_ONE> &x)
{
    for (auto &e : x.v) e = rnd(8);
    x.z = rnd(4);
}
template <uint32_t N_ONE>
static sc_bv<pOneArrSt_v<N_ONE>::_bitWidth> expect(const pOneArrSt_v<N_ONE> &x)
{
    sc_bv<pOneArrSt_v<N_ONE>::_bitWidth> bv;
    put(bv, 0, 4, x.z);
    for (unsigned i = 0; i < N_ONE; i++) {
        put(bv, 4 + 8 * i, 8, x.v[i]);
    }
    return bv;
}

template <uint32_t N_ONE>
static void fill(pOneSt_v<N_ONE> &x) { for (auto &e : x.v) e = rnd(8); }
template <uint32_t N_ONE>
static sc_bv<pOneSt_v<N_ONE>::_bitWidth> expect(const pOneSt_v<N_ONE> &x)
{
    sc_bv<pOneSt_v<N_ONE>::_bitWidth> bv;
    for (unsigned i = 0; i < N_ONE; i++) {
        put(bv, 8 * i, 8, x.v[i]);
    }
    return bv;
}

template <typename T>
static void exercise(const char *flavour, const char *name)
{
    for (unsigned it = 0; it < ITERATIONS; it++) {
        T x;
        fill(x);
        sc_bv<T::_bitWidth> want = expect(x);
        sc_bv<T::_bitWidth> bv = x.sc_pack();
        check(bv == want, flavour, "sc_pack() matches the per-field layout", name);
        constexpr int words = (T::_bitWidth + 31) / 32;
        uint32_t wantWords[words];
        for (int i = 0; i < words; i++) {
            wantWords[i] = want.get_word(i);
        }
        uint32_t packed[words];
        packWords(x, packed, runtimeWords(words));
        check(memcmp(packed, wantWords, sizeof(packed)) == 0, flavour, "pack() matches the per-field layout", name);
        T u;
        unpackWords(u, wantWords, runtimeWords(words));
        check(u == x, flavour, "unpack() of the per-field layout == x", name);
        T y;
        y.sc_unpack(bv);
        check(y == x, flavour, "sc_unpack(sc_pack(x)) == x", name);
        T z(bv);
        check(z == x, flavour, "T(sc_bv) == x", name);
    }
}

// A datapath field is a uint8_t * backdoor: sc_pack() copies the payload bytes
// it points at into the field's bits, and sc_unpack() writes them through the
// pointer the destination struct holds.
static void exerciseDatapath(const char *flavour)
{
    for (unsigned it = 0; it < ITERATIONS; it++) {
        uint8_t payload[4];
        for (auto &b : payload) b = rnd(8);
        dpSt x;
        x.tag = rnd(8);
        x.data = payload;
        x.len = rnd(4);
        sc_bv<dpSt::_bitWidth> want;
        put(want, 0, 4, x.len);
        for (unsigned i = 0; i < 4; i++) {
            put(want, 4 + 8 * i, 8, payload[i]);
        }
        put(want, 36, 8, x.tag);
        sc_bv<dpSt::_bitWidth> bv = x.sc_pack();
        check(bv == want, flavour, "sc_pack() places the payload bytes", "dpSt");
        uint8_t landed[4] = {};
        dpSt y;
        y.data = landed;
        y.sc_unpack(bv);
        check(y.tag == x.tag && y.len == x.len && y.data == landed, flavour,
              "sc_unpack() restores the fields and keeps the backdoor pointer", "dpSt");
        check(memcmp(landed, payload, sizeof(payload)) == 0, flavour,
              "sc_unpack() writes the payload bytes through the backdoor", "dpSt");

        dpOuterSt o;
        o.hdr = rnd(3);
        o.inner = x;
        sc_bv<dpOuterSt::_bitWidth> wantOuter;
        wantOuter.range(43, 0) = want;
        put(wantOuter, 44, 3, o.hdr);
        sc_bv<dpOuterSt::_bitWidth> bvOuter = o.sc_pack();
        check(bvOuter == wantOuter, flavour, "sc_pack() places the nested payload bytes", "dpOuterSt");
        uint8_t landedOuter[4] = {};
        dpOuterSt o2;
        o2.inner.data = landedOuter;
        o2.sc_unpack(bvOuter);
        check(o2.hdr == o.hdr && o2.inner.tag == x.tag && o2.inner.len == x.len, flavour,
              "sc_unpack() restores the nested fields", "dpOuterSt");
        check(memcmp(landedOuter, payload, sizeof(payload)) == 0, flavour,
              "sc_unpack() writes the nested payload bytes through the backdoor", "dpOuterSt");
    }
}

// A parameterizable array's length counts in _bitWidth even when its default
// length is one.
static void checkWidths(const char *flavour)
{
    check(pOneArrSt_v<1>::_bitWidth == 12, flavour, "_bitWidth counts one element", "pOneArrSt_v<1>");
    check(pOneArrSt_v<3>::_bitWidth == 28, flavour, "_bitWidth counts every element", "pOneArrSt_v<3>");
    check(pOneSt_v<1>::_bitWidth == 8, flavour, "_bitWidth counts one element", "pOneSt_v<1>");
    check(pOneSt_v<4>::_bitWidth == 32, flavour, "_bitWidth counts every element", "pOneSt_v<4>");
}

// A top field holding more bits than its type leaves them above _bitWidth in
// pack(); sc_pack() asserts on them rather than dropping them.
static void exerciseTail(const char *flavour)
{
    for (unsigned it = 0; it < ITERATIONS; it++) {
        smallSt s;
        fill(s);
        s.a = 0x10 | rnd(4);
        expectAssert(flavour, "sc_pack() asserts on a top field wider than its type", "smallSt",
                     [&] { (void)s.sc_pack(); });
        wideSt w;
        fill(w);
        w.hi = 0x10 | rnd(4);
        expectAssert(flavour, "sc_pack() asserts on a top field wider than its type", "wideSt",
                     [&] { (void)w.sc_pack(); });
    }
}

// The width-1 struct packs to bool and unpacks from bool or sc_bv<1>.
static void exerciseOneBit(const char *flavour)
{
    for (unsigned it = 0; it < ITERATIONS; it++) {
        oneSt x;
        x.e = rnd(1);
        bool b = x.sc_pack();
        check(b == (x.e == 1), flavour, "sc_pack() is the bit", "oneSt");
        oneSt::_packedSt p;
        x.pack(p);
        check(p == x.e, flavour, "sc_pack() matches pack()", "oneSt");
        oneSt y;
        y.sc_unpack(b);
        check(y == x, flavour, "sc_unpack(bool) round-trips", "oneSt");
        sc_bv<1> bv;
        bv[0] = b;
        oneSt z;
        z.sc_unpack(bv);
        check(z == x, flavour, "sc_unpack(sc_bv<1>) round-trips", "oneSt");
    }
}

static void runChecks(const char *flavour)
{
    exerciseOneBit(flavour);
    exercise<tinySt>(flavour, "tinySt");
    exercise<smallSt>(flavour, "smallSt");
    exercise<exact64St>(flavour, "exact64St");
    exercise<innerSt>(flavour, "innerSt");
    exercise<nestSt>(flavour, "nestSt");
    exercise<wideSt>(flavour, "wideSt");
    exercise<bigNestSt>(flavour, "bigNestSt");
    exercise<arrSt>(flavour, "arrSt");
    exercise<deepSt>(flavour, "deepSt");
    exercise<lowNestSt>(flavour, "lowNestSt");
    exercise<log2NSt>(flavour, "log2NSt");
    exercise<aliasSt>(flavour, "aliasSt");
    exercise<nHighSt>(flavour, "nHighSt");
    exercise<wordHighSt>(flavour, "wordHighSt");
    exercise<pix4St>(flavour, "pix4St");
    exercise<pix2St>(flavour, "pix2St");
    exercise<csiSt>(flavour, "csiSt");
    exercise<csiUnSt>(flavour, "csiUnSt");
    exercise<pixWideSt>(flavour, "pixWideSt");
    exerciseDatapath(flavour);
    exercise<pSt_v<8>>(flavour, "pSt_v<8>");
    exercise<pSt_v<40>>(flavour, "pSt_v<40>");
    exercise<pSt_v<1>>(flavour, "pSt_v<1>");
    exercise<pArrSt_v<3, 8>>(flavour, "pArrSt_v<3, 8>");
    exercise<pArrSt_v<6, 40>>(flavour, "pArrSt_v<6, 40>");
    exercise<pArrSt_v<1, 12>>(flavour, "pArrSt_v<1, 12>");
    exercise<pWideSt_v<70, 8>>(flavour, "pWideSt_v<70, 8>");
    exercise<pWideSt_v<64, 40>>(flavour, "pWideSt_v<64, 40>");
    exercise<pWideSt_v<128, 1>>(flavour, "pWideSt_v<128, 1>");
    exercise<pWArrSt_v<70>>(flavour, "pWArrSt_v<70>");
    exercise<pWArrSt_v<64>>(flavour, "pWArrSt_v<64>");
    exercise<pWArrSt_v<128>>(flavour, "pWArrSt_v<128>");
    exercise<pNestSt_v<3, 70, 8>>(flavour, "pNestSt_v<3, 70, 8>");
    exercise<pNestSt_v<6, 128, 40>>(flavour, "pNestSt_v<6, 128, 40>");
    exercise<pNestSt_v<2, 64, 5>>(flavour, "pNestSt_v<2, 64, 5>");
    exercise<pStrSt_v<8>>(flavour, "pStrSt_v<8>");
    exercise<pStrSt_v<20>>(flavour, "pStrSt_v<20>");
    exercise<pStrSt_v<30>>(flavour, "pStrSt_v<30>");
    exercise<pStrSt_v<40>>(flavour, "pStrSt_v<40>");
    exercise<awbLikeSt_v<26>>(flavour, "awbLikeSt_v<26>");
    exercise<awbLikeSt_v<16>>(flavour, "awbLikeSt_v<16>");
    exercise<awbLikeSt_v<34>>(flavour, "awbLikeSt_v<34>");
    exercise<pMisSt_v<64>>(flavour, "pMisSt_v<64>");
    exercise<pMisSt_v<32>>(flavour, "pMisSt_v<32>");
    exercise<pMisNSt_v<64>>(flavour, "pMisNSt_v<64>");
    exercise<pMisNSt_v<32>>(flavour, "pMisNSt_v<32>");
    exercise<pHoldSt_v<2>>(flavour, "pHoldSt_v<2>");
    exercise<pHoldSt_v<12>>(flavour, "pHoldSt_v<12>");
    exercise<pW2St_v<8>>(flavour, "pW2St_v<8>");
    exercise<pW2St_v<64>>(flavour, "pW2St_v<64>");
    exercise<pW2St_v<100>>(flavour, "pW2St_v<100>");
    exercise<pOneArrSt_v<1>>(flavour, "pOneArrSt_v<1>");
    exercise<pOneArrSt_v<3>>(flavour, "pOneArrSt_v<3>");
    exercise<pOneSt_v<1>>(flavour, "pOneSt_v<1>");
    exercise<pOneSt_v<4>>(flavour, "pOneSt_v<4>");
    checkWidths(flavour);
    exerciseTail(flavour);
}
