---
source_path: UserGuide/topics/plugin-subsystem.rst
title: ## |product-name| Plugins
---
## |product-name| Plugins

Nsight Systems plugins are tools that extend its data collection capabilities, available
via CLI with ``--enable`` command option and via GUI.
There are multiple locations where the Nsight Systems searches for available plugins
described in the Plugin discovery section.

The bundled plugins are created, documented and maintained by the Nsight Systems team.

In addition to the plugins created by the Nsight Systems team, we also have a
GitHub repository of plugins created and supported by third parties. See
Third Party Plugins List 
or GitHub repository .

Warning:

   Third party plugins are not tested or validated in any way by the
   Nsight Systems team. NVIDIA is not responsible for the content or behavior
   of those plugins.

#### How to launch a plugin

In CLI plugins are enabled with the ``--enable`` command option that also allows
passing arguments to the plugin. It's possible to launch multiple instances
of the same plugin by using multiple ``--enable`` options.

Depending on the plugin type it may be available in ``nsys profile``, ``nsys start``
or ``nsys launch`` commands. For example, a minimal plugin that only sets some
environment variables will be applicable to the ``nsys launch`` and ``nsys profile``
commands if the latter launches a profiled application because otherwise there is
little sense in modifying the environment. Refer to a plugin documentation to
find out its supported usage pattern.

Nsight Systems plugins can be configuration-only, standalone processes,
shared libraries injected into target processes, or any combination of these features.
When enabled, standalone plugin processes are launched just before the data collection
starts and are terminated right before the collection stops.
This default behavior can be amended, see the Developing an Nsight Systems Plugin section.
Configuration and in-process shared libraries plugins are tied to the lifetime
of a target process and are not unloaded after data collection stops.

Standalone plugin processes are launched with the same privileges as the
running instance of Nsight Systems. If a plugin needs elevated privileges
then Nsight Systems may need to run elevated.

#### How to pass arguments to a plugin

To pass arguments to a plugin, specify them as a part of ``--enable`` option
after plugin name when launching the target application. The arguments should
be separated by commas only (no spaces). On non-Windows platforms, commas can
be escaped with a backslash ``\\``, and the backslash itself can be escaped by
another backslash ``\\\\``. On Windows, use the caret ``^`` as the escape character
(e.g., ``^,`` for a literal comma), and ``^^`` for a literal caret. To include
spaces in an argument, enclose the argument in double quotes ``"``.

See the section on the :ref:`Amazon AWS Elastic Fabric Adapter (EFA)
Network Counters<AWS EFA Plugin>`  for an example.

#### Supported platforms

Nsight Systems plugins are supported on x86_64, arm64 Linux and x86_64 Windows.


#### Plugin discovery

Nsight Systems will search for plugins in the following locations:

    1. User-specified locations via environment variable.
    2. Plugins bundled with this version of the profiler.
    3. Third-party unversioned system-wide plugins.

The bundled and third-party plugins are placed in locations that should require elevated privileges for modification.
This allows Nsight Systems to assume that all files in those locations are trusted and perform no additional 
verification.

Warning:

    **Security notice**: The user is responsible for ensuring security of the locations specified via environment
    variable. Nsight Systems cannot perform security checks and will trust and may execute any plugin that was
    discovered via user-provided location.

**Third-party unversioned system-wide plugins**

The paths for these plugins are platform-dependent.

    | Linux: ``/opt/nvidia/nsight-systems-plugins``
    | Windows: ``C:\\Program Files\\NVIDIA Corporation\\Nsight Systems Plugins``

**User-specified locations via environment variable**

User may specify multiple lookup locations via environment variable: ``NSYS_PLUGIN_SEARCH_DIRS``
The location must be separated by a platform-dependent separator:

    | Linux: ``:``
    | Windows: ``;``

**Listing available plugins**

To list all available plugins use the ``nsys plugins list`` command.
It will collect all search locations and enumerate plugins in alphabetical
order. Plugins that have failed manifest validation will have an **(error)**
prefix. Note that it's not possible to enable any plugins as long as there's
at least one that fails validation.
