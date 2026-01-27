class Block:
    def __init__(self, content, proposer, committee):
        self.content = content
        self.signers = []
        self.proposer = proposer
        self.committee = committee

    def is_valid(self):
        return True

    def is_confirmed(self, validators, selected_voters):
        total_voting_power = sum(v.voting_power for v in validators)
        selected_voting_power = sum(sv.voting_power for sv in selected_voters)
        if (selected_voting_power/total_voting_power) > (2 / 3):
            return True
        return False