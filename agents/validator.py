import random
from model.block import Block

class Validator:
    def __init__ (self , id , stake):
        self.id = id
        self.stake = stake
        self.proposedBlocks = []
        self.delegators = {}
        self.votingPower = self.stake
        self.totalReward = 0
        self.score = 1000 # Validator score indicates chances of being selected by a delegator. Default everyone is 1000.
        self.count = 0 # Number of times the validator was in the committee
        self.dcount = 0 # total number of delegators
        self.overallRewards = 0 # reward for all voting power

    def propose(self, committee):
        r = random.randint(0, 100)
        b = Block(r, self, committee)
        self.proposedBlocks.append(b)
        return b

    def sign(self , block):
        if block.isValid():
            return True
        return False

    def selectVoters(self, votes):
        voters = []
        for voter in votes:
            if votes[voter]:
                voters.append(voter)
        return voters

    def removeDelegator(self, delegator):
        self.delegators[delegator] = 0
        self.votingPower -= delegator.stake

    def addDelegator(self, delegator):
        self.delegators[delegator] = delegator.stake
        self.votingPower += delegator.stake
        self.dcount += 1

    def updateReward(self, pool, reward, totalReward):
        self.overallRewards += reward
        self.totalReward += (self.stake / self.votingPower) * reward
        for delegator in self.delegators:
            if self.delegators[delegator] > 0:
                share = (delegator.stake/self.votingPower) * reward
                delegator.updateReward(pool, share, totalReward)