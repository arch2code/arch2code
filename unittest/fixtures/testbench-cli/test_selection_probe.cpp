// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
//
// Runs the shipped sc_main (common/scmain/main.cpp) with two testbenches.
// selectProbe declares tests alpha, beta and gamma with testController; each
// test thread prints "ran <name>" when its turn comes. noTestsProbe never calls
// set_test_names.

#include "main.cpp"
#include "testController.h"
#include <memory>
#include <string>

struct selectHarness : sc_module
{
    SC_HAS_PROCESS( selectHarness );
    explicit selectHarness( sc_module_name n ) : sc_module( n )
    {
        SC_THREAD( alpha );
        SC_THREAD( beta );
        SC_THREAD( gamma );
        SC_THREAD( finish );
    }

    void runTest( const std::string &name )
    {
        testController &controller = testController::GetInstance();
        controller.register_test_name( name );
        controller.wait_test( name, sc_time( 10, SC_NS ) );
        std::cout << "ran " << name << "\n";
        controller.test_complete( name );
    }
    void alpha() { runTest( "alpha" ); }
    void beta() { runTest( "beta" ); }
    void gamma() { runTest( "gamma" ); }
    void finish()
    {
        testController::GetInstance().wait_all_tests_complete();
        sc_stop();
    }
};

struct selectProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<selectHarness> harness;
    bool createTestBench( void ) override
    {
        testController::GetInstance().set_test_names( { "alpha", "beta", "gamma" } );
        harness = std::make_unique<selectHarness>( "harness" );
        return true;
    }
};

struct noTestsHarness : sc_module
{
    SC_HAS_PROCESS( noTestsHarness );
    explicit noTestsHarness( sc_module_name n ) : sc_module( n ) { SC_THREAD( run ); }
    void run()
    {
        wait( 10, SC_NS );
        std::cout << "ran noTests\n";
        sc_stop();
    }
};

struct noTestsProbeConfig : public testBenchConfigBase
{
    std::unique_ptr<noTestsHarness> harness;
    bool createTestBench( void ) override
    {
        harness = std::make_unique<noTestsHarness>( "harness" );
        return true;
    }
};

static int registerSelectionProbeConfigs()
{
    testBenchConfigFactory::registerTestBenchConfig( "selectProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<selectProbeConfig>(); } );
    testBenchConfigFactory::registerTestBenchConfig( "noTestsProbe", []( std::string ) -> std::shared_ptr<testBenchConfigBase> {
        return std::make_shared<noTestsProbeConfig>(); } );
    return 0;
}
[[maybe_unused]] static int selectionProbeConfigsRegistered = registerSelectionProbeConfigs();
