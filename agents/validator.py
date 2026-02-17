import random
from model.block import Block
from collections import deque

class Validator:
    def __init__ (self , id , stake, apr_window, is_pool=False, commission_rate=0.0):
        self.id = id
        self.stake = stake
        self.is_pool = is_pool
        self.commission_rate = commission_rate # for pools functionality
        self.proposed_blocks = []
        self.delegators = {}
        self.voting_power = self.stake
        self.score = 1000 # Validator score indicates chances of being selected by a delegator. Default everyone is 1000.
        self.count = 0 # Number of times the validator was in the committee
        self.dcount = 0 # total number of delegators
        # rewards
        self.overall_rewards = 0 # reward for all voting power
        self.total_reward = 0
        self._apr_window = apr_window
        self._rewards_window  = deque(maxlen=apr_window)
        self._vp_window  = deque(maxlen=apr_window)
        self._last_overall_rewards = 0.0
        self.apr = 0.0

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

    def update_reward(self, reward, total_reward):
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
        # delta rewards since last time we updated APR
        delta = self.overall_rewards - self._last_overall_rewards
        self._last_overall_rewards = self.overall_rewards

        self._rewards_window.append(delta)
        self._vp_window.append(self.voting_power)

        if len(self._vp_window) == 0:
            self.apr = 0.0
            return self.apr

        avg_vp = sum(self._vp_window) / len(self._vp_window)
        if avg_vp <= 0:
            self.apr = 0.0
            return self.apr

        window_rewards = sum(self._rewards_window)
        window_rounds = len(self._rewards_window)

        # annualize per-round return
        self.apr = (window_rewards / avg_vp) * (rounds_per_year / window_rounds)
        return self.apr

    def vote_for_leader(self, leader):
        return True