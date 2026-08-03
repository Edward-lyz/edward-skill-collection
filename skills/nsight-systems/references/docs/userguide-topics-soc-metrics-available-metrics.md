---
source_path: UserGuide/topics/soc-metrics-available-metrics.rst
title: ## Available metrics
---
## Available metrics

- **CPU Read Throughput**
    ``mcc__dram_throughput_srcnode_cpu_op_read.avg.pct_of_peak_sustained_elapsed``
  **CPU Write Throughput**
    ``mcc__dram_throughput_srcnode_cpu_op_write.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the SoC memory controllers were actively processing read/write operations from the CPU to the number of cycles in the same sample period as a percentage.

- **GPU Read Throughput**
    ``mcc__dram_throughput_srcnode_gpu_op_read.avg.pct_of_peak_sustained_elapsed``
  **GPU Write Throughput**
    ``mcc__dram_throughput_srcnode_gpu_op_write.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the SoC memory controllers were actively processing read/write operations from the GPU to the number of cycles in the same sample period as a percentage.

- **DBB Read Throughput**
    ``mcc__dram_throughput_srcnode_dbb_op_read.avg.pct_of_peak_sustained_elapsed``
  **DBB Write Throughput**
    ``mcc__dram_throughput_srcnode_dbb_op_write.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the SoC memory controllers were actively processing read/write operations from not-CPU/not-GPU to the number of cycles in the same sample period as a percentage.

- **DRAM Read Throughput**
    ``mcc__dram_throughput_op_read.avg.pct_of_peak_sustained_elapsed``
  **DRAM Write Throughput**
    ``mcc__dram_throughput_op_write.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the SoC memory controllers were actively processing read/write operations to the number of cycles in the same sample period as a percentage.

- **DLA0/DLA1 Active**
    ``nvdla__cycles_active.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the DLA (Deep Learning Accelerator) was actively processing a command to the number of cycles in the same sample period as a percentage.

- **DLA0/DLA1 Read Throughput**
    ``nvdla__dbb2nvdla_read_throughput.avg.pct_of_peak_sustained_elapsed``
  **DLA0/DLA1 Write Throughput**
    ``nvdla__nvdla2dbb_write_throughput.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the DLA (Deep Learning Accelerator) was actively processing read/write operations to the number of cycles in the same sample period as a percentage.

- **NVENC Active**
    ``nvenc__cycles_active.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the NVENC unit was actively processing a command to the number of cycles in the same sample period as a percentage.

- **NVENC Read Throughput**
    ``nvenc__memif2nvenc_read_throughput.avg.pct_of_peak_sustained_elapsed``
  **NVENC Write Throughput**
    ``nvenc__nvenc2memif_write_throughput.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the NVENC unit was actively processing read/write operations to the number of cycles in the same sample period as a percentage.

- **PVA VPU Active**
    ``pvavpu__vpu_cycles_active.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the PVA (Programmable Vision Accelerator) VPU (Vector Processing Unit) was actively processing a command to the number of cycles in the same sample period as a percentage.

- **PVA DMA Read Throughput**
    ``pva__dbb2pvadma_read_throughput.avg.pct_of_peak_sustained_elapsed``
  **PVA DMA Write Throughput**
    ``pva__pvadma2dbb_write_throughput.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the PVA (Programmable Vision Accelerator) VPU (Vector Processing Unit) was actively processing read/write operations to the number of cycles in the same sample period as a percentage.

Note:
      
      To enable PVA trace on DRIVE 6.0.8.0, run these two commands before
      mounting any additional partitions:
      
      ``echo 1 >/dev/nvpvadebugfs/pva0/tracing``
      ``echo 2 >/dev/nvpvadebugfs/pva0/trace_level``       


- **OFA Active**
    ``ofa_cycles_active.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the OFA (Optical Flow Accelerator) was actively processing a command to the number of cycles in the same sample period as a percentage.

- **OFA Read Throughput**
    ``ofa__memif2ofa_read_throughput.avg.pct_of_peak_sustained_elapsed``
  **OFA Write Throughput**
    ``ofa__ofa2memif_write_throughput.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the OFA (Optical Flow Accelerator) was actively processing read/write operations to the number of cycles in the same sample period as a percentage.

- **VIC Active**
    ``vic_cycles_active.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the VIC (Video Image Compositor) was actively processing a command to the number of cycles in the same sample period as a percentage.

- **VIC Read Throughput**
    ``vic__dbb2vic_read_throughput.avg.pct_of_peak_sustained_elapsed``
  **VIC Write Throughput**
    ``vic__vic2dbb_write_throughput.avg.pct_of_peak_sustained_elapsed``

  The ratio of cycles the VIC (Video Image Compositor) was actively processing read/write operations to the number of cycles in the same sample period as a percentage.
