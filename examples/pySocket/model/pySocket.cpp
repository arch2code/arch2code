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
    SC_THREAD(python2SystemCTest);
    SC_THREAD(systemC2PythonTest);
    SC_THREAD(python2SystemCEventThread);
    SC_THREAD(dut2PythonListener);
};

//  TODO: improve this code to avoid the clunky event handoff
void pySocket::python2SystemCEventThread(void)
{
    while (true) {
        wait(p2s_startEvent);
        pollfd pfd;
        pfd.fd = pySocketIpc::fd_py2sc_request();
        pfd.events = POLLIN;
        if (poll(&pfd, 1, -1) > 0) {
            p2s_dataReadyEvent.notify();
            // wait(0, SC_NS);
        }
    }
}

void pySocket::python2SystemCTest(void)
{
    testController &controller = testController::GetInstance();
    endOfTest eot;
    eot.registerVoter();

    std::string test_socket = "python2SystemCTest";
    controller.register_test_name(test_socket);
    
    // Wait for socket test
    controller.wait_test(test_socket, sc_time(1, SC_NS));

    {
        char buf[256];
        int count = 0;
        ssize_t n = 0;
        ssize_t m = 0;
        pollfd pfd;
        pfd.fd = pySocketIpc::fd_py2sc_request();
        pfd.events = POLLIN;
        do {
            p2s_startEvent.notify();
            wait(p2s_dataReadyEvent);
            n = 0;
            do {
                m = read(pySocketIpc::fd_py2sc_request(), buf + n, sizeof(buf) - n);
                if (m > 0) {
                    n += m;
                }
            } while (n < (ssize_t)sizeof(p2s_message_st));
            p2s_message_st message;
            message.param1 = *reinterpret_cast<uint32_t*>(buf);
            message.param2 = *reinterpret_cast<uint32_t*>(buf + 4);
            p2s_response_st response;
            test_req_ack->req(message, response);
            uint32_t sum = response.response;
            std::cout << "pySocket.py: received " << message.param1 << " " << message.param2 << " and sent " << sum << std::endl;
            write(pySocketIpc::fd_py2sc_response(), &sum, 4);
            count++;
        } while (count < 2);
    }

    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

void pySocket::systemC2PythonTest(void)
{
    testController &controller = testController::GetInstance();
    endOfTest eot;
    eot.registerVoter();

    std::string test_socket = "systemC2PythonTest";
    controller.register_test_name(test_socket);
    
    // Wait for socket test
    controller.wait_test(test_socket, sc_time(1, SC_NS));

    // test makes a request to the dut
    // dut will then make a request to the python code which will get processed in dut2PythonListener
    // the python code will then send a response back to the dut which will also be processed in dut2PythonListener
    // dut2PythonListener will then send a response back to the dut
    // the dut will respond to this test
    {
        p2s_message_st message;
        message.param1 = 0xcafef00d;
        message.param2 = 0x12345678;
        p2s_response_st response;
        test2Python_req_ack->req(message, response);
        Q_ASSERT(response.response == 0xdeadbeef, "response.response != 0xdeadbeef");

        // write 0 to request socket to indicate the end of the test
        message.param1 = 0x00000000;
        message.param2 = 0x00000000;
        test2Python_req_ack->req(message, response);
        Q_ASSERT(response.response == 0, "response.response != 0");
    }

    controller.test_complete(test_socket);
    eot.setEndOfTest(true);
}

void pySocket::dut2PythonListener(void)
{
    while (true) {
        p2s_message_st message;
        p2s_response_st response;
        dut2Python_req_ack->reqReceive(message);

        // write to python through socket
        write(pySocketIpc::fd_sc2py_request(), &message, sizeof(p2s_message_st));
        uint32_t response_value = 0;
        // read response from python through socket
        read(pySocketIpc::fd_sc2py_response(), &response_value, 4);

        // send response back to dut
        response.response = response_value;
        dut2Python_req_ack->ack(response);
    }
}