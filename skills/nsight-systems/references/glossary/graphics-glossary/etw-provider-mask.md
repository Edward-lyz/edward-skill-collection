# ETW provider mask

**Short:** The provider mask is the keyword bitmask plus level that a controller passes when enabling an ETW provider; together they tell the provider which event categories and severities to emit into the session.

**Details:**

- Each ETW provider defines its own keyword bits, where every bit names a category of events (for example, scheduler, memory, synchronization, or resource events).
- A controller passes a MatchAnyKeyword mask, and the provider emits an event when at least one of its keyword bits is also set in that mask.
- A MatchAllKeyword mask can further require that every set bit in the filter is present on the event; most controllers leave this zero.
- The level value (critical, error, warning, informational, verbose) gates by severity: the provider emits events whose declared level is at or below the requested level.
- Event-ID filters and stack-walk filters can be layered on top of the keyword and level to further narrow what the session captures.
- Keyword definitions are provider-specific, so the same bit value means different things across providers; values come from the provider's manifest or header.

**See also:**

- [ETW](etw.md)
- [DxgKrnl events](dxgkrnl-events.md)
- [WDDM](wddm.md)
- [VidMm / VidSch](vidmm-vidsch.md)
