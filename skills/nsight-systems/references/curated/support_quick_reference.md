# Nsight Systems Support Quick Reference

> Curated overlay: release-reviewed synthesis. Source inputs: QuadD/Docs/Rst/InstallationGuide; QuadD/Docs/Rst/ReleaseNotes; QuadD/Docs/Rst/UserGuide troubleshooting topics; NVIDIA Developer Nsight Systems get-started page. Official generated docs, live CLI/recipe help, and report-tool evidence remain authoritative when facts differ.



Use this for broad support questions. For exact OS, GPU, driver, package, or feature matrices, cite the generated Installation Guide for this release instead of answering from memory.

## Product name and `nsys`




`nsys` is the Nsight Systems command-line executable name. In shorthand, `nsys` usually means NVIDIA Nsight Systems, but it is safer to call it "the Nsight Systems CLI" than to describe it as a formal acronym.

## Creating a session or report




Nsight Systems is report/session centered, not an IDE project system in the normal source-code-project sense.

Common GUI flow:

1. Launch the GUI (`nsys-ui`).
2. Create or open a profiling session configuration.
3. Select the target, executable, arguments, working directory, and trace settings.
4. Start collection.
5. Open and save the generated `.nsys-rep` report.

Common CLI flow:

```text
nsys profile --trace=cuda,nvtx -o report ./app
```

Then open `report.nsys-rep` in the GUI, run `nsys stats`, or export the report for script-based analysis. Visual Studio integration is the main workflow where the docs describe Nsight Systems projects in the IDE sense.

## GUI availability




Yes. Nsight Systems includes a GUI for opening `.nsys-rep` reports, timeline analysis, summary and diagnostic views, multi-report workflows where supported, and configured local or remote profiling sessions.

The Installation Guide describes launching the GUI from the desktop icon or the `nsys-ui` executable in the Host subdirectory. Do not imply `nsys-ui` is always beside the target-side `nsys` CLI binary; package layouts can separate Host and Target directories.

## CUDA application support




Nsight Systems supports CUDA application profiling when the target platform, GPU, driver, and CUDA runtime are supported by the release. Enable CUDA tracing with `--trace=cuda` or the GUI CUDA trace option. CUDA views can include API calls, kernels, memory copies/sets, CUDA graphs/events where supported, and CPU/GPU timing relationships.

Use NVTX annotations to mark phases. Use Nsight Compute after Nsight Systems identifies a kernel that needs kernel-level hardware-counter, occupancy, roofline, or stall analysis. Nsight Systems shows timing, ordering, and activity relationships; it does not prove CUDA API correctness or numerical correctness.

## Requirements, platforms, and GPU support




Requirements change by release, package, platform, and feature. When the user needs exact support, ask for Nsight Systems version, package source, host OS, target OS, CPU architecture, GPU model, driver, CUDA version, embedded package, container/VM status, and the feature they want to collect.

Stable framing across current releases:

- Nsight Systems is a 64-bit host/target tool.
- Workstation/cloud/cluster workflows are primarily Linux and Windows on x86_64 or Arm SBSA.
- Embedded workflows depend on the matching JetPack/L4T or QNX package.
- macOS is host/viewer/remote-profiling oriented where supported; do not imply macOS is a CUDA target.
- Nsight Systems can view reports and collect CPU/timeline data without a local NVIDIA GPU, but GPU profiling requires a supported NVIDIA GPU, driver, CUDA/runtime stack, OS, and target package.
- Current x86_64 or Arm SBSA GPU profiling support starts with NVIDIA Turing architecture. Release notes state that versions starting with 2025.4 do not support Pascal or Volta; use an older compatible release for those devices when needed.
- GPU metrics, video hardware profiling, CPU sampling, context-switch tracing, backtraces, NIC/storage metrics, containers, VMs, WSL, system-wide collection, and embedded/QNX workflows can add narrower permissions or support limits.

## Report compatibility and file formats




Prefer opening a `.nsys-rep` with the same Nsight Systems version that collected it, or a newer compatible release. Older builds may fail to open newer reports. If collection and viewing came from different package sources, check both CLI and GUI/importer versions.

Common files:

- `.nsys-rep`: primary modern report file.
- `.qdstrm`: intermediate capture stream; use `nsys import` if automatic conversion did not complete.
- `.qdrep`: older report format; use a compatible Nsight Systems version when needed.
- `.qdproj`: GUI project file that references reports by path; not a shareable report by itself.
- Export formats: SQLite, text/JSON/JSONL, HDF5, Arrow, and Parquet where supported by live `nsys export --help`.

For "can't open my report" questions, check version compatibility, whether the file is a finalized `.nsys-rep`, whether the copy is complete, and whether the report is too large for the GUI host memory. Exported schemas are version-sensitive; inspect the concrete SQLite or Parquet schema before writing custom tooling.

## Metrics and trace categories




Sampled metrics depend on platform and selected features. Common categories include GPU metrics, CPU core/socket or PMU metrics, SoC metrics on embedded platforms, NIC/InfiniBand switch metrics, and storage metrics such as NFS, Lustre, and GPUDirect Storage where supported.

Timeline traces are separate from sampled metrics. CUDA API calls, kernels, memory copies, NVTX ranges, OS runtime events, MPI/NCCL calls, and graphics API events are timeline activities, not all sampled-counter metrics.

## Permissions and startup failures




Good first checks:

- Run `nsys --version`, `nsys --help`, and `nsys status -e` (or `nsys status --environment` when live help lists it).
- Verify the package matches the host/target OS and architecture.
- Confirm install, output, and temporary directories are readable, executable, and writable as needed.
- On Linux, check `/proc/sys/kernel/perf_event_paranoid`. CPU sampling, scheduling data, and backtraces can require a value of 2 or lower; broader system-wide collection can require stricter admin policy.
- Nsight Systems requires write permission to `/var/lock` on the target.
- In containers, CPU sampling and OS tracing may require a seccomp profile or capabilities that permit `perf_event_open`.
- GPU metrics/performance counters require the relevant counter permissions, often root on Linux or Administrator/UAC on Windows.
- For GUI startup problems, launch `nsys-ui` from a terminal, collect stdout/stderr, use dependency installer scripts when provided, and set `QT_DEBUG_PLUGINS=1` to diagnose missing Qt/XCB libraries.
- For GPU profiling failures, verify driver and device visibility with `nvidia-smi`, then check the release's driver/CUDA/GPU requirements.

A common temporary Linux fix for process-tree CPU sampling is:

```text
sudo sh -c 'echo 2 >/proc/sys/kernel/perf_event_paranoid'
```

Persistent changes should be made by an administrator under `/etc/sysctl.d/`.

## Download, packages, and cost




The public get-started page is:

```text
https://developer.nvidia.com/nsight-systems/get-started
```

Packages include Windows `.msi`, Linux `.run` / `.rpm` / `.deb`, and macOS `.dmg` host installers where supported. Linux package-manager installs use NVIDIA devtools repositories and packages such as `nsight-systems` or `nsight-systems-cli`.

Nsight Systems is free to download and use at no separate tool cost from NVIDIA Developer resources. For legal details, redistribution, or enterprise compliance, point to the package license/EULA for the release.

## Remote profiling




Nsight Systems supports GUI-driven remote profiling for supported remote Linux or Windows targets. Remote setup uses SSH-style target connections; Windows remote targets require OpenSSH Server setup for the documented Windows remoting path. Check firewall/network policy for SSH port 22 and the Nsight Systems agent/data port documented for the release. Avoid exposing profiler-agent ports broadly on untrusted networks.

Ask for host OS, target OS, package source, network/firewall setup, and whether the user profiles from GUI or CLI before giving exact commands. Do not describe `nsys --daemon` as the main workflow unless live docs/help for the selected release explicitly instruct it.

## Official documentation




Official documentation is available at:

```text
https://docs.nvidia.com/nsight-systems/
```

Key sections include the Installation Guide, User Guide, Analysis Guide, Release Notes, and versioned archives. Installed packages can also include offline documentation. Use live CLI help (`nsys --help`, `nsys profile --help`, and other subcommand help) for command-specific facts.

## Nsight Systems and other tools




Nsight Systems is the modern path for system-wide timeline profiling and replaces the legacy Visual Profiler timeline-style workflow for most current CUDA application profiling. Use it for CPU/GPU timeline analysis, CUDA API/kernel/memcpy ordering, synchronization, NVTX ranges, OS runtime activity, MPI/NCCL, and application-level bottleneck discovery.

Use Nsight Compute after Nsight Systems identifies a kernel that needs deep hardware-counter, occupancy, roofline, or stall analysis. Avoid claiming arbitrary profiler co-execution is supported; simultaneous tools can contend for injection hooks, sampling, or hardware counters.

## Empty reports




Common causes:

- The application exited before useful work occurred.
- `--delay` exceeded the application runtime.
- `--start-later=true` was used but `nsys start` was never issued.
- A capture range such as CUDA Profiler API, hotkey, or NVTX never opened, opened too late, or closed too early.
- Trace options did not include the expected activity.
- Data was not flushed because the application crashed or exited before CUDA work synchronized/finalized.
- Permissions, containers, seccomp, VM restrictions, or unsupported sampling settings prevented collection.

First checks: run without capture ranges, enable the expected trace source, inspect Diagnostics Summary, and load report context to check which tables have data.

## Application crashes while profiling




Known causes include restrictive container `seccomp` policies, Python multiprocessing with `fork`, MPI implementation issues, profiling overhead, and trace features that perturb timing-sensitive workloads. Start with a minimal trace, then add features one at a time. If CUDA data is incomplete, ensure GPU work is synchronized/finalized before exit when possible.

Ask for OS, container/seccomp status, MPI implementation/version, Python multiprocessing usage, CUDA/driver version, exact `nsys profile` command, and stderr/crash logs.

## MPI support




Nsight Systems supports MPI tracing for common MPI implementations such as Open MPI and MPICH. Enable MPI tracing with `--trace=mpi` or the GUI MPI checkbox when available. If implementation auto-detection fails, specify the implementation when supported by live help. Nsight Systems traces a subset of MPI APIs including point-to-point, collectives, one-sided operations, file I/O, and pack operations.

## General limitations




Mention these when asked broadly:

- Profiling adds overhead and can perturb timing-sensitive workloads.
- Reports can be large; long runs or broad traces can consume substantial disk space and memory.
- Virtualized, containerized, remote, and cloud environments can restrict CPU sampling, system calls, GPU counters, or filesystem access.
- Some features are platform-, driver-, GPU-architecture-, and privilege-dependent.
- Data can be incomplete when a trace domain was disabled, permissions blocked collection, buffers overflowed, the process exited before finalization, or a feature is unsupported on the target.
- Native report and export schemas are version-sensitive.

## JupyterLab and Advanced Analysis




There are two related workflows:

- **Profile from inside JupyterLab:** install the separate `jupyterlab-nvidia-nsight` extension in the Python/Jupyter environment that launches the server, restart JupyterLab, and ensure the server environment can find the Nsight Systems installation. The extension does not bundle `nsys`.
- **View recipe notebooks inside the Nsight Systems GUI:** run an Advanced Analysis recipe, keep the output directory intact, choose **File → Open**, select the generated `.nsys-analysis` file, and open the notebook such as `stats.ipynb` from the analysis view. Keep the `.nsys-analysis`, notebook, and Parquet files together.
- **Fallback:** if the extension cannot control the kernel, launch Jupyter under Nsight Systems from a shell, for example `nsys launch --trace=cuda,nvtx,cublas,cudnn jupyter lab`, then use the documented start/stop workflow for the cells or phases to profile.

If integration fails, check that the extension is installed in the same environment as the Jupyter server, restart JupyterLab, verify `nsys --version` works from that environment, and configure the Nsight Systems installation path in the extension settings.
