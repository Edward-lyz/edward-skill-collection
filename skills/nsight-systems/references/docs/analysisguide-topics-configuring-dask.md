---
source_path: AnalysisGuide/topics/configuring-dask.rst
title: ## Configuring Dask
---
## Configuring Dask

The multi-report analysis system does not offer options to configure the Dask environment. However, you could achieve this by modifying the recipe script directly or using one of the following from Dask’s configuration system:

-  YAML files: By default, Dask searches for all YAML files in ``~/.config/dask/`` or ``/etc/dask/``. This search path can be changed using the environment variable ``DASK_ROOT_CONFIG`` or ``DASK_CONFIG``. See the Dask documentation  for the complete list of locations and the lookup order. Example:


      $ cat example.yaml   
      'Distributed':
              'scheduler':
                  'allowed-failures': 5

-  Environment variables: Dask searches for all environment variables that start with ``DASK_``, then transforms keys by converting to lower-case and changing double-underscores to nested structures. See Dask documentation for the complete list of variables. Example:


      DASK_DISTRIBUTED__SCHEDULER__ALLOWED_FAILURES=5

**Dask Client**

With no configuration set, the dask-futures mode option initializes the Dask Client with the default arguments, which results in creating a LocalCluster in the background. The following are the YAML/environment variables that could be set to change the default behavior:

-  distributed.comm.timeouts.connect / DASK_DISTRIBUTED\__COMM\__TIMEOUTS\__CONNECT
-  client-name / DASK_CLIENT_NAME
-  scheduler-address / DASK_SCHEDULER_ADDRESS
-  distributed.client.heartbeat / DASK_DISTRIBUTED\__CLIENT\__HEARTBEAT
-  distributed.client.scheduler-info-interval / DASK_DISTRIBUTED\__CLIENT\__SCHEDULER_INFO_INTERVAL
-  distributed.client.preload / DASK_DISTRIBUTED\__CLIENT\__PRELOAD
-  distributed.client.preload-argv / DASK_DISTRIBUTED\__CLIENT\__PRELOAD_ARGV

**Recipe’s environment variables**

Recipe has its own list of environment variables to make the configuration more complete and flexible. These environment variables are either missing from Dask’s configuration system or specific to the recipe system:

-  NSYS_DASK_SCHEDULER_FILE: Path to a file with scheduler information. It will be used to initialize the Dask Client.
-  NSYS_DIR: Path to the directory of Nsight Systems containing the target and host directories. The nsys executable and the recipe dependencies will be searched in this directory instead of the one deduced from the currently running recipe file path.
