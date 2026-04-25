import io
import torch
import numpy as np
import lithops
import argparse
import csv

import fasta_generator as fg
from CNN_model import MultiMotifCNN, one_hot_encode_seq, model_params
from hpc_data_connectors import set_device


# Check if GPU is available
#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#print(f"Using device: {device}")

@set_device(device="gpu", gpus=4)    
def loadModel(id,model_params):
  print(f"Using device: {device}")
  model = MultiMotifCNN(num_filters=model_params["num_filters"], motif_len=model_params["motif_len"]).to(device)
  model_data = storage.get_object(bucket, model_name)
  buffer = io.BytesIO(model_data)
  model.load_state_dict(torch.load(buffer, map_location=device,weights_only=True))
  print("Model loaded from Lithops storage")
  return model

@set_device(device="gpu", gpus=4)    
def chunk_prediction(id,chunk_key):
  from CNN_model import MultiMotifCNN, one_hot_encode_seq, model_params
  print(f"Using device: {device}")
  storage = lithops.Storage()
  fasta_chunk_str = storage.get_object(bucket, chunk_key).decode('utf-8')

  # one-hot encode sequeces
  X, y = [], []
  headers=[]
  seq_id,sequences =None, ""
  lines = fasta_chunk_str.strip().split('\n')
  for line in lines:
    if line.startswith('>'):
      if seq_id:
        X.append(one_hot_encode_seq(sequences, len(sequences)))
      sequences = ""
      seq_id = line[1:]
      headers.append(seq_id)
      y.append(float(line.strip(':')[-1]))    
    else:
      sequences=sequences+line
  
  if seq_id:
    X.append(one_hot_encode_seq(sequences, len(sequences)))
   
  # Make the predictions
  model=loadModel(id,model_params)
  model.eval()
  chunk_results = []
  for seq in X:
    tensor = torch.tensor(np.array(seq), dtype=torch.float32, device=device)
    with torch.no_grad():
      output = model(tensor)
    chunk_results.append(output.item())

  return dict(zip(headers,chunk_results))

def chunk_model_detect(storage,chunk_keys,threshold=0.51):
  fexec = lithops.FunctionExecutor()
  fexec.map(chunk_prediction, chunk_keys,include_modules=['CNN_model'])
  results = fexec.get_result()
  fexec.clean()

  #Saving the results as CSV file
  rows = [('id', 'score', 'prediction')]  # header
  for k, v in results[0].items():
    pred = v > threshold
    rows.append((k, v, pred))
  buffer = io.StringIO()
  writer = csv.writer(buffer)
  writer.writerows(rows)
  csv_data = buffer.getvalue().encode('utf-8')
  storage.put_object(bucket, fasta_key+"_results.csv", csv_data)
 
  print("Distributed testing complete!")



if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Generate random DNA sequences in fasta format")
  parser.add_argument("--bucket_name",type=str,required=True, help='bucket to save files in')
  parser.add_argument('--fasta_name',type=str, default='training_dna.fasta', help='fasta_key name')
  parser.add_argument("--chunk_size", type=int, required=False, default=500, help="Total sequences per chunk")
  parser.add_argument("--model_name", type=str, required=True, help="Model to load")
  
  args = parser.parse_args()
   
  bucket = args.bucket_name
  fasta_key = args.fasta_name
  target_seqs_per_chunk=args.chunk_size
  model_name=args.model_name

  storage = lithops.Storage()
    
  #1. Read FASTA Data  
  print("Splitting into chunks...")
  storage = lithops.Storage()
  chunk_keys = fg.save_fasta_chunks_to_storage(storage, bucket, fasta_key, target_seqs_per_chunk)
  print(f"{len(chunk_keys)} chunks stored.")
  #print(f"{chunk_keys}" )
  
  #2. Running Lithops jobs
  print("Running Lithops jobs...")
  storage = lithops.Storage()
  chunk_model_detect(storage,chunk_keys,model_params["threshold"])
