from abc import ABC, abstractmethod
import random

class VotePolicy(ABC):
    @abstractmethod
    def decide_voters(self, committee, block):
        """return list of validators that are YES and included in 'vote power'"""
        pass

class ProbabilisticYesVotes(VotePolicy):
    def __init__(self, online_p=0.98, vote_p=0.995):
        self.online_p = online_p
        self.vote_p = vote_p

    def decide_voters(self, committee, block):
        yes = [committee.proposer] # leader is always included
        for v in committee.validators:
            if committee.proposer == v:
                continue
            if not v.vote_for_leader(committee.proposer):
                continue
            if random.random() > self.online_p:
                continue  # offline
            if random.random() <= self.vote_p:
                yes.append(v)  # vote for block
        return yes