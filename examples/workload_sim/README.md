# Time Series Workload Simulator

This tool generates **synthetic workload time series** for training and testing systems that need realistic task arrival patterns.  
It supports **trends, daily/weekly seasonality, bursts, noise, and change points**, and outputs both CSV data and plots.

---

## Usage

```bash
python workload_from_yaml.py \
  --config config_training.yaml \
  --seed 42 \
  --csv workload.csv \
  --plot workload.png
```

Arguments:
- `--config` : Path to YAML config file.  
- `--seed`   : Random seed (default = 123).  
- `--csv`    : Output CSV file (default = `workload.csv`).  
- `--plot`   : Output PNG file (default = `workload.png`).  

---

## Config File Parameters

All simulation parameters are defined in a **YAML config file**.

### **Basic setup**
| Parameter  | Type  | Description |
|------------|-------|-------------|
| `start`    | str   | Start timestamp of the simulation (e.g., `"2025-01-01 00:00"`) |
| `periods`  | int   | Number of time steps to generate |
| `freq`     | str   | Frequency (`H`=hourly, `T`=minutely, `D`=daily, …) |

---

### **Baseline & Trend**
| Parameter        | Type  | Description |
|------------------|-------|-------------|
| `base_rate`      | float | Base expected workload before seasonality/noise |
| `trend_per_step` | float | Linear growth (+) or decay (−) per step |

---

### **Seasonality**
| Parameter          | Type  | Description |
|--------------------|-------|-------------|
| `daily_seasonality` | float | Amplitude of daily cycle (24h rhythm) |
| `weekly_seasonality`| float | Amplitude of weekly cycle (7-day rhythm) |

---

### **Noise & Correlation**
| Parameter   | Type  | Description |
|-------------|-------|-------------|
| `noise_std` | float | Standard deviation of random noise |
| `ar1_phi`   | float | AR(1) autocorrelation factor (0 = independent noise, 0.8 = strongly correlated) |

---

### **Bursts**
Under the `bursts:` section:
| Parameter     | Type  | Description |
|---------------|-------|-------------|
| `probability` | float | Probability of a burst starting at each step |
| `mean_duration` | int | Average burst length (in steps) |
| `intensity`   | float | Multiplier for workload during a burst |

---

### **Change Points**
A list of events where the workload level changes.

```yaml
change_points:
  - at: "2025-01-10"
    delta: 10
    multiplier: 1.2
```

- **`at`**: Timestamp of change  
- **`delta`**: Additive adjustment  
- **`multiplier`**: Multiplicative adjustment  

---

### **Other**
| Parameter  | Type  | Description |
|------------|-------|-------------|
| `min_rate` | float | Lower bound to prevent negative/near-zero rates |

---

## Output

The simulator generates a CSV file with:

| Column     | Description |
|------------|-------------|
| `timestamp` | Time index |
| `rate`     | Expected workload rate (integer, after trends, seasonality, bursts, etc.) |
| `tasks`    | Actual workload (integer Poisson random draw from `rate`) |

It also produces a PNG plot of both series with integer y-axis ticks.

---

## Example Configs

### Training (2 weeks of hourly data)
```yaml
start: "2025-01-01 00:00"
periods: 336  # 14 days * 24 hours
freq: "H"
base_rate: 20
trend_per_step: 0.05
daily_seasonality: 8
weekly_seasonality: 4
noise_std: 2
ar1_phi: 0.3
bursts:
  probability: 0.01
  mean_duration: 12
  intensity: 2.5
change_points:
  - at: "2025-01-07"
    delta: 5
    multiplier: 1.1
min_rate: 1
```

### Testing (2 hours of minute-level data)
```yaml
start: "2025-01-15 08:00"
periods: 120  # 2 hours * 60 minutes
freq: "T"
base_rate: 10
trend_per_step: 0
daily_seasonality: 2
weekly_seasonality: 0
noise_std: 1
ar1_phi: 0
bursts:
  probability: 0.0
  mean_duration: 0
  intensity: 1.0
change_points: []
min_rate: 1
```



