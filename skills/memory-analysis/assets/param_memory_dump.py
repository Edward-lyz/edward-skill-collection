"""Standalone, model-agnostic parameter/buffer memory dump.

Compact version producing exactly the table the skill's diff parser consumes
(Name/Shape/Dtype/Numel/Memory(MB)/Note rows, then a `Total Parameters:` line).
Works on any nn.Module. Filename includes model class + pid so main and draft
(speculative) workers sharing a GPU do not overwrite each other.
"""

import datetime


def dump_param_memory_stats(model, output_file=None):
    import os
    import torch

    gpu_id = torch.cuda.current_device()
    tag = type(model).__name__
    output_file = output_file or f"/tmp/K3_param_memory_stats_gpu{gpu_id}_{tag}_{os.getpid()}.log"

    seen = set()
    gpu_param = cpu_param = 0
    rows = []
    for name, p in model.named_parameters():
        nb = p.numel() * p.element_size()
        ptr = p.data.data_ptr()
        dup = ptr in seen
        if not dup:
            seen.add(ptr)
            if p.is_cuda:
                gpu_param += nb
            else:
                cpu_param += nb
        rows.append((name, list(p.shape), str(p.dtype), p.numel(), nb, dup, p.is_cuda))

    gpu_buf = 0
    bufs = []
    for name, b in model.named_buffers():
        nb = b.numel() * b.element_size()
        ptr = b.data_ptr()
        dup = ptr in seen
        if not dup:
            seen.add(ptr)
            if b.is_cuda:
                gpu_buf += nb
        bufs.append((name, list(b.shape), str(b.dtype), b.numel(), nb, dup, b.is_cuda))

    with open(output_file, "w") as f:
        f.write("Model Parameter Memory Stats\n")
        f.write(f"Timestamp: {datetime.datetime.now()}\n")
        f.write("=" * 120 + "\n\n")
        f.write(f"{'Name':<80} {'Shape':<30} {'Dtype':<20} "
                f"{'Numel':<15} {'Memory (MB)':<15} {'Note':<10}\n")
        f.write("-" * 170 + "\n")
        for name, shape, dt, ne, mem, dup, cu in rows + bufs:
            note = "(tied)" if dup else ("(cpu)" if not cu else "")
            f.write(f"{name:<80} {str(shape):<30} {dt:<20} "
                    f"{ne:<15} {mem / (1024 ** 2):<15.4f} {note}\n")
        f.write("\n" + "=" * 120 + "\n")
        f.write(f"Total Parameters: {len(rows)}\n")
        f.write(f"Total Parameter Memory (GPU): {gpu_param / (1024 ** 3):.4f} GB\n")
        f.write(f"Total Parameter Memory (CPU): {cpu_param / (1024 ** 3):.4f} GB\n")
        f.write(f"Total Buffer Memory (GPU): {gpu_buf / (1024 ** 3):.4f} GB\n")
    return output_file
