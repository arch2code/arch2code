#ifndef SIMPLE_QUEUE_H
#define SIMPLE_QUEUE_H
#include <vector>
#include "q_assert.h"

template <typename T> 
class simpleQueue {
public:
    simpleQueue(std::size_t capacity) : data_(capacity), head_(0), tail_(0), size_(0), capacity_(capacity) {}
    ~simpleQueue() {
        // Properly destroy objects if T is not trivially destructible
        if constexpr (!std::is_trivially_destructible_v<T>) {
            while (!isEmpty()) {
                pop(); // Ensure all elements are destroyed
            }
        }
    }
    // Add an element to the queue
    void push(const T& item) {
        Q_ASSERT_CTX(!isFull(), __func__, "Queue is full");
        data_[tail_] = item;
        tail_ = (tail_ + 1) % capacity_;
        ++size_;
    }
    // Emplace an element directly into the queue
    template <typename... Args>
    void emplace(Args&&... args) {
        Q_ASSERT_CTX(!isFull(), __func__,"Queue is full");
        data_[tail_] = T(std::forward<Args>(args)...); // Perfect forward arguments
        tail_ = (tail_ + 1) % capacity_;
        ++size_;
    }

    // Remove an element from the queue
    T pop() 
    {
        Q_ASSERT_CTX(!isEmpty(), __func__, "Queue is empty");
        T item = data_[head_];
        head_ = (head_ + 1) % capacity_;
        --size_;
        return item;
    }

    // Check if the queue is empty
    bool isEmpty() const {
        return size_ == 0;
    }

    // Check if the queue is full
    bool isFull() const {
        return size_ == capacity_;
    }

    // Get the current size of the queue
    std::size_t size() const {
        return size_;
    }

    // Peek at the front element without removing
    T front() const 
    {
        Q_ASSERT_CTX(!isEmpty(), __func__, "Queue is empty");
        return data_[head_];
    }

private:
    std::vector<T> data_;
    std::size_t head_;
    std::size_t tail_;
    std::size_t size_;
    std::size_t capacity_;
};
#endif // SIMPLE_QUEUE_H