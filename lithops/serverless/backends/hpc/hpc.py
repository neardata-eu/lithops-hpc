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
import hashlib
import json
import logging
import os
import time

import pika
import pika.exceptions
import pika.spec

from lithops import utils
from lithops.constants import COMPUTE_CLI_MSG, RUNTIMES_PREFIX
from lithops.storage.utils import StorageNoSuchKeyError
from lithops.version import __version__

from .slurm import Slurm
from .slurm import SlurmPattern as SP
from .gekkofs import start_script

logger = logging.getLogger(__name__)

RETURN_QUEUE_POSTFIX = "_return"


class HpcBackend:
    """
    SLURM-based backend.
    """

    def __init__(self, hpc_config, internal_storage):
        """
        Initialize HPC Backend
        """
        logger.debug("Creating HPC client")

        self.name = "hpc"
        self.type = utils.BackendType.BATCH.value
        self.hpc_config = hpc_config
        self.internal_storage = internal_storage

        # TODO: connect to a rabbit if set in the config, otherwise deploy one
        # on HPC if configured to do so and update config

        # Init RabbitMQ
        self.amqp_url = self.hpc_config["amqp_url"]
        self.__params = pika.URLParameters(self.amqp_url)
        self.__connection = None
        self.__channel = None

        msg = COMPUTE_CLI_MSG.format("HPC")
        logger.info(f"{msg}")

    def __del__(self):
        if hasattr(self, "connection"):
            self.__connection.close()

    def __get_rmq_channel(self):
        if self.__connection:
            try:
                self.__connection.process_data_events()
            except pika.exceptions.AMQPConnectionError:
                logger.debug("RabbitMQ connection closed")
                self.__connection = None
                self.__channel = None
        if not self.__connection or self.__connection.is_closed:
            logger.debug("Connecting to RabbitMQ")
            self.__connection = pika.BlockingConnection(self.__params)
            self.__channel = self.__connection.channel()
        return self.__channel

    def __declare_rmq_queues(self, *queues):
        for queue in queues:
            self.__get_rmq_channel().queue_declare(queue=queue, durable=True)

    def __delete_rmq_queues(self, *queues):
        for queue in queues:
            self.__get_rmq_channel().queue_delete(queue=queue)

    def __publish_to_rabbit(self, queue, message):
        self.__get_rmq_channel().basic_publish(
            exchange="",
            routing_key=queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
        )

    def _format_runtime_name(self, runtime_name, version=__version__):
        name = f"{runtime_name}-{version}"
        name_hash = hashlib.sha1(name.encode()).hexdigest()[:10]

        py_version = utils.CURRENT_PY_VERSION.replace(".", "")
        return f"hpc-runtime-{version.replace('.', '')}-{py_version}-{name_hash}"

    def _get_default_runtime_name(self):
        """Generates the default runtime name"""
        # default runtime is the first item in the config
        return list(self.hpc_config["runtimes"].keys())[0]
        # py_version = utils.CURRENT_PY_VERSION.replace(".", "")
        # return f"default-hpc-runtime-v{py_version}"

    def _get_rabbit_task_queue(self, runtime_name):
        # return f"{runtime_name}_task_queue"
        return runtime_name

    def _get_rabbit_management_queue(self, runtime_name):
        return f"{runtime_name}_manage"

    def build_runtime(self, runtime_name, runtime_file, extra_args=[]):
        logger.debug("Building HPC runtime %s", runtime_name)
        logger.error("HPC runtimes cannot be built")

    def _save_runtime_job_id(self, key, job_id):
        path = [RUNTIMES_PREFIX, key + ".jid"]
        obj_key = "/".join(path).replace("\\", "/")
        logger.debug(
            "Uploading runtime job id to: {}://{}/{}".format(
                self.internal_storage.backend, self.internal_storage.bucket, obj_key
            )
        )
        self.internal_storage.storage.put_object(self.internal_storage.bucket, obj_key, job_id)

    def _get_runtime_job_id(self, key):
        path = [RUNTIMES_PREFIX, key + ".jid"]
        obj_key = "/".join(path).replace("\\", "/")
        try:
            return self.internal_storage.storage.get_object(self.internal_storage.bucket, obj_key).decode()
        except StorageNoSuchKeyError:
            logger.debug("Runtime job id not found in storage")
            return None

    def _delete_runtime_job_id(self, key):
        path = [RUNTIMES_PREFIX, key + ".jid"]
        obj_key = "/".join(path).replace("\\", "/")
        self.internal_storage.storage.delete_object(self.internal_storage.bucket, obj_key)

    def _deploy_runtime(self, runtime_name, runtime_config):
        """Deploy the HPC runtime"""
        logger.info(f"Running slurm job for HPC runtime: {runtime_name}")

        rabbit_url = self.hpc_config["amqp_url"]
        runtime_task_queue = runtime_config.get("rmq_queue", self._get_rabbit_task_queue(runtime_name))
        runtime_mng_queue = self._get_rabbit_management_queue(runtime_name)
        self.__declare_rmq_queues(runtime_mng_queue, runtime_task_queue)

        slurm_cmd = Slurm(
            job_name=f"lithops_hpc_workers-{runtime_name}",
            output=f"slurm_lithops_workers/{runtime_name}_{SP.JOB_ID}.out.log",
            error=f"slurm_lithops_workers/{runtime_name}_{SP.JOB_ID}.err.log",
            account=runtime_config["account"],
            qos=runtime_config["qos"],
            ntasks=runtime_config["num_workers"],
            cpus_per_task=runtime_config["cpus_worker"],
            # nodes=runtime_config["num_nodes"],
            time=runtime_config["max_time"],
            signal="SIGUSR1@20"
        )
        if "gpus_worker" in runtime_config:
            # slurm_cmd.add_arguments(gpus_per_task=runtime_config["gpus_worker"])
            slurm_cmd.add_arguments(gres=f"gpu:{runtime_config['gpus_worker']}")
        if "extra_slurm_args" in runtime_config:
            slurm_cmd.add_arguments(**runtime_config["extra_slurm_args"])
        slurm_cmd.add_cmd("export SRUN_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK}")

        entry_point = os.path.join(os.path.dirname(__file__), "entry_point.py")

        command = ["srun", "-l"]

        # GEKKOFS
        if "mode" in runtime_config and "gkfs" in runtime_config["mode"]:
            logger.info("Running HPC runtime with GKFS")
            gekko_sh = os.path.join(os.path.dirname(__file__), "gkfs_start.sh")
            with open(gekko_sh, "w") as f:
                f.write(start_script)
            slurm_cmd.add_cmd('export GKFS_BASE="/gpfs/${HOME}/gekkofs_base"')
            slurm_cmd.add_cmd('export GEKKODEPS="${GKFS_BASE}/iodeps"')
            slurm_cmd.add_cmd("export GKFS_LOG_LEVEL=0")
            slurm_cmd.add_cmd("export LIBGKFS_LOG=none")
            slurm_cmd.add_cmd('export GKFS="${GEKKODEPS}/lib64/libgkfs_intercept.so"')
            slurm_cmd.add_cmd('export LIBGKFS_HOSTS_FILE="${HOME}/test/gkfs_hosts.txt"')
            slurm_cmd.add_cmd('echo "Removing ${LIBGKFS_HOSTS_FILE}"')
            slurm_cmd.add_cmd('rm "${LIBGKFS_HOSTS_FILE}"')
            slurm_cmd.add_cmd(
                "srun -c ${SLURM_CPUS_ON_NODE}",
                "-n ${SLURM_NNODES} -N ${SLURM_NNODES}",
                "--mem=0 --overlap -overcommit --oversubscribe --export='ALL'",
                "/bin/bash",
                gekko_sh,
                "&",
            )
            slurm_cmd.add_cmd('while [[ ! -f "${LIBGKFS_HOSTS_FILE}" ]]; do sleep 1; done')
            slurm_cmd.add_cmd('while [[ $(wc -l < "$LIBGKFS_HOSTS_FILE") -lt ${SLURM_NNODES} ]]; do sleep 1; done')
            command.extend(
                [
                    "--mem=0",
                    "--oversubscribe",
                    "--overlap",
                    "--overcommit",
                    '--export="ALL",LD_PRELOAD=${GKFS}',
                ]
            )

        command.extend(
            [
                "python",
                entry_point,
                rabbit_url,
                runtime_mng_queue,
                runtime_task_queue,
                runtime_config["max_tasks_worker"],
            ]
        )
        slurm_job = slurm_cmd.sbatch(*command)
        if logger.level == logging.DEBUG:
            logger.debug(f"sbatch script:\n{slurm_cmd.script()}")
        slurm_job.wait()
        # while not slurm_job.wait(timeout=60):
        #     self.__connection.process_data_events()  # Avoid Rabbit to drop connection during long waits
        time.sleep(10)  # Wait to ensure initializations
        if not slurm_job.is_running():
            raise Exception("Slurm job failed. Check logs.")

        # save job id somewhere to cancel it afterwards (another python proc running delete)
        key = self.get_runtime_key(runtime_name, None)
        self._save_runtime_job_id(key, slurm_job.get_id())

    def deploy_runtime(self, runtime_name, memory, timeout):
        logger.debug("Deploying HPC runtime %s", runtime_name)
        logger.warning("HPC runtimes ignore memory and timeout config.")
        assert runtime_name in self.hpc_config["runtimes"], (
            f"Runtime '{runtime_name}' is not defined in the config file."
        )
        self._deploy_runtime(runtime_name, self.hpc_config["runtimes"][runtime_name])

        runtime_meta = self._generate_runtime_meta(runtime_name, memory)

        return runtime_meta

    def delete_runtime(self, runtime_name, runtime_memory, version=__version__):
        logger.info(f"Deleting HPC runtime {runtime_name}")

        key = self.get_runtime_key(runtime_name, runtime_memory, version)
        slurm_job_id = self._get_runtime_job_id(key)
        if not slurm_job_id:
            logger.info("Runtime is not deployed.")
            return

        slurm_job = Slurm.job_from_id(slurm_job_id)

        if slurm_job.is_running():
            payload = {}
            payload["log_level"] = logger.getEffectiveLevel()
            encoded_payload = utils.dict_to_b64str(payload)

            message = {"action": "stop", "payload": encoded_payload}

            runtime_config = self.hpc_config["runtimes"][runtime_name]
            runtime_mng_queue = self._get_rabbit_management_queue(runtime_name)
            # Send message(s) to RabbitMQ
            for _ in range(runtime_config["num_workers"]):
                self.__publish_to_rabbit(runtime_mng_queue, message)

            if slurm_job.wait("", sleep=5):
                logger.info(f"HPC runtime {runtime_name} stopped.")
            else:
                logger.error(f"Couldn't stop runtime {runtime_name}. Check slurm job {slurm_job_id}.")

        else:
            logger.info(f"HPC runtime {runtime_name} is already stopped.")
        self._delete_runtime_job_id(key)

    def clean(self, **kwargs):
        """
        Deletes all HPC runtimes for this user
        """
        logger.info("Cleaning HPC runtimes")

        # Delete all deployed runtimes
        for runtime_name in list(self.hpc_config["runtimes"].keys()):
            runtime_config = self.hpc_config["runtimes"][runtime_name]
            self.delete_runtime(runtime_name, 0, __version__)
            # Delete rabbit queues
            logger.info(f"Deleting RabbitMQ queues for runtime {runtime_name}")
            runtime_task_queue = runtime_config.get("rmq_queue", self._get_rabbit_task_queue(runtime_name))
            runtime_mng_queue = self._get_rabbit_management_queue(runtime_name)
            self.__delete_rmq_queues(runtime_task_queue, runtime_mng_queue, runtime_mng_queue + RETURN_QUEUE_POSTFIX)

    def list_runtimes(self, runtime_name="all"):
        """
        List HPC runtimes deployed for this user
        @param runtime_name: name of the runtime to list, 'all' to list all runtimes
        @return: list of tuples (runtime name, memory, version)
        """
        logger.debug(f"Listing HPC runtimes: {runtime_name}")
        runtime_names = list(self.hpc_config["runtimes"].keys())
        deployed = []
        for name in runtime_names:
            key = self.get_runtime_key(name, None)
            if self._get_runtime_job_id(key):
                deployed.append(name)

        if runtime_name == "all":
            runtimes = [(k, 0, __version__) for k in deployed]
            return runtimes
        if runtime_name in deployed:
            return [(runtime_name, 0, __version__)]
        else:
            return []

    def invoke(self, runtime_name, runtime_memory, job_payload):
        """
        Invoke function asynchronously
        @param runtime_name: name of the runtime
        @param runtime_memory: memory of the runtime in MB (ignored)
        @param job_payload: invoke dict payload
        @return: invocation ID
        """
        logger.debug("Invoking HPC function. runtime: %s", runtime_name)
        # logger.info(f"Payload: {job_payload}")

        granularity = self.hpc_config["worker_processes"]
        times, res = divmod(job_payload["total_calls"], granularity)

        for i in range(times + (1 if res != 0 else 0)):
            num_tasks = granularity if i < times else res
            payload_edited = job_payload.copy()

            start_index = i * granularity
            end_index = start_index + num_tasks

            payload_edited["call_ids"] = payload_edited["call_ids"][start_index:end_index]
            payload_edited["data_byte_ranges"] = payload_edited["data_byte_ranges"][start_index:end_index]
            payload_edited["total_calls"] = num_tasks

            message = {"action": "send_task", "payload": utils.dict_to_b64str(payload_edited)}

            runtime_config = self.hpc_config["runtimes"][runtime_name]
            runtime_task_queue = runtime_config.get("rmq_queue", self._get_rabbit_task_queue(runtime_name))
            self.__publish_to_rabbit(runtime_task_queue, message)
        job_key = job_payload["job_key"]
        activation_id = f"lithops-{job_key.lower()}"
        return activation_id

    def get_runtime_key(self, runtime_name, runtime_memory, version=__version__):
        """
        Method that creates and returns the runtime key.
        Runtime keys are used to uniquely identify runtimes within the storage,
        in order to know which runtimes are installed and which not.
        """
        name = self._format_runtime_name(runtime_name, version)
        runtime_key = os.path.join(self.name, version, name)
        return runtime_key

    def get_runtime_info(self):
        """
        Method that returns all the relevant information about the runtime set
        in config
        """
        if "runtime" not in self.hpc_config or self.hpc_config["runtime"] == "default":
            self.hpc_config["runtime"] = self._get_default_runtime_name()

        runtime_info = {
            "runtime_name": self.hpc_config["runtime"],
            "runtime_memory": self.hpc_config["runtime_memory"],
            "runtime_timeout": self.hpc_config["runtime_timeout"],
            "max_workers": self.hpc_config["max_workers"],
        }

        return runtime_info

    def _generate_runtime_meta(self, runtime_name, runtime_memory):
        """
        Extract preinstalled Python modules from function execution environment
        return : runtime meta dictionary
        """
        logger.debug(f"Extracting runtime metadata from: {runtime_name}")

        # hpc_runtime_name = self._format_runtime_name(runtime_name, runtime_memory)
        payload = {}
        payload["log_level"] = logger.getEffectiveLevel()
        encoded_payload = utils.dict_to_b64str(payload)

        message = {"action": "get_metadata", "payload": encoded_payload}

        # Declare return queue
        runtime_mng_queue = self._get_rabbit_management_queue(runtime_name)
        self.__declare_rmq_queues(runtime_mng_queue + RETURN_QUEUE_POSTFIX)

        # Send message to RabbitMQ
        self.__publish_to_rabbit(runtime_mng_queue, message)

        logger.debug("Waiting for runtime metadata")

        # Check until a new message arrives to the status_queue queue
        start_time = time.time()
        runtime_meta = None

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > 600:  # 10 minutes
                raise Exception("Unable to extract metadata from the runtime")

            method_frame, properties, body = self.__get_rmq_channel().basic_get(
                runtime_mng_queue + RETURN_QUEUE_POSTFIX
            )
            if method_frame:
                runtime_meta = json.loads(body)
                break
            else:
                logger.debug("...")

            time.sleep(1)

        if not runtime_meta or "preinstalls" not in runtime_meta:
            raise Exception(f"Failed getting runtime metadata: {runtime_meta}")

        return runtime_meta
