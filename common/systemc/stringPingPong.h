#ifndef STRING_PING_PONG_H
#define STRING_PING_PONG_H
#include <array>
#include <string>
#include "q_assert.h"

class stringPingPong {
public:

    // Push with lvalue reference (copy)
    void push(const std::string& str) {
        Q_ASSERT_CTX(buffer[pushIndex].empty(), __func__,"Overflow: Buffer is already full");
        buffer[pushIndex] = str;
        pushIndex ^= 1;
    }
    // Push with rvalue reference (move)
    void push(std::string&& str) {
        Q_ASSERT_CTX(buffer[pushIndex].empty(), __func__, "Overflow: Buffer is already full");
        buffer[pushIndex] = std::move(str);
        pushIndex ^= 1;
    }
    std::string pop() {
        Q_ASSERT_CTX(!buffer[popIndex].empty(), __func__, "Underflow: Buffer is empty");
        std::string result = buffer[popIndex];
        buffer[popIndex].clear();
        popIndex ^= 1;
        return result;
    }
    bool isEmpty() const {
        return buffer[popIndex].empty();
    }
    bool isFull() const {
        return !buffer[pushIndex].empty();
    }
private:
    std::array<std::string, 2> buffer;
    int pushIndex = 0;
    int popIndex = 0;
};
#endif // STRING_PING_PONG_H