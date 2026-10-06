// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef OPTIONAL_PAYLOAD_H
#define OPTIONAL_PAYLOAD_H
#include <type_traits>
#include <variant>

// An absent optional payload is spelled std::monostate. The sentinel is not
// a payload: it has no pack(), no _packedSt and no width, and is never asked
// for any of them, because every site that touches an optional payload is
// guarded by hasOptionalPayload. A design without the payload therefore emits
// exactly the code, the packed layout and the storage size it had before the
// payload existed.
//
// This is the single spelling of the optional payload presence test. Test
// through it rather than comparing against std::monostate directly.
template <typename T>
inline constexpr bool hasOptionalPayload = !std::is_same_v<T, std::monostate>;

// Optional payload bit contribution. A literal 0 for the sentinel, whose
// _bitWidth is never named; if constexpr is required here because a conditional
// expression would still instantiate the discarded T::_bitWidth.
template <typename T>
constexpr unsigned int optionalPayloadBitWidth()
{
    if constexpr (hasOptionalPayload<T>) {
        return T::_bitWidth;
    } else {
        return 0;
    }
}

#endif //OPTIONAL_PAYLOAD_H
