start_script = """
#!/bin/bash

module load gcc/12.3.0

#Regular exports
export OMPI_MCA_osc=sm
export OMPI_MCA_pml=ob1
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export FI_UNIVERSE_SIZE=500
#echo FI_UNIVERSE_SIZE $FI_UNIVERSE_SIZE

# GekkoFS mount point (can be any directory)
export GKFS_BASE=/gpfs/${HOME}/gekkofs_base
export GKFS_MNT=/gpfs/${HOME}/mnt
export GEKKODEPS=${GKFS_BASE}/iodeps
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${GEKKODEPS}/lib64:${GEKKODEPS}/lib
export PATH=$PATH:${GEKKODEPS}/iodeps/bin
export GKFS_DAEMON=$GEKKODEPS/bin/gkfs_daemon
export GKFS=$GEKKODEPS/lib64/libgkfs_intercept.so
export GKFS_PROXY=$GEKKODEPS/bin/gkfs_proxy
export GKFS_LIBC=$GEKKODEPS/lib64/libgkfs_libc_intercept.so

# Shared file for available servers
export GKFS_HOSTS_FILE=${HOME}/test/gkfs_hosts.txt
export GKFS_LOG_LEVEL=0
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

# Function to execute a command in the background and wait for it to finish
execute_command() {
    echo "Executing command: '$*'"
    "$@" &
    local pid=$!
    wait "$pid"
    status=$?
    if [ $status -eq 0 ]; then
        echo "Command '$*' completed successfully."
        return 0
    else
        echo "Command '$*' failed with exit code $status."
        return 1
    fi
}
#echo "Removing $LIBGKFS_HOSTS_FILE"
#rm $LIBGKFS_HOSTS_FILE
echo "Executing GKFS_DAEMON"
CMD1="${GKFS_DAEMON} --mountdir=${GKFS_MNT:?} --rootdir=${GKFS_ROOT:?} $COMM -l ib0 " # --proxy-protocol ofi+verbs --proxy-listen lo"
#if [ $SLURM_LOCALID -lt 0 ]; then
#   echo "Executing  GKFS_DAEMON on $SLURM_LOCALID/$SLURM_NODEID nodes "
#   execute_command $CMD1
#fi
execute_command $CMD1 #-s node_$SLURM_LOCALID  #Creates an additional directory within the rootdir, allowing multiple daemons on one node
#while [[ ! -f "${LIBGKFS_HOSTS_FILE}" ]]; do sleep 1; done
#while [[ $(wc -l < "$LIBGKFS_HOSTS_FILE") -lt ${SLURM_NNODES} ]]; do sleep 1; done

#sleep 10

#echo "Executing  Lithops workers"
#LD_PRELOAD=${GKFS} python $1 $2 $3 $4 $5
#while true; do sleep 1; done
"""
