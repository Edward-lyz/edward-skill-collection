---
source_path: UserGuide/topics/gpu-metrics-available-metrics.rst
title: #### Available metrics
---
#### Available metrics

-  **GPC Clock Frequency** - ``gpc__cycles_elapsed.avg.per_second``

   The average GPC clock frequency in hertz. In public documentation the GPC
   clock may be called the "Application" clock, "Graphic" clock, "Base" clock,
   or "Boost" clock.

Note:
      The collection mechanism for GPC can result in a small fluctuation between samples.


-  **SYS Clock Frequency** - ``sys__cycles_elapsed.avg.per_second``

   The average SYS clock frequency in hertz. The GPU front end (command processor), copy engines, and the performance monitor run at the SYS clock. On Turing and NVIDIA GA100 GPUs, the sampling frequency is based upon a period of SYS clocks (not time) so samples per second will vary with SYS clock. On NVIDIA GA10x GPUs, the sampling frequency is based upon a fixed frequency clock. The maximum frequency scales linearly with the SYS clock.

-  **GR Active** - ``gr__cycles_active.sum.pct_of_peak_sustained_elapsed``

   The percentage of cycles the graphics/compute engine is active. The graphics/compute engine is active if there is any work in the graphics pipe or if the compute pipe is processing work.

   GA100 MIG - MIG is not yet supported. This counter will report the activity of the primary GR engine.

-  **Sync Compute In Flight** - ``gr__dispatch_cycles_active_queue_sync.avg.pct_of_peak_sustained_elapsed``

   The percentage of cycles with synchronous compute in flight.

   CUDA: CUDA will only report synchronous queue in the case of MPS configured with 64 sub-context. Synchronous refers to work submitted in VEID=0.

   Graphics: This will be true if any compute work submitted from the direct queue is in flight.

-  **Async Compute in Flight** - ``gr__dispatch_cycles_active_queue_async.avg.pct_of_peak_sustained_elapsed``

   The percentage of cycles with asynchronous compute in flight.

   CUDA: CUDA will only report all compute work as asynchronous. The one exception is if MPS is configured and all 64 sub-context are in use. 1 sub-context (VEID=0) will report as synchronous.

   Graphics: This will be true if any compute work submitted from a compute queue is in flight.

-  **Draw Started** - ``fe__draw_count.avg.pct_of_peak_sustained_elapsed``

   The ratio of draw calls issued to the graphics pipe to the maximum sustained rate of the graphics pipe.

Note:
      The percentage will always be very low as the front end can issue draw calls significantly faster than the pipe can execute the draw call. The rendering of this row will be changed to help indicate when draw calls are being issued.


-  **Dispatch Started** - ``gr__dispatch_count.avg.pct_of_peak_sustained_elapsed``

   The ratio of compute grid launches (dispatches) to the compute pipe to the maximum sustained rate of the compute pipe.

Note:
      The percentage will always be very low as the front end can issue grid launches significantly faster than the pipe can execute the draw call. The rendering of this row will be changed to help indicate when grid launches are being issued.

-  **Vertex/Tess/Geometry Warps in Flight** - ``tpc__warps_active_shader_vtg_realtime.avg.pct_of_peak_sustained_elapsed``

   The ratio of active vertex, geometry, tessellation, and meshlet shader warps resident on the SMs to the maximum number of warps per SM as a percentage.

-  **Pixel Warps in Flight** - ``tpc__warps_active_shader_ps_realtime.avg.pct_of_peak_sustained_elapsed``

   The ratio of active pixel/fragment shader warps resident on the SMs to the maximum number of warps per SM as a percentage.

-  **Compute Warps in Flight** - ``tpc__warps_active_shader_cs_realtime.avg.pct_of_peak_sustained_elapsed``

   The ratio of active compute shader warps resident on the SMs to the maximum number of warps per SM as a percentage.

-  **Active SM Unused Warp Slots** - ``tpc__warps_inactive_sm_active_realtime.avg.pct_of_peak_sustained_elapsed``

   The ratio of inactive warp slots on the SMs to the maximum number of warps per SM as a percentage. This is an indication of how many more warps may fit on the SMs if occupancy is not limited by a resource such as max warps of a shader type, shared memory, registers per thread, or thread blocks per SM.

-  **Idle SM Unused Warp Slots** - ``tpc__warps_inactive_sm_idle_realtime.avg.pct_of_peak_sustained_elapsed``

   The ratio of inactive warps slots due to idle SMs to the the maximum number of warps per SM as a percentage.

   This is an indicator that the current workload on the SM is not sufficient to put work on all SMs. This can be due to: 
   
   -  CPU starving the GPU.

   -  Current work is too small to saturate the GPU.

   -  Current work is trailing off but blocking next work.

-  **SMs Active** - ``sm__cycles_active.avg.pct_of_peak_sustained_elapsed``

   The ratio of cycles SMs had at least 1 warp in flight (allocated on SM) to the number of cycles as a percentage. A value of 0 indicates all SMs were idle (no warps in flight). A value of 50% can indicate some gradient between all SMs active 50% of the sample period or 50% of SMs active 100% of the sample period.

-  **SM Issue** - ``sm__inst_executed_realtime.avg.pct_of_peak_sustained_elapsed``

   The ratio of cycles that SM sub-partitions (warp schedulers) issued an instruction to the number of cycles in the sample period as a percentage.

-  **Tensor Active** - ``sm__pipe_tensor_cycles_active_realtime.avg.pct_of_peak_sustained_elapsed``

   The ratio of cycles the SM tensor pipes were active issuing tensor instructions to the number of cycles in the sample period as a percentage.

   TU102/4/6: This metric is not available on TU10x for periodic sampling. Please see Tensor Active/FP16 Active.

-  **Tensor Active / FP16 Active** - ``sm__pipe_shared_cycles_active_realtime.avg.pct_of_peak_sustained_elapsed``

   TU102/4/6 only.

   The ratio of cycles the SM tensor pipes or FP16x2 pipes were active issuing tensor instructions to the number of cycles in the sample period as a percentage.

-  **DRAM Read Bandwidth** - ``dramc__read_throughput.avg.pct_of_peak_sustained_elapsed``, ``dram__read_throughput.avg.pct_of_peak_sustained_elapsed``

-  **VRAM Read Bandwidth** - ``FBPA.TriageA.dramc__read_throughput.avg.pct_of_peak_sustained_elapsed``, ``FBSP.TriageSCG.dramc__read_throughput.avg.pct_of_peak_sustained_elapsed``, ``FBSP.TriageAC.dramc__read_throughput.avg.pct_of_peak_sustained_elapsed``

   The ratio of cycles the DRAM interface was active reading data to the elapsed cycles in the same period as a percentage.

-  **DRAM Write Bandwidth** - ``dramc__write_throughput.avg.pct_of_peak_sustained_elapsed``, ``dram__write_throughput.avg.pct_of_peak_sustained_elapsed``

-  **VRAM Write Bandwidth** - ``FBPA.TriageA.dramc__write_throughput.avg.pct_of_peak_sustained_elapsed``, ``FBSP.TriageSCG.dramc__write_throughput.avg.pct_of_peak_sustained_elapsed``, ``FBSP.TriageAC.dramc__write_throughput.avg.pct_of_peak_sustained_elapsed``

   The ratio of cycles the DRAM interface was active writing data to the elapsed cycles in the same period as a percentage.

- **NVENC Active**
    ``NVENC.TriageTop.nvenc__cycles_active.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the NVENC unit was actively processing a command to the number of cycles in the same sample period as a percentage.

- **NVENC Read Throughput**
    ``NVENC.TriageTop.nvenc__memif2nvenc_read_throughput.avg.pct_of_peak_sustained_elapsed``
  **NVENC Write Throughput**
    ``NVENC.TriageTop.nvenc__nvenc2memif_write_throughput.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the NVENC unit was actively processing read/write operations to the number of cycles in the same sample period as a percentage.

- **OFA Active**
    ``OFA.TriageTop.ofa_cycles_active.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the OFA (Optical Flow Accelerator) was actively processing a command to the number of cycles in the same sample period as a percentage.

- **OFA Read Throughput**
    ``OFA.TriageTop.ofa__memif2ofa_read_throughput.avg.pct_of_peak_sustained_elapsed``
  **OFA Write Throughput**
    ``OFA.TriageTop.ofa__ofa2memif_write_throughput.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the OFA (Optical Flow Accelerator) was actively processing read/write operations to the number of cycles in the same sample period as a percentage.

-  **NVLink bytes received** - ``nvlrx__bytes.avg.pct_of_peak_sustained_elapsed``

   The ratio of bytes received on the NVLink interface to the maximum number of bytes receivable in the sample period as a percentage. This value includes protocol overhead.

-  **NVLink bytes transmitted** - ``nvltx__bytes.avg.pct_of_peak_sustained_elapsed``

   The ratio of bytes transmitted on the NVLink interface to the maximum number of bytes transmittable in the sample period as a percentage. This value includes protocol overhead.

-  **PCIe Read Throughput** - ``pcie__read_bytes.avg.pct_of_peak_sustained_elapsed``

   The ratio of bytes received on the PCIe interface to the maximum number of bytes receivable in the sample period as a percentage. The theoretical value is calculated based upon the PCIe generation and number of lanes. This value includes protocol overhead.

-  **PCIe Write Throughput** - ``pcie__write_bytes.avg.pct_of_peak_sustained_elapsed``

   The ratio of bytes transmitted on the PCIe interface to the maximum number of bytes receivable in the sample period as a percentage. The theoretical value is calculated based upon the PCIe generation and number of lanes. This value includes protocol overhead.

-  **PCIe Read Requests to BAR1** - ``pcie__rx_requests_aperture_bar1_op_read.sum``

-  **PCIe Write Requests to BAR1** - ``pcie__rx_requests_aperture_bar1_op_write.sum``

   BAR1 is a PCI Express (PCIe) interface used to allow the CPU or other devices to directly access GPU memory. The GPU normally transfers memory with its copy engines, which would not show up as BAR1 activity. The GPU drivers on the CPU do a small amount of BAR1 accesses, but heavier traffic is typically coming from other technologies.

   On Linux, technologies like GPU Direct, GPU Direct RDMA, and GPU Direct Storage transfer data across PCIe BAR1. In the case of GPU Direct RDMA, that would be an Ethernet or InfiniBand adapter directly writing to GPU memory.

   On Windows, Direct3D12 resources can also be made accessible directly to the CPU via NVAPI functions to support small writes or reads from GPU buffers, in this case too many BAR1 accesses can indicate a performance issue, like it has been demonstrated in the Optimizing DX12 Resource Uploads to the GPU Using CPU-Visible VRAM technical blog post.
