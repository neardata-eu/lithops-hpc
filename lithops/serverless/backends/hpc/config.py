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
    "runtime_timeout": float("inf"),  # This backend ignores runtime timeout, set to infinite by default
    "runtime_memory": None,  # Memory is ignored in this backend
    "worker_processes": 100,  # Determines how many messages are sent to rabbit per job
    "max_workers": 100,  # this sets the max number of workers per map, the backend ignores it for now
    "max_time": "03:00:00"  # Default max time for a runtime job
}


def load_config(config_data):
    for key in DEFAULT_CONFIG_KEYS:
        if key not in config_data["hpc"]:
            config_data["hpc"][key] = DEFAULT_CONFIG_KEYS[key]

    assert "runtimes" in config_data["hpc"], "You must define a runtime config for HPC backend."
    assert isinstance(config_data["hpc"]["runtimes"], dict), "HPC runtimes config should be a dict."
    assert len(config_data["hpc"]["runtimes"].items()) > 0, "At least one runtime config is needed for HPC backend."

    for k, v in config_data["hpc"]["runtimes"].items():
        assert "account" in v, f"HPC runtime {k} must define 'account'"
        assert "qos" in v, f"HPC runtime {k} must define 'qos'"
        assert "num_workers" in v, f"HPC runtime {k} must define 'num_workers'"
        assert "cpus_worker" in v, f"HPC runtime {k} must define 'cpus_worker'"
        v["max_tasks_worker"] = int(divmod(v["cpus_worker"], v["cpus_task"])[0]) if "cpus_task" in v else v["cpus_worker"]
        assert v["max_tasks_worker"] > 0, "HPC runtime 'cpus_task' has to be lower than or equal to 'cpus_worker'"
        if "extra_slurm_args" in v:
            assert isinstance(v["extra_slurm_args"], dict), f"HPC runtime {k}, 'extra_slurm_args' must be a dictionary."
        v["max_time"] = v.get("max_time", config_data["hpc"]["max_time"])

    assert "rabbitmq" in config_data and "amqp_url" in config_data["rabbitmq"], (
        "To use the HPC backend you must configure RabbitMQ."
    )
    config_data["hpc"]["amqp_url"] = config_data["rabbitmq"].get("amqp_url", False)
