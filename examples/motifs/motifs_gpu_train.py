import argparse
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import lithops
import io

import fasta_generator as fg
from CNN_model import MultiMotifCNN, one_hot_encode_seq, model_params
from hpc_data_connectors import set_device

# Check if GPU is available
#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#print(f"Using device: {device}")

# 1. Training model for each fasta-chunk
@set_device(device="gpu", gpus=4)    
def chunk_model_training(id,chunk_key):
  print(f"Using device: {device}")
  storage = lithops.Storage()
  fasta_chunk_str = storage.get_object(bucket, chunk_key).decode('utf-8')

  # one-hot encode sequeces
  X, y = [], []
  seq_id,sequences =None, ""
  lines = fasta_chunk_str.strip().split('\n')
  for line in lines:
    if line.startswith('>'):
      if seq_id:
        X.append(one_hot_encode_seq(sequences, len(sequences)))
      sequences = ""
      seq_id = line[1:]
      y.append(float(line.strip(':')[-1]))    
    else:
      sequences=sequences+line
  
  if seq_id:
    X.append(one_hot_encode_seq(sequences, len(sequences)))
  
  #  model Training
  model = MultiMotifCNN(num_filters=model_params["num_filters"], motif_len=model_params["motif_len"]).to(device)
  X_batch = torch.tensor(np.array(X),dtype=torch.float32, device=device)
  y_batch = torch.tensor(np.array(y),dtype=torch.float32, device=device)
    
  optimizer = optim.Adam(model.parameters(), lr=model_params["lr"])
  criterion = nn.BCELoss()

  for epoch in range(model_params["epochs"]):
    model.train()
    optimizer.zero_grad()
    preds = model(X_batch)
    loss = criterion(preds.squeeze(), y_batch)
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch+1} - Loss: {loss.item():.4f}")
    
  return model.get_weights()

# 2. Lithops Reduce Function
def reduce_models(results):
  # Stack weights from all workers
  conv_weights = np.stack([w[0] for w in results])
  conv_biases = np.stack([w[1] for w in results])
  fc_weights = np.stack([w[2] for w in results])
  fc_biases = np.stack([w[3] for w in results])
    
  # Average weights
  avg_weights = [
    np.mean(conv_weights, axis=0),
    np.mean(conv_biases, axis=0),
    np.mean(fc_weights, axis=0),
    np.mean(fc_biases, axis=0)
  ]
  return avg_weights

# 3. Main function to prepare batches, 
def run_cnn_motif_with_lithops(storage,chunk_keys):
  
  # Run Lithops tasks for training CNN models on different batches
  fexec = lithops.FunctionExecutor()
  fexec.map_reduce(chunk_model_training, chunk_keys, reduce_models)
  avg_weights = fexec.get_result()
  fexec.clean()

  # Create global model
  global_model = MultiMotifCNN(num_filters=model_params["num_filters"], motif_len=model_params["motif_len"])
  global_model.set_weights(avg_weights)

  # Save the model in storage
  buffer = io.BytesIO()
  torch.save(global_model.state_dict(), buffer)
  buffer.seek(0)
  storage.put_object(bucket,fasta_key+".model", buffer.read())
  
  print("Distributed training complete!")

#4. Main: Run the Full Workflow
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Generate random DNA sequences in fasta format")
  parser.add_argument("--bucket_name",type=str,required=True, help='bucket to save files in')
  parser.add_argument('--fasta_name',type=str, default='training_dna.fasta', help='fasta_key name')
  parser.add_argument("--chunk_size", type=int, required=False, default=500, help="Total sequences per chunk")

  args = parser.parse_args()
   
  bucket = args.bucket_name
  fasta_key = args.fasta_name
  target_seqs_per_chunk=args.chunk_size
  
  print("Splitting into chunks...")
  storage = lithops.Storage()
  chunk_keys = fg.save_fasta_chunks_to_storage(storage, bucket, fasta_key, target_seqs_per_chunk)
  print(f"{len(chunk_keys)} chunks stored.")
  print(f"{chunk_keys}" )

  print("Running Lithops jobs...")
  storage = lithops.Storage()
  run_cnn_motif_with_lithops(storage,chunk_keys)
