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

DEFAULT_CONFIG_KEYS = {
    "runtime_timeout": 600,  # Default: 10 minutes
    "runtime_memory": None,  # Memory is ignored in this backend
    "worker_processes": 100,  # Determines how many messages are sent to rabbit per job
    "max_workers": 100,  # this sets the max number of workers per map, the backend ignores it for now
}


def load_config(config_data):
    for key in DEFAULT_CONFIG_KEYS:
        if key not in config_data["hpc"]:
            config_data["hpc"][key] = DEFAULT_CONFIG_KEYS[key]

    assert "runtimes" in config_data["hpc"], "You must define a runtime config for HPC backend."
    assert isinstance(config_data["hpc"]["runtimes"], dict), "HPC runtimes config should be a dict."
    assert len(config_data["hpc"]["runtimes"].items()) > 0, "At least one runtime config is needed for HPC backend."

    for k, v in config_data["hpc"]["runtimes"].items():
        assert "slurm_account" in v, f"HPC runtime {k} must define a slurm_account"
        assert "slurm_qos" in v, f"HPC runtime {k} must define a slurm_qos"
        assert "num_nodes" in v, f"HPC runtime {k} must define num_nodes"
        assert "cpus_node" in v, f"HPC runtime {k} must define cpus_node"
        if "workers_node" not in v:
            v["workers_node"] = v["cpus_node"]

    assert "rabbitmq" in config_data and "amqp_url" in config_data["rabbitmq"], (
        "To use the HPC backend you must configure RabbitMQ."
    )
    config_data["hpc"]["amqp_url"] = config_data["rabbitmq"].get("amqp_url", False)
