from abc import ABC, abstractmethod
import random

class CommitteeSelector(ABC):
    @abstractmethod
    def select(self, validators, size):
        """return list of validators"""
        pass

class AllValidatorsSelector(CommitteeSelector):
    def select(self, validators, size):
        return list(validators)

class WeightedRandomCommitteeSelector(CommitteeSelector):
    def select(self, validators, size):
        size = min(size, len(validators))
        chosen = set()
        weights = [v.voting_power for v in validators]
        while len(chosen) < size:
            chosen.add(random.choices(validators, weights=weights, k=1)[0])
        return list(chosen)