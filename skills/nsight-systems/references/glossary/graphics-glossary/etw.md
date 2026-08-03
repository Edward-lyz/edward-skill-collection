# ETW

**Short:** Event Tracing for Windows is the OS-wide, high-throughput event-streaming facility built into Windows for kernel and user-mode components.

**Details:**

- ETW follows a three-role model: controllers start and stop sessions, providers emit events, and consumers read the stream.
- A session can be real-time (events delivered live to a consumer) or file-backed (events written to an ETL file for later replay).
- Each provider is identified by a GUID and exposes a schema of event IDs; controllers enable it with a level and a keyword bitmask to filter what is emitted.
- Keywords are bitflags that group related events by category; levels (critical, error, warning, informational, verbose) gate by severity.
- Sessions own ring buffers in kernel memory and have a lifetime independent of the controller that created them, so a session can outlive its starter and must be explicitly stopped.
- ETW is designed for low overhead, so it is the standard transport for OS, graphics, and driver telemetry on Windows.

**See also:**

- [DxgKrnl events](dxgkrnl-events.md)
- [WDDM](wddm.md)
- [ETW provider mask](etw-provider-mask.md)
