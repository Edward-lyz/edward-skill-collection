---
source_path: InstallationGuide/topics/installing-multi-report-analysis-system.rst
title: ## Installing Advanced Analysis System
---
## Installing Advanced Analysis System

The Nsight Systems advanced analysis system is located in the appropriate
``<install-dir>/target-<os>-<arch>/python/packages/nsys_recipe`` directory for 
your operating system and architecture.

**Recipe Dependencies**

The system is written in Python and depends on a set of Python packages. The
prerequisites are Python 3.10 or newer with pip and venv. 

Starting with Nsight Systems 2026.3.1, the analysis system executes using the version
of Python that is bundled with the Nsight Systems installation (currently Python 3.12.12). 
The first time you run the analysis system, it installs the required Python packages into
a virtual environment within your local directory in the following locations depending 
on your operating system:

* Linux: ``~/.nsightsystems/venv``
* Windows: ``%LOCALAPPDATA%\NVIDIA Nsight Systems\venv``  
* macOS: Recipe analysis will be supported in a future release, once the Nsys CLI is supported on macOS.

The virtual environment is created with the dependencies needed for the current analysis script.
Some recipes may require additional dependencies, which automatically trigger additional 
installation steps. For example, if the analysis script requires the ``dask`` package, the analysis system
automatically installs the ``dask`` package into the virtual environment. The installation can 
sometimes take a few minutes to complete, so be patient. You can monitor the installation progress 
by viewing the ``recipe_dependencies_install_log.txt`` file in the current working directory.


**Advanced usage: Custom Python Environment**

If you want to use a different version of Python than the one that is bundled with 
Nsight Systems, you can create a virtual environment with the desired version of Python
and install the required Python packages into it. Consult the Python documentation for 
more information on how to create a virtual environment.

For this to work, you must set the ``NSYSPYTHONEXE`` environment variable to point to
the Python executable in the custom Python environment:


   export NSYSPYTHONEXE=/path/to/python_executable

You can then install the required Python packages into the custom Python environment using 
the ``install.py`` script provided with Nsight Systems. The ``install.py``
script automates the installation of the analysis system recipe dependencies. You must select
one of the following options when you run the script:
``--current``, ``--venv PATH``, or ``--download``. Additionally, use ``--offline``
with ``--current`` or ``--venv`` to install from previously downloaded packages.


   <install-dir>/target-<os>-<arch>/python/packages/nsys_recipe/install.py

Options:

-  ``-h``: Display help
-  ``--current``: Install packages in the current environment. If a venv is
   active, packages will be installed there. Otherwise, packages will be
   installed in the system site-packages directory, which enables usage of
   ``nsys recipe`` without having to activate a virtual environment. However, new
   packages risk colliding with existing ones if different versions are required.
-  ``--venv PATH``: Install packages in a virtual environment. If the venv doesn't
   already exist, it is created. Using a venv prevents the risk of package version collision
   in the current environment.
-  ``--download``: Download wheel packages for offline installation
-  ``--offline``: Install packages from downloaded wheels (offline mode)
-  ``--no-jupyter``: Do not install requirements for the Jupyter notebook
-  ``--no-dask``: Do not install requirements for Dask
-  ``--quiet``: Only display errors

For example, to install the minimum required Python packages for the analysis system into the currently
active virtual environment, you can run the following command:


   <install-dir>/target-<os>-<arch>/python/packages/nsys_recipe/install.py --current --no-dask --no-jupyter


**Jupyter Notebook**

The Nsight Systems UI has the ability to load and display Jupyter notebooks. When you open a Jupyter notebook, 
the UI first attempts to launch the JupyterLab server using the default Python environment on your ``$PATH``.
If that fails, the UI will attempt to launch JupyterLab using the Nsight Systems Python environment, 
creating the venv if necessary. 

Note: macOS users should install JupyterLab into their default Python environment since the Nsys CLI and 
``install.py`` script are not currently supported on macOS.

You can also use ``NSYSPYTHONEXE`` to run Jupyter from your custom Python environment. This variable should 
be set to the path to the Python executable in your custom environment and it will launch JupyterLab using that
environment, like the following command:


   export NSYSPYTHONEXE=/path/to/python_executable
   $NSYSPYTHONEXE -m jupyter lab

Alternatively, you may launch JupyterLab independently to view the recipe outside of the Nsight Systems UI using:


   jupyter lab <path-to-notebook>
