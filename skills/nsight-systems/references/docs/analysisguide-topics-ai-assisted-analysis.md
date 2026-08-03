---
source_path: AnalysisGuide/topics/ai-assisted-analysis.rst
title: AI-Assisted Analysis
---
# AI-Assisted Analysis

Note:

   AI-Assisted Analysis is a **Preview Feature**.

Nsight Systems ships with an AI skill that helps users use the CLI, 
run post-collection analysis recipes and analyze the collected profiling data.
This skill is packed in a "bring your own" (BYO) pack that can be used with different 
AI agents. The skill pack works in a progressive discoverability mode, where SKILL.md 
is the starting point, which guides the agent to navigate the skill pack's vast knowledge 
base for Nsight Systems-related concepts, and directs the agent to follow a structured 
path for post-collection analysis. The workflow directs the agent to run skill pack's 
scripts to retrieve insights from the collected profiling data and to ground its answers 
in the product documentation.

## Directing an AI Agent to Use the Skill Pack

Point your agent at the skill file,
``<nsys-install-folder>/skills/nsight-systems/SKILL.md``, in one of two ways:

- **Persistent hook** — add a line to your agent's context root file (``CLAUDE.md``,
  ``AGENTS.md``, or equivalent):


     To use nsys refer to '<nsys-install-folder>/skills/nsight-systems/SKILL.md'

- **Single prompt** — reference the skill file in one request:


     Profile the CUDA kernels in ~/work/my_app with nsys as detailed in <nsys-install-folder>/skills/nsight-systems/SKILL.md

Both ``nsys --help`` and the Nsight Systems GUI report window print the resolved
path to let users easily copy the exact path of the SKILL.md file.

## What the Skill Pack Covers

The pack helps with Nsight Systems product, CLI, recipe, and report-analysis
questions. Its knowledge spans across different Nsight Systems profiling activities, 
including CPU and GPU work, CUDA API and kernel behavior, graphics APIs and frame
and stutter analysis, OS runtime, NVTX, MPI, and NCCL activity.


    Agentic AI is inherently non-deterministic: the same prompt can produce
    different results across runs, and outputs may be incomplete or inaccurate.
    Additionally, this skill is tested against a limited set of AI models, and results
    may vary between them and across versions. Treat results as drafts, and
    verify important findings against the Nsight Systems documentation, live CLI
    or recipe help, and the profiling report data before relying on them.
