import random
from abc import ABC, abstractmethod

class Setup(ABC):
    def __init__(self):
        self.bonus = 0
        self.variational = False

    def chooseProposer(self, validators):
        # shared logic
        return random.choice(validators)

    def selectCommittee(self, committee, pool):
        # template method
        selected = self.select_validators(pool, committee.size)

        for validator in selected:
            committee.validators.append(validator)
            validator.count += 1

    @abstractmethod
    def select_validators(self, pool, size):
        """
        Must return a list of `size` validators
        """
        pass