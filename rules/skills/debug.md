---
name: debug
description: Guide for using debugging tools in SystemC including trackers, assertions, logging, and status reporting
---
# Skill: Debugging

## Trackers
A tracker (`tracker<T>`) follows a tag, such as a command ID or a read tag, from allocation to release. It attaches an info object of type `T` to each live tag and prints that info wherever the tag is logged.

### Info type
`T` needs a `std::string prt()` method. It also needs a constructor that takes a `std::string`, because the tracker can create an info object itself from a channel's log string. Without that constructor `tracker<T>` does not compile.

```cpp
struct tagInfo {
    uint32_t cmdId = 0;
    std::string tagType;
    tagInfo() = default;
    explicit tagInfo(const std::string &s) : tagType(s) {}
    std::string prt() { return std::format("cmd:{} type:{}", cmdId, tagType); }
};
```

### Registration
Register every tracker in the testbench's `<dut>Config::createTestBench()`, before `createTbTop()`. Blocks and channels look their trackers up while the hierarchy is built, and `getTracker` asserts `Tracker not found` for a name not yet registered.

```cpp
bool createTestBench(void) override
{
    auto &trackers = trackerCollection::GetInstance();
    // appended to the alloc and dealloc log lines
    auto prtTag = [](int tag) { return std::format(" tag:0x{:x}", tag); };

    // tracker(size, name, log prefix, tag formatter)
    trackers.addTracker("cmd", std::make_shared<tracker<tagInfo>>(NUM_CMDS, "cmdTracker", "C#", prtTag));

    // trackers that draw sequence numbers from one shared counter
    auto seq = std::make_shared<uint64_t>(0);
    trackers.addTracker("rdTag", std::make_shared<tracker<tagInfo>>(NUM_TAGS, seq, "rdTag", "T#", prtTag));
    trackers.addTracker("wrTag", std::make_shared<tracker<tagInfo>>(NUM_TAGS, seq, "wrTag", "T#", prtTag));

    std::shared_ptr<blockBase> tb = createTbTop();
    return true;
}
```

### Use in a block
```cpp
// member, initialized in the constructor
std::shared_ptr<tracker<tagInfo>> rdTagTracker;
rdTagTracker(std::static_pointer_cast<tracker<tagInfo>>(trackerCollection::GetInstance().getTracker("rdTag")))

// allocate
auto info = std::make_shared<tagInfo>();
info->cmdId = cmdId;
rdTagTracker->alloc(rdTag, info, getTrackerRefCountDelta());
// update
rdTagTracker->setLen(rdTag, length);
// release
rdTagTracker->dealloc(rdTag, getTrackerRefCountDelta());
```

Pass `getTrackerRefCountDelta()` to `alloc` and `dealloc`. It halves the reference count step in tandem, where both sides allocate and release the same tag.

### Tracker fields in YAML
`generator: tracker(<name>)` on a structure field binds the tracker named `<name>` to every channel that carries the structure. The name `length` is reserved and binds no tracker.

```yaml
structures:
  rdTagSt:
    rdTag: {varType: rdTagT, generator: tracker(rdTag), desc: "Read tag"}
```

*   The channel looks the tracker up in its constructor, so the tracker must be registered before `createTbTop()`.
*   The channel logs every transfer through the tracker. A transfer whose tag is not allocated at that moment fails the run with `Invalid tracker interface data`. The check is a `Q_ASSERT_CTX`, so the steps under Assertions apply. Allocate the tag before the first transfer that carries it.

A transfer logs at `LOG_NORMAL`, so it appears only with `--verbosity high` or above:

```text
T#2d73{cmd:436 type:HOSTRD}rdTag:0x0a1
```

*   `T#` is the tracker's log prefix.
*   `2d73` is the allocation's sequence number, in hex. Trackers that share a counter never reuse one.
*   `{cmd:436 type:HOSTRD}` is the info object's `prt()`.
*   `rdTag:0x0a1` is the structure's own `prt()`.

The logging block's name comes before all of it.

## Assertions
`Q_ASSERT(cond, msg)` checks internal state. Outside a module, where there is no `name()`, use `Q_ASSERT_CTX`; see "Assertions and unique names" in `systemc-core`.

On failure, `Q_ASSERT`:
1.  prints the message and a stack trace;
2.  runs every registered status function, then dumps the trackers (the `_NODUMP` variants skip the dump);
3.  when called from a thread, waits 10 ns of simulated time, so the rest of the design keeps running and logging before the stop;
4.  records the failure as the exit status and stops the simulation.

```cpp
void myModule::processData(uint32_t index)
{
    Q_ASSERT(index < MAX_SIZE, "Index out of range");
    data_st data = dataArray[index];
}
```

## Status reporting
A status function dumps a block's state, such as queue contents or arbitration state. Register it in the constructor:

```cpp
logging::GetInstance().registerStatus(name(), [this](void){ statusPrint(); });

void myBlock::statusPrint(void)
{
    log_.logPrint(std::format("pending:{} state:{}", pending.size(), state), LOG_IMPORTANT);
}
```

Status functions run on a `Q_ASSERT`, on a watchdog timeout, on SIGINT or SIGTERM, and at the end of every run.

## Logging
For `logPrint`, levels and lazy formatting with a lambda, see "Logging and errors" in `systemc-core`.
