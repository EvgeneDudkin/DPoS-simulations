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
        pool_top_vp = self._top_voting_power(world.pools(), total_vp, k=10)

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

        snap = {
            "round": round_index,
            "total_voting_power": total_vp,
            "all_top_vp": all_top_vp,
            "pool_top_vp" : pool_top_vp,
            "pending_migrations": pending,
            "window_confirm_rate": confirm_rate,
            "window_rewards": self.window_rewards_distributed,
            "window_migrations_executed": self.window_migrations_executed,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "migration_rate" : migration_rate,
            "reward_delta_by_id" : reward_delta_by_id,
            "pools_apr" : [(v.id, v.apr) for v in world.pools()]
        }

        if self.keep_history:
            self.history.append(snap)

        return snap

    def report_if_needed(self, world, round_index):
        if round_index % self.print_frequency != 0:
            return
        pool_ids = {v.id for v in world.pools()}
        snap = self.snapshot(world, round_index)

        print("=== METRICS ===")
        print(f"Round: {snap['round']}")
        print(f"Total VP: {snap['total_voting_power']:.6f}")
        print(f"Top VP share (all): ", ", ".join([f"{vid}:{vp:.3f}" for vid, vp in snap["all_top_vp"]]))
        print(f"Top VP share (pools): ", ", ".join([f"{vid}:{vp:.3f}" for vid, vp in snap["pool_top_vp"]]))
        print(f"Pending migrations: {snap['pending_migrations']}")
        print(f"Confirm rate (last window): {snap['window_confirm_rate']:.3f}")
        print(f"Rewards distributed (last window): {snap['window_rewards']:.6f}")
        print(f"Migrations executed (last window): {snap['window_migrations_executed']}")
        print(f"Top validator gains in terms of delegators (last window): {snap['top_gainers']}")
        print(f"Top validator losses in terms of delegators (last window): {snap['top_losers']}")
        print(f"Migration rate: {snap['migration_rate']}")
        print(f"Top10 window rewards (all):  ",  ", ".join([f"{vid}:{amt:.6f}" for vid, amt in sorted(snap["reward_delta_by_id"].items(), key=lambda x: x[1], reverse=True)[:10]]))
        print(f"Top10 window rewards (pools):  ",  ", ".join([f"{vid}:{amt:.6f}" for vid, amt in sorted([(vid, delta) for vid, delta in snap["reward_delta_by_id"].items() if vid in pool_ids], key=lambda x: x[1], reverse=True)[:10]]))
        print(f"Top10 APRs (pools):  ",  ", ".join([f"{vid}:{apr:.6f}" for vid, apr in sorted(snap["pools_apr"], key=lambda x: x[1], reverse=True)[:10]]))

        print("===============")

        # reset window counters
        self.window_rounds = 0
        self.window_attempted_blocks = 0
        self.window_confirmed_blocks = 0
        self.window_rewards_distributed = 0.0
        self.window_migrations_executed = 0
        self.window_gained.clear()
        self.window_lost.clear()

    def _top_pools_by_apr(self, world, k=10):
        pools = world.pools()
        ranked = sorted(pools, key=lambda v: getattr(v, "apr", 0.0), reverse=True)[:k]
        return [(v.id, v.apr) for v in ranked]

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
