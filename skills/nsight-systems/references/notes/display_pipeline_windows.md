# Display Pipeline (Windows)




Windows path from ``IDXGISwapChain::Present()`` to pixels on the display, and the ETW events that expose each stage in NSys (``.nsys-rep``) and ETL traces.

> **Note**
>
> **Platform scope.** This doc is Windows-only -- DXGI / DWM / WDDM / DxgKrnl are all Windows concepts.

## Present models

Windows chooses a presentation path per swapchain. The path determines latency and which ETW events fire.

| Model | Path | Latency | ETW signature |
|---|---|---|---|
| **Hardware Composed Independent Flip (HCIF / MPO)** | App -> display hardware (multi-plane overlay) | Lowest | ``MMIOFlipMultiPlaneOverlay3`` + ``MMIOFlipMultiPlaneOverlay`` |
| **Independent Flip (Direct Flip)** | App -> display, bypassing DWM | Low | ``IndependentFlip`` + MMIOFlip\*; ``PresentHistory`` model ``D3DKMT_PM_REDIRECTED_FLIP`` |
| **DWM Composed Flip** | App -> DWM compositor -> display | Medium (+1 DWM frame) | Win32k ``TokenCompositionSurfaceObject`` / ``TokenStateChanged``; no MMIOFlip on the app's frame |
| **Legacy BitBlt** | App -> blit into DWM surface | Highest | DXGI ``Present`` only; no flip path |

**For performance analysis, prefer HCIF / Independent Flip.** If the trace shows DWM-composed or BitBlt for a fullscreen game, that is itself a finding. ``FlipTrueImmediate=1`` in an ``IndependentFlip`` event means the app requested non-VSync-aligned flips; physical refresh still gates actual update.

## ETW providers

Every event below comes from one of the providers in this table. Names use the ``Microsoft-Windows-*`` / ``NVIDIA-*`` manifest form; shorthand (e.g. ``DxgKrnl`` for ``Microsoft-Windows-DxgKrnl``) is used in the rest of this doc for brevity.

| Provider | GUID | Events contributed |
|---|---|---|
| ``Microsoft-Windows-DxgKrnl`` (aka **DxgKrnl**) | ``802EC45A-1E99-4B83-9920-87C98277BA9D`` | ``Present`` (42/43/184), ``QueuePacket`` start/stop, ``MMIOFlipMultiPlaneOverlay`` (259), ``MMIOFlipMultiPlaneOverlay3`` (386), ``VSyncDPC``, ``VSyncDPCMultiPlane``, ``IndependentFlip`` |
| ``Microsoft-Windows-DXGI`` | ``CA11C036-0102-4A2D-A6AD-F03CFED5D3C9`` | ``Present_Start`` / ``IDXGISwapChain_Present`` (user-mode, PID/TID) |
| ``Microsoft-Windows-Win32k`` | ``8C416C79-D49B-4F01-A467-E56D3AA8234C`` | ``TokenCompositionSurfaceObject``, ``TokenStateChanged`` (DWM composed-flip tokens) |
| ``Microsoft-Windows-Dwm-Core`` | ``9E9BBA3C-2E38-40CB-99F4-9E8281425164`` | DWM compositor events |
| ``NVIDIA-DD-External`` | ``AE4F8626-8265-40D1-A70B-11B64240E8E9`` | ``FlipRequest`` (driver-proposed flip time, QPC) |
| ``NVIDIA-PCL`` (Present-Composition Latency) | ``0D216F06-82A6-4D49-BC4F-8F38AE56EFAB`` | Reflex PCL events |

**xperf requires explicit providers -- there is no default.** ``xperf -start <session> -on <providers>`` only captures what you list. ``wevtutil get-publisher "<provider-name>"`` (elevated) confirms the GUID for a given driver build.

NSys captures DxgKrnl and DXGI by default (kernel + GPU trace options); ``NVIDIA-DD-External`` and ``VSyncDPC`` must be added explicitly at capture time.

## Pipeline stages

```text
DXGI Present -> Kernel Present -> QueuePacket -> MMIOFlipMPO3 -> MMIOFlipMPO -> Screen Time
```

| # | Stage | ETW event (provider) | Meaning |
|---|---|---|---|
| 1 | DXGI Present | ``Present_Start`` / ``IDXGISwapChain_Present`` (Microsoft-Windows-DXGI) | App called ``Present()``. CPU-side submission. |
| 2 | Kernel Present | ``Present`` (DxgKrnl, event IDs 42/43/**184** -- use 184 to avoid duplicates) | Windows kernel received the present. |
| 3 | QueuePacket | ``QueuePacket`` start/stop (DxgKrnl) | GPU work submission. ``present=1`` / ``bPresent=True`` flags flip packets. Assigns ``SubmitSequence``. Engine types: 1=3D, 2=VideoDecode, 3=VideoEncode, 6=Copy. |
| 4 | Layer registration | ``MMIOFlipMultiPlaneOverlay3`` (DxgKrnl, id 386) | Present registered on ``(VidPnSourceId, LayerIndex)``. Replaces any prior present on the same layer (flip-metering drop). |
| 5 | GPU ready | ``MMIOFlipMultiPlaneOverlay`` (DxgKrnl, id 259) | GPU signalled the frame is ready. Sets ``ready_time_ns``. **Not** the display time. |
| 6 | Screen time | ``FlipRequest`` / ``FlipEntryStatusAfterFlip`` / ``VSyncDPC[MultiPlane]`` | Frame is on the display. See derivation below. |

**Frame-time intervals: always start-to-start.** DXGI Present has both start (opcode=0) and stop (opcode=1); stop marks when the API call returned (i.e. time spent *inside* Present, often blocked on the flip queue). That is API latency, not frame time. For present-to-present frame time, use consecutive opcode=0 timestamps. For display cadence, use consecutive ``MMIOFlipMultiPlaneOverlay[3]`` timestamps.

## Two ID spaces

Matching events across stages requires two separate IDs. Confusing them breaks the chain.

| Space | Source | Used by |
|---|---|---|
| **SubmitSequence** | QueuePacket Field 3 (uint32) | MMIOFlipMPO (``Field 4 >> 32``), VSyncDPCMultiPlane (``Field 7 >> 32``), VSyncDPC (``FlipFenceId >> 32``) |
| **PresentId** | MMIOFlipMPO3 Field 4 (uint64) | ``FlipRequest`` Field 1 |

**Bridge:** MMIOFlipMPO3 carries *both* -- ``Field 24 = SubmitSequence``, ``Field 4 = PresentId``. Pair it with the preceding QueuePacket by SubmitSequence, then with the following ``FlipRequest`` by PresentId.

### WPA CSV / ETL positional fields

ETL payloads become positional ``Field N`` when exported via WPA / Nsight:

| Event | Field | Meaning |
|---|---|---|
| QueuePacket | 2 | PacketType (``DXGKETW_MMIOFLIP_COMMAND_BUFFER``, ...) |
| QueuePacket | 3 | SubmitSequence (strip commas) |
| QueuePacket | 7 | bPresent (``"True"``/``"False"``) |
| MMIOFlipMPO3 | 2 | VidPnSourceId |
| MMIOFlipMPO3 | 4 | PresentId (uint64 array) -- matches ``FlipRequest`` Field 1 |
| MMIOFlipMPO3 | 23 | LayerIndex (uint32 array) |
| MMIOFlipMPO3 | 24 | FlipSubmitSequence -- matches QueuePacket SubmitSequence |
| MMIOFlipMPO | 4 | FlipSubmitSequence (uint64, upper 32 bits = SubmitSequence) |
| MMIOFlipMPO | 23 | FlipEntryStatusAfterFlip (``FlipWaitComplete``, ``FlipWaitVSync``, ...) |
| FlipRequest | 1 | PresentId / token |
| FlipRequest | 3 | delay (observed 0) |
| FlipRequest | 4 | ``ts`` -- proposed flip time, **absolute QPC ticks** |
| VSyncDPCMultiPlane | 7 | FlipSubmitSequence array (upper 32 bits = SubmitSequence) |
| VSyncDPC | 9 | FlipFenceId (upper 32 bits = SubmitSequence) |

## Screen-time derivation

Run this priority chain per frame. Each step lists the provider it requires; if the provider isn't in the trace, fall through.

```text
1. FlipRequest (NVIDIA-DD-External, NVIDIA driver, ETL or NSys-with-custom-provider)
      -> screen_time = FlipRequest.ts (QPC) converted to trace-relative ns
      Most accurate: already accounts for VSync and multi-frame queuing.
      Match: FlipRequest.Field1 == MMIOFlipMPO3.Field4 (PresentId).

2. FlipEntryStatusAfterFlip on MMIOFlipMPO (DxgKrnl, always present)
      -> FlipWaitComplete / immediate statuses:  screen_time = ready_time
      -> FlipWaitVSync / FlipWaitHSync:           defer to step 3

3. VSyncDPC / VSyncDPCMultiPlane (DxgKrnl -- captured when DxgKrnl is in the xperf provider list; NSys requires explicit capture)
      -> screen_time = VSync timestamp where SubmitSequence matches
      Match: (Field 7 >> 32) or (FlipFenceId >> 32) == SubmitSequence.

4. Immediate fallback
      -> screen_time = ready_time  (GPU-ready timestamp)
```

**QPC conversion for FlipRequest (ETL).** DB timestamps are relative to trace start; ``FlipRequest.ts`` is absolute.

1. Estimate ``trace_start_qpc`` from the first ~20 FlipRequest events: ``trace_start_qpc = ts_qpc - event_ts_ns * qpc_freq / 1e9`` (take median).
2. ``screen_time_ns = (ts - trace_start_qpc) * 1e9 / qpc_freq``.
3. Clamp: flip time cannot decrease relative to the previous frame's flip.

``qpc_freq`` comes from ``TRACE_METADATA.qpc_frequency`` (ETL header).

### Graceful degradation when providers are missing

| Missing provider | Lost capability | Still derivable |
|---|---|---|
| **NVIDIA-DD-External** (no ``FlipRequest``) | Exact driver-proposed flip time; precise pacing under flip metering | Screen time via FlipEntryStatus -> VSyncDPC -> ready_time. Frame drops, GPU-ready timing, flip-to-flip intervals. **Warn** on CPU-present cadence when FG is suspected (see Flip metering). |
| **DxgKrnl VSyncDPC / VSyncDPCMultiPlane** | Deferred screen time for ``FlipWaitVSync`` / ``FlipWaitHSync`` frames | Classify those frames as VSync-deferred; use ``ready_time`` as a lower-bound approximation. Works for FlipWaitComplete frames. |
| **MMIOFlipMPO3** (id 386 missing; only ``MMIOFlipMultiPlaneOverlay`` present) | Layer registration, PresentId -> no FlipRequest matching, no layer-replacement drop detection | Screen time via FlipEntryStatus / VSyncDPC. Drops only via ``GPU present completions - flip count``. |
| **DxgKrnl MMIOFlip\*** (neither variant) | All GPU-ready and display-time data | CPU present cadence only. Cannot compute screen time or display-side drops. |
| **Microsoft-Windows-DXGI** | User-mode Present timestamps and PID/TID on the app side | Kernel Present (DxgKrnl id 184) still present -- frame-time intervals still work, but app attribution weakens. |
| **Microsoft-Windows-Win32k** | DWM composed-flip tokens | Cannot distinguish DWM-composed from Independent Flip for non-MPO paths; MPO path unaffected. |

Always record which providers were missing in analysis output so downstream consumers know the confidence level of ``screen_time_ns``.

## NSys vs ETL

| Aspect | NSys (.nsys-rep) | ETL (.etl / WPA CSV) |
|---|---|---|
| Schema | Named columns (``GENERIC_EVENT_TYPES``, ``WDDM_QUEUE_PACKET_*``) | Positional ``Field N`` on ``ETW_EVENTS`` |
| QueuePacket SubmitSequence | ``WDDM_QUEUE_PACKET_START_EVENTS.submitSequence`` | ``ETW_EVENTS.data`` Field 3 (present packets only) |
| FlipEntryStatusAfterFlip | Named field | MMIOFlipMPO Field 23 |
| ``FlipRequest`` (NVIDIA-DD-External) | Captured only if provider added at capture time | Captured only if ``NVIDIA-DD-External`` is in the xperf provider list |
| Thread IDs | All events | User-mode only; zero for DPC events (MMIOFlip, FlipRequest, VSyncDPC) |
| Screen-time chain when all providers captured | FlipEntryStatus -> ready_time (add ``NVIDIA-DD-External`` + ``VSyncDPC`` to extend the chain) | FlipRequest -> FlipEntryStatus -> VSyncDPC -> ready_time (requires capture of ``NVIDIA-DD-External`` and DxgKrnl ``VSyncDPC``) |

## VSync and VRR

VSync fires at the panel's base refresh rate regardless of VRR state (e.g. 16.667 ms at 60 Hz). With VRR (G-Sync / FreeSync / AdaptiveSync), scanout cadence floats; VSync interrupts may still be rock-solid at the base rate.

**There is no single VRR flag in ETW.** Use convergent evidence:

1. Flip-to-flip intervals are consistent but *not* a VSync multiple (e.g. 19-20 ms median on a 60 Hz display).
2. VSync interval stays at base rate with high consistency.
3. Flips do **not** cluster at 1x/2x/3x VSync.

## Flip metering (display-pipeline impact only)

When flip metering is active (always with DLSS Frame Generation), the driver paces flips, not CPU presents. One consequence matters for this pipeline:

- CPU-side DXGI Present calls bunch up -- N near-simultaneous presents per cycle (2 for FG x 2, 3 for FG x 3). **This is expected.** Do not conclude poor pacing from CPU-present cadence.
- Actual display pacing lives in ``FlipRequest.ts``. Without NVIDIA-DD-External, you cannot verify display pacing; report the CPU cadence with an explicit caveat.
- On the ``(VidPnSourceId, LayerIndex)`` layer, newer presents replace older ones via MMIOFlipMPO3. High replacement counts on FG traces are normal for the metering mechanism; sustained replacements on non-FG traces indicate GPU-faster-than-display.

## Dropped-frame detection

A frame is dropped when either:

1. **Layer replacement:** a newer MMIOFlipMPO3 registers on the same ``(VidPnSourceId, LayerIndex)`` before the prior present reached screen time.
2. **No screen time:** after full pipeline processing, ``screen_time_ns`` remains 0.

Coarse count when MMIOFlipMPO3 is unavailable:

```text
dropped = (QueuePacket present completions in window)

        - (MMIOFlipMultiPlaneOverlay count in window)
```

## Analysis workflows

### W1. Measure frame time

- **Present-to-present (CPU):** consecutive DxgKrnl ``Present`` (id 184, opcode=0) timestamps.
- **Display cadence:** consecutive ``MMIOFlipMultiPlaneOverlay[3]`` timestamps.
- Never mix start-to-stop. Never mix Present with MMIOFlip.

For bar-chart rows in analysis reports: ``t`` = Present start, ``v`` = interval to next start; bars tile because ``t[i] + v[i] == t[i+1]``.

### W2. Derive screen time per frame

1. Extract DxgKrnl ``Present`` events -> one display-pipeline event per present.
2. Match DXGI ``Present_Start`` within 10 ms on (PID, TID).
3. Match ``QueuePacket`` by (PID, TID) proximity within +/-100 us (WPA rounding can swap simultaneous events; strict FIFO breaks). Assign ``SubmitSequence``.
4. Walk ``MMIOFlip*`` events in timestamp order:
   - MPO3 -> register on ``(VidPnSourceId, LayerIndex)``, record PresentId.
   - MPO -> set ``ready_time_ns``, run the screen-time chain above.
5. Resolve ``FlipWaitVSync`` / ``FlipWaitHSync`` against ``VSyncDPCMultiPlane``.
6. Discard warm-up (events before first complete present); mark remaining incomplete frames as dropped.

### W3. Detect VRR active

Apply the three VSync/VRR heuristics above. Treat 2/3 as "VRR active"; 1/3 is inconclusive.

### W4. Detect missed flip (display-side stall)

Pattern: display holds a frame ~2x the normal interval while the GPU delivers on time.

Signature:

- Flip-to-flip interval ~ 2x median (e.g. 40 ms vs 20 ms).
- Two GPU present completions inside the long flip window (at +0 ms and +~20 ms).
- GPU frame time stable; no CPU-side correlate.

### W5. Sanity-check CPU present cadence when FG is on

1. If ``FlipRequest`` events are present -> use ``screen_time`` intervals; CPU cadence is diagnostic only.
2. If ``FlipRequest`` is missing and frame time shows FG x N clustering at the CPU present level -> **do not** call poor pacing. Report as "display pacing not verifiable -- NVIDIA-DD-External not captured".
3. Compare MMIOFlip-to-MMIOFlip intervals if available; those reflect real display cadence even without FlipRequest.

## See also

- Reflex SDK markers and the input-to-display latency pipeline: [reflex_overview.md](reflex_overview.md).
- Windows kernel scheduling effects on display-thread pacing (DPC preemption, GPU interrupt affinity): [windows_kernel_scheduling.md](windows_kernel_scheduling.md).
- Glossary terms used here: [present-mode](../glossary/graphics-glossary/present-mode.md), [swap-chain](../glossary/graphics-glossary/swap-chain.md), [vsync](../glossary/graphics-glossary/vsync.md), [fence](../glossary/graphics-glossary/fence.md), [dxgkrnl-events](../glossary/graphics-glossary/dxgkrnl-events.md).
