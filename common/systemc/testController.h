#ifndef TESTCONTROLLER_H
#define TESTCONTROLLER_H
// copyright the Arch2Code project contributors

#include "systemc.h"
#include <list>
#include <string>
#include <map>

class testController
{
public:
    // simple singleton that provides sequencing of tests through test number and event
    static testController &GetInstance() {
        static testController instance;
        return instance;
    }
    // function to allow initialization of the list of tests
    void set_test_names(std::list<std::string> test_names) {
        m_test_names = test_names;
        for (auto test_name : m_test_names) {
            m_test_name_registration_count[test_name] = 0;
        }
        m_total_tests = m_test_names.size();
        m_current_test = m_test_names.front();
        m_test_names.pop_front();
    }
    void register_test_name(std::string test_name) {
        // check if test name is valid
        if (m_test_name_registration_count.find(test_name) == m_test_name_registration_count.end()) {
            std::cout << "ERROR: test name " << test_name << " is not valid" << '\n';
            exit(1);
        }
        m_test_name_registration_count[test_name]++;
        // the first test is a special case, as it is started automatically
        if (test_name == m_current_test) {
            m_outstanding_completions++;
        }
    }
    void wait_test(std::string test_name) {
        // wait for test name match
        while (test_name != m_current_test) {
            wait(test_sequencer_event);
        }
    }
    void test_complete(std::string test_name) {
        if (test_name != m_current_test) {
            std::cout << "ERROR: test name " << test_name << " is not the current test" << '\n';
            exit(1);
        }
        m_outstanding_completions--;
        if (m_outstanding_completions == 0) {
            std::cout << "Completing test " << test_name << '\n';
            m_test_number++;
            if (m_test_number < m_total_tests) {
                m_current_test = m_test_names.front();
                m_test_names.pop_front();
                m_outstanding_completions = m_test_name_registration_count[m_current_test];
                std::cout << "Starting test " << m_current_test << '\n';
                test_sequencer_event.notify();
            } else {
                all_tests_complete_event.notify();
            }
        }
    }
    void wait_test_complete(std::string test_name) {
        while (test_name == m_current_test) {
            wait(test_sequencer_event);
        }
    }

    void wait_all_tests_complete() {
        wait(all_tests_complete_event);
    }

private:
    testController() :
    test_sequencer_event("test_sequencer_event")
    { }
    sc_event  test_sequencer_event;
    sc_event all_tests_complete_event;
    int m_test_number = 0;
    int m_total_tests = 0;
    std::list<std::string> m_test_names;
    std::string m_current_test;
    int m_outstanding_completions = 0;
    std::map<std::string, int> m_test_name_registration_count;

};

#endif //TESTCONTROLLER_H

