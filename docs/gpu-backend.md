# Lithops-HPC GPU Backend

This guide explains how to configure and deploy a GPU backend optimized for GPU-based computations, offering accelerated performance for GPU-intensive tasks.

---

## Using a GPU Runtime

### 1. Configure GPU Properties in `LITHOPS_CONFIG_FILE`

Add a new GPU runtime under the `hpc/runtime` section. Example:

```yaml
hpc:
  ...
  runtimes:
    <runtime_name>:
      account: <hpc_account>
      qos: <hpc_qos_account>
      num_workers: <total_workers>
      cpus_worker: <cpus_per_worker>  # e.g., MN5 requires 20 CPUs per GPU
      gpus_worker: <gpus_per_worker>
      ...
```

> Adjust the resource values according to your HPC provider's requirements.

---

### 2. Deploy the GPU Runtime

From your **local machine**:

```bash
lithops hpc connect
lithops hpc runtime_deploy <runtime_name>
```

Or from the **HPC provider**:

```bash
lithops runtime deploy <runtime_name>
```

---

### 3. Run a GPU Example

```bash
cd $LITHOPS_HPC_HOME/examples/gpu
export PYTHONPATH=$LITHOPS_HPC_HOME/hpc_data_connectors:$PYTHONPATH
mkdir plots
python flops_gpu_benchmark_v2.py \
  -b hpc -s pfs \
  --loopcount=5 \
  --matn=4096 \
  --memory=1024 \
  --outdir=plots \
  --tasks=4
```

---

##  FAQs



---

## 📎 Related Resources

- [Getting started with Lithops-HPC](#)
