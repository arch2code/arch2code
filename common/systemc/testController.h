#ifndef TESTCONTROLLER_H
#define TESTCONTROLLER_H
// copyright the Arch2Code project contributors

#include "systemc.h"
// sc_spawn for add_test, also in builds without SC_INCLUDE_DYNAMIC_PROCESSES.
#include "sysc/kernel/sc_dynamic_processes.h"
#include <algorithm>
#include <functional>
#include <list>
#include <set>
#include <string>
#include <map>
#include <vector>

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
        // add_test counted its bodies against the list it found; a new list would drop them.
        if (!m_tests_with_body.empty()) {
            std::cout << "ERROR: set_test_names runs after add_test or ADD_TEST registered a test. "
                      << "Call set_test_names once, before building the blocks that use ADD_TEST." << std::endl;
            exit(1);
        }
        // A re-call, valid only before any add_test, resets all sequencing state.
        m_test_number = 0;
        m_outstanding_completions = 0;
        m_test_name_registration_count.clear();
        m_declared_test_names = test_names;
        // Threads of unselected tests still register, then wait for a turn that never comes.
        for (const auto &test_name : m_declared_test_names) {
            m_test_name_registration_count[test_name] = 0;
        }
        if (!m_selected_tests.empty()) {
            test_names.remove_if([this](const std::string &test_name) {
                return std::find(m_selected_tests.begin(), m_selected_tests.end(), test_name) == m_selected_tests.end();
            });
        }
        m_test_names = std::move(test_names);
        m_total_tests = static_cast<int>(m_test_names.size());
        if (m_total_tests == 0) {
            m_current_test.clear();
            return;
        }
        m_current_test = m_test_names.front();
        m_test_names.pop_front();
    }
    // The --test names. set_test_names keeps only these, in the testbench's order.
    void select_tests(std::vector<std::string> test_names) {
        m_selected_tests = std::move(test_names);
    }
    // The names last passed to set_test_names, before --test selection.
    const std::list<std::string> &declared_test_names() const {
        return m_declared_test_names;
    }
    void register_test_name(std::string test_name) {
        // check if test name is valid
        if (m_test_name_registration_count.find(test_name) == m_test_name_registration_count.end()) {
            std::cout << "ERROR: test name " << test_name << " is not valid" << '\n';
            exit(1);
        }
        // add_test checks the same clash, for a register_test_name that runs first.
        if (m_tests_with_body.count(test_name)) {
            report_both_forms(test_name);
        }
        m_old_form_names.insert(test_name);
        count_registration(test_name);
    }
    // Runs body as test_name, in its set_test_names turn. Call from a module
    // constructor, after set_test_names. A test left out by --test is never
    // started. Several bodies may share a name; the test completes when all
    // of them return.
    void add_test(std::string test_name, std::function<void()> body) {
        if (m_test_name_registration_count.empty()) {
            std::cout << "ERROR: test name " << test_name << " is not valid: the test list is empty. "
                      << "Call set_test_names before ADD_TEST or add_test." << std::endl;
            exit(1);
        }
        if (m_test_name_registration_count.find(test_name) == m_test_name_registration_count.end()) {
            std::cout << "ERROR: test name " << test_name << " is not valid" << '\n';
            exit(1);
        }
        if (m_old_form_names.count(test_name)) {
            report_both_forms(test_name);
        }
        m_tests_with_body.insert(test_name);
        if (!is_selected(test_name)) {
            return;
        }
        count_registration(test_name);
        sc_core::sc_spawn([this, test_name, body]() {
            wait_test(test_name);
            body();
            test_complete(test_name);
        });
    }
    // True once any add_test has run.
    bool uses_add_test() const {
        return !m_tests_with_body.empty();
    }
    // The tests that will run and that no add_test gave a body, in run order.
    std::vector<std::string> tests_without_body() const {
        std::vector<std::string> missing;
        for (const auto &test_name : m_declared_test_names) {
            if (is_selected(test_name) && !m_tests_with_body.count(test_name)) {
                missing.push_back(test_name);
            }
        }
        return missing;
    }
    void wait_test(std::string test_name, sc_time delay = SC_ZERO_TIME) {
        // wait for test name match
        while (test_name != m_current_test) {
            wait(test_sequencer_event);
        }
        // Optional guardband (e.g. to avoid SC_ZERO_TIME enumeration).
        wait(delay);
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

    // A testbench that seeded no tests has not completed them. Without the
    // m_total_tests guard the comparison is trivially true before
    // set_test_names runs, so a run that checked nothing reports completion.
    bool are_all_tests_complete() {
        return m_total_tests > 0 && m_test_number >= m_total_tests;
    }

private:
    [[noreturn]] void report_both_forms(const std::string &test_name) {
        std::cout << "ERROR: test " << test_name << " runs with add_test or ADD_TEST and also calls register_test_name. "
                  << "Run each test one way, not both." << std::endl;
        exit(1);
    }
    void count_registration(const std::string &test_name) {
        m_test_name_registration_count[test_name]++;
        // the first test is a special case, as it is started automatically
        if (test_name == m_current_test) {
            m_outstanding_completions++;
        }
    }
    bool is_selected(const std::string &test_name) const {
        return test_name == m_current_test
            || std::find(m_test_names.begin(), m_test_names.end(), test_name) != m_test_names.end();
    }
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
    std::vector<std::string> m_selected_tests;
    std::list<std::string> m_declared_test_names;
    std::set<std::string> m_tests_with_body;
    std::set<std::string> m_old_form_names;

};

// Registers member function fn of this module as the test named fn, the way
// SC_THREAD(fn) registers a thread. Use in a module constructor.
#define ADD_TEST(fn) testController::GetInstance().add_test(#fn, [this]() { fn(); })

#endif //TESTCONTROLLER_H

