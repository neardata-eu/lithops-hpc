# Motif Detection GPU Pipeline

This project demonstrates a complete workflow to generate synthetic FASTA datasets, train a GPU-based motif detection model, and run inference on test data.

---

## Quick Start

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
export bucket_name=$(pwd)/data

mkdir -p $bucket_name

python fasta_generator.py --bucket_name $bucket_name --fasta_name training --num_seqs 100 --percentage_pos_seqs 0.6
python fasta_generator.py --bucket_name $bucket_name --fasta_name testing --num_seqs 100 --seed 1
python motifs_gpu_train.py --bucket_name $bucket_name --fasta_name training --chunk_size 20
python motifs-gpu-detect.py --bucket_name $bucket_name --fasta_name testing --chunk_size 20 --model_name training.model
```
---

## Overview

The pipeline consists of four main steps:

1. Set up the environment
2. Generate training and testing datasets
3. Train a GPU-based model
4. Run motif detection (inference)

---

## Prerequisites
- Python 3.11.9, torch 2.2.0, numpy 1.26.4
- GPU-CUDA support (recommended)

---

## Step 1: Setup Environment

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
export bucket_name=$(pwd)/data
```

---

## Step 2: Generate FASTA Datasets

### Training Dataset
```bash
python fasta_generator.py --bucket_name $bucket_name --fasta_name training --num_seqs 100 --percentage_pos_seqs 0.6
```

### Testing Dataset
```bash
python fasta_generator.py --bucket_name $bucket_name --fasta_name testing --num_seqs 100 --seed 1
```

---

## Step 3: Train the MOTIF Model

```bash
python motifs_train.py --bucket_name $bucket_name --fasta_name training --chunk_size 20
```

---

## Run Detection

```bash
python motifs_detect.py --bucket_name $bucket_name --fasta_name testing --chunk_size 20 --model_name training.model
```