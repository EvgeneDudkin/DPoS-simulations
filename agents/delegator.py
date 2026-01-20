import random

class Delegator:
    def __init__ (self , id , stake, aggressiveness = 1, loyalty = 0):
        self.id = id
        self.stake = stake
        self.boundedValidator = None
        self.totalReward = 0
        self.aggressiveness = aggressiveness #Describes how aggressive delegators are in terms of selecting the best validator.
        self.loyalty = loyalty #Describes delegators loyalty. Should be between 0 and 1. Bigger loyalty indicates that the delegator changes the validator less often.

    def delegateTo(self, validator):
        self.boundedValidator = validator

    def expectedEarning(self, pool, reward):
        totalVotingPower = sum(v.votingPower for v in pool)
        validatorShare = (self.boundedValidator.votingPower / totalVotingPower) * reward
        delegatorShare = (self.stake/self.boundedValidator.votingPower) * validatorShare
        return delegatorShare

    def chooseValidator(self, pool):
        changingChance = random.randint(1, 100)
        if changingChance <= (self.loyalty * 100):
            return self.boundedValidator  # stay

        weights = [validator.score ** self.aggressiveness for validator in pool]
        return random.choices(pool, weights=weights)[0]

    # def changeValidator(self, pool):
    #     changingChance = random.randint(1, 100)
    #     if changingChance <= (self.loyalty * 100):
    #         return
    #     if self.boundedValidator is not None:
    #         self.boundedValidator.removeDelegator(self)
    #     weights = [validator.score**self.aggressiveness for validator in pool]
    #     validator = random.choices(pool, weights=weights)[0]
    #     self.boundedValidator = validator
    #     self.boundedValidator.addDelegator(self)

    def updateReward(self, pool, reward, totalReward):
        self.totalReward += reward