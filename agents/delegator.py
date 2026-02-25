import random
import math

class Delegator:
    def __init__ (self , id , stake, aggressiveness = 1, loyalty = 0, apr_gap_threshold = 0.0035, streak_required = 1500,
                 pull_prob = 0.0, star_gap_multiplier = 3.0):
        self.id = id
        self.stake = stake
        self.bounded_validator = None
        self.total_reward = 0
        self.aggressiveness = aggressiveness #Describes how aggressive delegators are in terms of selecting the best validator.
        self.loyalty = loyalty #Describes delegators loyalty. Should be between 0 and 1. Bigger loyalty indicates that the delegator changes the validator less often.
        self.apr_gap_threshold = apr_gap_threshold
        self.streak_required = streak_required # number of 'underperforming' rounds in a row before considering the 'switch'/migration
        self.dissatisfied_streak = 0
        # Asymmetric flow-performance (Sirri & Tufano 1998):
        # pull_prob: per-round probability of opportunistically chasing a star pool
        # star_gap_multiplier: star_threshold = apr_gap_threshold * this factor
        self.pull_prob = pull_prob
        self.star_gap_multiplier = star_gap_multiplier

    def expected_earning(self, pool, reward):
        total_voting_power = sum(v.voting_power for v in pool)
        validator_share = (self.bounded_validator.voting_power / total_voting_power) * reward
        delegator_share = (self.stake / self.bounded_validator.voting_power) * validator_share
        return delegator_share

    def update_reward(self, reward):
        self.total_reward += reward

    def choose_validator_by_apr(self, pool):
        """
        Choose based on APR:
        - stay unless best APR exceeds current APR by more than threshold
        - even if dissatisfied, switch only with probability (1 - loyalty)
        - when switching, choose among pools weighted by APR^aggressiveness
        """
        # If not delegated yet, pick a pool biased by APR
        if self.bounded_validator is None:
            return self._pick_logit(pool, current=None)

        current = self.bounded_validator
        current_apr = current.apr

        # Find the best APR pool
        best = max(pool, key=lambda v: v.apr)
        best_apr = best.apr
        gap = best_apr - current_apr

        # PATH 1 — PULL: fast attraction to star performers.
        # Fires probabilistically each round when a large gap exists.
        # Models the convex upper tail of flow-performance relationship
        # (Sirri & Tufano 1998: top performers attract disproportionate inflows).
        if self.pull_prob > 0.0:
            star_threshold = self.apr_gap_threshold * self.star_gap_multiplier
            if gap > star_threshold and random.random() < self.pull_prob:
                return self._pick_logit(pool, current=current)

        # PATH 2 — PUSH: slow flee of underperformer.
        if gap > self.apr_gap_threshold:
            self.dissatisfied_streak += 1
        else:
            self.dissatisfied_streak = 0
            return current

        #  not enough rounds
        if self.dissatisfied_streak < self.streak_required:
            return current

        # Inertia: not everyone switches immediately
        if random.random() < self.loyalty:
            return current

        # Switch, but not always deterministically to the best
        return self._pick_logit(pool, current=current)

    def _pick_logit(self, pool, current=None):
        # utility = apr; can be extended further: apr - fee - risk - switching_cost
        # added switching_cost for race with small profit
        eps = 1e-12
        beta = max(1e-6, float(self.aggressiveness))

        # switching_cost: more stake - more expensive to switch
        switching_cost = 0.0005 * (1.0 + 0.5 * math.log1p(self.stake * 1e4))

        utilities = []
        for v in pool:
            u = max(v.apr, 0.0)
            if current is not None and v != current:
                u -= switching_cost
            utilities.append(u)

        # logit weights
        m = max(utilities) if utilities else 0.0
        weights = [math.exp(beta * (u - m)) + eps for u in utilities]

        chosen = random.choices(pool, weights=weights, k=1)[0]
        return chosen

    def _pick_weighted_by_apr(self, pool):
        # Ensure positive weights even if APR is 0
        eps = 1e-12
        weights = [(max(v.apr, 0.0) + eps) ** self.aggressiveness for v in pool]
        return random.choices(pool, weights=weights, k=1)[0]