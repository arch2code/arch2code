//
#include "testController.h"
#include "pySocketIpc.h"
#include <poll.h>
#include <unistd.h>
#include "endOfTest.h"

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "pySocket.h"
SC_HAS_PROCESS(pySocket);

pySocket::registerBlock pySocket::registerBlock_; //register the block with the factory

pySocket::pySocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("pySocket", name(), bbMode)
        ,pySocketBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(socketTest);
};

void pySocket::socketTest(void)
{
    testController &controller = testController::GetInstance();
    endOfTest eot;
    eot.registerVoter();

    std::string test_socket = "test_socket_rw";
    controller.register_test_name(test_socket);
    
    // Wait for socket test
    controller.wait_test(test_socket, sc_time(1, SC_NS));

    {
        char buf[256];
        int count = 0;
        ssize_t n = 0;
        pollfd pfd;
        pfd.fd = pySocketIpc::fd_py_to_sc();
        pfd.events = POLLIN;
        char scbuf[2][256] = {"sc_write_0\n", "sc_write_1\n"};
        do {
            n = 0;
            do {
                if (poll(&pfd, 1, 1000) > 0) {
                    n = read(pySocketIpc::fd_py_to_sc(), buf, sizeof(buf));
                } else {
                    wait(100, SC_NS);
                }
            } while (n==0);
            uint32_t int_val1 = *reinterpret_cast<int*>(buf);
            uint32_t int_val2 = *reinterpret_cast<int*>(buf + 4);
            uint32_t sum = int_val1 + int_val2;
            std::cout << "pySocket.py: received " << int_val1 << " " << int_val2 << std::endl;
            write(pySocketIpc::fd_sc_to_py(), &sum, 4);
            count++;
        } while (count < 2);
    }

    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

