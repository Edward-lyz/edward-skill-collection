---
source_path: UserGuide/topics/launching-ncu-from-gui.rst
title: ## Launching NVIDIA Nsight Compute from a CUDA Kernel
---
## Launching NVIDIA Nsight Compute from a CUDA Kernel

After you have used CUDA trace in Nsight Systems to locate a potential problem 
kernel, you may want to run NVIDIA Nsight Compute on that specific kernel. Right
click on the kernel to bring up a menu.

   :alt: Option to run NVIDIA Nsight Compute
   :class: image

If this is the first time that the user has selected this feature, then we show
the following dialog box to get their preferences:

   :alt: Settings for NVIDIA Nsight Compute
   :class: image

The first option invokes the NVIDIA Nsight Compute UI with known parameters. It
is the preferred option for local or remote profiling. The user must provide the
location of the ncu-ui executable. Nsight Systems will verify that the path and
executable are valid.

The second option is provided for the convenience of users who do not have
NVIDIA Nsight Compute installed on the host system, but simply want the command
line they can use to run the Nsight Compute on the remote target by themselves
without much automation.

   :alt: Dialog to give the command line to use with Nsight Compute
   :class: image

If the user selects the option to start the NCU UI, Nsight Systems invokes it
with any relevant parameters from the Nsight Systems run.

The screenshot below shows NCU UI invoked by Nsight Systems. The red circles
indicate the parameters pre-populated by Nsight Systems. Users may modify any
of these parameters before launching the application and profiling the selected
kernel.

   :alt: Nsight Compute launch gui
   :class: image
