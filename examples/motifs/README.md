# Motif Detection GPU Pipeline

This project demonstrates a complete workflow to generate synthetic FASTA datasets, train a GPU-based motif detection model, and run inference on test data.

---

## 📋 Overview

The pipeline consists of four main steps:

1. Set up the environment
2. Generate training and testing datasets
3. Train a GPU-based model
4. Run motif detection (inference)

---

## ⚙️ Prerequisites

- Python 3.x
- Required Python dependencies
- GPU support (recommended)
- CUDA properly configured (if using GPU)

---

## 🧩 Project Structure

.
├── fasta_generator.py
├── motifs_gpu_train.py
├── motifs-gpu-detect.py
├── data/
└── README.md

---

## 🔧 Step 1: Setup Environment

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
export bucket_name=$(pwd)/data
```

---

## 📁 Step 2: Generate FASTA Datasets

### Training Dataset
```bash
python fasta_generator.py --bucket_name $bucket_name --fasta_name training --num_seqs 100 --percentage_pos_seqs 0.6
```

### Testing Dataset
```bash
python fasta_generator.py --bucket_name $bucket_name --fasta_name testing --num_seqs 100 --seed 1
```

---

## 🧠 Step 3: Train the GPU Model

```bash
python motifs_gpu_train.py --bucket_name $bucket_name --fasta_name training --chunk_size 20
```

---

## 🔍 Step 4: Run Detection

```bash
python motifs-gpu-detect.py --bucket_name $bucket_name --fasta_name testing --chunk_size 20 --model_name training.model
```

---

## 🚀 Full Workflow

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
export bucket_name=$(pwd)/data

mkdir -p $bucket_name

python fasta_generator.py --bucket_name $bucket_name --fasta_name training --num_seqs 100 --percentage_pos_seqs 0.6
python fasta_generator.py --bucket_name $bucket_name --fasta_name testing --num_seqs 100 --seed 1
python motifs_gpu_train.py --bucket_name $bucket_name --fasta_name training --chunk_size 20
python motifs-gpu-detect.py --bucket_name $bucket_name --fasta_name testing --chunk_size 20 --model_name training.model
```

