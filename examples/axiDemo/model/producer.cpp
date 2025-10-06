// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "testController.h"

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "producer.h"
SC_HAS_PROCESS(producer);

producer::registerBlock producer::registerBlock_; //register the block with the factory

producer::producer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("producer", name(), bbMode)
        ,producerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(outAXI0Rd);
    SC_THREAD(outAXI1Rd);
    SC_THREAD(outAXI0Wr);
    SC_THREAD(outRespHandlerAXI0Wr);
    SC_THREAD(outAXI1Wr);
    SC_THREAD(outRespHandlerAXI1Wr);
    SC_THREAD(outAXI2Wr);
    SC_THREAD(outRespHandlerAXI2Wr);
    SC_THREAD(outAXI3Wr);
    SC_THREAD(outRespHandlerAXI3Wr);
}
#define LOOPCOUNT 10000
// send and recieve multicycle transactions
void producer::outAXI0Rd(void)
{
    std::string test_name = "test_axird0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    auto start = std::chrono::system_clock::now();
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiReadAddressSt<axiAddrSt> addr;
        addr.araddr.addr = loop;
        addr.arsize = 0x2; // 4 bytes
        addr.arlen = 255; // 256 transfer bursts
        addr.arburst = AXIBURST_INCR;
        addr.arid = 0x1;
        axiReadRespSt<axiDataSt> data;
        axiRd0->push_burst(256);
        axiRd0->sendAddr(addr);
        axiRd0->receiveData(data);
        axiReadRespSt<axiDataSt> *buff = reinterpret_cast<axiReadRespSt<axiDataSt> *>(axiRd0->getReadPtr());
        for (int i = 0; i < 256; i++)
        {
            if (buff[i].rresp != AXIRESP_OKAY ||
                buff[i].rid != addr.arid ||
                buff[i].rdata.data != (axiDataT)i * 0x01010101)
            {
                Q_ASSERT(false, "Data mismatch");
            }
        }
    }
    auto end = std::chrono::system_clock::now();
    std::chrono::duration<double> elapsed_seconds = end-start;
    log_.logPrint(std::format("Test {} Elapsed time: {:f}", test_name, elapsed_seconds.count()), LOG_ALWAYS);
    controller.test_complete(test_name);
}

// send and recieve single cycle transactions
void producer::outAXI1Rd(void)
{
    axiRd1->setCycleTransaction(PORTTYPE_OUT);
    std::string test_name = "test_axird1";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    auto start = std::chrono::system_clock::now();
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiReadAddressSt<axiAddrSt> addr;
        addr.araddr.addr = loop;
        addr.arsize = 0x2; // 4 bytes
        addr.arlen = 255; // 256 transfer bursts
        addr.arburst = AXIBURST_INCR;
        addr.arid = 0x1;
        axiReadRespSt<axiDataSt> cycleData;
        axiRd1->sendAddr(addr);
        for (int i = 0; i < 256; i++)
        {
            axiRd1->receiveDataCycle(cycleData);
            if (cycleData.rresp != AXIRESP_OKAY ||
                cycleData.rid != addr.arid ||
                cycleData.rdata.data != (axiDataT)i * 0x01010101)
            {
                Q_ASSERT(false, "Data mismatch");
            }
            if ((i == 255 && cycleData.rlast == 0) || (i < 255 && cycleData.rlast == 1))
            {
                log_.logPrint(std::format("Last set incorrectly on cycle: %i", i));
                Q_ASSERT(false, "last wrong");
            }
        }
    }
    auto end = std::chrono::system_clock::now();
    std::chrono::duration<double> elapsed_seconds = end-start;
    log_.logPrint(std::format("Test {} Elapsed time: {:f}", test_name, elapsed_seconds.count()), LOG_ALWAYS);
    controller.test_complete(test_name);
}
// send and recieve multicycle transactions
void producer::outAXI0Wr(void)
{
    std::string test_name = "test_axiwr0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    auto start = std::chrono::system_clock::now();
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiWriteAddressSt<axiAddrSt> addr;
        addr.awid = 0x1;
        addr.awaddr.addr = loop;
        addr.awlen = 255; // 256 transfer bursts
        addr.awsize = 0x2; // 4 bytes
        addr.awburst = AXIBURST_INCR;
        axiWr0->sendAddr(addr);
        axiWriteDataSt<axiDataSt, axiStrobeSt> *buff = reinterpret_cast<axiWriteDataSt<axiDataSt, axiStrobeSt> *>(axiWr0->getSendDataPtr());
        for (int i = 0; i < 256; i++)
        {
            buff[i].wid = addr.awid;
            buff[i].wdata.data = i * 0x01010101;
            buff[i].wstrb.strobe = 0xF;
            buff[i].wlast = (i == 255);
        }
        axiWr0->sendData(*buff, 256);
    }
    auto end = std::chrono::system_clock::now();
    std::chrono::duration<double> elapsed_seconds = end-start;
    log_.logPrint(std::format("Test {} Elapsed time: {:f}", test_name, elapsed_seconds.count()), LOG_ALWAYS);
    controller.test_complete(test_name);
}
void producer::outRespHandlerAXI0Wr(void)
{
    std::string test_name = "test_axiwr0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiWriteRespSt resp;
        axiWr0->receiveResp(resp);
        if (resp.bresp != AXIRESP_OKAY ||
            resp.bid != 0x1)
        {
            Q_ASSERT(false, "Data mismatch");
        }
    }
    controller.test_complete(test_name);
    log_.logPrint(std::format("Response Test {}", test_name ), LOG_ALWAYS);
}
// send multicycle transaction and recieve single cycle transaction
void producer::outAXI1Wr(void)
{
    std::string test_name = "test_axiwr1";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    auto start = std::chrono::system_clock::now();
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiWriteAddressSt<axiAddrSt> addr;
        addr.awid = 0x1;
        addr.awaddr.addr = loop;
        addr.awlen = 255; // 256 transfer bursts
        addr.awsize = 0x2; // 4 bytes
        addr.awburst = AXIBURST_INCR;
        axiWr1->sendAddr(addr);
        axiWriteDataSt<axiDataSt, axiStrobeSt> *buff = reinterpret_cast<axiWriteDataSt<axiDataSt, axiStrobeSt> *>(axiWr1->getSendDataPtr());
        for (int i = 0; i < 256; i++)
        {
            buff[i].wid = addr.awid;
            buff[i].wdata.data = i * 0x01010101;
            buff[i].wstrb.strobe = 0xF;
            buff[i].wlast = (i == 255);
        }
        axiWr1->sendData(*buff, 256);
    }
    auto end = std::chrono::system_clock::now();
    std::chrono::duration<double> elapsed_seconds = end-start;
    log_.logPrint(std::format("Test {} Elapsed time: {:f}", test_name, elapsed_seconds.count()), LOG_ALWAYS);
    controller.test_complete(test_name);
}
void producer::outRespHandlerAXI1Wr(void)
{
   std::string test_name = "test_axiwr1";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiWriteRespSt resp;
        axiWr1->receiveResp(resp);
        if (resp.bresp != AXIRESP_OKAY ||
            resp.bid != 0x1)
        {
            Q_ASSERT(false, "Data mismatch");
        }

    }
    controller.test_complete(test_name);
    log_.logPrint(std::format("Response Test {}", test_name ), LOG_ALWAYS);
}

// send single cycle transaction and recieve multicycle transaction
void producer::outAXI2Wr(void)
{
    axiWr2->setCycleTransaction(PORTTYPE_OUT);
    std::string test_name = "test_axiwr2";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    auto start = std::chrono::system_clock::now();
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiWriteAddressSt<axiAddrSt> addr;
        addr.awid = 0x1;
        addr.awaddr.addr = loop;
        addr.awlen = 255; // 256 transfer bursts
        addr.awsize = 0x2; // 4 bytes
        addr.awburst = AXIBURST_INCR;
        axiWr2->sendAddr(addr);
        for (int i = 0; i < 256; i++)
        {
            axiWriteDataSt<axiDataSt, axiStrobeSt> data;
            data.wid = addr.awid;
            data.wdata.data = i * 0x01010101;
            data.wstrb.strobe = 0xF;
            data.wlast = (i == 255);
            axiWr2->sendDataCycle(data);
        }
    }
    auto end = std::chrono::system_clock::now();
    std::chrono::duration<double> elapsed_seconds = end-start;
    log_.logPrint(std::format("Test {} Elapsed time: {:f}", test_name, elapsed_seconds.count()), LOG_ALWAYS);
    controller.test_complete(test_name);
}
void producer::outRespHandlerAXI2Wr(void)
{
   std::string test_name = "test_axiwr2";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiWriteRespSt resp;
        axiWr2->receiveResp(resp);
        if (resp.bresp != AXIRESP_OKAY ||
            resp.bid != 0x1)
        {
            Q_ASSERT(false, "Data mismatch");
        }

    }
    controller.test_complete(test_name);
}

// send and recieve single cycle transactions
void producer::outAXI3Wr(void)
{
    axiWr3->setCycleTransaction(PORTTYPE_OUT);
    std::string test_name = "test_axiwr3";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    auto start = std::chrono::system_clock::now();
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiWriteAddressSt<axiAddrSt> addr;
        addr.awid = 0x1;
        addr.awaddr.addr = loop;
        addr.awlen = 255; // 256 transfer bursts
        addr.awsize = 0x2; // 4 bytes
        addr.awburst = AXIBURST_INCR;
        axiWr3->sendAddr(addr);
        for (int i = 0; i < 256; i++)
        {
            axiWriteDataSt<axiDataSt, axiStrobeSt> data;
            data.wid = addr.awid;
            data.wdata.data = i * 0x01010101;
            data.wstrb.strobe = 0xF;
            data.wlast = (i == 255);
            axiWr3->sendDataCycle(data);
        }
    }
    auto end = std::chrono::system_clock::now();
    std::chrono::duration<double> elapsed_seconds = end-start;
    log_.logPrint(std::format("Test {} Elapsed time: {:f}", test_name, elapsed_seconds.count()), LOG_ALWAYS);
    controller.test_complete(test_name);
}
void producer::outRespHandlerAXI3Wr(void)
{
   std::string test_name = "test_axiwr3";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop = 0; loop < LOOPCOUNT; loop++)
    {
        axiWriteRespSt resp;
        axiWr3->receiveResp(resp);
        if (resp.bresp != AXIRESP_OKAY ||
            resp.bid != 0x1)
        {
            Q_ASSERT(false, "Data mismatch");
        }

    }
    log_.logPrint(std::format("Response Test {}", test_name ), LOG_ALWAYS);
    controller.test_complete(test_name);
}
