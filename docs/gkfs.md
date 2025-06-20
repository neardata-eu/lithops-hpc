# Lithops-HPC and GekkoFS 

## Installation of GekkoFS in MN5
#### 1. Obtain the gkfs code: clone the sources and set the ENV variables
```bash
module unload impi
module unload openmpi/4.1.5-gcc12.3
module unload openmpi
module load impi/2021.13
module load oneapi/2024.2
module load cmake
module load gcc/12.3.0

export BASE=${HOME}/gekkofs_base
export GEKKODEPS=${BASE}/iodeps
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${GEKKODEPS}/lib64:${GEKKODEPS}/lib
export PATH=$PATH:${GEKKODEPS}/iodeps/bin

mkdir $BASE
cd $BASE

git clone https://storage.bsc.es/gitlab/hpc/gekkofs.git
cd gekkofs
git checkout master
git submodule update --init --recursive
```

#### 2. Download and install deps
```bash
cd $BASE/gekkofs/scripts
./gkfs_dep.sh ${GEKKODEPS} ${GEKKODEPS}
```
#### 3. Ensure the chunk size configured in GKFS
Modify the constexpr auto chunksize = 524288; // in bytes (e.g., 524288 == 512KB)
```bash 
vim $BASE/gekkofs/include/config.hpp
```
#### 4. Compile gekkofs
```bash
cd $BASE/gekkofs
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=${GEKKODEPS} -DGKFS_BUILD_TESTS=OFF -DCMAKE_INSTALL_PREFIX=${GEKKODEPS} ..
make -j install
```
#### 5. Add environment variables to bashrc file
```bash
export GKFS_BASE="${HOME}/gekkofs_base"
```

## Enable GKFS in LITHOPS_CONFIG_FILE
Set the mode parameter to gkfs in the hpc section LITHOPS_CONFIG_FILE. It should looks like  
```yaml
hpc:
  worker_processes: <size of the RabbitMQ message>
  runtime: <name>
  runtimes:
    <name>:
      account: <hpc_account>
      qos: <hpc_qos>
      mode: gkfs
```
## Deploy runtime
```bash
lithops hpc runtime_deploy <runtime_name>
```

## Usage
#### 1. Set the ENV variables
```bash
#Regular exports
export OMPI_MCA_osc=sm
export OMPI_MCA_pml=ob1
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
 #When using TCP or Verbs providers and exceeding 256 peers, the FI_UNIVERSE_SIZE environment variable must be explicitly set to accommodate the larger peer count.
export FI_UNIVERSE_SIZE=1024

# GekkoFS mount point (can be any directory)
export GKFS_BASE="${HOME}/gekkofs_base"
export GKFS_MNT=${HOME}/mnt
export GEKKODEPS=${GKFS_BASE}/iodeps
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${GEKKODEPS}/lib64:${GEKKODEPS}/lib
export PATH=$PATH:${GEKKODEPS}/iodeps/bin
export GKFS_DAEMON=$GEKKODEPS/bin/gkfs_daemon
export GKFS=$GEKKODEPS/lib64/libgkfs_intercept.so
export GKFS_PROXY=$GEKKODEPS/bin/gkfs_proxy
export GKFS_LIBC=$GEKKODEPS/lib64/libgkfs_libc_intercept.so

# Shared file for available servers
export GKFS_HOSTS_FILE=${HOME}/test/gkfs_hosts.txt
#export GKFS_LOG_LEVEL=0
export LIBGKFS_HOSTS_FILE=${HOME}/test/gkfs_hosts.txt
export LIBGKFS_LOG_OUTPUT=${HOME}/test/clients_lithops.txt
#export LIBGKFS_LOG=info
export LIBGKFS_LOG_SYSCALL_FILTER=epoll_wait,epoll_create,epoll_ctl
export GKFS_DAEMON_LOG_PATH=${HOME}/test/servers_lithops.txt

# GekkoFS daemon and library paths
export GKFS_DAEMON="${GEKKODEPS}/bin/gkfs_daemon"
export GKFS="${GEKKODEPS}/lib64/libgkfs_intercept.so"
export GKFS_LIBC="${GEKKODEPS}/lib64/libgkfs_libc_intercept.so"

# # Persistent storage for GekkoFS data and Temporary directory for computation
export TMP_PATH=$TMPDIR
export GKFS_ROOT="${TMP_PATH}/agkfs_root"
#export COMM="-P ofi+sockets"
export COMM="-P ofi+verbs"
```
#### 2. Run the application
```bash
cd lithops-hpc
conda activate base-lithops
cd $LITHOPS_HPC_HOME/examples/sleep 
mkdir -p plots
LD_PRELOAD=${GKFS} python sleep.py
```
