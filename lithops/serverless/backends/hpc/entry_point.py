#
# (C) Copyright BSC, CloudLab 2025
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
import json
import logging
import os
import sys
import time
import uuid
from multiprocessing import Value
from threading import Thread

import pika
import pika.adapters.blocking_connection
import pika.channel
import pika.spec

from lithops.serverless.backends.hpc.hpc import RETURN_QUEUE_POSTFIX
from lithops.utils import b64str_to_dict, dict_to_b64str, setup_lithops_logger
from lithops.version import __version__
from lithops.worker import function_handler
from lithops.worker.utils import get_runtime_metadata

logger = logging.getLogger("lithops.worker")


def extract_runtime_meta(ch: pika.channel.Channel):
    logger.info(f"Lithops v{__version__} - Generating metadata")

    runtime_meta = get_runtime_metadata()
    ch.basic_publish(
        exchange="",
        routing_key=rmq_mng_queue + RETURN_QUEUE_POSTFIX,
        body=json.dumps(runtime_meta),
        properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
    )

    logger.info("Runtime metadata generated")


def run_job_k8s_rabbitmq(payload):
    logger.info(f"Lithops v{__version__} - Starting HPC execution")

    act_id = str(uuid.uuid4()).replace("-", "")[:12]
    os.environ["__LITHOPS_ACTIVATION_ID"] = act_id
    os.environ["__LITHOPS_BACKEND"] = "hpc"

    function_handler(payload)
    with running_jobs.get_lock():
        running_jobs.value += len(payload["call_ids"])

    logger.info("Finishing HPC execution")


def manage_work_queue(ch, method, payload):
    """Callback to receive the payload and run the jobs"""
    logger.info("Call from lithops received.")

    message = payload
    tasks = message["total_calls"]

    # If there are more tasks than cpus in the pod, we need to send a new message
    if tasks <= running_jobs.value:
        processes_to_start = tasks
    else:
        if running_jobs.value == 0:
            logger.info("All cpus are busy. Waiting for a cpu to be free")
            ch.basic_nack(delivery_tag=method.delivery_tag)
            time.sleep(0.5)
            return

        processes_to_start = running_jobs.value

        message_to_send = message.copy()
        message_to_send["total_calls"] = tasks - running_jobs.value
        message_to_send["call_ids"] = message_to_send["call_ids"][running_jobs.value:]
        message_to_send["data_byte_ranges"] = message_to_send["data_byte_ranges"][running_jobs.value:]
        message_to_send = {"action": "send_task", "payload": dict_to_b64str(message_to_send)}
        message["call_ids"] = message["call_ids"][: running_jobs.value]
        message["data_byte_ranges"] = message["data_byte_ranges"][: running_jobs.value]

        ch.basic_publish(
            exchange="",
            routing_key=rmq_task_queue,
            body=json.dumps(message_to_send),
            properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
        )

    logger.info(f"Starting {processes_to_start} processes")

    message["worker_processes"] = running_jobs.value
    with running_jobs.get_lock():
        running_jobs.value -= processes_to_start

    Thread(target=run_job_k8s_rabbitmq, args=([message])).start()

    ch.basic_ack(delivery_tag=method.delivery_tag)


def actions_switcher(ch, method, properties, body):
    message = json.loads(body)
    action = message["action"]
    encoded_payload = message["payload"]

    payload = b64str_to_dict(encoded_payload)
    setup_lithops_logger(payload.get("log_level", "INFO"))

    logger.info(f"Action {action} received from lithops.")

    if action == "get_metadata":
        extract_runtime_meta(ch)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    elif action == "send_task":
        manage_work_queue(ch, method, payload)
    elif action == "stop":
        ch.basic_ack(delivery_tag=method.delivery_tag)
        ch.basic_cancel(rt_consumer_tag)
        ch.basic_cancel(tk_consumer_tag)


if __name__ == "__main__":
    # Parse args
    rabbit_url = sys.argv[1]
    rmq_mng_queue = sys.argv[2]
    rmq_task_queue = sys.argv[3]
    task_concurrency = int(sys.argv[4])
    setup_lithops_logger("INFO")

    python_version = sys.version_info
    python_version = str(python_version[0]) + "." + str(python_version[1])
    logger.info(f"Lithops v{__version__} - Python version: {python_version}")
    logger.info(f"Starting HPC Lithops worker node...  max_tasks={task_concurrency}")
    # Shared variable to track running jobs / max concurrent tasks
    running_jobs = Value("i", task_concurrency)

    # Connect to rabbitmq
    params = pika.URLParameters(rabbit_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=rmq_mng_queue, durable=True)
    channel.queue_declare(queue=rmq_task_queue, durable=True)
    channel.basic_qos(prefetch_count=1)

    # Start listening for tasks/jobs
    rt_consumer_tag = channel.basic_consume(queue=rmq_mng_queue, on_message_callback=actions_switcher)
    tk_consumer_tag = channel.basic_consume(queue=rmq_task_queue, on_message_callback=actions_switcher)

    logger.info(f"Listening to RabbitMQ... task queue={rmq_task_queue}")
    channel.start_consuming()
    connection.close()
