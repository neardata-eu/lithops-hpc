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
import logging
import subprocess
import time

logger = logging.getLogger(__name__)


class SlurmJob:
    def __init__(self, job_id: str, script: str):
        self.job_id = job_id
        self.script = script

    def get_id(self):
        return self.job_id

    def wait(self, status="RUNNING", sleep=10, timeout=0) -> bool:
        logger.debug(f"Checking status of slurm job: {self.job_id}")

        current_status = "start"
        cmd = f'squeue -h -j {self.job_id} -o "%T"'
        start = time.time()
        while timeout == 0 or time.time() - start < timeout:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            current_status = result.stdout.strip()
            if not current_status or current_status == status:
                break
            logger.debug(f"Job {self.job_id} is: {current_status}")
            time.sleep(sleep)

        if current_status == status:
            logger.debug(f"Slurm job {self.job_id} is now: {current_status}")
        else:
            logger.debug(f"Slurm job {self.job_id} wait timeout.")
        return current_status == status

    def get_hostname(self):
        cmd = f'squeue -h -j {self.job_id} -o "%N"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        hostname = result.stdout.strip()
        # TODO: fix for jobs with more than one node
        return hostname

    def is_running(self):
        # cmd = f'squeue -h -j {self.job_id} -o "%T"'
        cmd = f'sacct -n -j {self.job_id} -o State | head -n 1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        # TODO: fix exception when job is not found
        assert result.returncode == 0, result.stderr
        current_status = result.stdout.strip()
        return current_status == "RUNNING"
