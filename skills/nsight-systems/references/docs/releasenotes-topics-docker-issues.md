---
source_path: ReleaseNotes/topics/docker-issues.rst
title: ## Docker Issues
---
## Docker Issues

-  In a Docker, when a system's host utilizes a kernel older than v4.3, it is not possible for Nsight Systems to collect sampling data unless both the host and Docker are running a RHEL or CentOS operating system utilizing kernel version 3.10.1-693 or newer. A user override for this will be made available in a future version.

-  When ``docker exec`` is called on a running container and stdout is kept open from a command invoked inside that shell, the exec shell hangs until the command exits. You can avoid this issue by running with ``docker exec --tty``. See the bug reports at:

-  https://github.com/moby/moby/issues/33039

-  https://github.com/drud/ddev/issues/732
