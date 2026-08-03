---
source_path: UserGuide/topics/soc-metrics-cli.rst
title: ## Launching SoC Metrics from the CLI
---
## Launching SoC Metrics from the CLI

SoC Metrics feature is controlled with 3 CLI switches:

-  ``--soc-metrics=[true|false]`` enables SoC Metrics sampling (default is false)
-  ``--soc-metrics-set=[<alias>|file:<file name>]`` selects metric set to use (default is the 1st suitable from the list)
-  ``--soc-metrics-frequency=[100..200000]`` selects sampling frequency in Hz (default is 10000).
   Abbreviated suffixes ``k`` and ``M`` are accepted (e.g. ``10k``, ``200k``).

To profile with default options:
::

   # Must be root or added to 'debug' group
   $ nsys profile --soc-metrics=true ./my-app
