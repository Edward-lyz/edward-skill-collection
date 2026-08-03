---
source_path: AnalysisGuide/topics/graphics_schema_pitfalls.rst
title: ## Graphics Schema Pitfalls
---
## Graphics Schema Pitfalls

Common SQL traps and misinterpretations when querying graphics-related tables in
the ``.sqlite`` database produced by ``nsys export``. Read these alongside the
sqlite-schema (table columns, ID encoding, timestamps, and query patterns)
and the sqlite-schema-pitfalls section.

### ETW_EVENTS gotchas (Windows traces)

- Columns are ``timestamp``, ``typeId``, ``globalTid``, ``opcode``, ``data``. **No** ``duration`` **column** -- ETW events are point-in-time, not intervals.
- Event names go through ``GENERIC_EVENT_TYPES.nameId`` -> ``StringIds.value``. Always join; comparing ``nameId`` against a string literal silently matches nothing.
- ``etwEventId`` is **not** a column on ``ETW_EVENTS`` -- it lives on ``GENERIC_EVENT_TYPES`` (the event-*type* metadata), reached via the same ``ETW_EVENTS.typeId`` -> ``GENERIC_EVENT_TYPES.typeId`` join as above. To filter by event id, join through the type table (``WHERE t.etwEventId = 184``), never ``WHERE etwEventId = 184`` directly on ``ETW_EVENTS``.
- DxgKrnl ``Present`` events are the event type with ``etwEventId = 184`` (the canonical CPU frame boundary on Windows). Other ``Present`` IDs (42 / 43) appear too -- de-duplicate by sticking to 184 for frame counting.

### DX12_API / VULKAN_API / OPENGL_API gotchas

- Columns are ``start``, ``end``, ``globalTid``, ``nameId``. **Duration =** ``(end - start)``. Use ``start`` / ``end``, **not** ``timestamp`` -- there is no ``timestamp`` column.
- API name goes through ``StringIds.value``. Always join.
