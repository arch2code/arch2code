# SystemC Documentation Package

**Created:** 2026-01-22  
**Purpose:** Comprehensive SystemC API documentation for arch2code users

---

## Overview

This package provides complete documentation for implementing hardware blocks using arch2code's SystemC infrastructure. It consists of two complementary documents:

1. **SYSTEMC_API_USER_REFERENCE.md** - Primary user reference
2. **SYSTEMC_DOCUMENTATION_GAPS.md** - Source code documentation assessment

---

## Document Descriptions

### SYSTEMC_API_USER_REFERENCE.md

**Audience:** C++ developers implementing hardware blocks

**Content:**
- **User APIs** (Primary focus)
  - Module logging
  - Register and memory access
  - Communication channels (rdy_vld, APB, memory, req_ack, etc.)
  - Transaction tracking
  
- **Framework Reference** (Brief overview)
  - blockBase, interfaceBase, portBase
  - addressMap, instanceFactory
  - Generated code infrastructure
  
- **Advanced Topics** (Power users)
  - Multi-cycle channel patterns
  - Synchronization (synchLock)
  - Tag encoding (encoderBase)
  - External thread integration (ThreadSafeEvent)
  - Backdoor access
  
- **Implementation Patterns**
  - Producer/consumer
  - APB master/slave
  - Register handlers
  - Multi-cycle bursts
  - Pipeline stages
  
- **Best Practices**
  - Thread design
  - Channel usage
  - Logging strategies
  - Error handling
  - Performance optimization
  - Debugging techniques

**Key Features:**
- Clear distinction between user-facing and framework APIs
- All examples extracted from real codebase
- Progressive complexity (basic → advanced)
- Comprehensive API coverage
- Practical implementation patterns

### SYSTEMC_DOCUMENTATION_GAPS.md

**Audience:** Framework maintainers and documentation authors

**Content:**
- File-by-file assessment of source documentation quality
- Specific improvement recommendations
- Priority rankings (High/Medium/Low)
- Documentation templates
- Coverage summary table

**Purpose:**
- Guide future source code documentation improvements
- Identify areas needing inline examples
- Highlight user vs framework API distinction needs
- Provide templates for consistent documentation

**Key Findings:**
- Overall: Good structural documentation
- Needs: Better user API distinction
- Needs: More inline examples
- Needs: Clearer parameter/return documentation

---

## Usage Guide

### For C++ Developers

**Start here:** `SYSTEMC_API_USER_REFERENCE.md`

**Quick navigation:**
1. Read Introduction (Section 1) for concepts
2. Jump to relevant sections:
   - Logging → Section 2
   - Registers/Memory → Section 3
   - Channels → Section 4
   - Debugging → Section 5
3. Use Implementation Patterns (Section 8) as templates
4. Apply Best Practices (Section 9)

**Common tasks:**
- "How do I read a register?" → Section 3.1
- "How do I use rdy_vld?" → Section 4.1
- "How do I log messages?" → Section 2
- "How do I debug transactions?" → Section 5
- "How do I implement APB slave?" → Section 8.5

### For Framework Maintainers

**Start here:** `SYSTEMC_DOCUMENTATION_GAPS.md`

**Use for:**
- Planning documentation improvements
- Prioritizing inline documentation work
- Understanding current documentation state
- Following documentation templates

**Priority improvements:**
1. hwRegister.h - Add user access section
2. hwMemory.h - Emphasize API usage
3. tracker.h - Separate user/framework APIs
4. addressMap.h - Add framework-only warning

### For AI Assistants

**Primary reference:** `SYSTEMC_API_USER_REFERENCE.md`

**Use for:**
- Answering user questions about SystemC APIs
- Generating implementation code
- Suggesting best practices
- Debugging user code issues

**Key principles:**
- User APIs (Sections 2-5) for implementation guidance
- Framework Reference (Section 6) for understanding generated code
- Advanced Topics (Section 7) for specialized features
- Never edit between GENERATED_CODE_BEGIN/END markers

---

## Relationship to Other Documentation

### ARCH2CODE_AI_RULES.md
**Covers:** Code generation workflow, YAML architecture, SystemVerilog

**Use when:**
- Defining architecture in YAML
- Understanding code generation
- Working with RTL/SystemVerilog
- Using make targets (gen, db, newmodule)

### SYSTEMC_API_USER_REFERENCE.md (This Package)
**Covers:** SystemC implementation, C++ user code

**Use when:**
- Implementing module behavior in .cpp files
- Using communication channels
- Accessing registers/memories
- Debugging SystemC models

**Complementary:** These documents cover different phases of the workflow:
1. ARCH2CODE_AI_RULES.md → Architecture definition and generation
2. SYSTEMC_API_USER_REFERENCE.md → Implementation and testing

---

## Maintenance Notes

### Keeping Documentation Current

**When to update SYSTEMC_API_USER_REFERENCE.md:**
- New channel types added
- API signatures change
- New user-facing features added
- Best practices evolve
- Examples updated

**When to update SYSTEMC_DOCUMENTATION_GAPS.md:**
- Source code documentation improved
- New files added to framework
- Documentation templates change
- Priorities shift

---

## Feedback and Improvements

This documentation is a living resource. Suggested improvements:

1. **Add more examples** as new patterns emerge
2. **Update based on user questions** - common issues become FAQ
3. **Expand advanced topics** as features mature
4. **Add performance benchmarks** for different patterns
5. **Create video tutorials** for complex topics
6. **Generate Doxygen** from source with cross-references

---

## Quick Reference Card

### Most Common APIs

```cpp
// Logging
log_.logPrint("Message", LOG_NORMAL);

// Register access (unclocked)
value = myReg.m_val;
myReg.m_val = value;

// Memory access (timed)
data = myMem.read(index);
myMem.write(index, data);

// rdy_vld channel
myPort->write(data);  // Source
myPort->read(data);   // Sink

// APB channel
apbPort->request(isWrite, addr, data);  // Master
apbPort->reqReceive(isWrite, addr, data);  // Slave
apbPort->complete(data);  // Slave read response

// Tracker debug
log_.logPrint(tracker->prt(tag));
```

### Common Patterns

```cpp
// Basic thread structure
void myModule::myThread() {
    wait(SC_ZERO_TIME);
    while (true) {
        inputPort->read(data);
        processData(data);
        outputPort->write(result);
    }
}

// Register handler (use template)
void myBlock::regHandler() {
    registerHandler<apbAddrSt, apbDataSt>(regs, apbReg, mask);
}
```

---

## Contact and Support

For questions or issues:
1. Check SYSTEMC_API_USER_REFERENCE.md first
2. Review example code in `builder/base/examples/`
3. Check ARCH2CODE_AI_RULES.md for generation issues
4. Consult source code with SYSTEMC_DOCUMENTATION_GAPS.md as guide

**Happy coding with arch2code!**
