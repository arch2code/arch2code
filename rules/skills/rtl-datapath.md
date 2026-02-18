# Skill: RTL Datapath

## Purpose
Guide the user on using common datapath components (`fifo`, `inPlaceList`, `rdyVldCapture`, `incDec`) in SystemVerilog.

## Implementation Location
All module instantiations and logic described below must be placed **after** the `// GENERATED_CODE_END` marker in your SystemVerilog file. **DO NOT** modify the auto-generated ports or parameters at the top of the file.

## Instructions

1.  **FIFOs:**
    *   **Standard:** `fifo`.
    *   **Async:** `async_fifo`.
    *   **Pass-Thru:** `fifo_passthru` (0-cycle delay).
    *   **Parameters:** `DEPTH`, `dataSt`.

    ```systemverilog
    fifo #(.DEPTH(16), .dataSt(myType)) uFifo (
        .clk(clk), .rst_n(rst_n),
        .push(push_sig), .data_in(data_in), .full(full_sig),
        .pop(pop_sig), .data_out(data_out), .empty(empty_sig)
    );
    ```

2.  **In-Place Lists (`inPlaceList`):**
    *   **Use Case:** Efficiently managing linked lists of items (e.g., free tag lists, queues) in hardware without pointer overhead.
    *   **Parameters:** `NUM_LIST`, `NUM_ITEMS`, `dataSt`, `nextSt`.
    *   **Ports:** `pushData`, `popData` (arrays for multi-port access).

    ```systemverilog
    // Example from tagScheduler.sv
    inPlaceList
    #(
        .dataSt   (hostRdTagListSt),
        .nextSt   (hostRdTagT),
        .NUM_LIST (1)
    )
    uRdTagListIPL(
        .pushData    (freeRdTagsPushData),
        .pushDataVld (freeRdTagsPushDataVld),
        .pushDataAck (freeRdTagsPushDataAck),
        .popData     (freeRdTagsPopData),
        .popDataVld  (freeRdTagsPopDataVld),
        .popDataAck  (freeRdTagsPopDataAck),
        .count       (),
        .dataTable   (hostRdTagList), // Connected memory interface
        .*
    );
    ```

3.  **Capture Logic (`rdyVldCapture`):**
    *   **Use Case:** Safely latching data from a `rdy_vld` interface into a local register, handling backpressure automatically.
    *   **Ports:** `captureIf` (source interface), `capData` (output reg), `dataVld` (valid flag), `clear` (reset flag).

    ```systemverilog
    // Example from tagScheduler.sv
    rdyVldCapture #(
        .dataSt(newCmdToTagSt)
    )
    u_rdyVldCapture(
        .captureIf (newCmdToTag),
        .capData   (cmd),
        .dataVld   (cmdVld),
        .clear     (cmdClear),
        .*
    );
    ```

4.  **Counters (`incDec`):**
    *   **Use Case:** Up/Down counters with overflow protection.
    *   **Ports:** `inc`, `dec`, `count`.

    ```systemverilog
    incDec
    #(
        .dataSt (cmdCountT)
    )
    uWritesInTransferIncDec(
        .inc   (writesInTransferInc),
        .dec   (writesInTransferDec),
        .count (writesInTransfer),
        .*
    );
    ```
