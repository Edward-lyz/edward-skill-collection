# Streamline and DLSS Frame Generation Detection




Reference for detecting NVIDIA Streamline (DLSS Super Resolution / Ray Reconstruction / Frame Generation, Reflex, and related features) in Nsight Systems traces: the `sl.*` modules and threads, and the verification procedure that separates "Streamline loaded" from "feature actually active".

Use this when asked whether DLSS, Frame Generation (FG), or Streamline is active in a trace, when a frame-time classifier reports inflated stutter counts that may be FG present cadence, or when a finding is about to attribute a stutter to flip metering. For the stutter classification this feeds, see [stutter_analysis.md](stutter_analysis.md); for the Windows present path and flip-metering timing, see [display_pipeline_windows.md](display_pipeline_windows.md); for Reflex markers, see [reflex_overview.md](reflex_overview.md).

Streamline is NVIDIA's feature-delivery runtime. It loads a set of `sl.*` modules that host features such as DLSS SR / RR / FG, Reflex, and Deep Learning Dynamic Super Resolution. **Presence of Streamline modules does not imply any feature is active** -- the runtime loads for feature detection and configuration regardless of in-game settings.

## DLSS SR vs FG -- independent features

DLSS Super Resolution (SR) and DLSS Frame Generation (FG) are **separate, independent features**. A game can use SR only, FG only, both, or neither.

| Feature                        | What it does                                                        | Label examples                                |
| ------------------------------ | ------------------------------------------------------------------- | --------------------------------------------- |
| **DLSS SR** (Super Resolution) | Upscales from a lower internal resolution to the display resolution | "DLSS Quality", "DLSS Performance", "DLSS SR" |
| **DLSS FG** (Frame Generation) | Generates interpolated frames between real frames                   | "DLSS FG 2x", "DLSS FG 3x"                    |

**"No upscaling" means no DLSS SR -- it does NOT mean no DLSS FG.** A task labelled "no upscaling" or "native resolution" can still have FG active. Check the configuration for explicit FG indicators ("DLSS SR + FG 2x" vs "DLSS FG 2x" vs "native"). Do not assume the absence of one implies the absence of the other.

## Modules and threads in traces

| Symbol              | Role                                                                  |
| ------------------- | --------------------------------------------------------------------- |
| `sl.interposer.dll` | Loader / DLL shim routing into Streamline                             |
| `sl.common.dll`     | Shared Streamline runtime                                             |
| `sl.dlss_g.dll`     | Frame Generation module (hooks Present on the game thread)            |
| `sl.reflex.dll`     | Reflex module (see [reflex_overview.md](reflex_overview.md))          |

Any `sl.*` thread or DLL tells you Streamline is **loaded**. That is all it tells you. The game may have Streamline initialised for feature detection while every feature is off. Module names use `.dll` on Windows and `.so` on Linux, but the thread names match (see [graphics_terminology.md](graphics_terminology.md)).

### How FG looks at the Present level

The game calls Present; `sl.dlss_g.dll` intercepts it, so the game's original Present does not produce its own ETW event. Instead, FG generates N presents of its own (2 in 2x mode, 3 in 3x mode, etc.). All ETW present events you see are FG-generated. This means you cannot compare "game presents" to "total presents" in ETW alone -- without Reflex markers to identify game render boundaries, the game's present cadence is not directly visible in ETW data.

## Streamline loaded is not the same as feature active

`sl.pacer`, `sl.dlssg`, or any `sl.*` module in a trace does NOT confirm FG is active. Streamline loads runtime modules for feature detection and configuration regardless of the in-game settings.

To confirm FG is actually active:

**With Reflex markers (reliable):** compare Reflex-tagged game frames to total DxgKrnl / DXGIPresent ETW events (see [How FG looks at the Present level](#how-fg-looks-at-the-present-level) for why only FG-generated presents are visible in ETW). If total ETW presents far exceed Reflex-tagged game frames, FG is active, and the ratio gives the multiplier directly.

**Without Reflex markers (heuristic, less certain):**

**If `sl.pacer` exists but has zero scheduling events and zero Present calls, FG is disabled.** Streamline is loaded, FG is off. Do not claim FG is active based on thread or DLL presence alone. Without Reflex events and without clear burst patterns it is difficult to determine whether FG is enabled -- state the uncertainty rather than guessing.

## Detection procedure

1. **Check for Reflex markers.** If present, compare Reflex-tagged game frames to total ETW presents. A ratio well above 1 confirms FG; the ratio gives the multiplier directly.
2. **Check for `sl.pacer` in `ThreadNames`.** Non-zero Present ETW events on its `globalTid` means FG is **likely** active, but not conclusive. Zero scheduling events and zero presents means FG is disabled.
3. **No Reflex markers, no `sl.pacer`:** examine the temporal pattern of ETW presents. Bursts (pairs or triples clustered with gaps) suggest FG via flip metering. Evenly-spaced presents suggest FG is not active. If neither signal is clear, state the uncertainty explicitly.

When the present cadence does show a stable 1-long + k-short burst pattern, the long-short oscillation is FG present pacing, not k independent stutters. Collapse each burst to one logical frame before counting stutters (the interpolation factor is k+1), and apply the catch-up exclusion described in [stutter_analysis.md](stutter_analysis.md).

## Related

- Stutter classification and FG inflation of CPU-classifier stutter counts: [stutter_analysis.md](stutter_analysis.md).
- Windows present path and ETW flip events: [display_pipeline_windows.md](display_pipeline_windows.md).

- Reflex markers, including the out-of-band (OOB) and Late Warp markers FG introduces: [reflex_overview.md](reflex_overview.md).
- Streamline thread naming and cross-platform module suffixes: [graphics_terminology.md](graphics_terminology.md).
