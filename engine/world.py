class World:
    def __init__(self, validators, delegators, setup, reward):
        self.validators = validators
        self.delegators = delegators
        self.setup = setup
        self.reward = reward

        self.blockchain = []
        self.round_index = 0
        self.pending_migrations = []  # list of dicts

    def pools(self):
        """Validators that are eligible to receive delegations."""
        return [v for v in self.validators if v.is_pool]

    def schedule_migration(self, delegator, from_validator, to_validator, execute_round):
        self.pending_migrations.append({
            "delegator": delegator,
            "from": from_validator,
            "to": to_validator,
            "execute_round": execute_round
        })

    def process_migrations(self, current_round):
        """
        Execute all migrations whose time has come.
        Model: delegator stays with old validator until execution time.
        """
        executed = [] # list of (old_validator, new_validator)
        remaining = []
        for m in self.pending_migrations:
            if m["execute_round"] <= current_round:
                d = m["delegator"]
                old = m["from"]
                new = m["to"]

                if d.bounded_validator != old:
                    continue  # unexpected behavior

                # apply transition centrally
                if old is not None:
                    old.remove_delegator(d)

                if new is not None:
                    d.bounded_validator = new
                    new.add_delegator(d)

                executed.append((old, new))
            else:
                remaining.append(m)

        self.pending_migrations = remaining
        return executed
