def _dump_param_memory_stats(self):
        """Dump all model parameter shapes, dtypes and memory usage to a local file."""
        import datetime

        gpu_id = torch.cuda.current_device()
        output_file = f"/tmp/K3_param_memory_stats_gpu{gpu_id}.log"
        total_memory_bytes = 0
        total_cpu_memory_bytes = 0
        param_info_list = []
        seen_data_ptrs = set()

        for name, param in self.named_parameters():
            numel = param.numel()
            element_size = param.element_size()  # bytes per element
            param_memory = numel * element_size
            ptr = param.data.data_ptr()
            is_duplicate = ptr in seen_data_ptrs
            if not is_duplicate:
                seen_data_ptrs.add(ptr)
                if param.is_cuda:
                    total_memory_bytes += param_memory
                else:
                    total_cpu_memory_bytes += param_memory
            param_info_list.append(
                (name, list(param.shape), str(param.dtype), numel, param_memory, is_duplicate, param.is_cuda)
            )

        # Also account for buffers (non-parameter persistent tensors)
        total_buffer_bytes = 0
        total_cpu_buffer_bytes = 0
        buffer_info_list = []
        for name, buf in self.named_buffers():
            numel = buf.numel()
            element_size = buf.element_size()
            buf_memory = numel * element_size
            ptr = buf.data_ptr()
            is_duplicate = ptr in seen_data_ptrs
            if not is_duplicate:
                seen_data_ptrs.add(ptr)
                if buf.is_cuda:
                    total_buffer_bytes += buf_memory
                else:
                    total_cpu_buffer_bytes += buf_memory
            buffer_info_list.append(
                (name, list(buf.shape), str(buf.dtype), numel, buf_memory, is_duplicate, buf.is_cuda)
            )

        total_all_bytes = total_memory_bytes + total_buffer_bytes
        total_all_cpu_bytes = total_cpu_memory_bytes + total_cpu_buffer_bytes

        with open(output_file, "w") as f:
            f.write(f"DeepSeek V4 Model Parameter Memory Stats\n")
            f.write(f"Timestamp: {datetime.datetime.now()}\n")
            f.write(f"{'=' * 120}\n\n")

            f.write(f"{'Name':<80} {'Shape':<30} {'Dtype':<20} {'Numel':<15} {'Memory (MB)':<15} {'Note':<10}\n")
            f.write(f"{'-' * 170}\n")

            for name, shape, dtype, numel, mem, is_dup, is_cuda in param_info_list:
                note = "(tied)" if is_dup else ("(cpu)" if not is_cuda else "")
                f.write(
                    f"{name:<80} {str(shape):<30} {dtype:<20} {numel:<15} {mem / (1024**2):<15.4f} {note}\n"
                )

            f.write(f"\n{'=' * 120}\n")
            f.write(f"Total Parameters: {len(param_info_list)}\n")
            f.write(f"Total Parameter Memory (GPU): {total_memory_bytes / (1024**3):.4f} GB\n")
            f.write(f"Total Parameter Memory (CPU): {total_cpu_memory_bytes / (1024**3):.4f} GB\n")

            if buffer_info_list:
                f.write(f"\n{'=' * 120}\n")
                f.write(f"Buffers:\n")
                f.write(f"{'-' * 170}\n")
                for name, shape, dtype, numel, mem, is_dup, is_cuda in buffer_info_list:
                    note = "(tied)" if is_dup else ("(cpu)" if not is_cuda else "")
                    f.write(
                        f"{name:<80} {str(shape):<30} {dtype:<20} {numel:<15} {mem / (1024**2):<15.4f} {note}\n"
                    )
                f.write(f"\nTotal Buffers: {len(buffer_info_list)}\n")
                f.write(f"Total Buffer Memory (GPU): {total_buffer_bytes / (1024**3):.4f} GB\n")
                f.write(f"Total Buffer Memory (CPU): {total_cpu_buffer_bytes / (1024**3):.4f} GB\n")

            f.write(f"\n{'=' * 120}\n")
            f.write(f"Grand Total GPU (Parameters + Buffers): {total_all_bytes / (1024**3):.4f} GB\n")
            f.write(f"Grand Total CPU (Parameters + Buffers): {total_all_cpu_bytes / (1024**3):.4f} GB\n")

            # Model CUDA memory statistics (only model params + buffers, deduplicated by data_ptr)
            f.write(f"\n{'=' * 120}\n")
            f.write(f"Model CUDA Memory Statistics (model only, deduplicated):\n")
            f.write(f"{'-' * 120}\n")
            model_cuda_param_bytes = total_memory_bytes
            model_cuda_buffer_bytes = total_buffer_bytes
            model_cuda_total_bytes = total_all_bytes
            f.write(f"  Model params (CUDA):             {model_cuda_param_bytes / (1024**3):.4f} GB\n")
            f.write(f"  Model buffers (CUDA):            {model_cuda_buffer_bytes / (1024**3):.4f} GB\n")
            f.write(f"  Model total (CUDA):              {model_cuda_total_bytes / (1024**3):.4f} GB\n")

            # Diagnostic: compare logical size vs actual storage size (detect in-place quantization)
            f.write(f"\n{'=' * 120}\n")
            f.write(f"Storage vs Logical Size Diagnostic:\n")
            f.write(f"{'-' * 120}\n")
            total_logical_bytes = 0
            total_storage_bytes = 0
            storage_mismatch_list = []
            seen_storage_ptrs = set()
            for name, param in self.named_parameters():
                if param.is_cuda:
                    storage_ptr = param.data.storage().data_ptr()
                    logical_size = param.numel() * param.element_size()
                    total_logical_bytes += logical_size
                    if storage_ptr not in seen_storage_ptrs:
                        seen_storage_ptrs.add(storage_ptr)
                        storage_size = param.data.storage().nbytes()
                        total_storage_bytes += storage_size
                        if storage_size != logical_size:
                            storage_mismatch_list.append(
                                (name, logical_size, storage_size)
                            )
            for name, buf in self.named_buffers():
                if buf.is_cuda:
                    storage_ptr = buf.storage().data_ptr()
                    logical_size = buf.numel() * buf.element_size()
                    total_logical_bytes += logical_size
                    if storage_ptr not in seen_storage_ptrs:
                        seen_storage_ptrs.add(storage_ptr)
                        storage_size = buf.storage().nbytes()
                        total_storage_bytes += storage_size
                        if storage_size != logical_size:
                            storage_mismatch_list.append(
                                (name, logical_size, storage_size)
                            )
            f.write(f"  Total logical size (sum numel*elem_size): {total_logical_bytes / (1024**3):.4f} GB\n")
            f.write(f"  Total actual storage (sum storage.nbytes, dedup): {total_storage_bytes / (1024**3):.4f} GB\n")
            f.write(f"  Difference (logical - storage): {(total_logical_bytes - total_storage_bytes) / (1024**3):.4f} GB\n")
            if storage_mismatch_list:
                f.write(f"\n  Parameters with storage != logical size ({len(storage_mismatch_list)}):\n")
                for name, logical, storage in storage_mismatch_list:
                    f.write(f"    {name:<70} logical={logical/(1024**2):.4f} MB  storage={storage/(1024**2):.4f} MB\n")
            else:
                f.write(f"  All parameters: storage size == logical size (no in-place quantization detected)\n")

            # Diagnostic: torch.cuda.memory_allocated vs model size (detect NCCL/other allocations)
            f.write(f"\n{'=' * 120}\n")
            f.write(f"CUDA Allocator Diagnostic:\n")
            f.write(f"{'-' * 120}\n")
            cuda_allocated = torch.cuda.memory_allocated()
            cuda_reserved = torch.cuda.memory_reserved()
            f.write(f"  torch.cuda.memory_allocated():   {cuda_allocated / (1024**3):.4f} GB\n")
            f.write(f"  torch.cuda.memory_reserved():    {cuda_reserved / (1024**3):.4f} GB\n")
            f.write(f"  Model total (storage dedup):     {total_storage_bytes / (1024**3):.4f} GB\n")
            f.write(f"  Non-model allocated (allocated - model_storage): {(cuda_allocated - total_storage_bytes) / (1024**3):.4f} GB\n")
            f.write(f"  (Positive = other CUDA allocs like NCCL buffers; Negative = some model on CPU or freed)\n")

            # Diagnostic: enumerate live CUDA tensors NOT in the model tree to localize
            # exactly which tensors make up the "Non-model allocated" diff.
            # This walks gc.get_objects() and aggregates by (type, dtype, shape).
            import gc as _gc

            f.write(f"\n{'=' * 120}\n")
            f.write(f"Non-model CUDA Tensor Breakdown (live tensors not in named_parameters/buffers):\n")
            f.write(f"{'-' * 120}\n")

            # 1) Build the set of storage data_ptrs that DO belong to the model tree.
            model_storage_ptrs = set()
            for _n, _p in self.named_parameters(remove_duplicate=True):
                if _p.is_cuda:
                    try:
                        model_storage_ptrs.add(_p.untyped_storage().data_ptr())
                    except Exception:
                        pass
            for _n, _b in self.named_buffers(remove_duplicate=True):
                if _b.is_cuda:
                    try:
                        model_storage_ptrs.add(_b.untyped_storage().data_ptr())
                    except Exception:
                        pass

            # 2) Walk every live tensor; keep only CUDA tensors whose storage is NOT in the model tree.
            from collections import defaultdict as _defaultdict
            seen_storage_ptrs_walk = set()
            agg = _defaultdict(lambda: [0, 0])  # key -> [count, bytes]
            samples = _defaultdict(list)        # key -> list of (referrer type names, attr-name guesses)
            non_model_total_bytes = 0
            for obj in _gc.get_objects():
                try:
                    if not torch.is_tensor(obj):
                        continue
                    if not obj.is_cuda:
                        continue
                    storage = obj.untyped_storage()
                    sptr = storage.data_ptr()
                    if sptr == 0:
                        continue
                    if sptr in model_storage_ptrs:
                        continue
                    if sptr in seen_storage_ptrs_walk:
                        continue
                    seen_storage_ptrs_walk.add(sptr)
                    nbytes = storage.nbytes()
                    non_model_total_bytes += nbytes
                    key = f"dtype={str(obj.dtype):<22} shape={str(tuple(obj.shape)):<32}"
                    agg[key][0] += 1
                    agg[key][1] += nbytes
                    if len(samples[key]) < 2:
                        # Try to find an owning module attribute name to help locate the tensor.
                        owner_hints = []
                        for ref in _gc.get_referrers(obj)[:6]:
                            ref_t = type(ref).__name__
                            attr_name = None
                            if isinstance(ref, dict):
                                # Could be a module __dict__ — find the key whose value is obj
                                try:
                                    for k, v in ref.items():
                                        if v is obj:
                                            attr_name = k
                                            break
                                except Exception:
                                    pass
                            owner_hints.append(f"{ref_t}" + (f"[{attr_name}]" if attr_name else ""))
                        samples[key].append(owner_hints)
                except Exception:
                    continue

            f.write(f"  Walked tensors total: {non_model_total_bytes / (1024**3):.4f} GB "
                    f"(should approximate 'Non-model allocated' above)\n\n")
            f.write(f"  {'Bytes (MB)':>14}  {'Count':>6}  Description\n")
            f.write(f"  {'-' * 14}  {'-' * 6}  {'-' * 90}\n")
            for key, (cnt, sz) in sorted(agg.items(), key=lambda x: -x[1][1]):
                f.write(f"  {sz / (1024**2):>14.3f}  {cnt:>6d}  {key}\n")
                for hints in samples[key]:
                    f.write(f"  {'':>14}  {'':>6}    referrers: {hints}\n")

            # ----------------------------------------------------------------
            # Segment fragmentation diagnostic.
            # Walks torch.cuda.memory_snapshot() segments and per-block records
            # to localize *which segments* hold model-vs-non-model live blocks
            # and how much each segment "wastes" (segment_size - allocated_in_segment).
            # ----------------------------------------------------------------
            f.write(f"\n{'=' * 120}\n")
            f.write(f"Segment Fragmentation Diagnostic (torch.cuda.memory_snapshot):\n")
            f.write(f"{'-' * 120}\n")
            try:
                segments = torch.cuda.memory_snapshot()
            except Exception as _e:
                segments = []
                f.write(f"  memory_snapshot() failed: {_e}\n")

            # Build a fresh lookup: storage data_ptr -> name (model param/buffer).
            # We use ADDRESS overlap below, so this gives us name hints when a
            # block.address matches a known model tensor's storage address.
            model_ptr_to_name = {}
            for _n, _p in self.named_parameters(remove_duplicate=True):
                if _p.is_cuda:
                    try:
                        model_ptr_to_name[_p.untyped_storage().data_ptr()] = (
                            f"param:{_n}"
                        )
                    except Exception:
                        pass
            for _n, _b in self.named_buffers(remove_duplicate=True):
                if _b.is_cuda:
                    try:
                        model_ptr_to_name[_b.untyped_storage().data_ptr()] = (
                            f"buf:{_n}"
                        )
                    except Exception:
                        pass

            # Aggregate counters.
            total_seg_size = 0
            total_active_size = 0
            total_inactive_size = 0          # cached but not handed out (slack)
            total_segments = 0
            bucket_edges_mb = [16, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 1 << 30]
            occupancy_buckets = {
                "0-25%": [0, 0],
                "25-50%": [0, 0],
                "50-75%": [0, 0],
                "75-90%": [0, 0],
                "90-100%": [0, 0],
            }  # label -> [segment_count, total_slack_bytes]
            size_buckets = {
                f"<={e}MB": [0, 0, 0]  # [count, total_size, total_slack]
                for e in bucket_edges_mb
            }

            # Per-segment detail rows (top by slack).
            seg_rows = []  # list of dicts

            for seg in segments:
                total_segments += 1
                seg_size = int(seg.get("total_size", 0))
                seg_active = int(seg.get("active_size", 0))
                seg_alloc = int(seg.get("allocated_size", 0))
                total_seg_size += seg_size
                total_active_size += seg_alloc
                # Use allocated_size (handed-out, regardless of active) for slack:
                seg_slack = seg_size - seg_alloc
                total_inactive_size += seg_slack

                # Occupancy bucket
                occ = (seg_alloc / seg_size) if seg_size > 0 else 0.0
                if occ < 0.25:
                    occupancy_buckets["0-25%"][0] += 1
                    occupancy_buckets["0-25%"][1] += seg_slack
                elif occ < 0.50:
                    occupancy_buckets["25-50%"][0] += 1
                    occupancy_buckets["25-50%"][1] += seg_slack
                elif occ < 0.75:
                    occupancy_buckets["50-75%"][0] += 1
                    occupancy_buckets["50-75%"][1] += seg_slack
                elif occ < 0.90:
                    occupancy_buckets["75-90%"][0] += 1
                    occupancy_buckets["75-90%"][1] += seg_slack
                else:
                    occupancy_buckets["90-100%"][0] += 1
                    occupancy_buckets["90-100%"][1] += seg_slack

                # Size bucket
                size_mb = seg_size / (1024**2)
                for edge in bucket_edges_mb:
                    if size_mb <= edge:
                        key = f"<={edge}MB"
                        size_buckets[key][0] += 1
                        size_buckets[key][1] += seg_size
                        size_buckets[key][2] += seg_slack
                        break

                # Classify blocks inside this segment.
                blocks = seg.get("blocks", []) or []
                cur_addr = int(seg.get("address", 0))
                model_block_bytes = 0
                non_model_block_bytes = 0
                free_block_bytes = 0
                model_block_cnt = 0
                non_model_block_cnt = 0
                free_block_cnt = 0
                first_model_name = None
                first_non_model_size = None
                for blk in blocks:
                    state = blk.get("state", "")
                    sz = int(blk.get("size", 0))
                    is_alloc = state in ("active_allocated", "inactive")
                    # Note: PyTorch's snapshot doesn't return per-block address
                    # directly; we walk cumulatively from segment.address.
                    blk_addr = cur_addr
                    cur_addr += sz
                    if state == "active_allocated":
                        nm = model_ptr_to_name.get(blk_addr)
                        if nm is not None:
                            model_block_bytes += sz
                            model_block_cnt += 1
                            if first_model_name is None:
                                first_model_name = nm
                        else:
                            non_model_block_bytes += sz
                            non_model_block_cnt += 1
                            if first_non_model_size is None:
                                first_non_model_size = sz
                    elif state == "inactive":
                        # Allocated but not currently active (PyTorch caching
                        # allocator keeps these to reuse). Counted as slack.
                        free_block_bytes += sz
                        free_block_cnt += 1
                    else:
                        # 'active_pending_free' / 'inactive' / pure free
                        free_block_bytes += sz
                        free_block_cnt += 1

                seg_rows.append({
                    "addr": int(seg.get("address", 0)),
                    "size": seg_size,
                    "alloc": seg_alloc,
                    "slack": seg_slack,
                    "occ": occ,
                    "n_blocks": len(blocks),
                    "model_bytes": model_block_bytes,
                    "non_model_bytes": non_model_block_bytes,
                    "free_bytes": free_block_bytes,
                    "model_cnt": model_block_cnt,
                    "non_model_cnt": non_model_block_cnt,
                    "free_cnt": free_block_cnt,
                    "first_model": first_model_name,
                    "first_non_model_size": first_non_model_size,
                    "pool": seg.get("segment_pool_id", None),
                    "stream": seg.get("stream", None),
                })

            # ---- Summary ----
            f.write(
                f"  Total segments: {total_segments}, "
                f"total reserved: {total_seg_size / (1024**3):.3f} GB, "
                f"total allocated: {total_active_size / (1024**3):.3f} GB, "
                f"total slack: {total_inactive_size / (1024**3):.3f} GB "
                f"({(total_inactive_size / max(total_seg_size, 1)) * 100:.1f}% of reserved)\n\n"
            )

            # Occupancy distribution
            f.write(f"  Segment occupancy distribution (alloc_size / segment_size):\n")
            f.write(f"  {'Bucket':<10}  {'#Seg':>6}  {'Total Slack (MB)':>20}\n")
            for label, (cnt, slack_b) in occupancy_buckets.items():
                f.write(
                    f"  {label:<10}  {cnt:>6d}  {slack_b / (1024**2):>20.3f}\n"
                )

            # Size distribution
            f.write(f"\n  Segment size distribution:\n")
            f.write(
                f"  {'Bucket':<12}  {'#Seg':>6}  {'Total Size (MB)':>18}  {'Total Slack (MB)':>20}\n"
            )
            for label, (cnt, sz, sl) in size_buckets.items():
                if cnt == 0:
                    continue
                f.write(
                    f"  {label:<12}  {cnt:>6d}  {sz / (1024**2):>18.3f}  {sl / (1024**2):>20.3f}\n"
                )

            # Top segments by slack
            seg_rows.sort(key=lambda r: -r["slack"])
            f.write(f"\n  Top 40 segments by SLACK (segment_size - allocated_size):\n")
            f.write(
                f"  {'Addr':>14}  {'Size MB':>10}  {'Alloc MB':>10}  {'Slack MB':>10}  "
                f"{'Occ%':>6}  {'#Blk':>5}  {'Mdl#':>5}  {'NM#':>5}  {'Fr#':>5}  "
                f"{'Mdl MB':>8}  {'NM MB':>8}  {'Fr MB':>8}  "
                f"{'Pool':>10}  {'Stream':>14}  Hint\n"
            )
            for r in seg_rows[:40]:
                hint = ""
                if r["first_model"] is not None:
                    hint = f"first_model={r['first_model']}"
                elif r["first_non_model_size"] is not None:
                    hint = f"first_non_model_size={r['first_non_model_size'] / (1024**2):.2f}MB"
                pool_str = str(r["pool"]) if r["pool"] is not None else "-"
                stream_str = str(r["stream"]) if r["stream"] is not None else "-"
                # Truncate to keep columns aligned
                if len(pool_str) > 10:
                    pool_str = pool_str[:10]
                if len(stream_str) > 14:
                    stream_str = stream_str[:14]
                f.write(
                    f"  0x{r['addr']:>12x}  "
                    f"{r['size'] / (1024**2):>10.3f}  "
                    f"{r['alloc'] / (1024**2):>10.3f}  "
                    f"{r['slack'] / (1024**2):>10.3f}  "
                    f"{r['occ'] * 100:>6.1f}  "
                    f"{r['n_blocks']:>5d}  "
                    f"{r['model_cnt']:>5d}  "
                    f"{r['non_model_cnt']:>5d}  "
                    f"{r['free_cnt']:>5d}  "
                    f"{r['model_bytes'] / (1024**2):>8.3f}  "
                    f"{r['non_model_bytes'] / (1024**2):>8.3f}  "
                    f"{r['free_bytes'] / (1024**2):>8.3f}  "
                    f"{pool_str:>10}  {stream_str:>14}  "
                    f"{hint}\n"
                )

            # Segments that hold draft (model) tensors AND have meaningful slack
            f.write(
                f"\n  Segments holding model tensors with >=10% slack "
                f"(strong evidence of small-tensor-pinning):\n"
            )
            f.write(
                f"  {'Size MB':>10}  {'Alloc MB':>10}  {'Slack MB':>10}  "
                f"{'Occ%':>6}  {'Mdl#':>5}  {'Mdl MB':>8}  First model tensor\n"
            )
            offenders_total_slack = 0
            offenders_count = 0
            for r in seg_rows:
                if r["model_cnt"] == 0:
                    continue
                if r["size"] == 0:
                    continue
                if r["slack"] / r["size"] < 0.10:
                    continue
                offenders_total_slack += r["slack"]
                offenders_count += 1
                if offenders_count <= 60:
                    f.write(
                        f"  {r['size'] / (1024**2):>10.3f}  "
                        f"{r['alloc'] / (1024**2):>10.3f}  "
                        f"{r['slack'] / (1024**2):>10.3f}  "
                        f"{r['occ'] * 100:>6.1f}  "
                        f"{r['model_cnt']:>5d}  "
                        f"{r['model_bytes'] / (1024**2):>8.3f}  "
                        f"{r['first_model']}\n"
                    )
            f.write(
                f"\n  Total such offender segments: {offenders_count}, "
                f"total slack pinned by model tensors: "
                f"{offenders_total_slack / (1024**3):.3f} GB\n"
            )

        logger.info(
            f"[DeepSeek V4] Model param memory stats dumped to {output_file}. "
            f"GPU params: {total_memory_bytes / (1024**3):.4f} GB, "
            f"GPU buffers: {total_buffer_bytes / (1024**3):.4f} GB, "
            f"GPU total: {total_all_bytes / (1024**3):.4f} GB, "
            f"CPU params: {total_cpu_memory_bytes / (1024**3):.4f} GB, "
            f"CPU buffers: {total_cpu_buffer_bytes / (1024**3):.4f} GB"
        )