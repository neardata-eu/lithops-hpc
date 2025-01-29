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
"""
Simplified implementation of a Slurm Python wrapper.

Adapted from https://pypi.org/project/simple-slurm/
"""

import argparse
import datetime
import math
import subprocess
from typing import Iterable

from .constants import SBATCH_ARGUMENTS
from .job import SlurmJob

FALSE_BOOLEAN = "IGNORE_FALSE_BOOLEAN"


class Slurm:
    """Simple proxy for running sbatch commands.

    See https://slurm.schedmd.com/sbatch.html for a complete description and
    arguments for the sbatch command.

    Arguments can be given as a list of key1, val1, key2, val2, ...
    or with keywords key1=val1, key2=val2, ... or both.
    Example:
        `Slurm('arg1', val1, 'arg2', val2, arg3=val3, arg4=val4)`
    """

    def __init__(self, *args: str, **kwargs):
        """Initialize the parser with the given arguments."""

        # initialize parser
        self.namespace = None
        self.parser = argparse.ArgumentParser()
        # self.squeue = SlurmSqueueWrapper()
        # self.scancel = SlurmScancelWrapper()

        # Parse any possible sbatch argument
        for keys in SBATCH_ARGUMENTS:
            # add argument into argparser
            self.parser.add_argument(*(fmt_key(k) for k in keys))

        # parse provided arguments into the namespace
        self.add_arguments(*args, **kwargs)

        # contain a list of "single-line" commands to dispatch
        self.run_cmds = []

    def _add_one_argument(self, key: str, value: str):
        """Parse the given key-value pair (the argument is given in key)."""
        key, value = fmt_key(key), fmt_value(value)
        if value is not FALSE_BOOLEAN:  # Skip bool args set to false
            self.namespace = self.parser.parse_args([key, value], namespace=self.namespace)

    def add_arguments(self, *args: str, **kwargs):
        """Parse the given key-value pairs.

        Both syntaxes *args and **kwargs are allowed, ex:
            add_arguments('arg1', val1, 'arg2', val2, arg3=val3, arg4=val4)
        """
        for key, value in zip(args[0::2], args[1::2]):
            self._add_one_argument(key, value)
        for key, value in kwargs.items():
            self._add_one_argument(key, value)
        return self

    def add_cmd(self, *cmd_args: str):
        """Add a new command to the command list, it can be provided as a single
        argument (ie. a string) or a collection of arguments (all converted to
        strings and spaces are added in-between).

        For example, these syntaxes are equivalent
            > slurm.add_cmd('python main.py --input 1')
            > slurm.add_cmd('python', 'main.py', '--input', 1)
        """
        cmd = " ".join([str(cmd) for cmd in cmd_args]).strip()
        if len(cmd):
            self.run_cmds.append(cmd)
        return self

    def reset_cmd(self):
        """Reset the command list"""
        self.run_cmds = []

    @staticmethod
    def _valid_key(key: str) -> str:
        """Long arguments (for slurm) constructed with '-' have been internally
        represented with '_' (for Python). Correct for this in the output.
        """
        return key.replace("_", "-")

    def script(self, shell: str = "/bin/bash", convert: bool = True):
        """Generate the sbatch script for the current arguments and commands"""

        header = (
            f"#!{shell}",
            "",
            *(f"#SBATCH --{self._valid_key(k):<19} {v}" for k, v in vars(self.namespace).items() if v is not None),
            "",
        )
        arguments = "\n".join(header)
        commands = "\n".join([cmd.replace("$", "\\$") if convert else cmd for cmd in self.run_cmds])
        script = "\n".join((arguments, commands)).strip() + "\n"
        return script

    def sbatch(
        self,
        *run_cmd: str,
        convert: bool = True,
        sbatch_cmd: str = "sbatch",
        shell: str = "/bin/bash",
        job_file: str = None,
    ) -> SlurmJob:
        """Run the sbatch command with all the (previously) set arguments and
        the provided command in 'run_cmd' alongside with the previously set
        commands using 'add_cmd'.

        Note that 'run_cmd' can accept multiple arguments. Thus, any of the
        other arguments must be given as key-value pairs:
        ```python
        > slurm.sbatch('python main.py')
        > slurm.sbatch('python', 'main.py')
        ```

        This function employs the 'here document' syntax, which requires that
        bash variables be scaped. This behavior is default, set 'convert'
        to False to disable it.

        This function employs the following syntax:
        ```bash
        $ slurm_cmd << EOF
        > bash_script
        > run_command
        > EOF
        ```
        For such reason if any bash variable is employed by the 'run_command',
        the '`$`' should be scaped. This behavior is default, set
        'convert' to False to disable it.

        If the argument 'job_file' is used, the script will be written to the
        designated file, and then the command `sbatch <job_file>` will be
        executed.
        """
        sbatch_cmd += " --parsable"
        self.add_cmd(*run_cmd)
        script = self.script(shell, convert)
        if job_file is not None:
            with open(job_file, "w") as fid:
                fid.write(script)
            cmd = sbatch_cmd + " " + job_file
        else:
            cmd = "\n".join(
                (
                    sbatch_cmd + " << EOF",
                    script,
                    "EOF",
                )
            )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        job_id = result.stdout.strip().split(";")[0]
        job = SlurmJob(job_id, script)
        return job

    @staticmethod
    def job_from_id(job_id) -> SlurmJob:
        cmd = f"sacct -B -j {job_id}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        script = result.stdout.strip()
        return SlurmJob(job_id, script)


# Create a setter for each individual sbatch argument
for keys in SBATCH_ARGUMENTS:
    key = keys[0]

    def set_key(self, value):
        return self.add_arguments(key, value)

    set_key.__name__ = f"set_{key}"
    set_key.__doc__ = f'Setter method for the argument "{key}"'
    setattr(Slurm, set_key.__name__, set_key)


def fmt_key(key: str) -> str:
    """Maintain correct formatting for keys in key-value pairs"""
    key = str(key).strip()
    if "-" not in key:
        key = f"--{key}" if len(key) > 1 else f"-{key}"
    return key


def fmt_value(value) -> str:
    """Maintain correct formatting for values in key-value pairs
    This function handles some special cases for the type of value:
        1) A 'range' object:
            Converts range(3, 15) into '3-14'.
            Useful for defining job arrays using a Python syntax.
            Note the correct form of handling the last element.
        2) A 'dict' object:
            Converts dict(after=65541, afterok=34987)
            into 'after:65541,afterok:34987'.
            Useful for arguments that have multiple 'sub-arguments',
            such as when declaring dependencies.
        3) A `datetime.timedelta` object:
            Converts timedelta(days=1, hours=2, minutes=3, seconds=4)
            into '1-02:03:04'.
            Useful for arguments involving time durations.
        4) An `iterable` object:
            Will recursively format each item
            Useful for defining lists of parameters
    """
    if isinstance(value, str):
        pass

    elif isinstance(value, range):
        start, stop, step = value.start, value.stop - 1, value.step
        value = f"{start}-{stop}" + ("" if value.step == 1 else f":{step}")

    elif isinstance(value, dict):
        value = ",".join((f"{k}:{fmt_value(v)}" for k, v in value.items()))

    elif isinstance(value, datetime.timedelta):
        time_format = "{days}-{hours2}:{minutes2}:{seconds2}"
        value = format_timedelta(value, time_format=time_format)

    elif isinstance(value, Iterable):
        value = ",".join((fmt_value(item) for item in value))

    elif isinstance(value, bool):
        # Booleans are flags, so no values. If false, we skip the arg.
        value = "" if value else FALSE_BOOLEAN

    return str(value).strip()


def format_timedelta(value: datetime.timedelta, time_format: str):
    """Format a datetime.timedelta (https://stackoverflow.com/a/30339105)"""
    if hasattr(value, "seconds"):
        seconds = value.seconds + value.days * 24 * 3600
    else:
        seconds = int(value)

    seconds_total = seconds

    minutes = int(math.floor(seconds / 60))
    minutes_total = minutes
    seconds -= minutes * 60

    hours = int(math.floor(minutes / 60))
    hours_total = hours
    minutes -= hours * 60

    days = int(math.floor(hours / 24))
    days_total = days
    hours -= days * 24

    years = int(math.floor(days / 365))
    years_total = years
    days -= years * 365

    return time_format.format(
        **{
            "seconds": seconds,
            "seconds2": str(seconds).zfill(2),
            "minutes": minutes,
            "minutes2": str(minutes).zfill(2),
            "hours": hours,
            "hours2": str(hours).zfill(2),
            "days": days,
            "years": years,
            "seconds_total": seconds_total,
            "minutes_total": minutes_total,
            "hours_total": hours_total,
            "days_total": days_total,
            "years_total": years_total,
        }
    )
