from model.committee import Committee

class Protocol:
    def __init__(self, committeeSize, validators, delegators, rounds, setup, reward):
        self.committeeSize = committeeSize
        self.validators = validators
        self.delegators = delegators
        self.rounds = rounds
        self.blockchain = []
        self.setup = setup
        self.reward = reward

    def selectCommittee(self):
        committee = Committee(self.committeeSize, self.setup)
        self.setup.selectCommittee(committee, self.validators)
        return committee

    def calculateRewards(self, committee):
        committee.calculateRewards(self.reward)

    def calculateValidatorsScores(self):
        #total = 0
        #for validator in self.validators:
            #total+= validator.totalReward
        total_rewards = sum(validator.totalReward for validator in self.validators)
        total_stake = sum(validator.votingPower for validator in self.validators)
        for validator in self.validators:
            if validator.count == 0:
                validator.score = 10000000
            else:
                validator.score = ((validator.totalReward / total_rewards) / (validator.votingPower * validator.count)) * 10000000

    def updateDelegations(self):
        for delegator in self.delegators:
            old = delegator.boundedValidator
            new = delegator.chooseValidator(self.validators)
            # if unchanged, do nothing
            if new == old:
                continue

            # apply transition centrally
            if old is not None:
                old.removeDelegator(delegator)

            if new is not None:
                delegator.boundedValidator = new
                new.addDelegator(delegator)

    def run(self):
        #committee = self.selectCommittee()
        #self.updateDelegations(committee)
        for i in range(self.rounds):
            print(i)
            self.updateDelegations()
            committee = self.selectCommittee()
            newBlock = committee.round()
            if newBlock is not None:
                self.blockchain.append(newBlock)
                self.calculateRewards(committee)
                self.calculateValidatorsScores()