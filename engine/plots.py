import matplotlib.pyplot as plt
import os

def _get_series(history, pool_ids, key):
    """
    history: list of snapshots (dicts)
    pool_ids: list[int]
    key: one of "apr", "voting_power", "delegators", "reward_delta", "net_flow"
    Returns: rounds(list), data(dict pool_id -> list)
    """
    rounds = []
    data = {pid: [] for pid in pool_ids}

    for snap in history:
        rounds.append(snap["round"])
        stats = snap["pool_stats"]  # dict pool_id -> dict

        for pid in pool_ids:
            if pid in stats:
                data[pid].append(stats[pid].get(key, 0.0))
            else:
                data[pid].append(0.0)

    return rounds, data

def store_pool_stats_plot(history, pool_ids, key, title, ylabel, folder, filename):
    rounds, data = _get_series(history, pool_ids, key)

    plt.figure()
    all_vals = []

    for pid in pool_ids:
        series = data[pid]
        plt.plot(rounds, series, label=str(pid))
        all_vals.extend(series)

    plt.xlabel("round")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(title="pool id", ncol=2, fontsize="small")

    ax = plt.gca()
    ax.ticklabel_format(style='plain', useOffset=False, axis='y')

    # auto-zoom
    if all_vals:
        y_min = min(all_vals)
        y_max = max(all_vals)
        pad = 0.05 * (y_max - y_min + 1e-12)  # small padding
        plt.ylim(y_min - pad, y_max + pad)

    plt.tight_layout()
    out_path = os.path.join(folder, filename)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()

def store_pool_netflow_bars_plots(history, pool_ids, folder, title="Net delegator flow per window"):
    rounds, data = _get_series(history, pool_ids, "net_flow")

    # bar plot: one figure per pool (cleanest), or overlay if few pools
    for pid in pool_ids:
        plt.figure()
        plt.bar(rounds, data[pid])
        plt.xlabel("round")
        plt.ylabel("net flow (gained - lost)")
        plt.title(f"{title} (pool {pid})")
        plt.tight_layout()
        out_path = os.path.join(folder, f"netflow_pool_{pid}.png")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        plt.savefig(out_path, dpi=150)
        plt.close()

# def choose_top_pools_by(history, key, k=10):
#     """
#     Choose pools based on the last snapshot's pool_stats by a key (e.g., "voting_power", "apr").
#     """
#     last = history[-1]["pool_stats"]
#     ranked = sorted(last.items(), key=lambda x: x[1].get(key, 0.0), reverse=True)
#     return [pid for pid, _stats in ranked[:k]]