from collections import defaultdict

class Metrics:
    def __init__(self, print_frequency=1000, keep_history=True):
        self.print_frequency = print_frequency
        self.keep_history = keep_history
        self.history = []  # list of dict snapshots

        # window counters
        self.window_rounds = 0
        self.window_attempted_blocks = 0
        self.window_confirmed_blocks = 0
        self.window_rewards_distributed = 0.0
        self.window_migrations_executed = 0
        self.window_gained = defaultdict(int)  # validator_id -> count
        self.window_lost = defaultdict(int) # validator_id -> count
        self._prev_overall_rewards = {}  # validator_id -> last seen overall_rewards

    def on_round_start(self):
        self.window_rounds += 1

    def on_block_attempt(self):
        self.window_attempted_blocks += 1

    def on_block_confirmed(self):
        self.window_confirmed_blocks += 1

    def on_rewards_distributed(self, amount):
        self.window_rewards_distributed += amount

    def on_migrations_executed(self, executed_pairs):
        self.window_migrations_executed += len(executed_pairs)
        for old, new in executed_pairs:
            if old is not None:
                self.window_lost[old.id] += 1
            if new is not None:
                self.window_gained[new.id] += 1

    def snapshot(self, world, round_index):
        validators = world.validators
        total_vp = sum(v.voting_power for v in validators)
        all_top_vp = self._top_voting_power(world.validators, total_vp, k=10)

        def top_k(d, k):
            return sorted(d.items(), key=lambda x: x[1], reverse=True)[:k]

        pending = len(world.pending_migrations)

        # window rates
        if self.window_attempted_blocks > 0:
            confirm_rate = self.window_confirmed_blocks / self.window_attempted_blocks
        else:
            confirm_rate = 0.0

        # delegators flow info
        top_gainers = top_k(self.window_gained, 5)
        top_losers = top_k(self.window_lost, 5)

        # migration rate
        migration_rate = self.window_migrations_executed / len(world.delegators)

        # rewards
        reward_delta_by_id = self._compute_window_reward_deltas(world.validators)

        # pools stats
        pool_stats = self._build_pool_stats(world, reward_delta_by_id)

        snap = {
            "round": round_index,
            "total_voting_power": total_vp,
            "all_top_vp": all_top_vp,
            "pending_migrations": pending,
            "window_confirm_rate": confirm_rate,
            "window_rewards": self.window_rewards_distributed,
            "window_migrations_executed": self.window_migrations_executed,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "migration_rate" : migration_rate,
            "reward_delta_by_id" : reward_delta_by_id,
            "pool_stats": pool_stats
        }

        if self.keep_history:
            self.history.append(snap)

        return snap

    def report_if_needed(self, world, round_index):
        if round_index % self.print_frequency != 0:
            return
        pool_ids = {v.id for v in world.pools()}
        snap = self.snapshot(world, round_index)

        pool_stats = snap["pool_stats"]

        pools_top10_apr = sorted(pool_stats.items(), key=lambda x: x[1]["apr"], reverse=True)[:10]
        pools_top10_delegators = sorted(pool_stats.items(), key=lambda x: x[1]["delegators"], reverse=True)[:10]
        pools_top10_rewards = sorted(pool_stats.items(), key=lambda x: x[1]["reward_delta"], reverse=True)[:10]
        pools_top10_vp = sorted(pool_stats.items(), key=lambda x: x[1]["voting_power"], reverse=True)[:10]
        pools_top10_net_flow = sorted(pool_stats.items(), key=lambda x: x[1]["net_flow"], reverse=True)[:10]

        print("=== METRICS ===")
        print(f"Round: {snap['round']}")
        print(f"Total VP: {snap['total_voting_power']:.6f}")
        print(f"Top VP share (all): ", ", ".join([f"{vid}:{vp:.3f}" for vid, vp in snap["all_top_vp"]]))
        print(f"Pending migrations: {snap['pending_migrations']}")
        print(f"Confirm rate (last window): {snap['window_confirm_rate']:.3f}")
        print(f"Rewards distributed (last window): {snap['window_rewards']:.6f}")
        print(f"Migrations executed (last window): {snap['window_migrations_executed']}")
        print(f"Top validator gains in terms of delegators (last window): {snap['top_gainers']}")
        print(f"Top validator losses in terms of delegators (last window): {snap['top_losers']}")
        print(f"Migration rate: {snap['migration_rate']}")
        print(f"Top10 window rewards (all):  ",  ", ".join([f"{vid}:{amt:.6f}" for vid, amt in sorted(snap["reward_delta_by_id"].items(), key=lambda x: x[1], reverse=True)[:10]]))
        print(f"Top10 window rewards (pools):  ",  ", ".join([f"{vid}:{amt:.6f}" for vid, amt in sorted([(vid, delta) for vid, delta in snap["reward_delta_by_id"].items() if vid in pool_ids], key=lambda x: x[1], reverse=True)[:10]]))
        # pools stats
        print("Top10 APR (pools):", ", ".join([f"{pid}:{st['apr']:.6f}" for pid, st in pools_top10_apr]))
        print("Top10 VP (pools):", ", ".join([f"{pid}:{st['voting_power']:.3f}" for pid, st in pools_top10_vp]))
        print("Top10 reward delta (pools):",
              ", ".join([f"{pid}:{st['reward_delta']:.6f}" for pid, st in pools_top10_rewards]))
        print("Top10 delegators (pools):", ", ".join([f"{pid}:{st['delegators']}" for pid, st in pools_top10_delegators]))
        print("Top10 net flow (pools):", ", ".join([f"{pid}:{st['net_flow']}" for pid, st in pools_top10_net_flow]))

        print("===============")

        # reset window counters
        self.window_rounds = 0
        self.window_attempted_blocks = 0
        self.window_confirmed_blocks = 0
        self.window_rewards_distributed = 0.0
        self.window_migrations_executed = 0
        self.window_gained.clear()
        self.window_lost.clear()

    def _build_pool_stats(self, world, reward_delta_by_id):
        pool_stats = {}
        for v in world.pools():
            vp = v.voting_power
            pool_stats[v.id] = {
                "apr": round(v.apr, 5),
                "voting_power": vp,
                "delegators": v.dcount,
                "reward_delta": reward_delta_by_id.get(v.id, 0.0),
                "gained": self.window_gained.get(v.id, 0),
                "lost": self.window_lost.get(v.id, 0),
            }
            pool_stats[v.id]["net_flow"] = pool_stats[v.id]["gained"] - pool_stats[v.id]["lost"]
        return pool_stats

    def _top_voting_power(self, validators, total,  k):
        if k > len(validators):
            raise ValueError("k must be <= than number of validators.")
        if total <= 0:
            return []
        ranked = sorted(validators, key=lambda v: v.voting_power, reverse=True)[:k]
        return [(v.id, v.voting_power / total) for v in ranked]

    def _compute_window_reward_deltas(self, validators):
        deltas = {}
        for v in validators:
            prev = self._prev_overall_rewards.get(v.id, 0.0)
            cur = v.overall_rewards
            deltas[v.id] = cur - prev
            self._prev_overall_rewards[v.id] = cur
        return deltas
