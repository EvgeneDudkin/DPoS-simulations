from model.committee import Committee
from engine.rewards import distribute_committee_rewards

class Protocol:
    def __init__(self, committee_size, world, rounds):
        self.committee_size = committee_size
        self.world = world
        self.rounds = rounds

    def select_committee(self):
        committee = Committee(self.committee_size, self.world.setup)
        self.world.setup.select_committee(committee, self.world.validators)
        return committee

    def calculate_rewards(self, committee):
        distribute_committee_rewards(committee, self.world.reward)

    def calculate_validators_scores(self):
        #total = 0
        #for validator in self.validators:
            #total+= validator.totalReward
        total_rewards = sum(validator.total_reward for validator in self.world.validators)
        total_stake = sum(validator.voting_power for validator in self.world.validators)
        for validator in self.world.validators:
            if validator.count == 0:
                validator.score = 10000000
            else:
                validator.score = ((validator.total_reward / total_rewards) / (validator.voting_power * validator.count)) * 10000000

    def update_delegations(self):
        for delegator in self.world.delegators:
            old = delegator.bounded_validator
            pool = self.world.pools()
            new = delegator.choose_validator(pool)
            # if unchanged, do nothing
            if new == old:
                continue

            # apply transition centrally
            if old is not None:
                old.remove_delegator(delegator)

            if new is not None:
                delegator.bounded_validator = new
                new.add_delegator(delegator)

    def run(self):
        #committee = self.selectCommittee()
        #self.updateDelegations(committee)
        for i in range(self.rounds):
            print(i)
            self.world.round_index = i
            self.update_delegations()
            committee = self.select_committee()
            new_block = committee.round()
            if new_block is not None:
                self.world.blockchain.append(new_block)
                self.calculate_rewards(committee)
                self.calculate_validators_scores()