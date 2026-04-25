# Motif Detection GPU Workflow

This guide explains how to generate FASTA datasets, train a GPU-based motif detection model, and run inference using the trained model.

---

## ⚙️ Setup Environment

Before running the scripts, set the required environment variables:

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
export bucket_name=$(pwd)/data
