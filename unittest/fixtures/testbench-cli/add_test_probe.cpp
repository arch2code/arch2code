// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Runs the shipped sc_main (common/scmain/main.cpp) with testbenches that run
// their tests with ADD_TEST. Each test prints "ran <name>" when it runs.
//
// addTestProbe lists alpha, shared, beta and gamma, and registers them out of
// that order. Two blocks each add a function named shared; the slow one returns
// 40 ns after the fast one.
// missingProbe lists forgotten and alsoForgotten, which nothing runs.
// mixedNamesProbe runs alpha with ADD_TEST and oldStyle with
// register_test_name and wait_test.
// mixedSameNameProbe runs alpha both ways.
// earlyOldFormProbe runs alpha both ways, calling register_test_name from a
// constructor before the ADD_TEST.
// oldFormProbe runs oldStyle the old way only.
// relistProbe calls set_test_names again after ADD_TEST.
// unlistedProbe runs ADD_TEST before set_test_names.
// The probes that should finish stop the simulation once every test completes,
// so a run that hangs reaches --scTimeLimit instead.

#include "main.cpp"
#include "testController.h"
#include <memory>
#include <string>

struct addTestHarness : sc_module
{
    SC_HAS_PROCESS( addTestHarness );
    explicit addTestHarness( sc_module_name n ) : sc_module( n )
    {
        ADD_TEST( gamma );
        ADD_TEST( beta );
        ADD_TEST( shared );
        ADD_TEST( alpha );
        SC_THREAD( finish );
    }
    void alpha() { wait( 10, SC_NS ); std::cout << "ran alpha\n"; }
    void beta() { wait( 10, SC_NS ); std::cout << "ran beta\n"; }
    void gamma() { wait( 10, SC_NS ); std::cout << "ran gamma\n"; }
    void shared() { wait( 10, SC_NS ); std::cout << "ran shared fast\n"; }
    void finish()
    {
        testController::GetInstance().wait_all_tests_complete();
        sc_stop();
    }
};

struct addTestPeer : sc_module
{
    SC_HAS_PROCESS( addTestPeer );
    explicit addTestPeer( sc_module_name n ) : sc_module( n ) { ADD_TEST( shared ); }
    void shared() { wait( 50, SC_NS ); std::cout << "ran shared slow\n"; }
};

struct addTestProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<addTestHarness> harness;
    std::unique_ptr<addTestPeer> peer;
    bool createTestBench( void ) override
    {
        testController::GetInstance().set_test_names( { "alpha", "shared", "beta", "gamma" } );
        harness = std::make_unique<addTestHarness>( "harness" );
        peer = std::make_unique<addTestPeer>( "peer" );
        return true;
    }
};

struct finisher : sc_module
{
    SC_HAS_PROCESS( finisher );
    explicit finisher( sc_module_name n ) : sc_module( n ) { SC_THREAD( finish ); }
    void finish()
    {
        testController::GetInstance().wait_all_tests_complete();
        sc_stop();
    }
};

struct missingHarness : sc_module
{
    SC_HAS_PROCESS( missingHarness );
    explicit missingHarness( sc_module_name n ) : sc_module( n ) { ADD_TEST( alpha ); }
    void alpha() { wait( 10, SC_NS ); std::cout << "ran alpha\n"; }
};

struct missingProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<missingHarness> harness;
    bool createTestBench( void ) override
    {
        testController::GetInstance().set_test_names( { "alpha", "forgotten", "alsoForgotten" } );
        harness = std::make_unique<missingHarness>( "harness" );
        return true;
    }
};

// Runs test_name the old way, from its own thread.
struct oldStyleHarness : sc_module
{
    SC_HAS_PROCESS( oldStyleHarness );
    oldStyleHarness( sc_module_name n, std::string test_name ) : sc_module( n ), m_test_name( test_name )
    {
        SC_THREAD( run );
    }
    void run()
    {
        testController &controller = testController::GetInstance();
        controller.register_test_name( m_test_name );
        controller.wait_test( m_test_name, sc_time( 10, SC_NS ) );
        std::cout << "ran " << m_test_name << " old style\n";
        controller.test_complete( m_test_name );
    }
    std::string m_test_name;
};

struct mixedNamesProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<missingHarness> harness;
    std::unique_ptr<oldStyleHarness> oldStyle;
    std::unique_ptr<finisher> done;
    bool createTestBench( void ) override
    {
        testController::GetInstance().set_test_names( { "alpha", "oldStyle" } );
        harness = std::make_unique<missingHarness>( "harness" );
        oldStyle = std::make_unique<oldStyleHarness>( "oldStyle", "oldStyle" );
        done = std::make_unique<finisher>( "done" );
        return true;
    }
};

struct mixedSameNameProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<missingHarness> harness;
    std::unique_ptr<oldStyleHarness> oldStyle;
    std::unique_ptr<finisher> done;
    bool createTestBench( void ) override
    {
        testController::GetInstance().set_test_names( { "alpha" } );
        harness = std::make_unique<missingHarness>( "harness" );
        oldStyle = std::make_unique<oldStyleHarness>( "oldStyle", "alpha" );
        done = std::make_unique<finisher>( "done" );
        return true;
    }
};

// Registers alpha from its constructor, then runs it the old way.
struct earlyOldStyleHarness : sc_module
{
    SC_HAS_PROCESS( earlyOldStyleHarness );
    explicit earlyOldStyleHarness( sc_module_name n ) : sc_module( n )
    {
        testController::GetInstance().register_test_name( "alpha" );
        SC_THREAD( run );
    }
    void run()
    {
        testController &controller = testController::GetInstance();
        controller.wait_test( "alpha", sc_time( 10, SC_NS ) );
        std::cout << "ran alpha old style\n";
        controller.test_complete( "alpha" );
    }
};

struct earlyOldFormProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<earlyOldStyleHarness> oldStyle;
    std::unique_ptr<missingHarness> harness;
    std::unique_ptr<finisher> done;
    bool createTestBench( void ) override
    {
        testController::GetInstance().set_test_names( { "alpha" } );
        oldStyle = std::make_unique<earlyOldStyleHarness>( "oldStyle" );
        harness = std::make_unique<missingHarness>( "harness" );
        done = std::make_unique<finisher>( "done" );
        return true;
    }
};

struct oldFormProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<oldStyleHarness> oldStyle;
    std::unique_ptr<finisher> done;
    bool createTestBench( void ) override
    {
        testController::GetInstance().set_test_names( { "oldStyle" } );
        oldStyle = std::make_unique<oldStyleHarness>( "oldStyle", "oldStyle" );
        done = std::make_unique<finisher>( "done" );
        return true;
    }
};

struct relistProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<missingHarness> harness;
    std::unique_ptr<finisher> done;
    bool createTestBench( void ) override
    {
        testController::GetInstance().set_test_names( { "alpha" } );
        harness = std::make_unique<missingHarness>( "harness" );
        done = std::make_unique<finisher>( "done" );
        testController::GetInstance().set_test_names( { "alpha" } );
        return true;
    }
};

struct unlistedProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<missingHarness> harness;
    bool createTestBench( void ) override
    {
        harness = std::make_unique<missingHarness>( "harness" );
        testController::GetInstance().set_test_names( { "alpha" } );
        return true;
    }
};

static int registerAddTestProbeConfigs()
{
    testBenchConfigFactory::registerTestBenchConfig( "addTestProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<addTestProbeConfig>(); } );
    testBenchConfigFactory::registerTestBenchConfig( "missingProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<missingProbeConfig>(); } );
    testBenchConfigFactory::registerTestBenchConfig( "mixedNamesProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<mixedNamesProbeConfig>(); } );
    testBenchConfigFactory::registerTestBenchConfig( "mixedSameNameProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<mixedSameNameProbeConfig>(); } );
    testBenchConfigFactory::registerTestBenchConfig( "earlyOldFormProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<earlyOldFormProbeConfig>(); } );
    testBenchConfigFactory::registerTestBenchConfig( "oldFormProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<oldFormProbeConfig>(); } );
    testBenchConfigFactory::registerTestBenchConfig( "relistProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<relistProbeConfig>(); } );
    testBenchConfigFactory::registerTestBenchConfig( "unlistedProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<unlistedProbeConfig>(); } );
    return 0;
}
[[maybe_unused]] static int addTestProbeConfigsRegistered = registerAddTestProbeConfigs();
