class Committee:
    def __init__(self, size, setup):
        self.size = size
        self.validators = []
        self.votes = {}
        self.proposer = None
        self.selectedVoters = []
        self.setup = setup

    def chooseProposer(self):
        self.proposer = self.setup.chooseProposer(self.validators)

    def totalVotersVotingPower(self):
        total = sum(v.votingPower for v in self.selectedVoters)
        return total

    def totalCommitteeVotingPower(self):
        total = sum(v.votingPower for v in self.validators)
        return total

    def calculateRewards(self, reward):
        bonus = self.setup.bonus * reward
        reward = reward - bonus
        total = self.totalVotersVotingPower()
        totalCommittee = self.totalCommitteeVotingPower()
        for validator in self.selectedVoters:
            share = (validator.votingPower / total) * reward
            if validator == self.proposer:
                if self.setup.variational:
                    bonus = ((total - ((2/3)*totalCommittee)) / ((1/3)*totalCommittee))*bonus
                    share += bonus
                else:
                    share += bonus
            validator.updateReward(self.validators, share, reward)

    def round(self):
        self.chooseProposer()
        newBlock = self.proposer.propose(self)
        for v in self.validators:
             self.votes[v] = v.sign(newBlock)
        self.selectedVoters = self.proposer.selectVoters(self.votes)
        if newBlock.isConfirmed(self.validators, self.selectedVoters):
            return newBlock
        else:
            print ("Invalid")
            return None