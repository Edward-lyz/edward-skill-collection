"""
GPU Memory Tracker for SGLang Server Startup.

This module provides utilities to systematically track GPU memory usage
across different modules during the SGLang server startup process.

Usage:
    from sglang.srt.utils.gpu_memory_tracker import GPUMemoryTracker

    tracker = GPUMemoryTracker(device="cuda", gpu_id=0)
    tracker.snapshot("before_nccl_init")
    # ... do NCCL init ...
    tracker.snapshot("after_nccl_init")
    tracker.print_summary()

Enable via environment variable:
    SGLANG_TRACK_GPU_MEMORY=1 python -m sglang.launch_server ...
"""

import gc
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

import torch

logger = logging.getLogger(__name__)

ENABLE_GPU_MEMORY_TRACKING = os.environ.get("SGLANG_TRACK_GPU_MEMORY", "0") == "1"


@dataclass
class MemorySnapshot:
    label: str
    timestamp_s: float
    allocated_gb: float  # torch.cuda.memory_allocated
    reserved_gb: float  # torch.cuda.memory_reserved
    free_gb: float  # from torch.cuda.mem_get_info
    total_gb: float  # from torch.cuda.mem_get_info

    @property
    def driver_used_gb(self) -> float:
        """All driver-visible used memory: total - free."""
        return self.total_gb - self.free_gb

    @property
    def torch_reserved_slack_gb(self) -> float:
        """PyTorch reserved but not actively allocated memory."""
        return self.reserved_gb - self.allocated_gb

    @property
    def non_torch_used_gb(self) -> float:
        """Driver-visible memory not owned by PyTorch's caching allocator."""
        return self.driver_used_gb - self.reserved_gb

    @property
    def driver_used_minus_torch_allocated_gb(self) -> float:
        """driver_used - torch_allocated = torch_reserved_slack + non_torch_used."""
        return self.driver_used_gb - self.allocated_gb


@dataclass
class GPUMemoryTracker:
    """Tracks GPU memory usage at various points during server startup."""

    device: str = "cuda"
    gpu_id: int = 0
    enabled: bool = field(default_factory=lambda: ENABLE_GPU_MEMORY_TRACKING)
    snapshots: List[MemorySnapshot] = field(default_factory=list)

    def snapshot(self, label: str):
        """Take a memory snapshot at the current point.

        Before measuring, we force garbage collection and release all cached
        (but unused) GPU memory back to the driver. This ensures that only
        *persistently allocated* tensors (weights, KV cache, CUDA graph buffers,
        NCCL buffers, etc.) are reflected in the measurement — temporary
        activations from forward passes or warmup are excluded.
        """
        if not self.enabled:
            return
        if self.device != "cuda":
            return

        import time

        # 1. Synchronize to ensure all async GPU ops are done
        torch.cuda.synchronize(self.gpu_id)

        # 2. Force Python GC to release any unreferenced tensors
        gc.collect()

        # 3. Release all cached memory from PyTorch allocator back to driver
        #    After this, memory_allocated() == only live tensors with active references
        #    memory_reserved() will drop to match allocated (mostly)
        torch.cuda.empty_cache()

        # 4. Now measure — this reflects only persistent allocations
        allocated = torch.cuda.memory_allocated(self.gpu_id) / (1024**3)
        reserved = torch.cuda.memory_reserved(self.gpu_id) / (1024**3)
        free, total = torch.cuda.mem_get_info(self.gpu_id)
        free_gb = free / (1024**3)
        total_gb = total / (1024**3)

        snap = MemorySnapshot(
            label=label,
            timestamp_s=time.time(),
            allocated_gb=allocated,
            reserved_gb=reserved,
            free_gb=free_gb,
            total_gb=total_gb,
        )
        self.snapshots.append(snap)

        logger.info(
            f"[GPU Memory Tracker] [{label}] "
            f"driver_used={snap.driver_used_gb:.3f} GB, "
            f"torch_allocated={allocated:.3f} GB, "
            f"torch_reserved={reserved:.3f} GB, "
            f"torch_reserved_slack={snap.torch_reserved_slack_gb:.3f} GB, "
            f"non_torch_used={snap.non_torch_used_gb:.3f} GB, "
            f"free={free_gb:.3f} GB, "
            f"total={total_gb:.3f} GB"
        )

    def get_delta(self, label_before: str, label_after: str) -> Optional[float]:
        """Get the memory delta (allocated) between two labeled snapshots."""
        before = next((s for s in self.snapshots if s.label == label_before), None)
        after = next((s for s in self.snapshots if s.label == label_after), None)
        if before and after:
            return after.allocated_gb - before.allocated_gb
        return None

    def print_summary(self):
        """Print a comprehensive summary of memory usage by module."""
        if not self.enabled or len(self.snapshots) < 2:
            return

        logger.info("=" * 80)
        logger.info("[GPU Memory Tracker] ===== GPU MEMORY USAGE SUMMARY =====")
        logger.info("=" * 80)

        # Print each snapshot
        logger.info(
            f"{'Stage':<45} "
            f"{'Driver Used':>12} "
            f"{'Torch Alloc':>12} "
            f"{'Torch Rsvd':>12} "
            f"{'Rsvd Slack':>12} "
            f"{'Non-Torch':>12} "
            f"{'Free':>12}"
        )
        logger.info("-" * 135)
        for snap in self.snapshots:
            logger.info(
                f"{snap.label:<45} "
                f"{snap.driver_used_gb:>9.3f} GB "
                f"{snap.allocated_gb:>9.3f} GB "
                f"{snap.reserved_gb:>9.3f} GB "
                f"{snap.torch_reserved_slack_gb:>9.3f} GB "
                f"{snap.non_torch_used_gb:>9.3f} GB "
                f"{snap.free_gb:>9.3f} GB"
            )

        # Print deltas between consecutive stages
        logger.info("")
        logger.info(
            f"{'Module':<45} "
            f"{'Driver Used':>15} "
            f"{'Torch Alloc':>15} "
            f"{'Torch Rsvd':>15} "
            f"{'Rsvd Slack':>15} "
            f"{'Non-Torch':>15} "
            f"{'Note':<20}"
        )
        logger.info(
            f"{'':<45} "
            f"{'(total-free)':>15} "
            f"{'(allocated)':>15} "
            f"{'(reserved)':>15} "
            f"{'(rsvd-alloc)':>15} "
            f"{'(driver-rsvd)':>15}"
        )
        logger.info("-" * 145)

        # Define expected module pairs.
        # Canonical stages (skill patch labels, role-aware target/draft) first;
        # legacy labels (native aiak commit 491ed25b / older logs) kept below so
        # both timelines render.
        module_pairs = [
            # ---- canonical stages ----
            ("Initial / CUDA Context", "initial", "after_set_device"),
            ("NCCL Init", "before_nccl_init", "after_nccl_init"),
            ("Load Target Model", "before_load_target_model", "after_load_target_model"),
            ("Load Draft Model", "before_load_draft_model", "after_load_draft_model"),
            ("Alloc Target KV Cache", "before_alloc_target_kv_cache", "after_alloc_target_kv_cache"),
            ("Alloc Draft KV Cache", "before_alloc_draft_kv_cache", "after_alloc_draft_kv_cache"),
            ("Configure Aux Hidden", "before_configure_aux_hidden", "after_configure_aux_hidden"),
            ("Target Build Attention Backends", "before_target_build_attention_backends", "after_target_build_attention_backends"),
            ("Prepare Replicated Q Proj", "before_prepare_replicated_q_proj", "after_prepare_replicated_q_proj"),
            ("Draft Build Attention Backends", "before_draft_build_attention_backends", "after_draft_build_attention_backends"),
            ("Target CUDA Graph", "before_target_cuda_graph", "after_target_cuda_graph"),
            ("Draft CUDA Graph", "before_draft_cuda_graph", "after_draft_cuda_graph"),
            # ---- legacy labels ----
            ("CUDA Context", "initial", "after_set_device"),
            ("NCCL/Distributed Init", "after_set_device", "after_nccl_init"),
            ("Model Weights Loading", "before_load_model", "after_load_model"),
            ("TorchAO Quantization", "after_load_model", "after_torchao"),
            ("KV Cache Allocation", "before_kv_cache", "after_kv_cache"),
            ("cuBLAS Workspace", "before_cublas", "after_cublas"),
            ("Attention Backend Init", "before_attention_backend", "after_attention_backend"),
            ("Kernel Warmup", "before_kernel_warmup", "after_kernel_warmup"),
            ("CUDA Graph Capture", "before_cuda_graph", "after_cuda_graph"),
            ("Piecewise CUDA Graph", "before_piecewise_cuda_graph", "after_piecewise_cuda_graph"),
            ("Symmetric Memory Pool", "before_symm_mem", "after_symm_mem"),
            # ---- Eagle draft worker phases ----
            ("[Draft] Inner Init (model load + kv cache + ...)", "draft_before_inner_init", "draft_after_inner_init"),
            ("[Draft] Attention Backend Init", "draft_before_attention_backend", "draft_after_attention_backend"),
            ("[Draft] Draft CUDA Graph Capture", "draft_before_draft_cuda_graph", "draft_after_draft_cuda_graph"),
            ("[Draft] Draft Extend CUDA Graph", "draft_before_draft_extend_cuda_graph", "draft_after_draft_extend_cuda_graph"),
        ]

        for module_name, before_label, after_label in module_pairs:
            before = next((s for s in self.snapshots if s.label == before_label), None)
            after = next((s for s in self.snapshots if s.label == after_label), None)
            if before and after:
                delta_driver_used = after.driver_used_gb - before.driver_used_gb
                delta_torch_allocated = after.allocated_gb - before.allocated_gb
                delta_torch_reserved = after.reserved_gb - before.reserved_gb
                delta_torch_reserved_slack = (
                    after.torch_reserved_slack_gb - before.torch_reserved_slack_gb
                )
                delta_non_torch_used = after.non_torch_used_gb - before.non_torch_used_gb

                note = ""
                if delta_non_torch_used > 0.01 and delta_torch_allocated < delta_driver_used * 0.5:
                    note = "<-- non-PyTorch alloc"
                elif delta_torch_reserved_slack > 0.01:
                    note = "<-- PyTorch reserved slack"

                logger.info(
                    f"{module_name:<45} "
                    f"{delta_driver_used:>+12.3f} GB "
                    f"{delta_torch_allocated:>+12.3f} GB "
                    f"{delta_torch_reserved:>+12.3f} GB "
                    f"{delta_torch_reserved_slack:>+12.3f} GB "
                    f"{delta_non_torch_used:>+12.3f} GB "
                    f"{note}"
                )

        # Overall summary
        logger.info("-" * 145)
        first = self.snapshots[0]
        last = self.snapshots[-1]
        logger.info(
            f"{'TOTAL (first -> last)':<45} "
            f"{(last.driver_used_gb - first.driver_used_gb):>+12.3f} GB "
            f"{(last.allocated_gb - first.allocated_gb):>+12.3f} GB "
            f"{(last.reserved_gb - first.reserved_gb):>+12.3f} GB "
            f"{(last.torch_reserved_slack_gb - first.torch_reserved_slack_gb):>+12.3f} GB "
            f"{(last.non_torch_used_gb - first.non_torch_used_gb):>+12.3f} GB"
        )
        logger.info("")
        logger.info(
            f"[GPU Memory Tracker] Final state: "
            f"driver_used={last.driver_used_gb:.3f} GB, "
            f"torch_allocated={last.allocated_gb:.3f} GB, "
            f"torch_reserved={last.reserved_gb:.3f} GB, "
            f"torch_reserved_slack={last.torch_reserved_slack_gb:.3f} GB, "
            f"non_torch_used={last.non_torch_used_gb:.3f} GB, "
            f"free={last.free_gb:.3f} GB / {last.total_gb:.3f} GB total"
        )
        logger.info(
            f"[GPU Memory Tracker] Accounting identity: "
            f"total={last.total_gb:.3f} GB = "
            f"free={last.free_gb:.3f} GB + "
            f"torch_reserved={last.reserved_gb:.3f} GB + "
            f"non_torch_used={last.non_torch_used_gb:.3f} GB"
        )
        logger.info(
            f"[GPU Memory Tracker] Driver used minus torch allocated: "
            f"{last.driver_used_minus_torch_allocated_gb:.3f} GB = "
            f"torch_reserved_slack={last.torch_reserved_slack_gb:.3f} GB + "
            f"non_torch_used={last.non_torch_used_gb:.3f} GB"
        )

        # Detailed PyTorch memory stats
        if self.device == "cuda":
            self._print_pytorch_memory_stats()

        logger.info("=" * 80)

    def _print_pytorch_memory_stats(self):
        """Print detailed PyTorch CUDA memory allocator stats."""
        logger.info("")
        logger.info("[GPU Memory Tracker] ----- PyTorch CUDA Memory Allocator Stats -----")
        stats = torch.cuda.memory_stats(self.gpu_id)
        keys_of_interest = [
            "allocated_bytes.all.current",
            "allocated_bytes.all.peak",
            "allocated_bytes.large_pool.current",
            "allocated_bytes.large_pool.peak",
            "allocated_bytes.small_pool.current",
            "allocated_bytes.small_pool.peak",
            "reserved_bytes.all.current",
            "reserved_bytes.all.peak",
            "reserved_bytes.large_pool.current",
            "reserved_bytes.large_pool.peak",
            "num_alloc_retries",
            "num_ooms",
        ]
        for key in keys_of_interest:
            if key in stats:
                val = stats[key]
                if "bytes" in key:
                    logger.info(f"  {key}: {val / (1024**3):.3f} GB")
                else:
                    logger.info(f"  {key}: {val}")


# Global tracker instance (per-process)
_global_tracker: Optional[GPUMemoryTracker] = None


def get_global_memory_tracker() -> Optional[GPUMemoryTracker]:
    return _global_tracker


def init_global_memory_tracker(device: str = "cuda", gpu_id: int = 0) -> GPUMemoryTracker:
    """Initialize the per-process tracker. Idempotent: a second call returns the existing
    instance so snapshots from main + draft workers accumulate in one timeline."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = GPUMemoryTracker(device=device, gpu_id=gpu_id)
    return _global_tracker
