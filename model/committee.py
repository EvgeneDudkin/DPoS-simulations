class Committee:
    def __init__(self, size, setup):
        self.size = size
        self.validators = []
        self.votes = {}
        self.proposer = None
        self.selectedVoters = []
        self.setup = setup

    def choose_proposer(self):
        self.proposer = self.setup.choose_proposer(self.validators)

    # def total_voters_voting_power(self):
    #     total = sum(v.voting_power for v in self.selectedVoters)
    #     return total
    #
    # def total_committee_voting_power(self):
    #     total = sum(v.voting_power for v in self.validators)
    #     return total

    # def calculate_rewards(self, reward):
    #     bonus = self.setup.bonus * reward
    #     reward = reward - bonus
    #     total = self.total_voters_voting_power()
    #     total_committee = self.total_committee_voting_power()
    #     for validator in self.selectedVoters:
    #         share = (validator.voting_power / total) * reward
    #         if validator == self.proposer:
    #             if self.setup.variational:
    #                 bonus = ((total - ((2/3)*total_committee)) / ((1/3)*total_committee))*bonus
    #                 share += bonus
    #             else:
    #                 share += bonus
    #         validator.update_reward(self.validators, share, reward)

    def round(self):
        self.choose_proposer()
        new_block = self.proposer.propose(self)
        for v in self.validators:
             self.votes[v] = v.sign(new_block)
        self.selectedVoters = self.proposer.select_voters(self.votes)
        if new_block.is_confirmed(self.validators, self.selectedVoters):
            return new_block
        else:
            print ("Invalid")
            return None