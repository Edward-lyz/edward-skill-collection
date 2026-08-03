# NVTX category

**Short:** An integer tag on an NVTX event, scoped to a domain, used to color-classify and filter events.

**Details:**

- The category is the ``category`` field on ``nvtxEventAttributes_t``, set by the producer on each ``nvtxRangePushEx``, ``nvtxRangeStartEx``, or ``nvtxMarkEx`` call.
- Category zero is the default; any other integer identifies a producer defined group such as "physics", "io", or "audio".
- A human readable name is bound to the integer once with ``nvtxDomainNameCategory`` (or the global ``nvtxNameCategory``), so events stay cheap to emit and only carry the id.
- Names are scoped to the enclosing domain: the same integer can mean different things in different domains, and is independent of categories registered globally.
- Profilers commonly assign a stable color per category and offer "group by category" views, letting users separate render work from streaming work inside a single domain.
- Categories complement, but do not replace, NVTX ranges and payloads: they classify an event, while ranges give it duration and payloads give it data.

**See also:**

- [NVTX domain](nvtx-domain.md)
- [NVTX range](nvtx-range.md)
- [NVTX mark](nvtx-mark.md)
- [NVTX payload](nvtx-payload.md)
