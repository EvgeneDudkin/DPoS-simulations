class Block:
    def __init__(self, content, proposer, committee):
        self.content = content
        self.signers = []
        self.proposer = proposer
        self.committee = committee

    def isValid(self):
        return True

    def isConfirmed(self , validators, selectedVoters):
        totalVotingPower = sum(v.votingPower for v in validators)
        selectedVotingPower = sum(sv.votingPower for sv in selectedVoters)
        if (selectedVotingPower/totalVotingPower) > (2 / 3):
            return True
        return False