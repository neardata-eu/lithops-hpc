# Lithops-HPC and GekkoFS 

## Installation of GekkoFS in MN5
```bash
module unload impi
module unload openmpi/4.1.5-gcc12.3
module unload openmpi
module load impi/2021.13
module load oneapi/2024.2
module load cmake
module load gcc/12.3.0

export BASE=${HOME}/gekkofs_base
export GEKKODEPS=${BASE}/iodeps
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${GEKKODEPS}/lib64:${GEKKODEPS}/lib
export PATH=$PATH:${GEKKODEPS}/iodeps/bin

mkdir $BASE
cd $BASE

git clone https://storage.bsc.es/gitlab/hpc/gekkofs.git
cd gekkofs
git checkout master
git submodule update --init --recursive

# Download and install deps
cd scripts
./gkfs_dep.sh ${GEKKODEPS} ${GEKKODEPS}

# Compile gekkofs
cd ..
mkdir build
cd build

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=${GEKKODEPS} -DGKFS_BUILD_TESTS=OFF -DCMAKE_INSTALL_PREFIX=${GEKKODEPS} ..
make -j install
# nore, in mogon module load compiler/GCC/12.3.0 is needed and std::filesystem link in userlib and proxy also...
```

#### 2. Enable GKFS in LITHOPS_CONFIG_FILE
```yaml
name: lithops-hpc
version: 1.0.0
description: Serverless computing over HPC clusters using Lithops
author: Your Name
license: MIT
repository: https://github.com/youruser/lithops-hpc
```
