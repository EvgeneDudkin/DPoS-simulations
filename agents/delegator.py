import random

class Delegator:
    def __init__ (self , id , stake, aggressiveness = 1, loyalty = 0, apr_gap_threshold = 0.0035):
        self.id = id
        self.stake = stake
        self.bounded_validator = None
        self.total_reward = 0
        self.aggressiveness = aggressiveness #Describes how aggressive delegators are in terms of selecting the best validator.
        self.loyalty = loyalty #Describes delegators loyalty. Should be between 0 and 1. Bigger loyalty indicates that the delegator changes the validator less often.
        self.apr_gap_threshold = apr_gap_threshold

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
            return self._pick_weighted_by_apr(pool)

        current = self.bounded_validator
        current_apr = current.apr

        # Find the best APR pool
        best = max(pool, key=lambda v: v.apr)
        best_apr = best.apr

        # Only consider switching if improvement is meaningful
        if (best_apr - current_apr) <= self.apr_gap_threshold:
            return current

        # Inertia: not everyone switches immediately
        if random.random() < self.loyalty:
            return current

        # Switch, but not always deterministically to the best
        return self._pick_weighted_by_apr(pool)

    def _pick_weighted_by_apr(self, pool):
        # Ensure positive weights even if APR is 0
        eps = 1e-12
        weights = [(max(v.apr, 0.0) + eps) ** self.aggressiveness for v in pool]
        return random.choices(pool, weights=weights, k=1)[0]