# Skill: Debugging

## Purpose
Guide the user on using debugging tools and techniques in SystemC, including Trackers, Assertions, Logging, and Status Reporting.

## Instructions

1.  **Trackers (`tracker<T>`):**
    *   **Crucial Debug Tool:** Used to track the lifecycle of objects (tags, commands) through the pipeline.
    *   Initialize via `trackerCollection::GetInstance().getTracker(...)`.
    *   **Lifecycle:**
        *   `alloc(tag, info, refDelta)`: Start tracking a tag.
        *   `dealloc(tag, refDelta)`: End tracking.
    *   **Ref Counting:** Use `getTrackerRefCountDelta()` for correct tandem verification reference counting.

    ```cpp
    // Example from tagScheduler.cpp
    std::shared_ptr<tracker<tagInfo>> rdTagTracker;
    // Constructor
    rdTagTracker(std::static_pointer_cast<tracker<tagInfo>>( trackerCollection::GetInstance().getTracker("rdTag") ))
    // Allocation
    auto tag = std::make_shared< tagInfo >();
    tag->cmdId = cmdId;
    // ... populate info
    rdTagTracker->alloc(rd.rdTag, tag, getTrackerRefCountDelta());
    // Update
    rdTagTracker->setLen(rd.rdTag, length);
    // Deallocation
    rdTagTracker->dealloc(rdTag, getTrackerRefCountDelta());
    ```

    *   **Info Struct:** Define a struct (e.g., `tagInfo`) with a `prt()` method for string representation in logs/waveforms.

    ```cpp
    struct tagInfo {
        uint32_t cmdId;
        std::string tagType;
        std::string prt() {
            return std::format("cmd:{} type:{}", cmdId, tagType);
        }
    };
    ```

2.  **Tracker Definition & Registration:**
    *   **Registration:** In a global initialization function (e.g., `trackerInit`), create the tracker and add it to the `trackerCollection`. This is typically called from your testbench configuration.

    ```cpp
    // 1. Define Tag Formatter (Optional)
    std::string myTagFormatter(int tag) {
        return std::format("tag:0x{:x}", tag);
    }

    // 2. Register in trackerInit()
    void trackerInit(void) {
        auto &trackers = trackerCollection::GetInstance();
        
        // Simple Tracker
        trackers.addTracker("cmd", std::make_shared<tracker<cmdIdInfo>>(
            NUM_COMMANDS,   // Depth
            "cmdTracker",   // Name
            "C#",           // Log Prefix
            cmdidAlloc      // Tag formatter func
        ));

        // Shared Counter Tracker (e.g., for unified Read/Write tags)
        // Useful when multiple trackers share the same sequence number space
        auto sharedCounter = std::make_shared<uint64_t>(0);
        
        auto rdTracker = std::make_shared<tracker<tagInfo>>(
            NUM_TAGS, 
            sharedCounter, 
            "rdTag",        // Name
            "T#",           // Log Prefix
            rdTagAlloc      // Tag formatter func
        );
        trackers.addTracker("rdTag", rdTracker);
    }
    ```

3.  **Tracker Integration in YAML:**
    *   **Generator Tag:** Use `generator: tracker(trackerName)` in your YAML structure definition to automatically link a field to a tracker.
    *   **Effect:** When this field is printed (e.g., in logs), the system automatically looks up the active tracker for that tag value and prints the tracker's info alongside the value.

    ```yaml
    # Example from sharedTop.yaml
    structures:
      rdTagSt:
        rdTag: {varType: rdTagT, generator: tracker(rdTag), desc: "Read tag"}
    ```

    *   **Log Output:** The log will show the tracker ID (e.g., `T#...`) and the content returned by your info struct's `prt()` method inside curly braces `{...}`.

    ```text
    # Log format: Prefix#TrackerID{InfoPrtOutput}FieldName:Value
    NVMe.FTL_retrieve:T#2d73{C#2cdb Type:HOSTRD cmdId:0x1b4}rdTag:0x0a1
    ```
    *   In this example:
        *   `T#2d73`: Unique Tracker ID.
        *   `{C#2cdb Type:HOSTRD cmdId:0x1b4}`: Output from `tagInfo::prt()`.
        *   `rdTag:0x0a1`: The actual field name and value.

4.  **Assertions (`Q_ASSERT`):**
    *   **Internal Consistency:** Use `Q_ASSERT` to verify internal state and assumptions.
    *   **Parameters:** Takes a condition and an error message string.
    *   **Failure:** Halts simulation immediately with the message if the condition is false.

    ```cpp
    void myModule::processData(uint32_t index) {
        // Verify index is within bounds before access
        Q_ASSERT(index < MAX_SIZE, "Index out of range");
        
        data_st data = dataArray[index];
        // ... processing logic ...
    }
    ```

5.  **Status Reporting:**
    *   **Simulation Hangs:** Implement `statusPrint(void)` to dump internal state (e.g., queue contents, current arbitration state) when simulation hangs or errors occur.
    *   **Registration:** Register the status callback in the constructor using `logging::GetInstance().registerStatus`.

    ```cpp
    // Constructor registration
    logging::GetInstance().registerStatus(name(), [this](void){ statusPrint();});

    // Implementation
    void hostTransferAscari::statusPrint(void) {
        log_.logPrint(std::format("stuckDebug:{:08x}", stuckDebug), LOG_IMPORTANT);
        // Dump queues, trackers, and other internal state
    }
    ```

6.  **Logging (Advanced):**
    *   **Lazy Evaluation:** Use lambdas for complex formatting to avoid performance overhead when logging is disabled for that level.
    *   **Levels:** Use appropriate log levels (`LOG_DEBUG`, `LOG_IMPORTANT`, etc.).

    ```cpp
    // Only formats the string if LOG_DEBUG is enabled
    log_.logPrint([&]() { return std::format("complex info: {}", calculate_debug_info()); }, LOG_DEBUG);
    ```
