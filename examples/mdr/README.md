# MDR Lithops

## Run MDR

Go to this application's directory:
```bash
cd mdr
```
Make sure the `plots` directory exists:
```bash
mkdir -p plots
```

### Python environment

If not already, install the `mdr-lithops` conda environment from the provided file:
```bash
mamba env update --file conda_env.yml
```
Activate it with:
```bash
conda activate mdr-lithops
```
To deactivate or remove if necessary:
```bash
conda deactivate
conda remove --name mdr-lithops --all
```

### Configure Lithops

Set up Lithops in the `.lithops_config` file.
Update RabbitMQ hostname, storage root, and runtime config.

Start a Lithops runtime:
```bash
lithops runtime deploy gpp
```
You can stop it with:
```bash
lithops runtime delete gpp
```

### Run application
Run the MDR SLURM job:
```bash
export HPC_QOS=gp_bsccs
export HPC_USER=bsc98
sbatch -A $HPC_USER -q $HPC_QOS mdr.slurm mdr_config.yml -w 10 -c 10000 -s 0 -e 5
```
`-w` is the number of workers and `-c` is the number of slices to split the input file into.
`-s` and `-e` set the start and end of the range of chunks to process. Skip the end to process until the last one.
An optional parameter `--plots` can be used to prefix the plots location. By default it is set to `plots/`.

Alternatively, allocate a node:
```bash
salloc -A $HPC_USER -q $HPC_QOS -c 112
```
And run the Python script there:
```bash
python mdr.py mdr_config.yml -w 10 -c 10000 -s 0 -e 5
```

## MDR Configuration file

The `mdr_config.yml` file contains most configuration.

The first part is for data.
- `root_path` acts a a base dir for data. Used as a bucket by Dataplug.
- `samples_file` points to the input VCF file to process. It should be a relative path from `root_path`.
- `patients_file` points to the patient info file containing labels for the samples. It should be a relative path from `root_path`.
- `output_dir` is the directory where the results will be sent. Also relative to `root_path`.

The other part contains the parameters for the MDR computation.
