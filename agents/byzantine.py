from agents.validator import Validator

class Byzantine (Validator):
    def __init__(self, id , stake, apr_window, victims, vote_omission_attack_on, vote_delay_attack_on):
        super().__init__(id , stake, apr_window=apr_window)
        self.victims = victims
        self.vote_omission_attack_on = vote_omission_attack_on
        self.vote_delay_attack_on = vote_delay_attack_on
        pass

    def select_voters(self, votes):
        if not self.vote_omission_attack_on:
            return super().select_voters(votes)
        voters = []
        for voter in votes:
            if voter not in self.victims:
                if votes[voter]:
                    voters.append(voter)
        return voters

    def vote_for_leader(self, leader):
        if not self.vote_delay_attack_on:
            return super().vote_for_leader(leader)

        return leader not in self.victims