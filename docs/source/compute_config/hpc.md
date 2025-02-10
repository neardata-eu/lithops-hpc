# HPC

Lithops with *HPC* as a compute backend.

This backend manages slurm jobs as a backbone for running Lithops tasks. Run it from the supercomputer cluster, with access to slurm commands and the shared FS space.

**Note:** This backend requires a RabbitMQ server for communication and coordination between Lithops components. It must be accessible by workers and clients.

## Configuration

### Configure RabbitMQ

A RabbitMQ server is required and must be accessible from the Lithops client (usually in login nodes or a slurm job) and workers (slurm jobs).
Set its URL in the Lithops RabbitMQ configuration section.
Monitoring with RabbitMQ is optional.

```yaml
lithops:
    backend: hpc
    monitoring: rabbitmq     # optional

rabbitmq:
    amqp_url: amqp://<username>:<password>@<rabbitmq_host>:<rabbitmq_port>/<vhost> 
```

Replace `<username>`, `<password>`, `<rabbitmq_host>`, `<rabbitmq_port>`, and `<vhost>` with your RabbitMQ credentials.

### Configure HPC backend

The HPC backend uses Lithops runtime deployments to start/stop workers.
HPC workers run in slurm jobs. For that, the Lithops client must have access to slurm commands to submit jobs and check their status.
HPC runtime configurations are defined in the Lithops config file.

```yaml
hpc:
    worker_processes: <WORKER_PROCESSES>
    runtime: <RUNTIME_NAME>
    runtimes:
        <runtime_name>:
            account: <SLURM_ACCOUNT>
            qos: <SLURM_QUEUE>
            num_workers: <NUM_LITHOPS_WORKERS>
            cpus_worker: <CPUS_PER_WORKER>
            cpus_task: <CPUS_PER_LITHOPS_TASK>
        <runtime2>:
            ...
```

When using one of these runtimes (either by setting the `runtime` key or specifying one on the `FunctionExecutor`), Lithops will spawn the corresponding slurm job (as a runtime deploy, which happens automatically the first time it is used).
This may take some time, which will appear as a cold start in the application execution.
Alternatively, you can start the runtime manually with the Lithops CLI `lithops runtime deploy <runtime_name>`.

Right after deployment, Lithops will generate the runtime metadata and store it in the configured storage, that further Lithops executions may use to know the runtime state.

Runtimes are not automatically removed. To do so, use the Lithops CLI `lithops runtime delete <runtime_name>`. This will stop the slurm job and remove any metadata in storage. If the slurm job is cancelled some other way, metadata will remain. Lithops should detect that the metadata is stale and remove it, when the job it points to is not active.

You can check the slurm job logs in the `slurm_lithops_workers` directory created in the client working directory (assuming it is in a shared PFS like GPFS or Lustre).

It is required to run the HPC backend in conjunction with the PFS storage backend, setting the `storage_root` to a path in the PFS shared space, available to all cluster nodes.

## Summary of Configuration Keys for HPC

| Group | Key                 | Default | Mandatory | Additional info    |
|-------|---------------------|---------|-----------|--------------------|
| hpc   | worker_processes    | 100 | no  | Number of tasks sent in each RabbitMQ message. Ideally, set to a multiple of the node's CPU count. |
| hpc   | runtime             |     | no  | Name of the HPC runtime to be used as the default. Must be one of the defined in the `runtimes` configuration. If skipped, or set to `"default"`, the first item in `runtimes` will be used. |
| hpc   | runtimes            |     | yes | Must contain at least one configuration of an HPC runtime. Each HPC runtime is a Slurm job running Lithops workers with a specific configuration (number of workers, partition, etc.). |
| hpc   | runtimes.account |     | yes | Slurm account name for this runtime configuration. |
| hpc   | runtimes.qos |     | yes | Slurm queue (QOS) name for this runtime configuration. |
| hpc   | runtimes.num_workers |     | yes | Number of Lithops workers to run for this runtime configuration. |
| hpc   | runtimes.cpus_worker |     | yes | Number of CPUs per Lithops worker for this runtime configuration. |
| hpc   | runtimes.cpus_task |  1  | no | Number CPUs per Lithops task (a function execution). It must be lower than `cpus_worker`, since it will define how many tasks can be fit concurrently on each worker. By default, workers take as many tasks as CPUs available. |
| hpc   | runtimes.gpus_worker |     | no | If specified, Lithops will deploy this runtime asking for GPU resources. This should be set to the number of GPUs per worker and QOS should point to a partition with GPU-accelerated nodes. |
| hpc   | runtimes.extra_slurm_args |     | no | Optionally pass arguments to the underlying Slurm job. This should contain a dictionary. |
| hpc   | runtimes.rmq_queue |     | no | Use a custom RabbitMQ queue for function invocations. By default, tasks are sent to a queue with the runtime name. You can set this to the name of another runtime to have them share the queue and split the workload. Or set all runtimes to a custom queue name so all of them split the workload. |


## Test Lithops
Once you have your compute and storage backends configured, you can run a hello world function with:

```bash
lithops hello -b hpc
```

To stop the workers:
```bash
lithops runtime delete <runtime_name>
```

## Viewing the execution logs

You can view the function executions logs in your local machine using the *lithops client*:

```bash
lithops logs poll
```
