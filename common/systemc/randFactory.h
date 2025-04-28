#ifndef RANDFACTORY_H
#define RANDFACTORY_H

#include <iostream>
#include <random>
#include <memory>
#include <boost/functional/hash.hpp>

class randObject;
class randUniformIntDistrObj;

class randFactory {
public:

    static std::size_t gSeed;

    static void setSeed(std::size_t seed) {
        gSeed = seed;
    }

    static std::size_t str2hash(std::string s) {
        boost::hash<std::string> hasher;
        return hasher(s);
    }

    static std::unique_ptr<randUniformIntDistrObj> createUniformRandDistrObj(std::size_t hash, int min, int max) {
        return std::make_unique<randUniformIntDistrObj>(hash, min, max);
    }

};

class randObject {

public:
    randObject(std::size_t hash = 0x0) {
        m_seed = randFactory::gSeed;
        // combine global seed and object hash value
        boost::hash_combine(m_seed, hash);
        m_gen = std::default_random_engine (m_seed);
    }
    virtual ~randObject() {}

    virtual int generate() = 0;

protected:
    std::size_t m_seed;
    std::default_random_engine m_gen;
};

template<typename _stdRandDistType>
class randTmplDistrObj : public randObject {

public:

    randTmplDistrObj(std::size_t hash, _stdRandDistType dist) : randObject(hash), m_dist(dist) {}

    int generate() override {
        return m_dist(m_gen);
    }

protected:
    _stdRandDistType m_dist;
};

class randUniformIntDistrObj: public randTmplDistrObj<std::uniform_int_distribution<int> > {

public:
    randUniformIntDistrObj(std::size_t hash, int min, int max) :
        randTmplDistrObj<std::uniform_int_distribution<int> >(hash, std::uniform_int_distribution<int>(min, max)){}

};

#endif // RANDFACTORY_H
