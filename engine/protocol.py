from model.committee import Committee
from engine.metrics import Metrics

class Protocol:
    def __init__(self, committee_size, world, rounds, migration_delay_rounds, rounds_per_year, update_delegation_warm_up_rounds, verbose):
        self.committee_size = committee_size
        self.world = world
        self.rounds = rounds
        self.migration_delay_rounds = migration_delay_rounds
        self.metrics = Metrics(print_frequency=1000)
        self.rounds_per_year = rounds_per_year
        self.update_delegation_warm_up_rounds = update_delegation_warm_up_rounds
        self.verbose = verbose

    def select_committee(self):
        committee = Committee(self.committee_size, self.world.setup)
        self.world.setup.select_committee(committee, self.world.validators)
        return committee

    def calculate_rewards(self, committee):
        self.world.setup.distribute_rewards(
            committee,
            reward_amount=self.world.reward)

    def update_delegations(self):
        pool = self.world.pools()
        for delegator in self.world.delegators:
            # If already waiting to migrate, skip decisions — O(1) set lookup
            if id(delegator) in self.world._pending_delegator_set:
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

            # Update uptime score for every validator every round, regardless of
            # block confirmation. signed=True iff the validator's signature was
            # included in the proposer's selected_voters set. Under a vote-omission
            # attack the victim is excluded here even though it voted → score drops.
            signed_ids = {id(v) for v in committee.selected_voters}
            for v in self.world.validators:
                v.update_uptime(id(v) in signed_ids)

            if new_block is not None:
                self.world.blockchain.append(new_block)
                self.metrics.on_block_confirmed()

                self.calculate_rewards(committee)
                self.metrics.on_rewards_distributed(self.world.reward)

                for v in self.world.validators:
                    v.update_apr(self.rounds_per_year)

            self.metrics.report_if_needed(self.world, i, self.verbose)