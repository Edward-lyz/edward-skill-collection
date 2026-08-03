# Nsight Systems Troubleshooting Symptom Guide

> Curated overlay: release-reviewed synthesis. Source inputs: QuadD/Docs/Rst/UserGuide troubleshooting topics; QuadD/Docs/Rst/InstallationGuide requirements and setup topics; QuadD/Docs/Rst/ReleaseNotes known issues. Official generated docs, live CLI/recipe help, and report-tool evidence remain authoritative when facts differ.



This curated guide summarizes common Nsight Systems support symptoms and the evidence to collect. Prefer official generated docs when they provide a direct answer; use this file to connect broad user wording to the right docs/tool checks.

## Empty or nearly empty report




Likely causes to check:

- The application exited before the profiler collected or flushed useful data.
- Capture range collection was enabled but the capture range never opened, opened too late, or closed before relevant work occurred.
- Collection was delayed or stopped early by command-line options or GUI controls.
- The selected traces did not include the activity the user expected, for example CUDA trace disabled when asking about kernels.
- Target permissions, container restrictions, or unsupported CPU sampling settings prevented data collection.
- The report was generated from a run that failed before finalization.

How to verify:

- Load report context and inspect table counts for CUDA, NVTX, OS runtime, MPI/NCCL, and diagnostic tables.
- Check diagnostics/events if present.
- Ask for the exact `nsys profile ...` command, capture-range options, target OS/container status, and whether the application completed normally.

## Application crashes or changes behavior under profiling




Known/documented causes include:

- Applications using `seccomp` can terminate or become unstable because profiling requires system calls that the policy blocks. Disable seccomp if possible or use only less-invasive sampling features.
- Some MPI versions/configurations have known issues. Open MPI 4.0.1 can crash at process end when profiled; a documented workaround is to use another Open MPI version or add `--mca btl ^vader`.
- MPICH 3.0.x `MPI_Status` layout differences can cause memory corruption in some cases.
- Python multiprocessing with the `fork` start method can interact poorly with injected profiling; prefer `spawn` where possible.
- CUDA tracing can expose application/library issues or increase overhead enough to affect timing-sensitive programs. Narrow capture ranges and reduce trace features when diagnosing.
- On vGPU, the CUDA profiler grant is required; without it, sessions can abort, crash, or produce corrupted reports.

How to verify:

- Ask for OS, container/seccomp status, MPI implementation/version, Python multiprocessing usage, CUDA Toolkit/driver, and the exact `nsys profile` command.
- Try a minimal collection first, then add trace features one at a time.

## GUI does not start or cannot connect




Checks:

- Launch the GUI with the `nsys-ui` executable in the Host subdirectory of the installation.
- Confirm host OS/package matches the downloaded installer.
- On Linux GUI startup failures, collect the terminal output. Missing desktop/Qt/XCB libraries are a common class of issue; the exact missing library name matters.
- If the GUI state appears corrupted, reset the user settings file only after preserving logs if support needs them.
- For remote target issues, verify SSH/target setup and whether the host can install target-side binaries.

## Installation or package problems




Checks:

- Use the package matching the host OS and architecture. Nsight Systems packages include Windows `.msi`, Linux `.run`/`.rpm`/`.deb`, and macOS `.dmg` packages where supported by the release.
- Install into a directory where the user has write and execute permissions.
- For package-manager installs, distinguish the local repository package from the actual `nsight-systems` or `nsight-systems-cli` package.
- The CLI is located in the Target directory. The GUI is launched from the Host directory.
- Advanced Analysis recipes use the `nsys_recipe` Python package under `<install-dir>/target-<os>-<arch>/python/packages/nsys_recipe`; dependencies may install on first use or through `install.py`.

## System requirements and permissions




Checks:

- Use the generated Installation Guide requirement pages for current per-platform requirements.
- Some CPU sampling/counter features require system settings or permissions. Use `nsys status --environment` when available from the installed CLI to inspect relevant system status.
- Container, VM, WSL, QNX, DRIVE OS, vGPU, and remote-target workflows can have extra setup requirements; answer from the matching generated docs section rather than general memory.
