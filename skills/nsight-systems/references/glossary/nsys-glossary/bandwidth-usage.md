# Bandwidth usage

**Short:** The measured data rate carried by a transfer path (interconnect or memory bus) over time, expressed in bytes per second.

**Details:**

- Common paths a profiler tracks are PCIe (for example Gen4 x16), NVLink between GPUs, the on-package GPU memory bus (HBM or GDDR), the system DRAM channels, and the network interface for distributed workloads.
- Each path has a theoretical peak set by link width, generation, and clock. Useful throughput is lower because of protocol overhead, ECC, and access-pattern inefficiency.
- A trace usually renders bandwidth as a stacked rate plot: one band per client or channel, summed against the link's peak. Saturation is visible as a flat top at or near peak; idle gaps show as flat zero.
- Sample resolution matters. A short burst that saturates a link can be smoothed away when the counter is averaged over a long window, so the chart may understate peak pressure.

**See also:**

- [GPU bound](../graphics-glossary/gpu-bound.md)
- [Memory transfer](../graphics-glossary/memory-transfer.md)
- [Resource migration](../graphics-glossary/resource-migration.md)
