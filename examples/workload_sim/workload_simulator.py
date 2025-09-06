import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from dataclasses import dataclass, field
from typing import List, Optional
import argparse

# --------------------------
# Simulator definitions
# --------------------------
@dataclass
class BurstSpec:
    probability: float = 0.01
    mean_duration: int = 24
    intensity: float = 3.0

@dataclass
class ChangePoint:
    at: str
    delta: float = 0.0
    multiplier: float = 1.0

@dataclass
class WorkloadConfig:
    start: str = "2025-01-01"
    periods: int = 24*14
    freq: str = "H"
    base_rate: float = 20.0
    trend_per_step: float = 0.0
    daily_seasonality: float = 8.0
    weekly_seasonality: float = 4.0
    noise_std: float = 2.0
    ar1_phi: float = 0.0
    bursts: Optional[BurstSpec] = field(default_factory=BurstSpec)
    change_points: List[ChangePoint] = field(default_factory=list)
    min_rate: float = 0.1

# --------------------------
# Helper functions
# --------------------------

def _seasonal_terms(index: pd.DatetimeIndex, daily_amp: float, weekly_amp: float) -> np.ndarray:
    t = np.arange(len(index))
    daily = daily_amp * np.sin(2*np.pi*(t % 24)/24.0)
    weekly = weekly_amp * np.sin(2*np.pi*(t % (24*7))/(24.0*7.0))
    return daily + weekly

def _apply_change_points(index: pd.DatetimeIndex, base: np.ndarray, cps: List[ChangePoint]) -> np.ndarray:
    if not cps:
        return base
    adjusted = base.copy()
    for cp in sorted(cps, key=lambda c: pd.Timestamp(c.at)):
        mask = index >= pd.Timestamp(cp.at)
        adjusted[mask] = (adjusted[mask] + cp.delta) * cp.multiplier
    return adjusted

def _simulate_bursts(n: int, probability: float, mean_duration: int, rng: np.random.Generator) -> np.ndarray:
    state = 0
    on = np.zeros(n, dtype=bool)
    p_end = 1.0 / max(1, mean_duration)
    for i in range(n):
        if state == 0:
            if rng.random() < probability:
                state = 1
        else:
            on[i] = True
            if rng.random() < p_end:
                state = 0
    return on

def simulate_workload(cfg: WorkloadConfig, seed: Optional[int] = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start=cfg.start, periods=cfg.periods, freq=cfg.freq)
    n = len(idx)

    # baseline + trend
    base = cfg.base_rate + cfg.trend_per_step * np.arange(n)

    # add seasonality
    lam = base + _seasonal_terms(idx, cfg.daily_seasonality, cfg.weekly_seasonality)

    # apply change points
    lam = _apply_change_points(idx, lam, cfg.change_points)

    # bursts
    if cfg.bursts and cfg.bursts.probability > 0:
        burst_mask = _simulate_bursts(n, cfg.bursts.probability, cfg.bursts.mean_duration, rng)
        lam = np.where(burst_mask, lam * cfg.bursts.intensity, lam)

    # noise
    if cfg.ar1_phi != 0:
        eps = rng.normal(0, cfg.noise_std, size=n)
        ar = np.zeros(n)
        for i in range(1, n):
            ar[i] = cfg.ar1_phi * ar[i-1] + eps[i]
        lam = lam + ar
    else:
        lam = lam + rng.normal(0, cfg.noise_std, size=n)

    lam = np.clip(lam, cfg.min_rate, None)

    # ensure integer rate
    lam_int = np.rint(lam).astype(int)

    # simulate integer tasks
    tasks = rng.poisson(lam_int)

    return pd.DataFrame({"timestamp": idx, "rate": lam_int, "tasks": tasks}).set_index("timestamp")

# --------------------------
# Config loader
# --------------------------

def load_config_from_yaml(path: str) -> WorkloadConfig:
    with open(path, "r") as f:
        cfg_dict = yaml.safe_load(f)

    bursts_cfg = cfg_dict.get("bursts", {})
    bursts = BurstSpec(**bursts_cfg) if bursts_cfg else None

    cps_cfg = cfg_dict.get("change_points", [])
    change_points = [ChangePoint(**cp) for cp in cps_cfg]

    return WorkloadConfig(
        start=cfg_dict.get("start", "2025-01-01"),
        periods=cfg_dict.get("periods", 24*14),
        freq=cfg_dict.get("freq", "H"),
        base_rate=cfg_dict.get("base_rate", 20.0),
        trend_per_step=cfg_dict.get("trend_per_step", 0.0),
        daily_seasonality=cfg_dict.get("daily_seasonality", 8.0),
        weekly_seasonality=cfg_dict.get("weekly_seasonality", 4.0),
        noise_std=cfg_dict.get("noise_std", 2.0),
        ar1_phi=cfg_dict.get("ar1_phi", 0.0),
        bursts=bursts,
        change_points=change_points,
        min_rate=cfg_dict.get("min_rate", 0.1),
    )

# --------------------------
# Main CLI
# --------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Time Series Workload Simulator")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--seed", type=int, default=123, help="Random seed")
    parser.add_argument("--csv", default="workload.csv", help="Output CSV filename")
    parser.add_argument("--plot", default="workload.png", help="Output PNG plot filename")
    args = parser.parse_args()

    cfg = load_config_from_yaml(args.config)
    df = simulate_workload(cfg, seed=args.seed)

    df.to_csv(args.csv)
    print(f"Saved {args.csv}")

    # plot both rate and tasks (with integer y-axis)
    plt.figure(figsize=(10,4))
    #plt.plot(df.index, df["rate"], label="rate (int)", linestyle="--")
    plt.plot(df.index, df["tasks"], label="Tasks", alpha=0.7)
    #plt.title(f"Workload from {args.config}")
    plt.xlabel("Timestamp",fontdict={'family': 'Times New Roman', 'fontsize': 12})
    plt.ylabel("Tasks",fontdict={'family': 'Times New Roman', 'fontsize': 12})
    plt.legend(
        prop={'family': 'Times New Roman', 'size': 12},  # font for legend
        title_fontproperties={'family': 'Times New Roman', 'size': 12}  # font for legend title
        )
    plt.grid()
    # enforce integer ticks on y-axis
    ax = plt.gca()
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    plt.tight_layout()
    plt.savefig(args.plot, dpi=300)
    print(f"Saved {args.plot}")
    plt.show(block=True)
