# Reflex Overview




NVIDIA Reflex reduces input-to-display latency by coordinating CPU pacing with GPU work tracking. The game emits markers that define the latency pipeline; the driver uses them to pace frame submission so the GPU finishes the prior frame just before the CPU hands it the next one.

> **Note**
>
> **Platform scope.** Reflex is primarily delivered on Windows via the ``nvwgf2um`` driver path. Streamline (``sl.reflex``) is cross-platform; Linux titles (Proton, native Vulkan) can integrate Reflex through Streamline. The marker concepts below apply on both platforms; provider names below are mostly Windows-flavoured. See "Cross-platform notes" at the end.

This document covers only the concepts needed to read a trace. For rule-level validation (integration correctness, Sleep positioning, frame-ID consistency, mid-frame GPU idle, etc.), use the appropriate Reflex-analysis tooling rather than relying on a generic trace.

## Markers

Each marker carries a **frame ID** that follows a frame through the pipeline. Duration markers have matched start/end events; instants fire once.

| Event | Marker | Kind | Purpose |
|---|---|---|---|
| 0/1 | Simulation | duration | Game sim (physics, AI, input) |
| 2/3 | Render Submit | duration | GPU command recording + submission |
| 4/5 | Present | duration | Present API call (DXGI / vkQueuePresentKHR) |
| 7 | Trigger Flash | instant | Latency-measurement flash |
| 8 | PC Latency Ping | instant | Latency probe |
| 9/10 | OOB Render Submit | duration | Frame Generation render |
| 11/12 | OOB Present | duration | Frame Generation present |
| 13 | Input Sample | instant | Input sampling |
| 14 | Delta T Calc | instant | Frame-time delta |
| 15/16 | Late Warp Present | duration | Late Warp FG present |
| 17 | Camera Constructed | instant | Camera setup done |
| 18/19 | Late Warp Render Submit | duration | Late Warp FG render |

**Sleep** has no frame ID -- it is positioned by timeline and must fire *before* input sampling and Simulation to yield latency reduction.

#### Per-frame flow

```text
Sleep -> Input / Ping -> Simulation -> Render Submit -> Present
```

OOB and Late Warp markers interleave with the main flow when Frame Generation is active; they carry their own frame IDs, so matching by ID still works.

#### Marker providers

Three possible sources -- more than one may be present in the same trace.

| Provider | Origin | Notes |
|---|---|---|
| **LatencyMarker** | ``nvwgf2um`` driver ETW (Windows) | Most detailed. Includes Sleep and driver-side timing. Names like ``Sim Start/End``, ``Render Start/End``, ``Present Start/End``, ``Sleep Start/End``, ``Input Sample``. |
| **PCLStats** | Legacy ETW provider (Windows) | Event types 0-19 per the table above. Older integrations. |
| **NVTX** | NVTX Reflex domain | Cross-platform. Only present from NSys if reflex-sdk-events were captured. |

## Modules and threads

- ``sl.reflex.dll`` **/** ``sl.reflex.so`` -- Streamline Reflex module. Commonly the leaf function on the Present thread when Reflex is active.
- ``nvwgf2um`` -- Windows driver; emits LatencyMarker ETW events and ``NVWGF2UM - StutterStats Frame Event``. Presence of StutterStats events is definitive evidence of Reflex.
- **Threading** -- Simulation and Render/Present should be on separate threads. Single-threaded integrations can let frame N's Sleep block frame N-1's Render/Present.

## GPU overlap (the core metric)

Reflex's job is to keep the system slightly GPU-bound so the GPU is never idle waiting for CPU work.

- **Positive overlap** -- new GPU work is submitted before the GPU finishes the prior frame. GPU-bound. Reflex is effective.
- **Negative overlap** -- GPU is idle waiting for CPU submission. CPU-bound. Reflex cannot reduce latency further.
- **Target** -- ~1.5 ms overlap, evaluated over a rolling 3-frame window. Above target -> Reflex lengthens Sleep; below -> shortens it.

## Detecting Reflex in a trace

In order of confidence:

1. **LatencyMarker ETW / StutterStats events** in ``GENERIC_EVENT_TYPES`` (Windows) -- definitive.
2. ``sl.reflex.dll`` **/** ``sl.reflex.so`` in CPU-sample callstacks -- strong.
3. **PCLStats** events -- legacy Windows integrations only.
4. **NVTX Reflex markers** in ``NVTX_EVENTS`` -- present on either platform if reflex-sdk-events were captured in NSys.

When detected, spot-check:

- All three core duration markers present (Simulation, Render Submit, Present).
- Sleep present. Missing Sleep = no latency reduction.
- Frame IDs consistent across markers within a frame.
- OOB / Late Warp markers -> Frame Generation is active.

## Cross-platform notes

- The Reflex SDK is the same set of markers regardless of platform. Where the trace records them differs:
  - **Windows**: LatencyMarker / PCLStats / StutterStats ETW events, plus NVTX (if captured), plus ``sl.reflex.dll`` on callstacks.
  - **Linux / Vulkan**: NVTX markers (if captured) and ``sl.reflex.so`` on callstacks. ETW-based providers do not apply.
- "GPU overlap" as the central metric is platform-agnostic -- the calculation is the same on both, only the data sources differ.
- Frame Generation (``OOB Render Submit``, ``OOB Present``, ``Late Warp *``) is available on both Windows and Linux for supported titles; expect to see those markers wherever DLSS Frame Generation is active.

## See also

- Display side of the pipeline (Windows): [display_pipeline_windows.md](display_pipeline_windows.md).
- Glossary terms: [reflex-render-latency](../glossary/graphics-glossary/reflex-render-latency.md), [fps-frame-time](../glossary/graphics-glossary/fps-frame-time.md), [nvtx-range](../glossary/nsys-glossary/nvtx-range.md).
