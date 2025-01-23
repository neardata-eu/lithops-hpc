#
# (C) Copyright BSC 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

SBATCH_ARGUMENTS = [
    ["account", "A"],
    ["acctg_freq"],
    ["array", "a"],
    ["batch"],
    ["bb"],
    ["bbf"],
    ["begin", "b"],
    ["chdir", "D"],
    ["cluster_constraint"],
    ["clusters", "M"],
    ["comment"],
    ["constraint", "C"],
    ["container"],
    ["container_id"],
    ["contiguous"],
    ["core_spec", "S"],
    ["cores_per_socket"],
    ["cpu_freq"],
    ["cpus_per_gpu"],
    ["cpus_per_task", "c"],
    ["deadline"],
    ["delay_boot"],
    ["dependency", "d"],
    ["distribution", "m"],
    ["error", "e"],
    ["exclude", "x"],
    ["exclusive"],
    ["export"],
    ["export_file"],
    ["extra"],
    ["extra_node_info", "B"],
    ["get_user_env"],
    ["gid"],
    ["gpu_bind"],
    ["gpu_freq"],
    ["gpus_per_node"],
    ["gpus_per_socket"],
    ["gpus_per_task"],
    ["gpus", "G"],
    ["gres"],
    ["gres_flags"],
    ["hint"],
    ["hold", "H"],
    ["ignore_pbs"],
    ["input", "i"],
    ["job_name", "J"],
    ["kill_on_invalid_dep"],
    ["licenses", "L"],
    ["mail_type"],
    ["mail_user"],
    ["mcs_label"],
    ["mem"],
    ["mem_bind"],
    ["mem_per_cpu"],
    ["mem_per_gpu"],
    ["mincpus"],
    ["network"],
    ["nice"],
    ["no_kill", "k"],
    ["no_requeue"],
    ["nodefile", "F"],
    ["nodelist", "w"],
    ["nodes", "N"],
    ["ntasks_per_core"],
    ["ntasks_per_gpu"],
    ["ntasks_per_node"],
    ["ntasks_per_socket"],
    ["ntasks", "n"],
    ["open_mode"],
    ["output", "o"],
    ["overcommit", "O"],
    ["oversubscribe", "s"],
    ["partition", "p"],
    ["power"],
    ["prefer"],
    ["priority"],
    ["profile"],
    ["propagate"],
    ["qos", "q"],
    ["quiet", "Q"],
    ["reboot"],
    ["requeue"],
    ["reservation"],
    ["signal"],
    ["sockets_per_node"],
    ["spread_job"],
    ["switches"],
    ["test_only"],
    ["thread_spec"],
    ["threads_per_core"],
    ["time_min"],
    ["time", "t"],
    ["tmp"],
    ["tres_per_task"],
    ["uid"],
    ["use_min_nodes"],
    ["verbose", "v"],
    ["wait_all_nodes"],
    ["wait", "W"],
    ["wckey"],
    ["wrap"],
]


class SlurmPattern:
    """Patterns for sbatch properties in filenames."""

    DO_NOT_PROCESS = "\\"
    PERCENTAGE = "%%"
    JOB_ARRAY_MASTER_ID = "%A"
    JOB_ARRAY_ID = "%a"
    JOB_ID_STEP_ID = "%J"
    JOB_ID = "%j"
    HOSTNAME = "%N"
    NODE_IDENTIFIER = "%n"
    STEP_ID = "%s"
    TASK_IDENTIFIER = "%t"
    USER_NAME = "%u"
    JOB_NAME = "%x"


class SlurmEnv:
    SLURM_ARRAY_TASK_COUNT = "$SLURM_ARRAY_TASK_COUNT"
    SLURM_ARRAY_TASK_ID = "$SLURM_ARRAY_TASK_ID"
    SLURM_ARRAY_TASK_MAX = "$SLURM_ARRAY_TASK_MAX"
    SLURM_ARRAY_TASK_MIN = "$SLURM_ARRAY_TASK_MIN"
    SLURM_ARRAY_TASK_STEP = "$SLURM_ARRAY_TASK_STEP"
    SLURM_ARRAY_JOB_ID = "$SLURM_ARRAY_JOB_ID"
    SLURM_CLUSTER_NAME = "$SLURM_CLUSTER_NAME"
    SLURM_CPUS_ON_NODE = "$SLURM_CPUS_ON_NODE"
    SLURM_CPUS_PER_GPU = "$SLURM_CPUS_PER_GPU"
    SLURM_CPUS_PER_TASK = "$SLURM_CPUS_PER_TASK"
    SLURM_DISTRIBUTION = "$SLURM_DISTRIBUTION"
    SLURM_EXPORT_ENV = "$SLURM_EXPORT_ENV"
    SLURM_GPUS = "$SLURM_GPUS"
    SLURM_GPU_BIND = "$SLURM_GPU_BIND"
    SLURM_GPU_FREQ = "$SLURM_GPU_FREQ"
    SLURM_GPUS_PER_NODE = "$SLURM_GPUS_PER_NODE"
    SLURM_GPUS_PER_SOCKET = "$SLURM_GPUS_PER_SOCKET"
    SLURM_GPUS_PER_TASK = "$SLURM_GPUS_PER_TASK"
    SLURM_GTIDS = "$SLURM_GTIDS"
    SLURM_JOB_ACCOUNT = "$SLURM_JOB_ACCOUNT"
    SLURM_JOBID = "$SLURM_JOBID"
    SLURM_JOB_ID = "$SLURM_JOB_ID"
    SLURM_JOB_CPUS_PER_NODE = "$SLURM_JOB_CPUS_PER_NODE"
    SLURM_JOB_DEPENDENCY = "$SLURM_JOB_DEPENDENCY"
    SLURM_JOB_NAME = "$SLURM_JOB_NAME"
    SLURM_JOBNODELIST = "$SLURM_JOBNODELIST"
    SLURM_JOB_NODELIST = "$SLURM_JOB_NODELIST"
    SLURM_JOBNUM_NODES = "$SLURM_JOBNUM_NODES"
    SLURM_JOB_NUM_NODES = "$SLURM_JOB_NUM_NODES"
    SLURM_JOB_PARTITION = "$SLURM_JOB_PARTITION"
    SLURM_JOB_QOS = "$SLURM_JOB_QOS"
    SLURM_JOB_RESERVATION = "$SLURM_JOB_RESERVATION"
    SLURM_LOCALID = "$SLURM_LOCALID"
    SLURM_MEM_PER_CPU = "$SLURM_MEM_PER_CPU"
    SLURM_MEM_PER_GPU = "$SLURM_MEM_PER_GPU"
    SLURM_MEM_PER_NODE = "$SLURM_MEM_PER_NODE"
    SLURM_NODE_ALIASES = "$SLURM_NODE_ALIASES"
    SLURM_NODEID = "$SLURM_NODEID"
    SLURM_NPROCS = "$SLURM_NPROCS"
    SLURM_NTASKS = "$SLURM_NTASKS"
    SLURM_NTASKS_PER_CORE = "$SLURM_NTASKS_PER_CORE"
    SLURM_NTASKS_PER_NODE = "$SLURM_NTASKS_PER_NODE"
    SLURM_NTASKS_PER_SOCKET = "$SLURM_NTASKS_PER_SOCKET"
    SLURM_HET_SIZE = "$SLURM_HET_SIZE"
    SLURM_PRIO_PROCESS = "$SLURM_PRIO_PROCESS"
    SLURM_PROCID = "$SLURM_PROCID"
    SLURM_PROFILE = "$SLURM_PROFILE"
    SLURM_RESTART_COUNT = "$SLURM_RESTART_COUNT"
    SLURM_SUBMIT_DIR = "$SLURM_SUBMIT_DIR"
    SLURM_SUBMIT_HOST = "$SLURM_SUBMIT_HOST"
    SLURM_TASKS_PER_NODE = "$SLURM_TASKS_PER_NODE"
    SLURM_TASK_PID = "$SLURM_TASK_PID"
    SLURM_TOPOLOGY_ADDR = "$SLURM_TOPOLOGY_ADDR"
    SLURM_TOPOLOGY_ADDR_PATTERN = "$SLURM_TOPOLOGY_ADDR_PATTERN"
    SLURMD_NODENAME = "$SLURMD_NODENAME"
