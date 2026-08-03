---
source_path: UserGuide/topics/profile-within-jupyterlab.rst
title: Profiling within JupyterLab
---
# Profiling within JupyterLab

The JupyterLab Nsight extension integrates Nsight Systems profiling into
JupyterLab for profiling of Jupyter notebook cells. CUDA kernels launched by the
cells as well as CUDA and Python code execution can be profiled and analyzed.

For more information and to install the extension, go to `JupyterLab Nsight
extension on PyPI <https://pypi.org/project/jupyterlab-nvidia-nsight/>`_

**Basic usage of JupyterLab Nsight extension**

- Install the extension by running ``pip install jupyterlab-nvidia-nsight``.
    - Nsight Systems is not bundled with this extension. It should be installed separately.
- Launch (or restart) JupyterLab.
- Set Nsight Systems installation location in the extension settings (NVIDIA Nsight --> Settings...).
    - Leave this setting empty if Nsight Systems CLI executable is already in the system path.
- Open a notebook and enable Nsight Systems (NVIDIA Nsight --> Profiling with Nsight Systems...).
    - Set the desired options for `nsys launch` command (e.g., ``--trace=cuda,nvtx,cublas,cudnn``).
    - This restarts the JupyterLab kernel.
    - A new green arrow icon appears in the notebook toolbar,
      and can be used to profile cells execution.
- (Optional) Open the generated report file in Nsight Systems GUI inside JupyterLab
  by double clicking on the report file.

**Fallback Example** - How to use Nsight Systems to profile code in individual cells of
a Jupyter notebook when the extension is not available.

- Launch jupyter-lab with Nsight Systems using the desired trace options. For
  example: 

    nsys launch --trace=cuda,nvtx,cublas,cudnn jupyter lab


- (optional) Add NVTX ranges to the important operations in the notebook using
  range_push and range_pop. These NVTX ranges add information but are not used
  to define the profiling capture.
- To profile a cell, add a shell command to ``nsys start`` at the top of the
  cell and a shell command to ``nsys stop`` at the bottom of the cell. We
  recommend using the the absolute path to ``nsys`` on your system to make sure
  it is found.
- Save the notebook.
- Run all the cells required for the code you want to profile, then run the cell
  you want to profile.
- Each time the cell with ``nsys start`` and ``nsys stop`` is run, a new
  .nsys-rep file will be generated.
- Open the nsys-rep file in nsys-ui.
