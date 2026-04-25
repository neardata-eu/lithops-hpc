import random
import lithops
import argparse

# 1. Generate Random FASTA Data
def generate_random_fasta(num_seqs=5000, seq_len=200, motif="TATAAA", seed=0 , percentage_pos_seqs=0.5):
  random.seed(seed)  
  bases = ['A', 'C', 'G', 'T']
  total_pos_seqs=int(num_seqs*percentage_pos_seqs)
  pos_seq=random.sample(range(num_seqs), total_pos_seqs)
  labels,lines = [],[]
  for i in range(num_seqs):
    label=0
    sequence = ''.join(random.choices(bases, k=seq_len))
    if i in pos_seq:
      pos = random.randint(0, seq_len - len(motif))
      sequence = sequence[:pos] + motif + sequence[pos+len(motif):]
      label=1
    header = f">seq_{i}:{label}"
    lines.append(header)
    lines.append(sequence)
    labels.append(str(label))
  return '\n'.join(labels),'\n'.join(lines)

# 2. Upload FASTA to Storage
def upload_test_fasta_file(bucket, key, num_seqs=5000, seq_len=200, seed=0, percentage_pos_seqs=0.5):
    storage = lithops.Storage()
    labels,fasta_content = generate_random_fasta(num_seqs, seq_len, seed=seed,percentage_pos_seqs=percentage_pos_seqs)
    storage.put_object(bucket, key+".fasta", fasta_content.encode('utf-8'))
    storage.put_object(bucket, key+".labels", labels.encode('utf-8'))

# 3. Split FASTA by Number of Sequences
def save_fasta_chunks_to_storage(storage, bucket, key, target_seqs_per_chunk=500):
    fasta_str = storage.get_object(bucket, key+".fasta").decode('utf-8')
    lines = fasta_str.strip().split('\n')

    chunk_keys = []
    current_chunk = []
    seq_count = 0
    chunk_id = 0

    for line in lines:
        if line.startswith('>'):
            if seq_count >= target_seqs_per_chunk:
                chunk_data = '\n'.join(current_chunk).encode('utf-8')
                chunk_key = f'chunks/{key}_chunk{chunk_id}.fasta'
                storage.put_object(bucket, chunk_key, chunk_data)
                chunk_keys.append(chunk_key)
                chunk_id += 1
                current_chunk = []
                seq_count = 0
            seq_count += 1
        current_chunk.append(line)

    if current_chunk:
        chunk_data = '\n'.join(current_chunk).encode('utf-8')
        chunk_key = f'chunks/{key}_chunk{chunk_id}.fasta'
        storage.put_object(bucket, chunk_key, chunk_data)
        chunk_keys.append(chunk_key)

    return chunk_keys

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Generate random DNA sequences in fasta format")
  parser.add_argument("--bucket_name",type=str,required=True, help='bucket to save files in')
  parser.add_argument('--fasta_name',type=str, default='training_dna.fasta', help='fasta_key name')
  parser.add_argument("--num_seqs", type=int, required=False, default=5000, help="Number of sequences to generate")
  parser.add_argument("--seq_len", type=int, required=False, default=200, help="Sequence lenght")
  parser.add_argument("--seed", type=int, required=False, default=0, help="Random seed generator")
  parser.add_argument("--percentage_pos_seqs", type=float, required=False, default=0.5, help="Percentage of positive sequences")

  args = parser.parse_args()
   
  bucket = args.bucket_name
  fasta_key = args.fasta_name
  num_seqs=args.num_seqs
  seq_len=args.seq_len
  seed=args.seed
  percentage_pos_seqs=args.percentage_pos_seqs

  upload_test_fasta_file(bucket, fasta_key, num_seqs, seq_len, seed, percentage_pos_seqs)