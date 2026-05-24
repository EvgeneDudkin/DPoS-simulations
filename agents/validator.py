import random
from model.block import Block
# from collections import deque

class Validator:
    def __init__ (self , id , stake, apr_window, is_pool=False, commission_rate=0.0):
        self.id = id
        self.stake = stake
        self.is_pool = is_pool
        self.commission_rate = commission_rate # for pools functionality
        self.proposed_blocks = []
        self.delegators = {}
        self.voting_power = self.stake
        self.count = 0 # Number of times the validator was in the committee
        self.dcount = 0 # total number of delegators
        # rewards
        self.overall_rewards = 0 # reward for all voting power
        self.total_reward = 0
        self._apr_window = apr_window
        self._alpha_ema = 2.0 / (apr_window + 1.0)   # precomputed once; shared by APR and uptime EMA
        self._last_overall_rewards = 0.0
        self.apr = 0.0             # gross APR (before commission deduction)
        self.delegator_apr = 0.0   # net APR that delegators actually earn (after commission)
        self._ema_return = 0.0
        # reliability / uptime score: EMA participation rate in [0, 1].
        # Tracks fraction of rounds where this validator's signature was included
        # in the confirmed selected_voters set. 1.0 = fully reliable, 0.0 = always offline.
        # Starts at 1.0 to give validators benefit-of-the-doubt during warm-up.
        self.score = 1.0
        self._ema_uptime = 1.0

    def propose(self, committee):
        r = random.randint(0, 100)
        b = Block(r, self, committee)
        self.proposed_blocks.append(b)
        return b

    def sign(self , block):
        if block.is_valid():
            return True
        return False

    def select_voters(self, votes):
        voters = []
        for voter in votes:
            if votes[voter]:
                voters.append(voter)
        return voters

    def remove_delegator(self, delegator):
        self.delegators[delegator] = 0
        self.voting_power -= delegator.stake
        self.dcount -= 1

    def add_delegator(self, delegator):
        if not self.is_pool:
            raise ValueError(f"Validator {self.id} is not a pool and cannot accept delegations.")

        self.delegators[delegator] = delegator.stake
        self.voting_power += delegator.stake
        self.dcount += 1

    def update_reward(self, reward):
        self.overall_rewards += reward

        # in case of pool -> + commission
        if self.is_pool and self.commission_rate > 0:
            commission = reward * self.commission_rate
            self.total_reward += commission
            distributable = reward - commission
        else:
            distributable = reward

        operator_staker_share = distributable * (self.stake / self.voting_power)
        self.total_reward += operator_staker_share

        for delegator in self.delegators:
            if self.delegators[delegator] > 0:
                share = (delegator.stake / self.voting_power) * distributable
                delegator.update_reward(share)

    def update_apr(self, rounds_per_year):
        """
        EMA-smoothed APR over a rolling window of apr_window rounds.

        APR validation notes (real-world alignment):
        - `delta / vp` is the per-round gross return per unit of voting power,
          equivalent to what on-chain staking dashboards compute:
          (rewards_in_window / total_stake) * (rounds_per_year / window_rounds).
        - EMA with alpha = 2/(window+1) gives a half-life of ~window/2 rounds,
          appropriate for a 7-day smoothing window (apr_window=1575 Ethereum epochs).
        - `delegator_apr` subtracts the commission taken by the pool operator,
          matching what real liquid-staking platforms (Lido, Cosmos validators)
          display to delegators. Delegators use this signal, not the gross APR.
        """
        delta = self.overall_rewards - self._last_overall_rewards
        self._last_overall_rewards = self.overall_rewards

        vp = self.voting_power
        if vp <= 0:
            self.apr = 0.0
            self.delegator_apr = 0.0
            return self.apr

        r = delta / vp                                    # gross per-round return per VP unit
        self._ema_return = (1.0 - self._alpha_ema) * self._ema_return + self._alpha_ema * r

        self.apr = self._ema_return * rounds_per_year     # gross annualized APR
        self.delegator_apr = self.apr * (1.0 - self.commission_rate)  # net APR delegators compare
        return self.apr

    def update_uptime(self, signed: bool):
        """
        EMA update of participation rate (reliability score).

        Called every round with signed=True when this validator's signature was
        included in committee.selected_voters, False otherwise.

        Uses the same EMA window as APR for consistency. Equivalent to the
        uptime metric tracked by real DPoS networks (e.g., Cosmos slashing module
        tracks signed-blocks / total-blocks over a sliding window and jails
        validators whose uptime drops below 5%).

        score ∈ [0, 1]:  1.0 = always participates, 0.0 = never participates.
        Under a vote-omission attack the victim's score drops because the Byzantine
        proposer excludes its signature — the same observable effect delegators see
        when monitoring block explorers.
        """
        self._ema_uptime = (1.0 - self._alpha_ema) * self._ema_uptime + self._alpha_ema * (1.0 if signed else 0.0)
        self.score = self._ema_uptime


    def vote_for_leader(self, leader):
        return True