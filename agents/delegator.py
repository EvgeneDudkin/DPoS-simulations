import random

class Delegator:
    def __init__ (self , id , stake, aggressiveness = 1, loyalty = 0):
        self.id = id
        self.stake = stake
        self.bounded_validator = None
        self.total_reward = 0
        self.aggressiveness = aggressiveness #Describes how aggressive delegators are in terms of selecting the best validator.
        self.loyalty = loyalty #Describes delegators loyalty. Should be between 0 and 1. Bigger loyalty indicates that the delegator changes the validator less often.

    # def delegate_to(self, validator):
    #     self.bounded_validator = validator
    #     validator.add_delegator(self)

    def expected_earning(self, pool, reward):
        total_voting_power = sum(v.voting_power for v in pool)
        validator_share = (self.bounded_validator.voting_power / total_voting_power) * reward
        delegator_share = (self.stake / self.bounded_validator.voting_power) * validator_share
        return delegator_share

    def choose_validator(self, pool):
        changing_chance = random.randint(1, 100)
        if changing_chance <= (self.loyalty * 100):
            return self.bounded_validator  # stay

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

    def update_reward(self, pool, reward, total_reward):
        self.total_reward += reward