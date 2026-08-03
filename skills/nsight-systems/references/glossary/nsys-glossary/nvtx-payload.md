# NVTX payload

**Short:** Typed data attached to an NVTX event so tools can show structured context instead of a bare name.

**Details:**

- A payload is the optional value field on an NVTX event attributes record (for example ``nvtxEventAttributes_t::payload`` populated by ``nvtxRangePushEx`` or ``nvtxMarkEx``).
- The predefined ``payload`` is a union of numeric scalars only: signed and unsigned 32 and 64 bit integers, and single and double precision floats; string or text data is not a payload type and belongs to the separate ``message`` field on the same event attributes record.
- Extended payloads carry structured data: a producer registers a schema describing field names, types, and nesting, then events reference that schema by a payload id so the binary blob can be decoded later.
- Schemas support nested structs and arrays, so one event can carry a frame descriptor, MPI peer ranks, or a small stack of source locations.
- Profilers use the schema to render a payload as a tooltip or table, turning opaque numbers into named fields like communicator, function, file, and line.

**See also:**

- [NVTX range](nvtx-range.md)
- [NVTX mark](nvtx-mark.md)
- [NVTX domain](nvtx-domain.md)
- [NVTX category](nvtx-category.md)
