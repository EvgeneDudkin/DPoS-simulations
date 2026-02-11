class Setup:
    def __init__(self, committee_selector, proposer_selector, vote_policy, reward_policy, pool_commission_rate=0.0):
        self.committee_selector = committee_selector
        self.proposer_selector = proposer_selector
        self.vote_policy = vote_policy
        self.reward_policy = reward_policy
        self.pool_commission_rate = pool_commission_rate

    def select_committee(self, committee, validators):
        committee.validators = self.committee_selector.select(validators, committee.size)
        for v in committee.validators:
            v.count += 1

    def choose_proposer(self, committee):
        committee.proposer = self.proposer_selector.choose(committee.validators)

    def get_voters(self, committee, block):
        return self.vote_policy.decide_voters(committee, block)

    def distribute_rewards(self, committee, reward_amount):
        self.reward_policy.distribute(committee, reward_amount)