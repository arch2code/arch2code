# Skill: SystemC Interfaces

## Purpose
Guide the user on using communication interfaces (`rdy_vld`, `push_ack`, `axi`) in SystemC models.

## References
*   **API Reference:** `SYSTEMC_API_USER_REFERENCE.md` (See "Communication Channels")

## Implementation Location
All logic and member usage described below must be implemented in the manual sections of your `.h` and `.cpp` files, specifically **after** the `// GENERATED_CODE_END` markers.

## Instructions

1.  **Interface Usage (Auto-Generated Ports):**
    *   **Do Not Instantiate:** Interface ports are **auto-generated** in the base class. Do not declare them manually.
    *   **Access:** Access ports as pointers using the arrow operator `->`.
    *   **Types:** Common types include `rdy_vld`, `push_ack`, `req_ack`, `axi_read`, `axi_write`.
    *   **Reference:** See `builder/interfaces/<type>/<type>_channel.h` for complete API details.

2.  **Interface Reference Table:**

    | Interface | Initiator (Source) API | Target (Destination) API | Description |
    | :--- | :--- | :--- | :--- |
    | **rdy_vld** | `write(data)` | `read(data)` | Streaming data with backpressure |
    | **push_ack** | `push(data)` | `pushReceive(data)`<br>`ack()` | Sender-driven handshake |
    | **pop_ack** | `pop(data)` | `popReceive()`<br>`ack(data)` | Receiver-driven handshake |
    | **req_ack** | `req(req_data, ack_data)` | `reqReceive(req_data)`<br>`ack(ack_data)` | Request-response transaction |
    | **apb** | `request(isWrite, addr, data)` | `reqReceive(isWrite, addr, data)`<br>`complete(data)` (Read Only) | APB register access |
    | **axi_read** | `sendAddr(addr)`<br>`receiveData(resp)` | `receiveAddr(addr)`<br>`sendData(resp)` | AXI Read channel |
    | **axi_write** | `sendAddr(addr)`<br>`sendData(data)`<br>`receiveResp(resp)` | `receiveAddr(addr)`<br>`receiveData(data)`<br>`sendResp(resp)` | AXI Write channel |
    | **axi4_stream**| `sendInfo(info)` | `receiveInfo(info)` | AXI4-Stream protocol |
    | **memory** | `request(isWrite, addr, data)` | `reqReceive(isWrite, addr, data)`<br>`complete(data)` (Read Only) | Memory access protocol |
    | **status** | `write(data)` | `read(data)` | Unidirectional signal (no handshake) |
    | **notify_ack** | `notify()` | `waitNotify()`<br>`ack()` | Event notification with ack |
    | **external_reg**| `write(val)`<br>`reg_read(val)` | `read(val)`<br>`reg_write(val)` | External register access |

    > **Note:** This table covers the standard system interfaces. Additional specialized interfaces may be available in `a2cPro` or provided by the user.

3.  **Advanced Synchronization:**
    *   For multi-interface arbitration (using `setExternalEvent` and `isActive`), refer to the **SystemC Synchronization** skill.
