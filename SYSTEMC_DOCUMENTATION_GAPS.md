# SystemC Source Documentation Quality Assessment

**Date:** 2026-01-22  
**Purpose:** Document areas where source code documentation could be improved  
**Scope:** Files in `builder/base/common/systemc/` and `builder/base/interfaces/`

---

## Executive Summary

This assessment reviews the inline documentation quality of arch2code SystemC source files. Overall, the codebase has **good structural documentation** but could benefit from more comprehensive user-facing API documentation, particularly:

1. **User API distinction** - Better marking of user-facing vs framework-internal methods
2. **Usage examples** - More inline examples for complex APIs
3. **Parameter documentation** - More detailed parameter descriptions
4. **Return value documentation** - Clearer documentation of return values and error conditions

---

## File-by-File Assessment

### Interfaces (builder/base/interfaces/)

#### ✅ GOOD: rdy_vld_channel.h
**Status:** Well-documented

**Strengths:**
- Clear class-level documentation
- Method signatures are clear
- Protocol diagram in header comment

**Improvements Needed:**
- Add @param/@return Doxygen tags
- Document multi-cycle usage patterns in header
- Mark user-facing vs framework methods

**Example Missing Documentation:**
```cpp
// Current: Just signature
virtual void writeClocked(const T& data) = 0;

// Should include:
/// @brief Write one beat of a multi-cycle burst transfer
/// @param data Data value for this beat
/// @note Must be preceded by push_burst() or write(data, size)
/// @see push_burst(), getWritePtr()
virtual void writeClocked(const T& data) = 0;
```

#### ✅ GOOD: apb_channel.h
**Status:** Well-documented

**Strengths:**
- Clear protocol description in header
- Method purposes obvious from names

**Improvements Needed:**
- Document blocking vs non-blocking behavior
- Add timing model documentation
- Document error handling

#### ⚠️ NEEDS WORK: status_channel.h
**Status:** Minimal documentation

**Improvements Needed:**
- Explain update vs read semantics
- Document when blocking vs non-blocking should be used
- Add usage examples

#### ⚠️ NEEDS WORK: notify_ack_channel.h
**Status:** Basic documentation

**Improvements Needed:**
- Clarify use cases vs other protocols
- Document timing behavior
- Add example of notify pattern

#### ✅ ADEQUATE: req_ack_channel.h
**Status:** Basic but functional

**Strengths:**
- Clear method names
- Protocol diagram present

**Improvements Needed:**
- Document relationship between request and ack types
- Add timing model notes

#### ✅ ADEQUATE: push_ack_channel.h, pop_ack_channel.h
**Status:** Minimal but clear

**Improvements Needed:**
- Document flow control mechanism
- Add example usage patterns

---

### Common SystemC (builder/base/common/systemc/)

#### ✅ GOOD: blockBase.h
**Status:** Well-documented

**Strengths:**
- Class purpose clearly stated
- Logging mechanism documented

**Improvements Needed:**
- **Mark user-facing APIs** - Only `log_` is user-facing
- Add note: "Most methods framework-only, see SYSTEMC_API_REFERENCE.md"
- Document tandem mode for users who encounter it

**Suggested Addition:**
```cpp
/// @class blockBase
/// @brief Base class for all SystemC modules in arch2code
/// @note USER API: Only log_ member is intended for user code
/// @note Other methods are framework-internal (used in generated code)
/// @see SYSTEMC_API_USER_REFERENCE.md for user API documentation
```

#### ✅ GOOD: logging.h
**Status:** Well-documented

**Strengths:**
- Log levels documented
- Hierarchical logging explained

**Improvements Needed:**
- Add more examples of lambda usage
- Document performance implications
- Add filtering examples

#### ⚠️ NEEDS WORK: tracker.h
**Status:** Minimal user-facing documentation

**Issues:**
- Doesn't clearly distinguish user APIs from framework APIs
- Missing examples of prt(), info(), getString()
- Backdoor pointer usage not explained

**Improvements Needed:**
```cpp
// Add section:
/// @section USER_API User-Facing Methods
/// - prt(tag) - Print transaction info
/// - prt(tag, msg) - Print with message prefix
/// - getString(tag) - Get parseable string
/// - info(tag) - Get transaction info object
/// - getBackdoorPtr(tag) - Get buffer pointer (advanced)
/// - getLen(tag) - Get transaction length
///
/// @section FRAMEWORK_API Framework-Only Methods
/// - alloc() - DO NOT CALL (automatic)
/// - dealloc() - DO NOT CALL (automatic)
/// - setTracker() - Framework configuration
```

#### ⚠️ NEEDS WORK: hwRegister.h
**Status:** Implementation-focused, lacks user guidance

**Issues:**
- No clear documentation of m_val vs read()/write()
- Framework constructors not marked
- User access patterns not documented

**Improvements Needed:**
```cpp
/// @section USER_ACCESS User Code Access
/// Preferred (unclocked): myReg.m_val = value;
/// Timed (clocked): myReg.write(value);
/// Field access: myReg.m_val.field = x;
///
/// @section FRAMEWORK Framework-Only APIs
/// Constructors, cpu_read(), cpu_write(), registerEvent()
/// used in generated register handlers only
```

#### ⚠️ NEEDS WORK: hwMemory.h
**Status:** Complex API, insufficient user documentation

**Issues:**
- Doesn't emphasize "always use APIs, not direct access"
- RMW semantics unclear
- Port binding not explained (framework-only)

**Improvements Needed:**
```cpp
/// @section USER_ACCESS Memory Access Methods
/// @warning ALWAYS use memory APIs, never direct member access
///
/// Basic Access:
/// - read(index) - Timed read (preferred)
/// - write(index, value) - Timed write (preferred)
/// - [index] - Direct access (no timing, use with caution)
///
/// Atomic Operations:
/// - readRMW(index, magic) - Start atomic read-modify-write
/// - writeRMW(index, value) - Complete atomic RMW
/// - releaseRMW(index) - Release lock without writing
/// - lock(index, magic) - Acquire lock only
///
/// @section FRAMEWORK Framework-Only APIs
/// - bindPort() - Used in generated code
/// - configureSynch() - Framework configuration
```

#### ⚠️ NEEDS WORK: addressMap.h
**Status:** Framework-focused, needs user note

**Issues:**
- All methods are framework-only
- Should explicitly state this

**Improvements Needed:**
```cpp
/// @class addressMap
/// @brief Address space manager for registers and memories
/// @warning FRAMEWORK API ONLY - Not for user code
/// @note Users should access registers/memories directly (see hwRegister, hwMemory)
/// @note These methods used in generated register handlers only
```

#### ✅ GOOD: interfaceBase.h
**Status:** Adequate framework documentation

**Strengths:**
- Purpose clear
- Configuration methods documented

**Improvements Needed:**
- Add note that this is framework-only
- Point users to channel-specific APIs

#### ✅ ADEQUATE: portBase.h
**Status:** Clear framework interface

**Improvements Needed:**
- Mark as framework-only
- Note that users call channel methods instead

#### ⚠️ NEEDS WORK: synchLock.h
**Status:** Advanced API, needs more explanation

**Issues:**
- Use cases not clearly explained
- Relationship to memory RMW not documented
- Examples missing

**Improvements Needed:**
- Add use case documentation
- Note: "Used internally by hwMemory RMW operations"
- Add example of custom usage

#### ⚠️ NEEDS WORK: encoderBase.h
**Status:** Complex API, minimal documentation

**Issues:**
- Purpose unclear to new users
- Configuration structure not explained
- No usage examples

**Improvements Needed:**
- Add detailed class documentation
- Explain use cases (tag multiplexing)
- Add complete example

#### ✅ ADEQUATE: asyncEvent.h (ThreadSafeEvent)
**Status:** Basic but functional

**Strengths:**
- Purpose clear from class name
- Factory pattern documented

**Improvements Needed:**
- Add threading model documentation
- Add complete example with external thread
- Document safety guarantees

#### ⚠️ NEEDS WORK: multiCycleBase.h
**Status:** Internal implementation, minimal docs

**Issues:**
- User-facing aspects unclear
- Integration with channels not explained

**Improvements Needed:**
- Mark as framework/internal
- Document what users see vs what's internal

#### ⚠️ NEEDS WORK: pingPongBuffer.h
**Status:** Implementation-heavy, lacks overview

**Issues:**
- Use cases not clearly stated
- Integration with channels not explained

**Improvements Needed:**
- Add overview of ping-pong buffering
- Document when/why to use
- Add usage example

#### ⚠️ NEEDS WORK: timedDelay.h
**Status:** Configuration-focused, missing user context

**Issues:**
- User vs framework configuration unclear
- When timing is applied not documented

**Improvements Needed:**
- Document delay application points
- Note framework configuration (users don't set directly)

---

## Priority Improvements

### High Priority (Affects Daily Use)

1. **hwRegister.h** - Add clear "User Access" section documenting `m_val` vs `read()`/`write()`
   ```cpp
   /// @section USER_ACCESS Direct Register Access
   /// - Preferred unclocked: myReg.m_val = value
   /// - Timed access: myReg.write(value)
   ```

2. **hwMemory.h** - Emphasize "always use APIs, not direct access"
   ```cpp
   /// @warning ALWAYS use memory APIs (read/write), not direct member access
   ```

3. **tracker.h** - Clearly separate user APIs from framework APIs
   - Mark: prt(), info(), getString(), getBackdoorPtr(), getLen() as USER
   - Mark: alloc(), dealloc(), setTracker() as FRAMEWORK

4. **addressMap.h** - Add prominent note: "FRAMEWORK ONLY - Not for user code"

### Medium Priority (Improves Understanding)

5. **Channel headers** - Add consistent @section USER_API / FRAMEWORK_API markers

6. **blockBase.h** - Note that only `log_` is user-facing

7. **encoderBase.h** - Add complete usage example with explanation

8. **asyncEvent.h** - Add threading model and complete example

### Low Priority (Nice to Have)

9. **synchLock.h** - Add use case documentation and examples

10. **pingPongBuffer.h** - Add overview and integration documentation

11. **multiCycleBase.h** - Document user-visible vs internal aspects

---

## Documentation Pattern Recommendations

### Suggested Template for User-Facing Classes

```cpp
/// @class ClassName
/// @brief One-line purpose
///
/// Detailed description of what this class does and when to use it.
///
/// @section USER_API User-Facing Methods
/// List and briefly describe methods intended for user code:
/// - method1() - Brief description
/// - method2() - Brief description
///
/// @section FRAMEWORK_API Framework-Only Methods
/// List methods used in generated code (not for users):
/// - frameworkMethod1() - Brief description
///
/// @section EXAMPLES Usage Examples
/// @code
/// // Example of typical usage
/// myClass obj;
/// obj.method1();
/// @endcode
///
/// @see Related classes or documentation files
```

### Method Documentation Template

```cpp
/// @brief One-line description
/// @param paramName Parameter description
/// @return Return value description
/// @note Important usage notes
/// @warning Critical warnings
/// @see Related methods
/// @example
/// @code
/// // Usage example
/// method(param);
/// @endcode
```

---

## Coverage Summary

| File | User API Doc | Framework Doc | Examples | Overall |
|------|-------------|---------------|----------|---------|
| rdy_vld_channel.h | Good | Good | Missing | ✅ Good |
| apb_channel.h | Good | Good | Missing | ✅ Good |
| status_channel.h | Basic | Basic | Missing | ⚠️ Needs Work |
| req_ack_channel.h | Adequate | Adequate | Missing | ✅ Adequate |
| push_ack_channel.h | Basic | Basic | Missing | ⚠️ Needs Work |
| pop_ack_channel.h | Basic | Basic | Missing | ⚠️ Needs Work |
| notify_ack_channel.h | Basic | Basic | Missing | ⚠️ Needs Work |
| blockBase.h | Adequate | Good | Good | ✅ Good |
| logging.h | Good | Good | Some | ✅ Good |
| tracker.h | Poor | Adequate | Missing | ⚠️ Needs Work |
| hwRegister.h | Poor | Adequate | Missing | ⚠️ Needs Work |
| hwMemory.h | Poor | Adequate | Missing | ⚠️ Needs Work |
| addressMap.h | N/A | Adequate | N/A | ⚠️ Add Warning |
| interfaceBase.h | N/A | Good | N/A | ✅ Adequate |
| portBase.h | N/A | Good | N/A | ✅ Adequate |
| synchLock.h | Poor | Adequate | Missing | ⚠️ Needs Work |
| encoderBase.h | Poor | Adequate | Missing | ⚠️ Needs Work |
| asyncEvent.h | Basic | Adequate | Missing | ⚠️ Needs Work |
| multiCycleBase.h | Poor | Basic | Missing | ⚠️ Needs Work |
| pingPongBuffer.h | Poor | Basic | Missing | ⚠️ Needs Work |
| timedDelay.h | N/A | Adequate | N/A | ✅ Adequate |

**Legend:**
- ✅ Good: Well-documented, minimal improvement needed
- ✅ Adequate: Functional documentation, could be enhanced
- ⚠️ Needs Work: Significant improvements recommended

---

## Recommendations

1. **Add USER_API / FRAMEWORK_API sections** to all major classes
2. **Add inline examples** for complex APIs (tracker, encoder, asyncEvent)
3. **Mark preferred access methods** prominently (e.g., `m_val` for registers)
4. **Add usage warnings** where appropriate (e.g., memory direct access)
5. **Create Doxygen configuration** to generate comprehensive API docs
6. **Cross-reference** to SYSTEMC_API_USER_REFERENCE.md for detailed usage

These improvements will make the source code more self-documenting and reduce the learning curve for new developers.
