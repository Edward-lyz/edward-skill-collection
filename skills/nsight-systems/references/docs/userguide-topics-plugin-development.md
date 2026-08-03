---
source_path: UserGuide/topics/plugin-development.rst
title: ## Developing an |product-name| Plugin
---
## Developing an |product-name| Plugin

#### Plugin manifest file

Plugin manifest is a file in the YAML format. It describes a plugin, its features and requirements.
Nsight Systems validates all discovered manifests when at least one plugin has been enabled and will
refuse to run the given command if any manifest fails the validation.

**Supported top-level manifest keys**

  :name: table_plugin_manifest_keys_table
  :class: table-compact

  +-----------------------------+----------+------------+----------------------------------------------------------+
  | Name                        | Required | Value type | Description                                              |
  +=============================+==========+============+==========================================================+
  | PluginName                  | Yes      | String     | A globally unique name for selecting the plugin via      |
  |                             |          |            | ``--enable`` command.                                    |
  +-----------------------------+----------+------------+----------------------------------------------------------+
  | Description                 | Yes      | String     | A short description printed when listing plugins.        |
  +-----------------------------+----------+------------+----------------------------------------------------------+
  | ExtendedDescription         | No       | String     | Full description of a plugin.                            |
  +-----------------------------+----------+------------+----------------------------------------------------------+
  | ExtendedDescriptionForGui   | No       | String     | Full description of a plugin shown in the GUI.           |
  +-----------------------------+----------+------------+----------------------------------------------------------+
  | TargetEnvironment           | No       | Dictionary | Amend and possibly override the environment when         |
  |                             |          |            | launching a profiled application. Empty and duplicate    |
  |                             |          |            | keys are not allowed.                                    |
  +-----------------------------+----------+------------+----------------------------------------------------------+
  | ExecutablePath              | No       | String     | A path to a standalone plugin executable file. Both      |
  |                             |          |            | absolute and relative paths are supported. The manifest  |
  |                             |          |            | path is used as a base for relative executable paths. The|
  |                             |          |            | given path must exist for a manifest to pass validation. |
  +-----------------------------+----------+------------+----------------------------------------------------------+
  | LibraryPath                 | No       | String     | A path to a shared library that will be injected into    |
  |                             |          |            | profiled processes. Both absolute and relative paths are |
  |                             |          |            | supported. The manifest path is used a as base for       |
  |                             |          |            | relative executable paths. The given path must exist for |
  |                             |          |            | a manifest to pass validation.                           |
  +-----------------------------+----------+------------+----------------------------------------------------------+
  | RequiresInitialization      | No       | Boolean    | If enabled, a standalone plugin must call the Collector  |
  |                             |          |            | API method ``nsysdkCollectorCompleteInitialization``     |
  |                             |          |            | before first observable transition from ``IDLE`` to      |
  |                             |          |            | ``COLLECTING`` state is allowed. This gives the plugin   |
  |                             |          |            | an opportunity to perform lengthy initialization before  |
  |                             |          |            | the profiler starts capturing report data.               |
  |                             |          |            | If a plugin process terminates before calling            |
  |                             |          |            | ``nsysdkCollectorCompleteInitialization`` then the wait  |
  |                             |          |            | is cancelled.                                            |
  |                             |          |            | The profiler will generate a diagnostic message and      |
  |                             |          |            | start collecting report data normally if the plugin does |
  |                             |          |            | not make the call after 30 seconds.                      |
  |                             |          |            | Default value is ``False``.                              |
  +-----------------------------+----------+------------+----------------------------------------------------------+
  | TerminateAfterCollection    | No       | Boolean    | If ``True`` (default), the standalone plugin is          |
  |                             |          |            | terminated after each report collection completes. If    |
  |                             |          |            | ``False``, the plugin is allowed to run between report   |
  |                             |          |            | collections for the duration of profiling session.       |
  |                             |          |            | Combined with the initialization feature allows the      |
  |                             |          |            | plugin to init once, then start and stop quickly when    |
  |                             |          |            | collector state changes.                                 |
  +-----------------------------+----------+------------+----------------------------------------------------------+

At least one of the ``ExecutablePath``, ``LibraryPath``, or ``TargetEnvironment`` entries is required but all can be
used simultaneously in any combination.

**Example manifest file**


    PluginName: unique_name
    ExecutablePath: bin/plugin
    LibraryPath: libPlugin.so
    TargetEnvironment: {KEY: VALUE}
    Description: This is an example plugin manifest.


#### Plugin types

A plugin manifest may specify one or more actionable entries: ``ExecutablePath``, ``LibraryPath``,
``TargetEnvironment``. They are named as "standalone", "in-process", and "configuration" plugin types. When selected
with ``--enable`` option Nsight Systems will perform all applicable actionable entries.
The "in-process" and "configuration" plugin types are only executed when starting a profiled application.
The "standalone" plugin type is executed every time the report collection is started.

#### NsysDK Collector

The NsysDK Collector is an API for plugins to communicate with the profiler. It's a header-only library
that allows fetching current profiler state and extend data collection scope through the finalization stage.
Documentation is embedded into source files and additionally covered in this section.
The library sources are deployed with Nsight Systems installation, for example
``/opt/nvidia/nsight-systems/2026.2.1/target-linux-x64/nsysdk``.

#### Deploying plugins

During plugin development it's more convenient for Nsight Systems to pick it up directly
from a build output location rather than copy the binary each time to the pre-defined search
path. The easiest way to do this is to export the ``NSYS_PLUGIN_SEARCH_DIRS`` environment variable
with the location of a folder that contains the plugin manifest.

#### Minimal standalone plugin

Simple standalone plugins are expected to initialize and shutdown near instantly.
Nsight Systems uses SIGTERM for indicating that a plugin needs to stop producing data and exit,
so it expects plugins to gracefully handle the signal and exit cleanly.
The data collected from plugins is in the form of NVTX events ,
stdout and stderr streams.
The source code for the ``network_interface`` plugin is deployed as an example in
``<profiler installation dir>/target-linux-x64/samples/NetworkPlugin.cpp``.

#### Deferred events standalone plugin

In some cases plugins may need to perform post-processing of the collected data
or are obtaining their data from another source that only becomes available after a
delay. In such cases if plugins were to immediately shutdown following a signal from
the profiler some data would be lost. To avoid this, a plugin may acquire finalization
tokens through the NsysDK Collector API. Once successfully obtained, these tokens
will prevent profiler from stopping data collection until all tokens have been released
allowing plugins to finish emitting their events. A plugin process may release finalization
tokens explicitly or simply exit to have the tokens it held automatically released.

Note, that this feature is not designed for facilitating a lengthy de-initialization as
the profiling data collection is still running in this state. If a plugin needs significant
time to shutdown then it should release finalization tokens explicitly and handle SIGTERM signal.

The sample code below is a skeleton implementation of a plugin that utilizes finalization tokens.
Compile the example with ``g++ -I ./nvtx/include -I ./nsysdk/include -ldl plugin.cpp``.
On POSIX platforms the NVTX library requires adding the ``-ldl`` linker option. Refer to the
NVTX documentation  to learn how to use the deferred events feature.


    #include <nvtx3/nvToolsExt.h>
    #include <nsysdk/collector.h>

    #include <chrono>
    #include <thread>

    int main(int argc, char* argv[])
    {
        // <Plugin initialization>

        // Only needed if the plugin manifest sets the "RequiresInitialization" flag.
        // if (nsysdkCollectorCompleteInitialization() != NSYSDK_SUCCESS)
        //     return 1;

        if (!nsysdkCollectorAcquireFinalizationToken())
            return 1; // Not launched as a plugin.

        if (nsysdkCollectorWaitForState(NSYSDK_COLLECTOR_STATE_COLLECTING, 0) != NSYSDK_SUCCESS)
            return 1; // Profiling didn't start.

        while (nsysdkCollectorGetState() == NSYSDK_COLLECTOR_STATE_COLLECTING)
        {
            // Profiling data collection is active at this point.
            // A real plugin would be collecting and emitting data here.
            nvtxRangePushA("Workload imitation");
            std::this_thread::sleep_for(std::chrono::seconds(1));
            nvtxRangePop();
        }

        if (nsysdkCollectorGetState() != NSYSDK_COLLECTOR_STATE_FINALIZING)
            return 1; // Profiling might have been cancelled.

        // The data collection scope has been extended, emit NVTX deferred events here.
        nvtxRangePushA("Deferred events imitation");
        std::this_thread::sleep_for(std::chrono::seconds(1));
        nvtxRangePop();

        return 0;
    }


#### In-process shared library plugin

Nsight Systems supports plugins in the form of shared libraries loaded into the profiled application process.
Such plugins are analogous to the standalone plugin type with the exception of their lifetime management:
in-process plugins are loaded once and never unloaded after. If there are resources that the plugin must
release, then it should use the NsysDK Collector API to track the profiler state.

Since there's no portable analog of the ``main`` function in shared libraries, in-process plugins should export
a function that serves as a replacement: receives user-provided arguments and starts any processing threads if needed.
The signature of the initialization function is:


    int PluginLibraryInit(int argc, const char* argv[])


The initialization function is called before the profiled application begins executing its ``main`` function.
If multiple in-process plugins are enabled, they are initialized sequentially in an unspecified order.
Because there's no timeout for the initialization function execution, it should finish in a reasonable amount of time
to avoid blocking the rest of profiling data collection. If an in-process plugin actively collects data rather than
does some one-off modification it'll typically launch and detach a thread in the initialization function.
A plugin may return a non-zero exit code from the initialization function to indicate an error and generate a diagnostic
message.

Another difference from standalone plugins is that there's no automatic collection of NVTX events from the profiled
application. If an in-process plugin generates events that should be collected, their event types need to be manually
selected.

#### In-process plugin process-exit handler

An in-process plugin sometimes needs to do a final piece of work when the profiled process is about to exit, for example
to flush data that only becomes available at the very end of the run and emit it as NVTX events. A plain libc ``atexit``
handler registered by the plugin is **not** suitable for this: because the plugin is a dynamically loaded library, its
``atexit`` handler runs during the dynamic loader's library finalization, which happens *after* Nsight Systems has already
torn down its data collection. NVTX events emitted from such a handler are therefore lost.

To support this, the NsysDK Collector API provides a function that an in-process plugin can call to register a
process-exit handler:


    #include <nsysdk/collector.h>

    typedef void(NSYSDK_API* nsysdkCollectorExitHandler_t)(void* userData);

    int nsysdkCollectorRegisterExitHandler(nsysdkCollectorExitHandler_t handler, void* userData);

The plugin calls this from its ``PluginLibraryInit`` function. Nsight Systems invokes the registered handler late during
process shutdown, while data collection is still active and just before it is torn down, so NVTX events emitted from the
handler are captured. The ``userData`` pointer is passed back to the handler when it is invoked. As with all in-process
plugin NVTX, the relevant event types must be selected for collection (for example via ``--trace=nvtx``).


    static void NSYSDK_API MyExitHandler(void* userData) { /* emit final NVTX events */ }

    int PluginLibraryInit(int argc, const char* argv[])
    {
        // ... regular initialization ...
        nsysdkCollectorRegisterExitHandler(&MyExitHandler, /* userData */ NULL);
        return 0;
    }

**Usage rules**

- ``nsysdkCollectorRegisterExitHandler`` may only be called from within an in-process plugin's ``PluginLibraryInit``
  function. The profiler attributes the call to the plugin currently being initialized and the call is ignored with a
  diagnostic message if the function is called at any other time, such as from a thread the plugin spawned, after
  initialization has returned, or from a standalone plugin.
- The method only appends a handler. There's no way to reset a previously registered handler.

When more than one in-process plugin registers a handler, the handlers run concurrently, each on its own thread that is
created during plugin initialization (before the workload runs). Nsight Systems waits for all handlers to finish before
proceeding with teardown, bounded by a timeout. A handler should therefore complete promptly: it delays process
termination and the final flush of collected data. Once timeout is reached the process teardown proceeds regardless and
any data emitted past this point may be lost.

**Limitations**

- The handler only runs on a normal process exit. It does not run when the process terminates abnormally (for example via
  ``_exit``, ``abort``, an uncaught signal, or being killed), since Nsight Systems has no opportunity to invoke it.
- The handler does not run in child processes created by ``fork`` without ``exec``; only the process in which the plugin
  was initialized invokes it.


#### Multiple plugin start requests

Nsight Systems supports plugins across several sub-commands, including ``nsys profile``, ``nsys launch``, and ``nsys start``.
During a single profiling session, you might enable the same plugin more than once, with identical or differing argument
lists.
One common case is the same plugin enabled in multiple ``nsys start`` commands.
Another is a manifest that lists both standalone and in-process entries while you enable the plugin from ``start`` and
``launch``.

Nsight Systems launches standalone plugins when report data collection begins.
For a given standalone plugin, every configuration that shares the same arguments is merged into a single process launch.
If you pass different argument sets for that plugin, each distinct set starts its own instance.

Once in-process plugins have been initialized, the set of plugins and their arguments is frozen so that every instance
of the target application sub-processes receives a consistent plugins initialization sequence.
Until a target application has been launched, newer sets of plugin arguments override the older ones, so that if the
target process is started after a series of system-wide collections it uses the most recent set of plugin configurations.
