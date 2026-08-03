---
source_path: UserGuide/topics/slurm-steps.rst
title: ## Profiling Slurm Jobs Running in Containers (Enroot/Pyxis or OCI)
---
## Profiling Slurm Jobs Running in Containers (Enroot/Pyxis or OCI)

When jobs are launched through Slurm and executed inside a container runtime —
either Pyxis/Enroot (common on NVIDIA and HPC clusters) or a generic OCI
runtime (Docker, containerd, Podman, CRI-O) - Nsight Systems can still be used
to profile the workload, but the CLI (``nsys``) itself must be made available
*inside* the container that Slurm launches, not just on the host.

The recommended pattern is **"inject, don't rebuild"**: keep ``nsys`` installed
once on the bare-metal compute node and bind-mount it into the container at
launch time, then wrap the in-container command with ``nsys profile`` exactly
as you would in a non-containerized MPI/Slurm job. This avoids baking Nsight
Systems into every container image and makes it easy to upgrade the profiler
independently of the workload.

There are three steps, regardless of the container runtime:

1. Install Nsight Systems (examples below use ``2026.2.1``) on the bare-metal
   Slurm compute nodes.
2. Bind-mount that install into the container at the same absolute path via
   the container runtime's configuration.
3. Invoke ``nsys profile`` by absolute path (or, if you prefer, extend the
   container's ``PATH`` without replacing it). A wrapper script is only needed
   when you want per-rank logic.

See also the "Handling Application Launchers (mpirun, deepspeed, etc)" and
"Enable Docker Collection" sections — the same rules about rank-based wrapper
scripts, ``%q{...}`` output templates, and ``perf_event_open`` apply here.

#### Install |product-name| on the Target Compute Nodes

Install the same Nsight Systems build on every compute node that the Slurm
job may be scheduled on, and use an identical path on all nodes, e.g.:


   /opt/nvidia/nsight-systems/2026.2.1

A shared filesystem (NFS, Lustre, GPFS) works as well, as long as the path is
readable on every node and on the container's mount namespace after the bind
mount is applied.

Verify on one node:


   $ /opt/nvidia/nsight-systems/2026.2.1/bin/nsys --version

and confirm the printed version matches what you expect to bind-mount into
the container.

Note:

   **Keep CLI and UI versions aligned.** The Nsight Systems GUI /
   ``nsys-ui`` used to open a report should be the **same or newer** than the
   CLI that produced it. Reports from a newer CLI opened in an older GUI are
   the common failure mode. The ``.qdrep`` → ``.nsys-rep`` format change was
   in 2021.4, so any 2021.4-or-newer GUI can at least load the file; whether
   all timeline features render correctly still depends on the GUI being
   ≥ CLI version. Pin one version across all compute nodes so the bind mount
   resolves consistently.

### Host kernel requirements

Profiling from inside a container still depends on the host kernel, so make
sure the host satisfies the normal Nsight Systems requirements:

- ``perf_event_paranoid`` is permissive enough on the host (typically
  ``<= 2``). You can verify readiness from inside the container with
  ``nsys status --environment``.
- The container has access to ``perf_event_open`` — see "Enable Docker
  Collection" above. For OCI runtimes this means ``--cap-add=SYS_ADMIN``,
  ``--privileged``, or a custom seccomp profile that allows
  ``perf_event_open``. Enroot launches containers unprivileged and, by
  default, does not install Docker's restrictive seccomp profile on top of
  the host policy, so ``perf_event_open`` is typically usable without extra
  flags — but verify with ``nsys status --environment`` inside the
  container before assuming it.
- CUDA/NVIDIA driver libraries are already made available in the container by
  the runtime (NVIDIA Container Toolkit for OCI, ``--container-mounts`` + the
  NVIDIA hook for Pyxis/Enroot). The Nsight Systems bind mount does not
  change that.

#### Make ``nsys`` Visible Inside the Container

### Option A — Pyxis/Enroot via ``srun --container-mounts``

Pyxis (the Slurm SPANK plugin for Enroot) exposes Enroot container launches as
``srun`` flags. The ``--container-mounts`` flag accepts
``SRC:DST[:FLAGS][,SRC:DST...]`` (multiple flags are joined with ``+``, e.g.
``ro+rprivate``). Bind-mount the host install into the container and invoke
``nsys`` by absolute path so nothing in the image environment is modified:


   srun \
     --container-image=nvcr.io#nvidia/pytorch:<tag> \
     --container-mounts=/opt/nvidia/nsight-systems/2026.2.1:/opt/nvidia/nsight-systems/2026.2.1:ro \
     /opt/nvidia/nsight-systems/2026.2.1/bin/nsys profile \
       -t cuda,nvtx,mpi \
       -o /reports/run_%q{SLURM_PROCID}_%p \
       python train.py

Key points:

- ``--container-mounts=<host>:<container>:ro`` bind-mounts the host install
  read-only. ``ro`` is enough — the profiler does not write inside its own
  install tree.
- Calling ``nsys`` via its absolute in-container path avoids touching the
  image's ``PATH`` at all. If you prefer ``nsys`` on ``PATH`` (for example
  for interactive use), append it *inside* the container rather than
  replacing the image ``PATH``:


     srun \
       --container-image=nvcr.io#nvidia/pytorch:<tag> \
       --container-mounts=/opt/nvidia/nsight-systems/2026.2.1:/opt/nvidia/nsight-systems/2026.2.1:ro \
       --export=ALL,NSYS_PATH=/opt/nvidia/nsight-systems/2026.2.1/bin \
       --container-env=NSYS_PATH \
       bash -lc 'PATH="$PATH:$NSYS_PATH"; nsys profile -o /reports/run_%q{SLURM_PROCID}_%p python train.py'
- If you need ``nsys`` reports to land on a shared filesystem, also bind-mount
  the output directory (e.g.
  ``--container-mounts=...,/scratch/$USER/reports:/reports:rw``) and pass
  ``-o /reports/...`` to ``nsys profile``.

Before adding ``nsys`` to the command line, do a quick container-runtime
preflight:


   srun --container-image=nvcr.io#nvidia/pytorch:<tag> /bin/true

If this fails, fix the base Pyxis/Enroot launch path first, then add
``--container-mounts`` and profiling.

### Option B — Enroot ``mounts.d`` + ``environ.d`` (recommended, image-independent)

When you do not control the ``srun`` invocation (for example a fleet-wide
Slurm setup), Enroot can inject the mount and extend ``PATH`` via its
standard configuration directories under ``ENROOT_SYSCONF_PATH`` (default
``/etc/enroot``). This is the idiomatic Enroot approach and does not require
a custom hook script.

``/etc/enroot/mounts.d/nsys.fstab``:


   # Bind-mount the host Nsight Systems install into every Enroot container.
   /opt/nvidia/nsight-systems/2026.2.1 /opt/nvidia/nsight-systems/2026.2.1 none bind,ro,nosuid,nodev 0 0

``/etc/enroot/environ.d/nsys.env``:


   # Make `nsys` visible on PATH inside every Enroot container.
   PATH=/opt/nvidia/nsight-systems/2026.2.1/bin:${PATH}

Both files are applied automatically to every container launched via Enroot
(and therefore via Pyxis). No image changes are needed.

### Option C — Enroot pre-start hook (only if you need logic)

Use a hook script only when you need conditional behavior (for example, pick
a different Nsight Systems install based on the image or the host's GPU
family). Hooks live in ``/etc/enroot/hooks.d/`` with a ``.sh`` extension and
run with full capabilities before the container switches to its final root.
They receive ``ENROOT_ROOTFS``, ``ENROOT_MOUNTS``, and ``ENROOT_ENVIRON``.

``/etc/enroot/hooks.d/50-nsys.sh``:


   #!/usr/bin/env bash
   # Append a bind mount for Nsight Systems to the container's mount file,
   # and add it to PATH via the environ file. Prefer mounts.d / environ.d
   # unless you actually need logic here.

   set -euo pipefail

   : "${ENROOT_MOUNTS:?not set}"
   : "${ENROOT_ENVIRON:?not set}"

   NSYS_HOST_PREFIX="/opt/nvidia/nsight-systems/2026.2.1"
   NSYS_IN_CONTAINER="/opt/nvidia/nsight-systems/2026.2.1"

   echo "${NSYS_HOST_PREFIX} ${NSYS_IN_CONTAINER} none bind,ro,nosuid,nodev 0 0" \
       >> "${ENROOT_MOUNTS}"
   echo "PATH=${NSYS_IN_CONTAINER}/bin:\${PATH}" >> "${ENROOT_ENVIRON}"

### Option D — OCI runtime (Docker / Podman / containerd / CRI-O)

For containers launched through an OCI runtime under Slurm (for example via
``srun --container-...`` wired to a Docker or container orchestrator, or via
a site-specific launcher), declare the bind mount in the container
configuration and invoke ``nsys`` by its absolute in-container path so the
image's own ``PATH`` and other environment variables are preserved.

Docker / Podman flags on the launch command:


   docker run --rm --gpus all \
     --cap-add=SYS_ADMIN \
     -v /opt/nvidia/nsight-systems/2026.2.1:/opt/nvidia/nsight-systems/2026.2.1:ro \
     my-workload:latest \
     /opt/nvidia/nsight-systems/2026.2.1/bin/nsys profile \
       -t cuda,nvtx,mpi \
       -o /reports/run_%p \
       python train.py

Or in the OCI runtime ``config.json`` (for a container spec consumed by
``runc``/``crun``):


   {
     "process": {
       "args": [
         "/opt/nvidia/nsight-systems/2026.2.1/bin/nsys",
         "profile",
         "-t", "cuda,nvtx,mpi",
         "-o", "/reports/run_%p",
         "python", "train.py"
       ]
     },
     "mounts": [
       {
         "destination": "/opt/nvidia/nsight-systems/2026.2.1",
         "type": "bind",
         "source": "/opt/nvidia/nsight-systems/2026.2.1",
         "options": ["rbind", "ro"]
       }
     ]
   }

Notes for OCI runtimes:

- Add ``--cap-add=SYS_ADMIN`` (or the custom seccomp profile described in
  "Enable Docker Collection") so ``perf_event_open`` is not blocked.
- Calling ``nsys`` by absolute path means the image's own ``PATH`` (and any
  other ``ENV`` set by the image) is preserved. If you'd rather have ``nsys``
  on ``PATH``, append inside the container (``PATH="$PATH:/opt/nvidia/nsight-systems/2026.2.1/bin"``)
  instead of replacing ``PATH`` via ``-e`` / ``process.env``.
- GPU exposure is still the runtime's responsibility (``--gpus all`` / NVIDIA
  Container Toolkit hook / ``nvidia.com/gpu`` device plugin). The Nsight
  Systems mount does not change that.
- If ``-o`` writes to a host directory, add a second bind mount for it
  (``-v /scratch/$USER/reports:/reports:rw`` or a corresponding ``mounts``
  entry) — the profiler cannot write through a read-only mount.

#### Wrap the In-Container Command with ``nsys profile``

Once the Nsight Systems install is bind-mounted, the invocation is identical
to the non-container Slurm + MPI pattern. In multi-node jobs, the launcher
runs outside the profiler and ``nsys profile`` wraps the per-rank program:


   srun [srun args] \
     --container-image=... --container-mounts=... \
     /opt/nvidia/nsight-systems/2026.2.1/bin/nsys profile -t cuda,nvtx,mpi \
       -o /reports/run_%q{SLURM_PROCID}_%p \
       ./myapp [app args]

Use ``%q{SLURM_PROCID}`` (Slurm) / ``%q{OMPI_COMM_WORLD_RANK}`` (Open MPI) /
``%q{PMI_RANK}`` (MPICH) or ``%p`` in ``-o`` so concurrent ranks do not
clobber each other's report file. ``%h`` (hostname) and ``%%`` (literal
``%``) are also supported.

Warning:

   An error will occur if several processes want to write to the same report
   file at the same time.

### Profiling only a subset of ranks

To reduce trace volume, profile just a representative rank. Put a wrapper
script inside the container (or bind-mounted in) and call it instead of the
binary. Example ``nsys_profile.sh`` for Slurm:


   #!/bin/bash
   # Profile only the node-local rank 0. Use $SLURM_PROCID for global rank 0.
   NSYS_PATH="${NSYS_PATH:-/opt/nvidia/nsight-systems/2026.2.1/bin}"
   PATH="${PATH}:${NSYS_PATH}"
   if [ "${SLURM_LOCALID}" -eq 0 ]; then
     nsys profile -t cuda,nvtx,mpi \
       -e NSYS_MPI_STORE_TEAMS_PER_RANK=1 \
       -o /reports/run_%q{SLURM_PROCID}_%p \
       "$@"
   else
     "$@"
   fi

Launch:


   srun --container-image=... \
        --container-mounts=/opt/nvidia/nsight-systems/2026.2.1:/opt/nvidia/nsight-systems/2026.2.1:ro,/scratch/$USER/reports:/reports:rw \
        --export=ALL,NSYS_PATH=/opt/nvidia/nsight-systems/2026.2.1/bin \
        --container-env=NSYS_PATH \
        ./nsys_profile.sh python train.py

Note:

   If only a subset of MPI ranks is profiled, set
   ``NSYS_MPI_STORE_TEAMS_PER_RANK=1`` so all members of custom MPI
   communicators are stored per rank. Otherwise the run may hang or fail
   with an MPI error. If communicator tracking itself is the problem, it can
   be disabled with ``NSYS_MPI_DISABLE_COMMUNICATOR_TRACKING=1``.

### GPU and NIC metrics with multiple ranks per node

As in the non-container case, if more than one rank per node would enable
GPU/NIC metric collection, restrict it to one rank to avoid contention:


   #!/bin/bash
   if [ "${SLURM_LOCALID}" -eq 0 ]; then
     nsys profile --nic-metrics=lf --gpu-metrics-devices=all "$@"
   else
     nsys profile "$@"
   fi

Or one rank per GPU, with metrics scoped to that GPU:


   #!/bin/bash
   nsys profile -e CUDA_VISIBLE_DEVICES=${SLURM_LOCALID} \
                --gpu-metrics-devices=${SLURM_LOCALID} "$@"

#### Troubleshooting checklist

   :header-rows: 1
   :widths: 30 30 40

   * - Symptom
     - Likely cause
     - Fix
   * - ``nsys: command not found`` inside container
     - Bind mount missing, or ``nsys`` not on ``PATH``
     - Verify ``ls /opt/nvidia/nsight-systems/<ver>/bin/nsys`` inside the
       container. Prefer calling ``nsys`` by absolute path; if you need it
       on ``PATH``, append inside the container (``PATH="$PATH:.../bin"``).
   * - ``nsys --version`` reports an unexpected release
     - Wrong host install picked up, or a floating symlink
     - Mount an explicit versioned prefix
       (``/opt/nvidia/nsight-systems/2026.2.1``), not
       ``/opt/nvidia/nsight-systems/current``.
   * - ``nsys status --environment`` reports sampling disabled, or
       ``Failed to create perf event``
     - ``perf_event_open`` blocked by container or host
     - OCI: add ``--cap-add=SYS_ADMIN`` or the seccomp profile from
       "Enable Docker Collection". Enroot: ensure host
       ``perf_event_paranoid <= 2`` and no site seccomp is shadowing it.
   * - Reports not visible after the job ends
     - Output path is container-only
     - Point ``-o`` at a writable bind mount (e.g. ``/reports`` backed by
       ``/scratch/$USER/reports``).
   * - Several ranks overwrite the same ``.nsys-rep``
     - ``-o`` not rank-templated
     - Use ``%q{SLURM_PROCID}`` / ``%q{OMPI_COMM_WORLD_RANK}`` /
       ``%q{PMI_RANK}`` / ``%p`` in ``-o``.
   * - Profiler version mismatch across nodes
     - Different host installs per node
     - Pin the same version at the same path on every node, or use a
       shared filesystem.
   * - ``pyxis: failed to import docker image`` with
       ``mkdir: cannot create directory '/run/enroot': Permission denied``
     - Enroot runtime dir not provisioned or not writable for the job user
     - Ensure ``/run/enroot`` exists and is world-traversable with a
       per-user ``/run/enroot/user-<uid>``, or set ``ENROOT_RUNTIME_PATH``
       to a writable path. Quick dev setup:
       ``sudo install -d -m 1777 /run/enroot && sudo install -d -m 700 -o "$USER" -g "$USER" /run/enroot/user-$(id -u)``.
   * - ``enroot``/``pyxis`` import fails with ``Could not process JSON input``
     - Registry endpoint resolved to a web page (e.g. ``docker.io``
       redirects to ``www.docker.com``)
     - Use an explicit registry: ``docker://registry-1.docker.io/library/ubuntu:22.04``
       or Pyxis form ``registry-1.docker.io#library/ubuntu:22.04``.
   * - GUI refuses to open a report produced by the container
     - GUI older than the CLI that recorded the report
     - Upgrade the Nsight Systems GUI to match or exceed the CLI version.
