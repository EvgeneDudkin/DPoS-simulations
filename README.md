# DPoS Attack Simulations

## Introduction

This repository contains the simulation framework developed for a Master's thesis on **staking pool attack profitability in Delegated Proof-of-Stake (DPoS) liquid staking markets**.

The central research question is: *Can Byzantine attacks that are individually unprofitable become profitable when their side effects are accounted for?*

The hypothesis is that attacks targeting a competitor's staking pool degrade that pool's reliability score and APR, which triggers rational delegators to migrate their stake away from the victim. If an allied pool captures those migrating delegators, the combined economic gain (ally's extra rewards) can outweigh the attacker's cost — making the attack net profitable for the coordinated entity.

The framework is an **agent-based model (ABM)** built around two attack types:

- **Vote Omission**: the Byzantine proposer filters the victim validator's signature out of the block, denying it rewards and dropping its uptime score.
- **Vote Delay**: the Byzantine validator withholds its vote when the victim is the proposer, reducing the victim's leader reward-bonus 

Both attacks are modeled against two protocol configurations — **Cosmos** and **Ethereum** (with Lido and Rocket Pool commission structures) — and results are compared against analytical formulas from Baloochestani & Jehl (2025).

---

## Getting Started

### Prerequisites

| Tool | Version / Notes |
|------|----------------|
| Python | 3.13.9 or higher |
| pip | bundled with Python |
| Git | any recent version |
| VS Code | recommended (1.119+) |

**Python packages** (installed via pip — see Installation):

- `matplotlib` — plot generation
- No other third-party dependencies; the simulation uses only the Python standard library (`random`, `math`, `os`, `time`)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/EvgeneDudkin/DPoS-simulations.git
   cd DPoS-simulations
   ```

2. **Create and activate a virtual environment** (recommended)

   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install matplotlib
   ```

4. **Create the output directory** (the simulation writes plots here)

   ```bash
   mkdir out
   ```

---

## Build and Test

### Running the simulation

The entry point is `main.py`. It runs a **baseline** simulation (no attack) followed by an **attack** simulation, then computes and prints effectiveness and cost metrics.

```bash
python main.py
```

Output is printed to the console and plots are saved to `out/baseline/` and `out/attack/`.

### Configuring a run

Open `main.py` and edit the parameters near the bottom of the file:

```python
# Switch between Cosmos and Ethereum protocol
setup = get_cosmos_setup_with_proposer_bonus(online_p=1, vote_p=1)
# setup = get_eth_lido_setup(online_p=1, vote_p=1)

# Attacker and victim voting power fractions
v_pow = [0.005]   # victim pool stake
b_pow = [0.3]     # Byzantine attacker stake

# Enable/disable attacks
vote_omission_attack_on = True
vote_delay_attack_on    = False

# Delegator behavior
loyalty           = 0.8    # inertia (0 = always migrate, 1 = never migrate)
pull_prob         = 0.03   # star-chasing probability per round
```

Other parameters (market-related parameters, world configuration, competetive pools configuration and many others) can also be changed / modified / adjusted. For that the knowldege about the system and framework inderstanding is needed.

### Generated outputs

| File | Description |
|------|-------------|
| `out/{run}/apr_over_time.png` | Pool gross APR over time |
| `out/{run}/vp_share_over_time.png` | Voting power / market share evolution |
| `out/{run}/delegators_over_time.png` | Delegator count per pool |
| `out/{run}/score_over_time.png` | Pool uptime/reliability score |
| `out/{run}/netflow/netflow_pool_<id>.png` | Net delegator flow per reporting window |

---

## Contribute

Contributions, extensions, and follow-up research are welcome. To contribute:

1. **Fork** the repository on GitHub and clone your fork locally.
2. Create a **feature branch** from `master`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes and commit them with a descriptive message.
4. **Open a pull request** against `master` with a clear description of what was changed and why.

### Code structure overview

```
agents/      — Validator, Delegator, Byzantine (agent logic)
engine/      — Protocol loop, World state, Initializer, Metrics, Plots
setups/      — Pluggable strategies: committee, proposer, vote, reward policies
model/       — Block and Committee data structures
main.py      — Entry point and protocol configuration functions
docs/        — Architecture / design / docs 
```
