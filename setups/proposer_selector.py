from abc import ABC, abstractmethod
import random

class ProposerSelector(ABC):
    @abstractmethod
    def choose(self, committee_validators):
        pass

class WeightedProposerSelector(ProposerSelector):
    def choose(self, committee_validators):
        weights = [v.voting_power for v in committee_validators]
        return random.choices(committee_validators, weights=weights, k=1)[0]