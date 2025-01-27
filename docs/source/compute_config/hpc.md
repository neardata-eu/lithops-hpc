# HPC

Lithops with *HPC* as a serverless compute backend.

This backend manages slurm jobs as a backbone for running Lithops tasks. Run it from the supercomputer cluster, with access to slurm commands and the shred FS space.

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

The HPC backend uses runtime deployments to start/stop workers.
HPC workers run in slurm jobs. For that, the Lithops client must have access to slurm commands to submit jobs and check their status.
HPC runtime configurations are defined in the Lithops config file.

```yaml
hpc:
    worker_processes: <WORKER_PROCESSES>
    runtime: <RUNTIME_NAME>
    runtimes:
        <runtime_name>:
            slurm_account: <SLURM_ACCOUNT>
            slurm_qos: <SLURM_QUEUE>
            num_nodes: <SLURM_JOB_NODES>
            cpus_node: <CPUS_PER_NODE>
            workers_node: <WORKERS_PER_NODE>
        <runtime2>:
            ...
```

When using one of these runtimes (either by setting the `runtime` key or specifying one on the `FunctionExecutor`), Lithops will spawn the corresponding slurm job (as a runtime deploy, which happens automatically the first time it is used).
Then it will generate its metadata and store it in the configured storage, that further Lithops executions may use to know the runtime state.
Runtimes are not automatically removed. To do so, use the Lithops CLI `lithops runtime delete <runtime_name>`. This will stop the slurm job and remove any metadata in storage.

You can check the slurm job logs in the `slurm_lw` directory created in the client working directory (assuming it is in a shared FS like GPFS or Lustre).

It is required to run the HPC backend in conjunction with the localhost storage backend, setting the `storage_bucket` to a path in the FS shared space, available to all cluster nodes.

## Summary of Configuration Keys for HPC

| Group | Key                 | Default | Mandatory | Additional info    |
|-------|---------------------|---------|-----------|--------------------|
| hpc   | worker_processes    | 100 | no  | Number of tasks sent in each RabbitMQ message. Ideally, set to a multiple of the node's CPU count. |
| hpc   | runtime             |     | no  | Name of the HPC runtime to be used as the default. Must be one of the defined in the `runtimes` configuration. If skipped, or set to `default`, the first item in `runtimes` will be used. |
| hpc   | runtimes            |     | yes | Must contain at least one configuration of aof an HPC runtime. Each HPC runtime is a Slurm job running lithops workers with a specific configuration (number of nodes, partition, etc.). |
| hpc   | runtimes.slurm_account |     | yes | Slurm account name for this runtime configuration. |
| hpc   | runtimes.slurm_qos |     | yes | Slurm queue name for this runtime configuration. |
| hpc   | runtimes.num_nodes |     | yes | Number of nodes to request to Slurm for this runtime configuration. |
| hpc   | runtimes.cpus_node |     | yes | Number of CPUs per node to request to Slurm for this runtime configuration. |
| hpc   | runtimes.workers_node |     | no | Number of tasks each node accepts to run concurrently for this runtime configuration. If not set, this will be set to `cpus_node`. |


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
