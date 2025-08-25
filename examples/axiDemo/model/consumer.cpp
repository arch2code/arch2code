// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#include "testController.h"

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "consumer.h"
SC_HAS_PROCESS(consumer);

consumer::registerBlock consumer::registerBlock_; //register the block with the factory

consumer::consumer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("consumer", name(), bbMode)
        ,consumerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(inAXI0Rd);
    SC_THREAD(inAXI1Rd);
    SC_THREAD(inAXI0Wr);
    SC_THREAD(inAXI1Wr);
    SC_THREAD(inAXI2Wr);
    SC_THREAD(inAXI3Wr);
}
#define LOOPCOUNT 10000
// send and recieve multicycle transactions
void consumer::inAXI0Rd(void)
{
    std::string test_name = "test_axird0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop=0; loop < LOOPCOUNT; loop++) {
        axiReadAddressSt<axiAddrSt> addr;
        axiReadRespSt<axiDataSt> *resp; // array of max number of bursts
        resp = reinterpret_cast<axiReadRespSt<axiDataSt> *>(axiRd0->getWritePtr());
        axiRd0->receiveAddr(addr);
        int num_bursts = addr.arlen + 1;
        for (int i = 0; i < num_bursts; i++)
        {
            resp[i].rresp = AXIRESP_OKAY;
            resp[i].rid = addr.arid;
            resp[i].rdata.data = i * 0x01010101;
        }
        axiRd0->sendData(*resp, num_bursts);
    }
    controller.test_complete(test_name);
}
// send and recieve single cycle transactions
void consumer::inAXI1Rd(void)
{
    axiRd1->setCycleTransaction(PORTTYPE_IN);
    std::string test_name = "test_axird1";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop=0; loop < LOOPCOUNT; loop++) {
        axiReadAddressSt<axiAddrSt> addr;
        axiReadRespSt<axiDataSt> resp;
        axiRd1->receiveAddr(addr);
        for (int i = 0; i < 256; i++)
        {
            resp.rresp = AXIRESP_OKAY;
            resp.rid = addr.arid;
            resp.rdata.data = i * 0x01010101;
            resp.rlast = (i == 255);
            axiRd1->sendDataCycle(resp);
        }
    }
    controller.test_complete(test_name);
}

// send and recieve multicycle transactions
void consumer::inAXI0Wr(void)
{
    std::string test_name = "test_axiwr0";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop=0; loop < LOOPCOUNT; loop++) {
        axiWriteAddressSt<axiAddrSt> addr;
        axiWriteDataSt<axiDataSt, axiStrobeSt> *data; // array of max number of bursts
        axiWriteDataSt<axiDataSt, axiStrobeSt> dummy;
        axiWriteRespSt resp;
        axiWr0->receiveAddr(addr);
        int num_bursts = addr.awlen + 1;
        axiWr0->receiveData(dummy);
        data = reinterpret_cast<axiWriteDataSt<axiDataSt, axiStrobeSt> *>(axiWr0->getReceiveDataPtr());
        resp.bresp = AXIRESP_OKAY;
        for (int i = 0; i < num_bursts; i++)
        {
            if (data[i].wid != addr.awid ||
                data[i].wdata.data != (axiDataT)i * 0x01010101 ||
                data[i].wstrb.strobe != 0xF ||
                ((i == 255) != data[i].wlast))
            {
                log_.logPrint("Data mismatch");
                resp.bresp = AXIRESP_SLVERR;
            }
        }
        resp.bid = addr.awid;
        axiWr0->sendResp(resp);
    }
    controller.test_complete(test_name);
}
// send multicycle transaction and recieve single cycle transaction
void consumer::inAXI1Wr(void)
{
    axiWr1->setCycleTransaction(PORTTYPE_IN);
    std::string test_name = "test_axiwr1";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop=0; loop < LOOPCOUNT; loop++) {
        axiWriteAddressSt<axiAddrSt> addr;
        axiWriteDataSt<axiDataSt, axiStrobeSt> data;
        axiWriteRespSt resp;
        axiWr1->receiveAddr(addr);
        int num_bursts = addr.awlen + 1;
        for (int i = 0; i < num_bursts; i++)
        {
            axiWr1->receiveDataCycle(data);
            if (data.wid != addr.awid ||
                data.wdata.data != (axiDataT)i * 0x01010101 ||
                data.wstrb.strobe != 0xF ||
                ((i == 255) != data.wlast))
            {
                log_.logPrint("Data mismatch");
                resp.bresp = AXIRESP_SLVERR;
            } else {
                resp.bresp = AXIRESP_OKAY;
            }
        }
        resp.bid = addr.awid;
        axiWr1->sendRespCycle(resp);
    }
    controller.test_complete(test_name);

}
// send single cycle transaction and recieve multicycle transaction
void consumer::inAXI2Wr(void)
{
    std::string test_name = "test_axiwr2";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop=0; loop < LOOPCOUNT; loop++) {
        axiWriteAddressSt<axiAddrSt> addr;
        axiWriteDataSt<axiDataSt, axiStrobeSt> *data; // array of max number of bursts
        axiWriteDataSt<axiDataSt, axiStrobeSt> dummy;
        axiWriteRespSt resp;
        resp.bresp = AXIRESP_OKAY;
        axiWr2->receiveAddr(addr);
        int num_bursts = addr.awlen + 1;
        axiWr2->receiveData(dummy);
        data = reinterpret_cast<axiWriteDataSt<axiDataSt, axiStrobeSt> *>(axiWr2->getReceiveDataPtr());
        for (int i = 0; i < num_bursts; i++)
        {
            if (data[i].wid != addr.awid ||
                data[i].wdata.data != (axiDataT)i * 0x01010101 ||
                data[i].wstrb.strobe != 0xF ||
                ((i == 255) != data[i].wlast))
            {
                log_.logPrint("Data mismatch");
                resp.bresp = AXIRESP_SLVERR;
            }
        }
        resp.bid = addr.awid;
        axiWr2->sendResp(resp);
    }
    controller.test_complete(test_name);
}

// send and recieve single cycle transactions
void consumer::inAXI3Wr(void)
{
    axiWr3->setCycleTransaction(PORTTYPE_IN);
    std::string test_name = "test_axiwr3";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for(int loop=0; loop < LOOPCOUNT; loop++) {
        axiWriteAddressSt<axiAddrSt> addr;
        axiWriteDataSt<axiDataSt, axiStrobeSt> data;
        axiWriteRespSt resp;
        resp.bresp = AXIRESP_OKAY;
        axiWr3->receiveAddr(addr);
        int num_bursts = addr.awlen + 1;
        for (int i = 0; i < num_bursts; i++)
        {
            axiWr3->receiveDataCycle(data);
            if (data.wid != addr.awid ||
                data.wdata.data != (axiDataT)i * 0x01010101 ||
                data.wstrb.strobe != 0xF ||
                ((i == 255) != data.wlast))
            {
                log_.logPrint("Data mismatch");
                resp.bresp = AXIRESP_SLVERR;
            }
        }
        resp.bid = data.wid;
        axiWr3->sendRespCycle(resp);
    }
    controller.test_complete(test_name);

}
