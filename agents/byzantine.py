from agents.validator import Validator

class Byzantine (Validator):
    def __init__(self, id , stake, victims, omission):
        super().__init__(id , stake)
        self.victims = victims
        self.omission = omission
        pass

    def selectVoters(self, votes):
        if not self.omission:
            return super().selectVoters(votes)
        voters = []
        for voter in votes:
            if voter not in self.victims:
                if votes[voter]:
                    voters.append(voter)
        return voters