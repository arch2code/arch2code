//

#include "systemc.h"
#include <string>
#include <stdlib.h>
#include <unistd.h>
#include <limits.h>
#include <sys/wait.h>
#include <cstdio>

#include "instanceFactory.h"
#include "socketFactory.h"
#include "socketTransport.h"
#include "testBenchConfigFactory.h"
#include "endOfTest.h"
#include "testController.h"

// Absolute path to pySocket.py: do not rely on getcwd() — runs may start from FIPS/rundir or .../pySocket/rundir.
std::string resolvePySocketScriptPath()
{
    if (const char *env = getenv("PYSOCKET_PY_SCRIPT")) {
        if (env[0] != '\0') {
            char resolved[PATH_MAX];
            if (realpath(env, resolved) != nullptr) {
                return std::string(resolved);
            }
            return std::string(env);
        }
    }

    // get the full path of the current executable
    char self_path[PATH_MAX];
    const ssize_t n = readlink("/proc/self/exe", self_path, sizeof(self_path) - 1);
    if (n < 0) {
        return {};
    }
    self_path[n] = '\0';
    std::string build_dir(self_path);
    const auto slash = build_dir.find_last_of('/');
    if (slash == std::string::npos) {
        return {};
    }
    build_dir.resize(slash);

    // build the path to the pySocket.py script relative to the executable
    const std::string candidate = build_dir + "/../../pySocket.py";
    // resolve the path to the pySocket.py script if it exists
    char resolved[PATH_MAX];
    if (realpath(candidate.c_str(), resolved) != nullptr) {
        // python code found, return the path
        return std::string(resolved);
    }
    // python code not found, return an empty string
    return {};
}

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=tbConfig

class pySocketConfig : public testBenchConfigBase
{
public:
    struct registerTestBenchConfig
    {
        registerTestBenchConfig()
        {
            // lamda function to construct the testbench
            testBenchConfigFactory::registerTestBenchConfig("pySocket", [](std::string) -> std::shared_ptr<testBenchConfigBase> { return static_cast<std::shared_ptr<testBenchConfigBase>> (std::make_shared<pySocketConfig>());}, is_default_testbench_v<pySocketConfig>);
        }
    };
    static registerTestBenchConfig registerTestBenchConfig_;
    virtual ~pySocketConfig() override = default; // Explicit Virtual Destructor
    // static constexpr bool isDefaultTestBench = true; // move out of generated section and uncomment to set this tb as default
// GENERATED_CODE_END

private:
    pid_t python_pid_ = -1;
    std::string ports_file_ = "";
    std::string ports_env_file_ = "";
    bool skip_sidecar_ = false;

public:
    bool createTestBench(void) override
    {
        instanceFactory::registerInstance("pySocket_tb.u_pySocket", "socket");

        std::shared_ptr<blockBase> tb = instanceFactory::createInstance("", "pySocket_tb", "pySocket_tb", "");

        if (socketFactory::registerInterface("test_req_ack") == 0) {
            return false;
        }
        if (socketFactory::registerInterface("test2Python_req_ack") == 0) {
            socketFactory::shutdownAll();
            return false;
        }
        if (socketFactory::registerInterface("dut2Python_req_ack") == 0) {
            socketFactory::shutdownAll();
            return false;
        }

        if (setenv("PYSOCKET_PORTS", socketFactory::getPortString().c_str(), 1) != 0) {
            socketFactory::shutdownAll();
            return false;
        }

        if (ports_file_.empty() && getenv("PYSOCKET_PORTS_FILE") != nullptr) {
            ports_file_ = getenv("PYSOCKET_PORTS_FILE");
        }
        if (!ports_file_.empty()) {
            FILE *fp = std::fopen(ports_file_.c_str(), "w");
            if (fp != nullptr) {
                std::fprintf(fp, "%s\n", socketFactory::getPortString().c_str());
                std::fclose(fp);
            }
        }

        if (ports_env_file_.empty() && getenv("PYSOCKET_PORTS_ENV_FILE") != nullptr) {
            ports_env_file_ = getenv("PYSOCKET_PORTS_ENV_FILE");
        }
        if (!ports_env_file_.empty()) {
            FILE *fp = std::fopen(ports_env_file_.c_str(), "w");
            if (fp != nullptr) {
                std::fprintf(fp, "export PYSOCKET_PORTS=%s\n", socketFactory::getPortString().c_str());
                std::fclose(fp);
            }
        }

        if (getenv("PYSOCKET_SKIP_PYTHON_SIDECAR") != nullptr) {
            skip_sidecar_ = true;
        }
        std::string sc_ports_file = "";
        if (!skip_sidecar_) {
            const std::string script_path = resolvePySocketScriptPath();
            if (script_path.empty()) {
                socketFactory::shutdownAll();
                return false;
            }
            pid_t sc_pid = getpid();
            sc_ports_file = "/tmp/pysocket_ports_" + std::to_string(sc_pid) + ".env";
            FILE *fp = std::fopen(sc_ports_file.c_str(), "w");
            if (fp != nullptr) {
                std::fprintf(fp, "%s", socketFactory::getPortString().c_str());
                std::fclose(fp);
            }
            pid_t pid = fork();
            if (pid == 0) {
                execlp("python3", "python3", script_path.c_str(), sc_ports_file.c_str(), nullptr);
                _exit(127);
            }
            if (pid < 0) {
                socketFactory::shutdownAll();
                return false;
            }
            python_pid_ = pid;
        } else {
            python_pid_ = -1;
        }

        socketFactory::acceptAll();

        if (socketFactory::getFd("test_req_ack") < 0 || socketFactory::getFd("test2Python_req_ack") < 0
            || socketFactory::getFd("dut2Python_req_ack") < 0) {
            socketFactory::shutdownAll();
            return false;
        }

        // Remove the ports file if it exists since we have already connected
        if (!sc_ports_file.empty()) {
            std::remove(sc_ports_file.c_str());
        }
        testController &controller = testController::GetInstance();
        controller.set_test_names({
            "python2SystemCTest",
            "systemC2PythonTest"
        });

        (void)tb;
        return true;
    }

    void addProgramOptions(po::options_description &options) override
    {
        options.add_options()
            ("PYSOCKET_PORTS_FILE", po::value<std::string>(&ports_file_)->default_value(""), "File to write the ports to")
            ("PYSOCKET_PORTS_ENV_FILE", po::value<std::string>(&ports_env_file_)->default_value(""), "File to write the ports environment variables to")
            ("PYSOCKET_SKIP_PYTHON_SIDECAR", po::value<bool>(&skip_sidecar_)->default_value(false), "Skip the Python sidecar");
    }

    void beforeFullSim(void) override
    {
        // Do not call set_test_names here: coordinator SC_THREADs may have already run during
        // zero-time enumeration; set_test_names resets registration counts and leaves
        // m_outstanding_completions inconsistent with threads that already registered.

        // Release Python sidecar to send transactions only after enumeration and startup barrier.
        for (const char *ifc : {"test_req_ack", "test2Python_req_ack", "dut2Python_req_ack"}) {
            const int fd = socketFactory::getFd(ifc);
            if (fd < 0 || !socket_send_msg(fd, MSG_SYNC, nullptr, 0)) {
                return;
            }
        }
    }

    void final(void) override
    {
        // Close sockets first so the Python sidecar can unblock from recv, then reap the child.
        socketFactory::shutdownAll();
        if (python_pid_ > 0) {
            int status = 0;
            (void)waitpid(python_pid_, &status, 0);
            python_pid_ = -1;
        }
        // Final cleanup if needed
        Q_ASSERT_CTX(endOfTestState::GetInstance().isEndOfTest(), "final", "Premature end of test detected");
        errorCode::pass();
    }

};
pySocketConfig::registerTestBenchConfig pySocketConfig::registerTestBenchConfig_; //register the testBench with the factory
