import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

# Set model parameters
model_params = {
  "num_filters": 32,
  "motif_len": 6,
  "epochs": 200,
  "lr": 0.001,
  "threshold":0.51
}

# 1. one-hot encode 
def one_hot_encode_seq(seq, max_len=200):
  mapping = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
  encoded = np.zeros((4, max_len))  
  for i, base in enumerate(seq):
    if base in mapping and i < max_len:
      encoded[mapping[base], i] = 1
    #If base is 'N', leave the position as zeros
  return encoded

# 2. CNN Model for Motif Detection
class MultiMotifCNN(nn.Module):
  def __init__(self, num_filters=10, motif_len=6):
    super().__init__()
    self.conv = nn.Conv1d(in_channels=4, out_channels=num_filters, kernel_size=motif_len)
    self.relu = nn.ReLU()
    self.pool = nn.AdaptiveMaxPool1d(1)
    self.fc = nn.Linear(num_filters, 1)
        
  def forward(self, x):
    #x = x.permute(0, 2, 1)  # (batch, 4, seq_len)
    x = self.conv(x)         # (batch, num_filters, seq_len - motif_len + 1)
    x = self.relu(x)
    x = self.pool(x).squeeze(-1)  # (batch, num_filters)
    return torch.sigmoid(self.fc(x))
    
  def get_weights(self):
    return [
      self.conv.weight.data.cpu().numpy(),
      self.conv.bias.data.cpu().numpy(),
      self.fc.weight.data.cpu().numpy(),
      self.fc.bias.data.cpu().numpy()
    ]
    
  def set_weights(self, weights):
    with torch.no_grad():
      self.conv.weight.data = torch.from_numpy(weights[0])
      self.conv.bias.data = torch.from_numpy(weights[1])
      self.fc.weight.data = torch.from_numpy(weights[2])
      self.fc.bias.data = torch.from_numpy(weights[3])