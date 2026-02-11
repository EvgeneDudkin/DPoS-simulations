from model.committee import Committee
from engine.metrics import Metrics

class Protocol:
    def __init__(self, committee_size, world, rounds, migration_delay_rounds, rounds_per_year, update_delegation_warm_up_rounds):
        self.committee_size = committee_size
        self.world = world
        self.rounds = rounds
        self.migration_delay_rounds = migration_delay_rounds
        self.metrics = Metrics(print_frequency=1000)
        self.rounds_per_year = rounds_per_year
        self.update_delegation_warm_up_rounds = update_delegation_warm_up_rounds

    def select_committee(self):
        committee = Committee(self.committee_size, self.world.setup)
        self.world.setup.select_committee(committee, self.world.validators)
        return committee

    def calculate_rewards(self, committee):
        self.world.setup.distribute_rewards(
            committee,
            reward_amount=self.world.reward)

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
        pool = self.world.pools()
        for delegator in self.world.delegators:
            # If already waiting to migrate, skip decisions
            if any(m["delegator"] == delegator for m in self.world.pending_migrations):
                continue

            old = delegator.bounded_validator
            new = delegator.choose_validator_by_apr(pool)

            # if unchanged, do nothing
            if new == old:
                continue

            execute_round = self.world.round_index + self.migration_delay_rounds
            self.world.schedule_migration(delegator, old, new, execute_round)

    def run(self):
        #committee = self.selectCommittee()
        #self.updateDelegations(committee)
        for i in range(self.rounds):
            self.world.round_index = i
            self.metrics.on_round_start()

            executed = self.world.process_migrations(i)  # execute scheduled moves
            self.metrics.on_migrations_executed(executed)

            if self.world.round_index > self.update_delegation_warm_up_rounds: # need to wait some time
                self.update_delegations() # schedule new moves (not apply instantly)

            committee = self.select_committee()
            self.metrics.on_block_attempt()
            new_block = committee.round()
            if new_block is not None:
                self.world.blockchain.append(new_block)
                self.metrics.on_block_confirmed()

                self.calculate_rewards(committee)
                self.metrics.on_rewards_distributed(self.world.reward)

                for v in self.world.validators:
                    v.update_apr(self.rounds_per_year)

                self.calculate_validators_scores()

            self.metrics.report_if_needed(self.world, i)