---
source_path: InstallationGuide/topics/package-manager-installation.rst
title: ## Package Manager Installation
---
## Package Manager Installation


Installation using RPM or Debian packages interfaces with your system’s package
management system. When using RPM or Debian local repo installers, the
downloaded package contains a repository snapshot stored on the local
filesystem in /var/. Such a package only informs the package manager where to
find the actual installation packages, but will not install them.

If the online network repository is enabled, RPM or Debian packages will be
automatically downloaded at installation time using the package manager:
apt-get, dnf, yum, or zypper.

Users can download Nsight Systems (full package **nsight-systems** or CLI-only
package **nsight-systems-cli**) from publicly available repositories. The below
commands are given as examples and are not intended to be precisely correct.

**Ubuntu (minimal setup for containers)**

These instructions assume that you have root in the container.  Example
command to launch a container: ``sudo docker run -it --rm ubuntu:latest bash``

*Ubuntu 26.04*


   apt update
   apt install -y --no-install-recommends gnupg2 wget ca-certificates
   wget -O- https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub \
     | gpg --dearmor \
     | tee /usr/share/keyrings/nvidia-devtools-keyring.gpg > /dev/null
   echo "deb [signed-by=/usr/share/keyrings/nvidia-devtools-keyring.gpg] \
   https://developer.download.nvidia.com/devtools/repos/ubuntu$(source /etc/lsb-release; echo "$DISTRIB_RELEASE" | tr -d .)/$(dpkg --print-architecture)/ /" \
     | tee /etc/apt/sources.list.d/nvidia-devtools.list
   apt update
   apt install nsight-systems-cli

*Ubuntu 24.04 and earlier*


   apt update
   apt install -y --no-install-recommends gnupg
   echo "deb http://developer.download.nvidia.com/devtools/repos/ubuntu$(source /etc/lsb-release; echo "$DISTRIB_RELEASE" | tr -d .)/$(dpkg --print-architecture) /" | tee /etc/apt/sources.list.d/nvidia-devtools.list
   apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
   apt update
   apt install nsight-systems-cli


**Ubuntu (desktop)**

*Ubuntu 26.04*


  sudo apt install gnupg2 wget ca-certificates
  wget -O- https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub \
    | gpg --dearmor \
    | sudo tee /usr/share/keyrings/nvidia-devtools-keyring.gpg > /dev/null
  echo "deb [signed-by=/usr/share/keyrings/nvidia-devtools-keyring.gpg] \
  https://developer.download.nvidia.com/devtools/repos/ubuntu$(source /etc/lsb-release; echo "$DISTRIB_RELEASE" | tr -d .)/$(dpkg --print-architecture)/ /" \
    | sudo tee /etc/apt/sources.list.d/nvidia-devtools.list
  sudo apt update
  sudo apt install nsight-systems

*Ubuntu 24.04 and earlier*


  sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
  sudo add-apt-repository "deb https://developer.download.nvidia.com/devtools/repos/ubuntu$(source /etc/lsb-release; echo "$DISTRIB_RELEASE" | tr -d .)/$(dpkg --print-architecture)/ /"
  sudo apt install nsight-systems


**CentOS and RHEL (minimal setup for containers)**

Same as above for Ubuntu, these instructions assume that you have root in the
container.  Example command to launch a container:
``sudo docker run -it --rm centos:latest bash``


  rpm --import https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
  sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
  sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
  dnf install -y 'dnf-command(config-manager)'
  dnf config-manager --add-repo "https://developer.download.nvidia.com/devtools/repos/rhel$(source /etc/os-release; echo ${VERSION_ID%%.*})/$(rpm --eval '%{_arch}' | sed s/aarch/arm/)/"
  dnf install -y nsight-systems-cli


**CentOS and RHEL (desktop)**


  sudo rpm --import https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
  sudo dnf install -y 'dnf-command(config-manager)'
  sudo dnf config-manager --add-repo "https://developer.download.nvidia.com/devtools/repos/rhel$(source /etc/os-release; echo ${VERSION_ID%%.*})/$(rpm --eval '%{_arch}' | sed s/aarch/arm/)/"
  sudo dnf install nsight-systems
