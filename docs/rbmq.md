# Lithops-HPC and RabbitMQ (RBMQ)
This guide explains how to configure and deploy a RabbitMQ (RBMQ) messaging system for Lithops on an HPC cluster using Singularity containers and SLURM.

---

## RBMQ Configuration (on Local PC)

### 1. Set user credentials

```bash
cd $LITHOPS_HPC_HOME/rabbitmq/sif/
vim rabbitmq4.def
# Add/edit the following lines:
export RABBITMQ_USER=<user>
export RABBITMQ_PASSWORD=<password>
export RABBITMQ_VHOST=<vhost-name>
```

---

### 2. Enable RabbitMQ plugins

```bash
vim rabbitmq4.def
# Example:
rabbitmq-plugins enable plugin1
rabbitmq-plugins enable plugin2
```

---

### 3. Build the Singularity image

```bash
sudo singularity build rabbitmq4.sif rabbitmq4.def
```

---

### 4. Transfer the image to the HPC cluster

```bash
scp rabbitmq4.sif <user>@<hpc>:${LITHOPS_HPC_HOME}/rabbitmq/sif/
```

---

### 5. Edit SLURM startup scripts (optional)

Update the following files to match your cluster's setup:

- `start_rabbitmq_master.sh`: Starts the RBMQ container, updates config, and forwards ports.
- `rabbitmq_master.slurm`: Defines CPU/tasks for deploying the RBMQ service.

> Note: `rmq_ip` is extracted from `/etc/hosts` and may vary per system.

```bash
cd $LITHOPS_HPC_HOME/rabbitmq/
vim start_rabbitmq_master.sh
vim rabbitmq_master.slurm
```

---

### 6. Copy SLURM scripts to the HPC cluster

```bash
scp *.sh <user>@<hpc>:${LITHOPS_HPC_HOME}/rabbitmq/
scp *.slurm <user>@<hpc>:${LITHOPS_HPC_HOME}/rabbitmq/
```

---

## RBMQ Installation (on HPC)

### 1. Set the RabbitMQ home path

```bash
echo "export RABBITMQ_HOME=${LITHOPS_HPC_HOME}/rabbitmq/" >> ~/.bashrc
source ~/.bashrc
```

---

### 2. Start the RBMQ service (via Lithops)

Lithops will automatically start the RBMQ service when deploying a compute backend:

**From HPC:**

```bash
lithops runtime deploy <runtime-name>
```

**From local PC:**

```bash
lithops hpc connect
lithops hpc runtime_deploy <runtime-name>
```

---

### 3. Manually start RBMQ (optional)

```bash
$RABBITMQ_HOME/start_rabbitmq_master.sh
```

---

##  RBMQ Settings in `LITHOPS_CONFIG_FILE`

RabbitMQ settings can be auto-configured during backend deployment. To configure manually:

### Client side (local PC):

```yaml
rabbitmq:
  amqp_url: amqp://<user>:<pass>@localhost:5672/<vhost>
```

---

### Provider side (HPC cluster):

```yaml
rabbitmq:
  amqp_url: amqp://<user>:<pass>@<node-ip>:5672/<vhost>
```

---

### Advanced HPC settings:

Specify the size of RabbitMQ messages in tasks:

```yaml
hpc:
  worker_processes: <message-task-size>
```

> Example: If `worker_processes: 112` and you launch 200 tasks, two RabbitMQ messages will be sent: one with 112 and one with 88.

---

### Optional: Share a task queue between runtimes

```yaml
rmq_queue: <shared-queue-name>
```

> Example: You can define a second runtime `hpc2` that uses the same queue as `hpc-default` for load balancing.

---

## FAQs

1. **Error: "Failed to create tunnel"**  
   ➤ Delete the socket directory and rerun `start_rabbitmq_master.sh`.

2. **Error: `pika.exceptions.AMQPConnectionError`**  
   ➤ RabbitMQ is likely not running. Try starting it manually.

3. **Error: `paramiko.ssh_exception.SSHException`**  
   ➤ SSH connection failed. Run `lithops hpc connect` to re-establish it.
