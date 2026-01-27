import random
from model.block import Block

class Validator:
    def __init__ (self , id , stake, is_pool=False):
        self.id = id
        self.stake = stake
        self.is_pool = is_pool
        self.proposed_blocks = []
        self.delegators = {}
        self.voting_power = self.stake
        self.total_reward = 0
        self.score = 1000 # Validator score indicates chances of being selected by a delegator. Default everyone is 1000.
        self.count = 0 # Number of times the validator was in the committee
        self.dcount = 0 # total number of delegators
        self.overall_rewards = 0 # reward for all voting power

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

    def update_reward(self, pool, reward, total_reward):
        self.overall_rewards += reward
        self.total_reward += (self.stake / self.voting_power) * reward
        for delegator in self.delegators:
            if self.delegators[delegator] > 0:
                share = (delegator.stake / self.voting_power) * reward
                delegator.update_reward(pool, share, total_reward)