import random
from setups.base_setup import Setup

class RandomSelect(Setup):
    def __init__(self):
        super().__init__()
        self.bonus = 0
        self.variational = False

    def select_validators(self, pool, size):
        weights = [validator.voting_power for validator in pool]
        selected = set()

        while len(selected) < size:
            chosen = random.choices(pool, weights=weights)[0]
            selected.add(chosen)

        return list(selected)